"""Multi-provider AI client abstraction (stdlib only).

Supports OpenAI and Google Gemini via their respective REST APIs.
Uses urllib from the standard library — no external dependencies.
"""

import json
import urllib.request
import urllib.error

from .config import get_openai_key, get_ai_config
from .ssl_context import get_ssl_context


class AIProvider:
    """Abstract base for AI providers."""

    def chat(self, messages, tools=None, max_tokens=1500, temperature=0.4):
        """Send a chat completion request.

        Args:
            messages: List of {role, content} dicts.
            tools: Optional list of tool definitions.
            max_tokens: Maximum response tokens.
            temperature: Sampling temperature.

        Returns:
            dict with keys:
                content (str): Text response.
                tool_calls (list): List of {id, name, arguments} dicts.
        """
        raise NotImplementedError


class OpenAIProvider(AIProvider):
    """OpenAI API (GPT-4o, GPT-5.2, etc.)"""

    def __init__(self, api_key, model="gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"

    # Models that require max_completion_tokens instead of max_tokens
    _NEW_PARAM_MODELS = ("gpt-5", "o1", "o3", "o4")

    def _uses_new_tokens_param(self):
        return any(self.model.startswith(prefix) for prefix in self._NEW_PARAM_MODELS)

    def chat(self, messages, tools=None, max_tokens=1500, temperature=0.4):
        body = {
            "model": self.model,
            "messages": messages,
        }
        if self._uses_new_tokens_param():
            body["max_completion_tokens"] = max_tokens
        else:
            body["max_tokens"] = max_tokens
            body["temperature"] = temperature
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"

        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=90, context=get_ssl_context()) as resp:
                result = json.load(resp)
                msg = result["choices"][0]["message"]

                tool_calls = []
                for tc in msg.get("tool_calls", []):
                    tool_calls.append({
                        "id": tc["id"],
                        "name": tc["function"]["name"],
                        "arguments": json.loads(tc["function"]["arguments"]),
                    })

                return {
                    "content": msg.get("content", ""),
                    "tool_calls": tool_calls,
                }
        except Exception as e:
            return {"content": f"AI 응답 오류: {e}", "tool_calls": []}


class GeminiProvider(AIProvider):
    """Google Gemini API via OpenAI-compatible endpoint.

    Gemini provides an OpenAI-compatible endpoint at:
    https://generativelanguage.googleapis.com/v1beta/openai/chat/completions

    This allows using the same message format as OpenAI.
    """

    def __init__(self, api_key, model="gemini-3-flash-preview"):
        self.api_key = api_key
        self.model = model
        self.base_url = (
            "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        )

    def chat(self, messages, tools=None, max_tokens=1500, temperature=0.4):
        body = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"

        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=90, context=get_ssl_context()) as resp:
                result = json.load(resp)
                msg = result["choices"][0]["message"]

                tool_calls = []
                for tc in msg.get("tool_calls", []):
                    tool_calls.append({
                        "id": tc["id"],
                        "name": tc["function"]["name"],
                        "arguments": json.loads(tc["function"]["arguments"]),
                    })

                return {
                    "content": msg.get("content", ""),
                    "tool_calls": tool_calls,
                }
        except Exception as e:
            return {"content": f"AI 응답 오류: {e}", "tool_calls": []}


class FallbackProvider(AIProvider):
    """Wraps a primary and fallback provider.

    If the primary provider raises an error, automatically retries
    with the fallback provider.
    """

    def __init__(self, primary, fallback):
        self.primary = primary
        self.fallback = fallback

    def chat(self, messages, tools=None, max_tokens=1500, temperature=0.4):
        result = self.primary.chat(messages, tools, max_tokens, temperature)
        content = result.get("content") or ""
        if content.startswith("AI 응답 오류:") and self.fallback:
            return self.fallback.chat(messages, tools, max_tokens, temperature)
        return result


def _create_provider(provider_name, model, config):
    """Create a provider instance from config values."""
    if provider_name == "gemini":
        api_key = config.get("gemini_api_key", "")
        return GeminiProvider(api_key, model)
    # Default: openai
    return OpenAIProvider(get_openai_key(), model)


def get_provider():
    """Factory: return the configured AI provider.

    Reads AI_PROVIDER, AI_MODEL from environment via get_ai_config().
    Supports optional AI_FALLBACK_PROVIDER / AI_FALLBACK_MODEL.
    """
    config = get_ai_config()
    provider_name = config.get("provider", "openai")
    model = config.get("model", "gpt-4o-mini")

    primary = _create_provider(provider_name, model, config)

    fallback_provider = config.get("fallback_provider")
    fallback_model = config.get("fallback_model", "gpt-4o-mini")
    if fallback_provider:
        fallback = _create_provider(fallback_provider, fallback_model, config)
        return FallbackProvider(primary, fallback)

    return primary
