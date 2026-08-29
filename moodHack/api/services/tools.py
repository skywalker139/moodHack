"""Tool definitions exposed to the agent via function calling.

Each tool has a JSON Schema (for the model) and a Python callable (executed
server-side). Returning plain dicts keeps the agent layer decoupled from the
LLM provider.
"""
import json
from typing import Any, Callable

from . import rag
from api.models import MoodJournal, MoodResource


def _search_knowledge_base(arguments: dict[str, Any]) -> dict[str, Any]:
    query = str(arguments.get("query", ""))
    results = rag.search_knowledge_base(query, top_k=5)
    return {"query": query, "results": results}


def _get_mood_coping(arguments: dict[str, Any]) -> dict[str, Any]:
    mood = str(arguments.get("mood", ""))
    resource = rag.get_mood_resource(mood)
    if resource is None:
        return {"mood": mood, "found": False, "results": []}
    return {"mood": mood, "found": True, "results": [resource]}


def _suggest_articles(arguments: dict[str, Any]) -> dict[str, Any]:
    topic = str(arguments.get("topic", ""))
    results = rag.suggest_articles(topic, top_k=5)
    return {"topic": topic, "results": results}


def _save_mood_journal(arguments: dict[str, Any]) -> dict[str, Any]:
    mood = str(arguments.get("mood", ""))
    note = str(arguments.get("note", ""))
    entry = MoodJournal.objects.create(mood=mood, note=note)
    return {
        "saved": True,
        "mood": entry.mood,
        "note": entry.note,
        "created_at": entry.created_at.isoformat(),
    }


TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search the moodHack knowledge base for coping mechanisms, "
                "mood descriptions, music suggestions, and related articles."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (e.g. 'anxiety coping').",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_mood_coping",
            "description": (
                "Get structured coping mechanisms and music suggestions for a "
                "specific mood (e.g. 'anxious', 'happy', 'lonely')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "mood": {
                        "type": "string",
                        "description": "The mood name to look up.",
                    }
                },
                "required": ["mood"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_articles",
            "description": (
                "Find articles from the moodHack article library on a topic "
                "(e.g. 'anxiety', 'mindfulness', 'depression')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic to find articles about.",
                    }
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_mood_journal",
            "description": (
                "Save a mood journal entry with an optional free-text note."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "mood": {
                        "type": "string",
                        "description": "The mood being journaled.",
                    },
                    "note": {
                        "type": "string",
                        "description": "Optional reflection note.",
                    },
                },
                "required": ["mood"],
            },
        },
    },
]

TOOL_IMPLEMENTATIONS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "search_knowledge_base": _search_knowledge_base,
    "get_mood_coping": _get_mood_coping,
    "suggest_articles": _suggest_articles,
    "save_mood_journal": _save_mood_journal,
}


def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute a tool by name and return its JSON-serializable result."""
    if name not in TOOL_IMPLEMENTATIONS:
        return {"error": f"Unknown tool: {name}"}
    try:
        return TOOL_IMPLEMENTATIONS[name](arguments)
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}
