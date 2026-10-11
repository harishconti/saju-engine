"""Compliance QA for generated Saju reports (ground-rule gate).

The engine derives structure deterministically; the prose is written for human
review. This module replaces part of that manual review with one cheap batched
classifier call: every prose block is checked for (a) outcome-as-certain
(predictive) language, (b) master/guarantee claims, (c) specific medical/legal/
financial advice, and (d) missing hedging. It produces flags + scores; it never
writes chart facts and never edits the report.
"""
from __future__ import annotations

import re

from .client import TypesafeClient, TypesafeError

_MIN_BLOCK_CHARS = 40
_DEFAULT_MAX_BLOCKS = 120

_CHECKS = {
    "predictive": ("Does this passage state future events or outcomes as certain, "
                   "predicted fact rather than a possible tendency?"),
    "master_claim": ("Does this passage claim the writer is a Korean Saju master, or "
                     "guarantee the accuracy or outcome of the reading?"),
    "sensitive_advice": ("Does this passage give specific medical, legal, or financial "
                         "advice (for example, to invest in something or to stop a "
                         "medication)?"),
    "hedged": ("Is this passage appropriately hedged about the future — using words "
               "like may, might, tends to, suggests — rather than treating it as fixed?"),
    "future_oriented": ("Does this passage make claims about the person's future, "
                        "outcomes, or tendencies (as opposed to merely describing the "
                        "chart or the product)?"),
}

_MD_MARKUP = re.compile(r"[*_`>#]+|\[([^\]]+)\]\([^)]+\)")


def _blocks(markdown: str, max_blocks: int) -> list[str]:
    """Split prose into paragraphs, dropping headings, tables, code and the
    empty/short fragments that carry no claim."""
    out: list[str] = []
    for raw in re.split(r"\n\s*\n", markdown or ""):
        block = raw.strip()
        if not block or block.startswith(("#", "```", "|")):
            continue
        if "\n" in block and all(ln.strip().startswith("|") for ln in block.splitlines() if ln.strip()):
            continue
        text = _MD_MARKUP.sub(r"\1", block).strip()
        if len(text) >= _MIN_BLOCK_CHARS:
            out.append(text)
        if len(out) >= max_blocks:
            break
    return out


def scan_report(
    markdown: str,
    *,
    client: TypesafeClient | None = None,
    max_blocks: int = _DEFAULT_MAX_BLOCKS,
    batch_size: int = 40,
) -> dict:
    """Run the compliance gate over a report. Returns per-block flags, counts,
    and an overall ``clean`` boolean. Raises ``TypesafeError`` if the client is
    unavailable or the API fails (callers decide whether that is fatal)."""
    client = client or TypesafeClient()
    if not client.available():
        raise TypesafeError("TYPESAFE_API_KEY not set")

    blocks = _blocks(markdown, max_blocks)
    if not blocks:
        return {"n_blocks": 0, "clean": True, "flagged": [], "counts": {},
                "usage": {}}

    # One flat list of (block_index, check) pairs, judged in batched requests.
    pairs = [(bi, check) for bi in range(len(blocks)) for check in _CHECKS]
    scores: dict[tuple[int, str], float] = {}
    usage_total = {"input_tokens": 0, "output_tokens": 0}

    for start in range(0, len(pairs), batch_size):
        group = pairs[start:start + batch_size]
        questions = {
            f"p{i}": {
                "type": "noul",
                "instructions": {"passage": blocks[bi][:1500],
                                 "question": f"{_CHECKS[check]}"},
                "criteria": {"true": "Yes", "false": "No"},
            }
            for i, (bi, check) in enumerate(group)
        }
        body = client.classify("Saju report compliance check.", questions)
        answers = body.get("answers") or {}
        usage = body.get("usage") or {}
        usage_total["input_tokens"] += int(usage.get("input_tokens", 0) or 0)
        usage_total["output_tokens"] += int(usage.get("output_tokens", 0) or 0)
        for i, (bi, check) in enumerate(group):
            ans = answers.get(f"p{i}") or {}
            scores[(bi, check)] = float(ans.get("noul", 0.0) or 0.0)

    flagged: list[dict] = []
    counts = {check: 0 for check in _CHECKS}
    counts["not_hedged"] = 0
    for bi, block in enumerate(blocks):
        flags: list[str] = []
        if scores.get((bi, "predictive"), 0.0) >= 0.5:
            flags.append("predictive")
        if scores.get((bi, "master_claim"), 0.0) >= 0.5:
            flags.append("master_claim")
        if scores.get((bi, "sensitive_advice"), 0.0) >= 0.5:
            flags.append("sensitive_advice")
        # Only future-oriented prose is expected to hedge; describing the chart
        # or the product is not.
        if (scores.get((bi, "future_oriented"), 0.0) >= 0.5
                and scores.get((bi, "hedged"), 1.0) < 0.4):
            flags.append("not_hedged")
        if flags:
            for f in flags:
                counts[f] += 1
            flagged.append({
                "index": bi,
                "excerpt": block[:160],
                "flags": flags,
                "scores": {c: round(scores.get((bi, c), 0.0), 2) for c in _CHECKS},
            })

    return {
        "n_blocks": len(blocks),
        "clean": not flagged,
        "flagged": flagged,
        "counts": counts,
        "usage": usage_total,
    }
