"""Review-time AI drafting for Saju reports. Suggest-only, never in the delivery path.

This package exists to answer one question before anything is wired into the
product: **does grounded generation actually produce the specificity the engine's
templates cannot?** Nothing here is called while a client is waiting, nothing here
touches a delivered report, and every draft it returns must pass a deterministic
validator before a human even looks at it.

The shape of the safety story, in one paragraph: the *engine* owns the facts. A
drafting request gets a **grounding pack** — computed chart facts, a short set of
excerpts from `knowledge/`, and an explicit list of constraints — and nothing else.
It must answer with structured JSON that cites the excerpts it was given. A
deterministic validator then rejects unknown citations, invented numbers, wrong
length, missing birth-time caveats, and anything the repo's client-ready gate flags.
A reviewer reads the result and accepts or discards it. Because the model is never
in the delivery path, a provider outage is a non-event and a bad generation cannot
reach a client.

Privacy: the pack carries **no personally identifying data** — no name, birth date,
birth time, or place. The letter is written in the second person and the engine
substitutes the client's name downstream. `build_pack` takes the real values only so
it can prove they are absent (see ``pii_terms``).
"""
from __future__ import annotations

from .client import LlmClient, LlmError
from .letter import Draft, draft_letter, parse_payload
from .pack import Excerpt, GroundingPack, build_pack
from .prompt import build_messages
from .validate import Problem, validate

__all__ = [
    "Draft",
    "Excerpt",
    "GroundingPack",
    "LlmClient",
    "LlmError",
    "Problem",
    "build_messages",
    "build_pack",
    "draft_letter",
    "parse_payload",
    "validate",
]
