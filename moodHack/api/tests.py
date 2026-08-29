import json

from django.test import TestCase
from django.urls import reverse

from api.models import Article, MoodResource
from api.services.agent import Agent, AgentResult
from api.services.rag import search_knowledge_base


class RAGTests(TestCase):
    def setUp(self):
        MoodResource.objects.create(
            mood="ANXIOUS",
            primary_emotion="FEAR",
            description="Persistent worry and unease.",
            coping_mechanisms=["Breathe slowly.", "Write down worries."],
            music_suggestions=["Weightless - Marconi Union"],
            resource_links=[{"title": "Mind", "url": "https://www.mind.org.uk/"}],
            keywords=["anxiety", "worry", "stress"],
        )
        Article.objects.create(
            title="Anxiety Coping Strategies",
            url="https://example.com/anxiety",
            description="Practical techniques for managing anxiety.",
            topics=["anxiety", "coping"],
            source="Example",
        )

    def test_search_finds_mood_by_keyword(self):
        results = search_knowledge_base("anxiety", top_k=3)
        types = [r["type"] for r in results]
        self.assertIn("mood", types)

    def test_search_finds_article(self):
        results = search_knowledge_base("coping techniques", top_k=3)
        self.assertTrue(any(r["type"] == "article" for r in results))

    def test_search_empty_query_returns_nothing(self):
        self.assertEqual(search_knowledge_base(""), [])


class AgentTests(TestCase):
    class FakeLLM:
        def __init__(self, responses):
            self.responses = list(responses)
            self.calls = []

        def chat(self, messages, tools=None, **kwargs):
            self.calls.append({"messages": messages, "tools": tools})
            return self.responses.pop(0)

    def test_agent_returns_reply_without_tools(self):
        fake = self.FakeLLM(
            [
                {
                    "text": "Take a deep breath.",
                    "tool_calls": [],
                    "usage": {},
                    "finish_reason": "stop",
                }
            ]
        )
        agent = Agent(llm_client=fake)
        result = agent.run("I feel anxious")
        self.assertIsInstance(result, AgentResult)
        self.assertEqual(result.reply, "Take a deep breath.")
        self.assertEqual(result.tool_activity, [])

    def test_agent_executes_tool_call(self):
        fake = self.FakeLLM(
            [
                {
                    "text": "",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "name": "search_knowledge_base",
                            "arguments": json.dumps({"query": "anxiety"}),
                        }
                    ],
                    "usage": {},
                    "finish_reason": "tool_calls",
                },
                {
                    "text": "Here is what I found.",
                    "tool_calls": [],
                    "usage": {},
                    "finish_reason": "stop",
                },
            ]
        )
        agent = Agent(llm_client=fake)
        result = agent.run("How do I cope with anxiety?")
        self.assertEqual(result.reply, "Here is what I found.")
        self.assertEqual(len(result.tool_activity), 1)
        self.assertEqual(result.tool_activity[0]["tool"], "search_knowledge_base")


class APITests(TestCase):
    def test_index_renders_spa(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "moodHack")

    def test_moods_returns_taxonomy(self):
        response = self.client.get(reverse("moods"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("taxonomy", data)
        self.assertTrue(any(e["primary"] == "HAPPY" for e in data["taxonomy"]))

    def test_articles_empty_by_default(self):
        response = self.client.get(reverse("articles"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["articles"], [])

    def test_mood_requires_mood(self):
        response = self.client.post(reverse("mood"), data="{}", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_journal_requires_mood(self):
        response = self.client.post(
            reverse("journal"), data="{}", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
