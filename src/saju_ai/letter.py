"""The drafting step itself: pack -> prompt -> call -> parse -> validate.

Nothing here writes to a report. It returns a :class:`Draft` for a human to read, and
the caller decides what to do with it. That is the whole safety model: the model
proposes, the validator disposes, the reviewer accepts.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from .client import LlmClient, LlmError
from .pack import GroundingPack
from .prompt import PROMPT_VERSION, build_messages
from .validate import Problem, validate


@dataclass
class Draft:
    """A validated-or-flagged suggestion, with the provenance to audit it later."""

    payload: Dict[str, Any]
    problems: List[Problem]
    pack: GroundingPack
    provider: str = ""
    model: str = ""
    prompt_version: str = PROMPT_VERSION
    usage: Dict[str, Any] = field(default_factory=dict)

    @property
    def letter(self) -> str:
        return (self.payload.get("letter") or "").strip()

    @property
    def features(self) -> List[str]:
        features = self.payload.get("features")
        return list(features) if isinstance(features, list) else []

    @property
    def ok(self) -> bool:
        """True when nothing objected — the reviewer's starting point."""
        return not self.problems

    def provenance(self) -> Dict[str, Any]:
        return {
            "provider": self.provider, "model": self.model,
            "prompt_version": self.prompt_version, "usage": self.usage,
            "citations": self.payload.get("citations") or [],
            "features": self.features, "problems": [p.code for p in self.problems],
        }


def parse_payload(text: str) -> Dict[str, Any]:
    """Pull the JSON object out of a response, tolerating code fences and preamble.

    Providers wrap their JSON differently depending on the model and the day, and a
    parse failure should be a clear error rather than a stack trace halfway through a
    review. Braces are scanned rather than regexed so nested objects survive.
    """
    if not text or not text.strip():
        raise ValueError("empty response")
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        cleaned = cleaned.rsplit("```", 1)[0]
    start = cleaned.find("{")
    if start < 0:
        raise ValueError("no JSON object in the response")
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(cleaned)):
        char = cleaned[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return json.loads(cleaned[start:index + 1])
    raise ValueError("unterminated JSON object in the response")


def draft_letter(
    pack: GroundingPack,
    client: Optional[LlmClient] = None,
    *,
    max_tokens: int = 1200,
    timeout: Optional[float] = None,
    temperature: float = 0.6,
    extra_problems: Sequence[Problem] = (),
) -> Draft:
    """Ask for a draft of ``pack`` and validate it. Raises ``LlmError`` on a call failure."""
    client = client or LlmClient()
    system, user = build_messages(pack)
    completion = client.complete(system, user, max_tokens=max_tokens, timeout=timeout,
                                  temperature=temperature)
    try:
        payload = parse_payload(completion.text)
    except ValueError as exc:
        if completion.finish_reason == "length":
            # The commonest cause by far: a reasoning model spent the budget thinking and
            # the JSON was cut off mid-object. Say so, and show the tail we can see.
            raise LlmError(
                f"{completion.provider} cut the reply off at the token budget "
                f"(finish_reason=length, {completion.usage.get('completion_tokens', '?')} "
                f"completion tokens); raise --max-tokens. Reply tail: "
                f"{completion.text[-120:]!r}") from exc
        raise LlmError(f"could not read the reply ({exc}); reply tail: "
                       f"{completion.text[-160:]!r}") from exc
    problems = list(validate(payload, pack)) + list(extra_problems)
    return Draft(payload=payload, problems=problems, pack=pack,
                 provider=completion.provider, model=completion.model,
                 usage=dict(completion.usage or {}))
