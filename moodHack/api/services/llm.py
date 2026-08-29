"""DeepSeek LLM client.

DeepSeek's API is OpenAI-compatible, so we use the `openai` SDK pointed at the
DeepSeek base URL. The model name and API key come from the environment
(DEEPSEEK_MODEL / DEEPSEEK_API_KEY) so nothing is hardcoded.
"""
import json
import os
import time
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


class LLMError(Exception):
    """Raised when the LLM provider call fails after retries."""


class LLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        if provider == "deepseek":
            self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
            self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
            self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", DEEPSEEK_BASE_URL)
        else:
            self.api_key = api_key or os.getenv("GEMINI_API_KEY")
            self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
            self.base_url = base_url or os.getenv("GEMINI_BASE_URL", GEMINI_BASE_URL)
        self.timeout = timeout
        self.max_retries = max_retries

    @property
    def _client(self):
        if self.api_key is None:
            raise LLMError(
                "No LLM API key is set. Add GEMINI_API_KEY (or DEEPSEEK_API_KEY) to your .env file."
            )
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise LLMError(
                "The `openai` package is required. Run: pip install openai"
            ) from exc
        return OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        json_mode: bool = False,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Call the chat completions endpoint with retries.

        Returns a normalized dict: {text, tool_calls, usage, finish_reason}.
        tool_calls keep raw `arguments` strings so they can be round-tripped
        back into assistant messages unchanged.
        """
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                client = self._client
                request_kwargs: dict[str, Any] = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                }
                if tools:
                    request_kwargs["tools"] = tools
                    request_kwargs["tool_choice"] = "auto"
                if json_mode:
                    request_kwargs["response_format"] = {"type": "json_object"}
                request_kwargs.update(kwargs)

                response = client.chat.completions.create(**request_kwargs)
                return self._normalize(response)

            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)

        raise LLMError(f"DeepSeek call failed after {self.max_retries} attempts: {last_error}")

    def _normalize(self, response: Any) -> dict[str, Any]:
        choice = response.choices[0]
        message = choice.message

        tool_calls: list[dict[str, Any]] = []
        raw_tool_calls = getattr(message, "tool_calls", None) or []
        for tc in raw_tool_calls:
            tool_calls.append(
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": tc.function.arguments or "{}",
                }
            )

        usage = {}
        if getattr(response, "usage", None):
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return {
            "text": message.content or "",
            "tool_calls": tool_calls,
            "usage": usage,
            "finish_reason": choice.finish_reason,
        }

    @staticmethod
    def parse_arguments(arguments: str) -> dict[str, Any]:
        """Parse a tool-call arguments string into a dict, tolerating junk."""
        try:
            parsed = json.loads(arguments)
            return parsed if isinstance(parsed, dict) else {}
        except (ValueError, TypeError):
            return {}
