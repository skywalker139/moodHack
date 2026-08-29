"""ReAct-style agent loop with tool calls.

The agent repeatedly calls the LLM; whenever the model requests a tool call we
execute it server-side and feed the result back, up to MAX_ITERATIONS times.
The final assistant message is returned along with any tool activity and
articles surfaced during the loop.
"""
import json
from typing import Any, Optional

from . import tools
from .llm import LLMClient

MAX_ITERATIONS = 6

SYSTEM_PROMPT = """You are moodHack, a warm, grounded emotional-wellness assistant.

Your purpose is to help people understand and manage their emotions. You can:
- Look up evidence-based coping mechanisms and music for specific moods.
- Search a curated knowledge base for mood and wellness guidance.
- Recommend articles from the moodHack article library.
- Save a mood journal entry when the user wants to reflect.

Guidelines:
- Be empathetic and practical, never clinical or dismissive.
- Use the available tools when the user asks for coping mechanisms, music,
  articles, or when grounding your answer in the knowledge base helps.
- When you recommend an article, cite its title and URL clearly.
- If a user expresses self-harm or crisis intent, gently encourage them to
  contact a trusted person or a local crisis line immediately, and keep your
  tone supportive.
- Respond in clear, concise markdown (headings, bullet lists, bold where
  helpful).
"""


class AgentResult:
    def __init__(
        self,
        reply: str,
        tool_activity: list[dict[str, Any]],
        articles: list[dict[str, Any]],
    ):
        self.reply = reply
        self.tool_activity = tool_activity
        self.articles = articles


class Agent:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def run(
        self,
        user_message: str,
        history: Optional[list[dict[str, Any]]] = None,
    ) -> AgentResult:
        """Run the agent loop and return the final reply + tool trace."""
        messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        tool_activity: list[dict[str, Any]] = []
        articles: list[dict[str, Any]] = []

        for _ in range(MAX_ITERATIONS):
            response = self.llm.chat(messages=messages, tools=tools.TOOLS)

            if response["tool_calls"]:
                # Reconstruct the assistant message in the exact format the
                # provider expects for round-tripping tool calls.
                messages.append(
                    {
                        "role": "assistant",
                        "content": response["text"] or "",
                        "tool_calls": [
                            {
                                "id": call["id"],
                                "type": "function",
                                "function": {
                                    "name": call["name"],
                                    "arguments": call["arguments"],
                                },
                            }
                            for call in response["tool_calls"]
                        ],
                    }
                )

                for call in response["tool_calls"]:
                    name = call["name"]
                    arguments = LLMClient.parse_arguments(call["arguments"])
                    result = tools.execute_tool(name, arguments)

                    tool_activity.append(
                        {
                            "tool": name,
                            "arguments": arguments,
                            "result": result,
                        }
                    )

                    if isinstance(result, dict):
                        for item in result.get("results", []):
                            if isinstance(item, dict) and item.get("type") == "article":
                                articles.append(item)

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call["id"],
                            "content": _serialize(result),
                        }
                    )
                continue

            reply = response["text"] or ""
            break
        else:
            final_response = self.llm.chat(messages=messages, tools=None)
            reply = final_response["text"] or ""

        return AgentResult(
            reply=reply,
            tool_activity=tool_activity,
            articles=_dedupe(articles),
        )


def _dedupe(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    unique: list[dict[str, Any]] = []
    for article in articles:
        key = article.get("url") or article.get("title")
        if key and key not in seen:
            seen.add(key)
            unique.append(article)
    return unique


def _serialize(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)
