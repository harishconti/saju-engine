"""Prompt assembly. Deterministic, and printable so it can be reviewed before sending.

The system prompt states the job and the output contract; the user message is the
grounding pack verbatim. Keeping them separate matters: the system half is the part
we version and audit, the pack is the part that changes per chart.
"""
from __future__ import annotations

import json

from .pack import GroundingPack

# Bump when the wording changes: `letter.draft_letter` records it in the result so an
# accepted draft can be traced back to the instructions that produced it.
PROMPT_VERSION = "letter-v1"

OUTPUT_SCHEMA = {
    "letter": "string — the letter, ready to paste, without a greeting or signature",
    "features": ["2-3 short names of the chart features the letter leans on"],
    "citations": [{"file": "knowledge filename, exactly as given", "section": "the excerpt's section heading"}],
}

_SYSTEM = """\
You are drafting one page of a Saju (Korean Four Pillars) reading for a client, for a
human reviewer to edit. Everything you may use is in the GROUNDING PACK: the computed
chart FACTS and short EXCERPTS from the tradition's reference notes. You have no other
knowledge about this person, and you must not invent any.

Write the letter the reviewer signs. It is the page that proves a person read *this*
order, so it must be specific to *this* chart: name the two or three features that drive
the rest of the reading and say what they mean, in plain English. The FACTS contain at
least one vivid, concrete detail — two branches of the same kind, a chart at noon in
midsummer, a knife-edge birth time, an unusual star. Lead with the strongest one and
tie the others to it.

Rules, all of which a validator checks:

- Obey every line of CONSTRAINTS.
- Use only FACTS for anything specific to this chart. Do not add a number, a year, a
  branch, a percentage or a relationship that is not written there.
- Every interpretive claim must rest on an EXCERPT. Cite by its exact id.
- If the FACTS contain hour_uncertainty, the letter must address it in one sentence.
- Plain, warm, second person. No jargon, no machinery, no prices, no absolutes.

Reply with JSON only, no prose around it, exactly this shape:

{shape}
""".format(shape=json.dumps(OUTPUT_SCHEMA, ensure_ascii=False, indent=2))


def system_prompt() -> str:
    return _SYSTEM


def build_messages(pack: GroundingPack) -> tuple[str, str]:
    """(system, user) for one drafting request."""
    return _SYSTEM, pack.render()
