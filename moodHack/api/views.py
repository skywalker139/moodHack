"""JSON API views for moodHack.

All endpoints live under /api/. The frontend is served as static files, so the
JSON API is CSRF-exempt (there is no session cookie in play). This is a dev
posture; a real deployment should serve the SPA through Django and keep CSRF.
"""
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Article, ChatMessage, ChatSession, MoodJournal
from .services.agent import Agent
from .services import rag


def _body(request) -> dict:
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return {}


def _error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"error": message}, status=status)


def index(request):
    from django.shortcuts import render

    return render(request, "index.html")


@csrf_exempt
@require_POST
def chat(request):
    body = _body(request)
    message = (body.get("message") or "").strip()
    if not message:
        return _error("`message` is required.")

    session_id = body.get("session_id")
    session = None
    if session_id:
        try:
            session = ChatSession.objects.get(session_id=session_id)
        except (ChatSession.DoesNotExist, ValueError):
            session = None

    if session is None:
        session = ChatSession.objects.create()
        if session_id:
            # Preserve the client-provided id when valid-looking, otherwise
            # the model has its own generated id and we use that.
            pass

    # Persist the user message.
    ChatMessage.objects.create(session=session, role="user", content=message)

    # Build history for the agent (last N turns, excluding the just-saved user
    # message which is passed as the current prompt).
    history_qs = ChatMessage.objects.filter(session=session).order_by("created_at")
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in history_qs
        if msg.role in ("user", "assistant")
    ]
    # Drop the trailing user message we just appended; the agent gets it fresh.
    if history and history[-1]["role"] == "user" and history[-1]["content"] == message:
        history.pop()

    agent = Agent()
    result = agent.run(message, history=history)

    ChatMessage.objects.create(
        session=session,
        role="assistant",
        content=result.reply,
        tool_calls=result.tool_activity,
        articles=result.articles,
    )

    return JsonResponse(
        {
            "session_id": str(session.session_id),
            "reply": result.reply,
            "tool_calls": result.tool_activity,
            "articles": result.articles,
        }
    )


@csrf_exempt
@require_POST
def mood(request):
    body = _body(request)
    mood_name = (body.get("mood") or "").strip()
    if not mood_name:
        return _error("`mood` is required.")

    resource = rag.get_mood_resource(mood_name)
    if resource is None:
        return JsonResponse(
            {
                "mood": mood_name,
                "found": False,
                "results": [],
                "message": "No coping data found for this mood yet.",
            }
        )

    articles = rag.suggest_articles(mood_name, top_k=3)
    return JsonResponse(
        {
            "mood": mood_name,
            "found": True,
            "results": [resource],
            "articles": articles,
        }
    )


@require_GET
def articles(request):
    articles_qs = Article.objects.all()
    return JsonResponse(
        {
            "articles": [
                {
                    "title": a.title,
                    "url": a.url,
                    "description": a.description,
                    "topics": a.topics,
                    "source": a.source,
                }
                for a in articles_qs
            ]
        }
    )


@csrf_exempt
@require_POST
def refresh_articles(request):
    """Trigger the optional article scraper, if enabled."""
    from django.core.management import call_command

    try:
        call_command("scrape_articles")
        added = Article.objects.count()
    except Exception as exc:  # noqa: BLE001
        return JsonResponse(
            {"status": "error", "message": f"Scraper failed: {exc}"}, status=500
        )
    return JsonResponse({"status": "success", "article_count": added})


@csrf_exempt
@require_POST
def journal(request):
    body = _body(request)
    mood_name = (body.get("mood") or "").strip()
    note = (body.get("note") or "").strip()
    if not mood_name:
        return _error("`mood` is required.")

    entry = MoodJournal.objects.create(mood=mood_name, note=note)
    return JsonResponse(
        {
            "saved": True,
            "mood": entry.mood,
            "note": entry.note,
            "created_at": entry.created_at.isoformat(),
        }
    )


@require_GET
def history(request):
    session_id = request.GET.get("session_id")
    if not session_id:
        return _error("`session_id` query parameter is required.")

    try:
        session = ChatSession.objects.get(session_id=session_id)
    except (ChatSession.DoesNotExist, ValueError):
        return JsonResponse({"session_id": session_id, "messages": []})

    messages = [
        {
            "role": msg.role,
            "content": msg.content,
            "tool_calls": msg.tool_calls,
            "articles": msg.articles,
            "created_at": msg.created_at.isoformat(),
        }
        for msg in session.messages.filter(role__in=("user", "assistant"))
    ]
    return JsonResponse({"session_id": session_id, "messages": messages})


@require_GET
def moods(request):
    """Return the full mood taxonomy (primary -> secondary -> tertiary)."""
    from . import seed_data

    taxonomy = []
    for primary in seed_data.PRIMARY_EMOTIONS:
        entry = {
            "primary": primary,
            "secondary": [],
        }
        for secondary in seed_data.MOOD_TAXONOMY.get(primary, []):
            entry["secondary"].append(
                {
                    "mood": secondary,
                    "tertiary": seed_data.TERTIARY_MOODS.get(secondary, []),
                }
            )
        taxonomy.append(entry)

    return JsonResponse({"taxonomy": taxonomy})
