"""Optional TypeSafe/Jev classifier client for Saju report QA and intake triage.

This package is deliberately separate from the deterministic ``saju_engine``
core: it never computes chart facts, and it is only imported by the QA/ops
paths. It uses the standard library only (no new runtime dependency) and is
gated behind the ``TYPESAFE_API_KEY`` environment variable.

Endpoint: ``POST https://api.typesafe.ai/v1/systemone`` with
``{"model", "state", "questions"}``; questions are typed ``noul`` (yes/no),
``choice``, or ``score`` (see https://docs.typesafe.ai/api).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

_ENDPOINT = "https://api.typesafe.ai/v1/systemone"


class TypesafeError(RuntimeError):
    """Raised when a classify call cannot be made or the API returns an error."""


class TypesafeClient:
    """Minimal TypeSafe/Jev client (key from ``TYPESAFE_API_KEY`` by default)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        endpoint: str = _ENDPOINT,
        timeout: float = 60.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self.endpoint = endpoint
        self.timeout = timeout

    def _key(self) -> str:
        return (self._api_key or os.getenv("TYPESAFE_API_KEY", "")).strip()

    def _model_name(self) -> str:
        return self._model or os.getenv("SAJU_CLASSIFY_MODEL", "jev-latest")

    def available(self) -> bool:
        return bool(self._key())

    def classify(self, state, questions: dict, *, timeout: float | None = None) -> dict:
        """Evaluate ``state`` against ``questions``; returns the parsed body
        (``{"model", "answers", "usage"}``). Raises ``TypesafeError`` on any
        failure so callers can catch one exception type."""
        key = self._key()
        if not key:
            raise TypesafeError("TYPESAFE_API_KEY not set")
        if not isinstance(questions, dict) or not questions:
            raise TypesafeError("questions must be a non-empty map")
        body = json.dumps({"model": self._model_name(), "state": state,
                           "questions": questions}).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint, data=body, method="POST",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout or self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", "replace")[:300]
            except (OSError, ValueError):
                detail = ""
            raise TypesafeError(f"HTTP {exc.code}: {detail}") from exc
        except Exception as exc:
            raise TypesafeError(f"{type(exc).__name__}: {exc}") from exc
