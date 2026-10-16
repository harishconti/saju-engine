"""Provider adapters for the drafting step. Standard library only, key from the env.

Three providers, because the choice should be the owner's and switching should cost one
flag: **Ollama Cloud** (default), Anthropic's Messages API, and OpenAI's Chat
Completions. All are plain HTTPS calls, so nothing new enters the dependency set and
nothing needs hosting — which is the point: there is no model server to run.

Deliberately mirroring `saju_qa.client`: env-gated, one typed exception, an
``available()`` check so callers can degrade instead of crashing.

Model ids: Ollama's default below is **verified against the live endpoint** (see
`--dry-run` docs and the tests). The other two require an explicit model, on purpose —
guessed ids age badly and a stale default reads as a bug in our code rather than in the
config.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

ANTHROPIC_ENDPOINT = "https://api.anthropic.com/v1/messages"
OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
# Ollama Cloud speaks the OpenAI chat-completions shape. Its API host is `ollama.com`
# (`api.ollama.com` answers 405 on this path), verified live 2026-10-16.
OLLAMA_ENDPOINT = "https://ollama.com/v1/chat/completions"

_KEYS = {
    "ollama": "OLLAMA_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}
_ENDPOINTS = {
    "ollama": OLLAMA_ENDPOINT,
    "anthropic": ANTHROPIC_ENDPOINT,
    "openai": OPENAI_ENDPOINT,
}
# Endpoint overrides, for a proxy or a self-hosted Ollama (`http://localhost:11434/v1`).
_ENDPOINT_ENV = {"ollama": "OLLAMA_BASE_URL", "anthropic": "ANTHROPIC_BASE_URL",
                 "openai": "OPENAI_BASE_URL"}
# Verified live. Override with --model / SAJU_LLM_MODEL / OLLAMA_MODEL.
OLLAMA_DEFAULT_MODEL = "deepseek-v4.1-flash"


class LlmError(RuntimeError):
    """Raised when a drafting call cannot be made or the provider returns an error."""


@dataclass
class Completion:
    text: str
    provider: str
    model: str
    usage: Dict[str, Any] = field(default_factory=dict)
    # "stop" | "length" | ... — "length" means the reply was cut off, which for a JSON
    # contract shows up as an unterminated object rather than an obvious error.
    finish_reason: str = ""


class LlmClient:
    """Minimal drafting client: ``provider`` = "anthropic" | "openai"."""

    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        timeout: float = 120.0,
    ) -> None:
        self._provider = provider
        self._api_key = api_key
        self._model = model
        self._endpoint = endpoint
        self.timeout = timeout

    # ── configuration ────────────────────────────────────────────────────────────

    def provider(self) -> str:
        if self._provider:
            return self._provider.strip().lower()
        configured = (os.getenv("SAJU_LLM_PROVIDER") or "").strip().lower()
        if configured:
            return configured
        # Whichever key is present, preferring the cheapest verified default.
        for name in ("ollama", "anthropic", "openai"):
            if (os.getenv(_KEYS[name]) or "").strip():
                return name
        return "ollama"

    def _key(self) -> str:
        explicit = (self._api_key or "").strip()
        if explicit:
            return explicit
        return (os.getenv(_KEYS.get(self.provider(), ""), "") or "").strip()

    def model(self) -> str:
        for candidate in (self._model, os.getenv("SAJU_LLM_MODEL"),
                          os.getenv("OLLAMA_MODEL") if self.provider() == "ollama" else ""):
            name = (candidate or "").strip()
            if name:
                return name
        if self.provider() == "ollama":
            return OLLAMA_DEFAULT_MODEL
        raise LlmError(
            "no model configured: pass --model, or set SAJU_LLM_MODEL to the "
            f"{self.provider()} model id you want"
        )

    def available(self) -> bool:
        try:
            return bool(self._key()) and self.provider() in _KEYS
        except Exception:  # pragma: no cover - defensive
            return False

    def endpoint(self) -> str:
        if self._endpoint:
            return self._endpoint
        provider = self.provider()
        override = (os.getenv(_ENDPOINT_ENV.get(provider, ""), "") or "").strip()
        if override:
            # A base URL is friendlier than a full path: accept either.
            if override.rstrip("/").endswith("/v1"):
                return override.rstrip("/") + "/chat/completions"
            return override
        return _ENDPOINTS.get(provider, "")

    # ── the call ─────────────────────────────────────────────────────────────────

    def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 8000,
        timeout: Optional[float] = None,
        temperature: float = 0.6,
    ) -> Completion:
        provider = self.provider()
        if provider not in _KEYS:
            raise LlmError(f"unknown provider {provider!r}; expected 'anthropic' or 'openai'")
        key = self._key()
        if not key:
            raise LlmError(f"{_KEYS[provider]} is not set")
        model = self.model()

        if provider == "anthropic":
            body = {
                "model": model, "max_tokens": max_tokens, "temperature": temperature,
                "system": system, "messages": [{"role": "user", "content": user}],
            }
            headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
        else:  # ollama and openai share the chat-completions shape
            body = {
                "model": model, "max_tokens": max_tokens, "temperature": temperature,
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}],
            }
            headers = {"Authorization": f"Bearer {key}"}
        headers["Content-Type"] = "application/json"

        request = urllib.request.Request(
            self.endpoint(), data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            method="POST", headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout or self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", "replace")[:300]
            except (OSError, ValueError):
                detail = ""
            raise LlmError(f"HTTP {exc.code} from {provider}: {detail}") from exc
        except Exception as exc:
            raise LlmError(f"{type(exc).__name__} calling {provider}: {exc}") from exc

        choices = payload.get("choices") or []
        finish = ""
        if provider != "anthropic" and choices and isinstance(choices[0], dict):
            finish = choices[0].get("finish_reason") or ""
        elif provider == "anthropic":
            finish = payload.get("stop_reason") or ""
        return Completion(text=_extract_text(provider, payload), provider=provider,
                          model=model, usage=payload.get("usage") or {},
                          finish_reason=finish)


def _extract_text(provider: str, payload: Dict[str, Any]) -> str:
    """Pull the assistant text out of a provider response, or say what was missing."""
    if provider == "anthropic":
        blocks = payload.get("content") or []
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "text":
                return block.get("text") or ""
        raise LlmError("anthropic response had no text block")
    choices = payload.get("choices") or []
    if choices and isinstance(choices[0], dict):
        choice = choices[0]
        message = choice.get("message") or {}
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, str) and content.strip():
            return content
        # A reasoning model (DeepSeek Flash on Ollama, for one) returns its thinking in
        # `reasoning` and its answer in `content`. If the budget ran out mid-thought,
        # `content` is empty and the failure looks like "the model said nothing" — say
        # what actually happened instead, because the fix is a bigger --max-tokens.
        reasoning = message.get("reasoning") or message.get("reasoning_content") if isinstance(message, dict) else None
        if reasoning and choice.get("finish_reason") == "length":
            raise LlmError(
                f"{provider} spent the whole token budget reasoning "
                f"({len(str(reasoning))} chars of `reasoning`, finish_reason=length); "
                "raise --max-tokens"
            )
        if isinstance(content, str):
            return content
    raise LlmError(f"{provider} response had no message content")
