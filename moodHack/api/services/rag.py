"""Retrieval over the seeded knowledge base (mood resources + articles).

Uses lightweight lexical scoring (term-frequency overlap) which is sufficient
for the seed corpus size and avoids a native vector-store dependency in SQLite.
"""
import math
import re
from collections import Counter
from typing import Any

from api.models import Article, MoodResource

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
    "have", "how", "i", "in", "is", "it", "its", "me", "my", "of", "on",
    "or", "our", "the", "this", "that", "to", "was", "we", "what", "when",
    "where", "which", "with", "you", "your", "do", "does", "can", "should",
    "some", "about", "into", "not", "if", "than", "then", "there", "they",
    "am", "feeling", "feel", "mood", "moods", "help", "please", "suggest",
    "suggestion", "suggestions",
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return [
        token
        for token in _TOKEN_RE.findall(text.lower())
        if token not in _STOPWORDS and len(token) > 1
    ]


def _score(query_terms: Counter, doc_text: str) -> float:
    doc_terms = Counter(_tokenize(doc_text))
    if not doc_terms:
        return 0.0
    score = 0.0
    for term, q_count in query_terms.items():
        if term in doc_terms:
            tf = doc_terms[term]
            score += q_count * (1 + math.log(tf))
    return score


def _mood_to_doc(mood: MoodResource) -> dict[str, Any]:
    return {
        "type": "mood",
        "mood": mood.mood,
        "primary_emotion": mood.primary_emotion,
        "description": mood.description,
        "coping_mechanisms": mood.coping_mechanisms,
        "music_suggestions": mood.music_suggestions,
        "resource_links": mood.resource_links,
    }


def _article_to_doc(article: Article) -> dict[str, Any]:
    return {
        "type": "article",
        "title": article.title,
        "url": article.url,
        "description": article.description,
        "topics": article.topics,
        "source": article.source,
    }


def search_knowledge_base(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Return the top-k matching mood resources and articles for a query."""
    query_terms = Counter(_tokenize(query))
    if not query_terms:
        return []

    scored: list[tuple[float, dict[str, Any]]] = []

    for mood in MoodResource.objects.all():
        text = " ".join(
            [
                mood.mood,
                mood.primary_emotion,
                mood.description,
                " ".join(mood.coping_mechanisms or []),
                " ".join(mood.music_suggestions or []),
                " ".join(mood.keywords or []),
            ]
        )
        score = _score(query_terms, text)
        if score > 0:
            scored.append((score, _mood_to_doc(mood)))

    for article in Article.objects.all():
        text = " ".join(
            [
                article.title,
                article.description,
                " ".join(article.topics or []),
            ]
        )
        score = _score(query_terms, text)
        if score > 0:
            scored.append((score, _article_to_doc(article)))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]


def get_mood_resource(mood: str) -> dict[str, Any] | None:
    """Fetch a single mood resource by name (case-insensitive)."""
    try:
        resource = MoodResource.objects.get(mood__iexact=mood.strip())
    except MoodResource.DoesNotExist:
        return None
    return _mood_to_doc(resource)


def suggest_articles(topic: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Return top-k articles matching a topic."""
    query_terms = Counter(_tokenize(topic))
    if not query_terms:
        return []

    scored: list[tuple[float, dict[str, Any]]] = []
    for article in Article.objects.all():
        text = " ".join(
            [
                article.title,
                article.description,
                " ".join(article.topics or []),
            ]
        )
        score = _score(query_terms, text)
        if score > 0:
            scored.append((score, _article_to_doc(article)))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]
