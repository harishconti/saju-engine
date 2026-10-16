#!/usr/bin/env python3
"""Draft the reader's letter for a Saju report — review-time, suggest-only.

    # 1. See exactly what would be sent. No key, no network, no cost.
    python3 tools/suggest_letter.py --from-chart --name "RM (Kim Nam-joon)" --gender M \
        --birth-year 1994 --birth-month 9 --birth-day 12 --birth-hour 13 --birth-minute 28 \
        --city "Seoul" --longitude 126.978 --utc-offset 9 --dry-run

    # 2. Ask a provider for a draft, and validate it.
    export ANTHROPIC_API_KEY=...   ANTHROPIC_API_KEY, or OPENAI_API_KEY
    export SAJU_LLM_MODEL=...      the provider's current model id
    python3 tools/suggest_letter.py --from-chart ... --out /tmp/letter.md

Why it exists: the audit's own highest-value page — "a letter from your reader" — is the
one page that cannot be templated, and the intake's "main concern" is collected and read
by nobody. This drafts that page from the chart the engine already computed, grounded in
`knowledge/`, and hands it to a reviewer.

Guardrails, all of them load-bearing:

* **Never in the delivery path.** It runs when the owner asks, on the owner's machine or
  in the review console. A provider outage cannot affect a client.
* **No PII leaves here.** The pack carries chart facts and doctrine excerpts only — no
  name, birth date, time or place. The letter is written as "you"; the name is added
  downstream by the engine. `--dry-run` prints the pack so this can be checked by eye,
  and the tool refuses to send a pack that contains any supplied PII.
* **Structured output, then a deterministic validator.** Unknown citations, invented
  numbers, wrong length, a missing birth-time caveat, ground-rule violations, or anything
  the client-ready gate flags all fail the draft — so a bad generation is visible, not
  subtle.
* **Suggest-only.** It writes to `--out` or stdout. It never edits a report.

Exit codes: 0 clean draft (or `--dry-run`), 1 the draft has problems, 2 cannot ask
(no key/model) or bad usage.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from saju_ai import LlmClient, LlmError, build_pack, draft_letter  # noqa: E402
from saju_ai.client import OLLAMA_DEFAULT_MODEL  # noqa: E402
from saju_ai.validate import summarise  # noqa: E402
from saju_html.chart_input import add_chart_args, chart_from_args, chart_markdown  # noqa: E402

from qa_client_ready import scan as gate_scan  # noqa: E402

# Only these are read out of an env file. Loading the webapp's whole .env would spread
# unrelated secrets (database, payment keys) into this process for no reason.
_ENV_KEYS = (
    "OLLAMA_API_KEY", "OLLAMA_MODEL", "OLLAMA_BASE_URL",
    "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
    "ANTHROPIC_BASE_URL", "OPENAI_BASE_URL",
    "SAJU_LLM_PROVIDER", "SAJU_LLM_MODEL",
)


def load_env_file(path: Path) -> int:
    """Apply the allowlisted keys from ``path``; never override what is already set.

    Returns how many were applied. Values are read and never printed — the one line we
    emit names the file, not the contents.
    """
    if not path.exists():
        return 0
    applied = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in _ENV_KEYS and value and key not in os.environ:
            os.environ[key] = value
            applied += 1
    return applied


def _pack_for(args) -> "object":
    """Compute the chart, render its report markdown, and build the grounding pack."""
    chart = chart_from_args(args.parser, args)
    tier = args.tier
    report_md = chart_markdown(chart, tier, title=args.title or "Saju Reading")
    pii = [args.name, args.city, str(args.birth_year or ""), str(args.birth_day or "")]
    return build_pack(chart, report_md, section="letter", pii_terms=pii)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--title", default="Saju Reading")
    ap.add_argument("--tier", default="deep",
                    help="the tier whose report the letter must be consistent with")
    add_chart_args(ap)
    ap.add_argument("--dry-run", action="store_true",
                    help="print the grounding pack and prompt; make no request")
    ap.add_argument("--out", type=Path, default=None,
                    help="write the suggestion here (markdown); default is stdout")
    ap.add_argument("--json", action="store_true", help="machine-readable result")
    ap.add_argument("--provider", default=None,
                    help="ollama (default when its key is present) | anthropic | openai")
    ap.add_argument("--model", default=None,
                    help="overrides SAJU_LLM_MODEL; ollama defaults to "
                         f"{OLLAMA_DEFAULT_MODEL}")
    ap.add_argument("--endpoint", default=None, help="override the API endpoint")
    ap.add_argument("--temperature", type=float, default=0.6)
    ap.add_argument("--max-tokens", type=int, default=8000,
                    help="reasoning models spend part of this thinking before the JSON; "
                         "8000 is a comfortable budget for a 250-word letter")
    ap.add_argument("--timeout", type=float, default=120.0)
    ap.add_argument("--env-file", type=Path,
                    default=REPO_ROOT / "apps" / "web" / ".env",
                    help="read the provider key from here if it is not already in the "
                         "environment (default: apps/web/.env)")
    args = ap.parse_args(argv)
    args.parser = ap  # chart_from_args needs the parser to report usage errors

    if not args.from_chart:
        ap.error("--from-chart with birth data is required (the letter is chart-specific)")

    pack = _pack_for(args)

    if args.dry_run:
        # The auditability feature: see the whole request before spending anything.
        print(pack.render())
        print("\n--- no request was made (--dry-run) ---")
        return 0

    leaked = pack.contains_pii()
    if leaked:
        print(f"error: the grounding pack contains PII {leaked!r}; refusing to send it",
              file=sys.stderr)
        return 2

    applied = load_env_file(args.env_file) if args.env_file else 0
    if applied:
        print(f"loaded {applied} setting(s) from {args.env_file} (values not shown)",
              file=sys.stderr)

    client = LlmClient(provider=args.provider, model=args.model,
                       endpoint=args.endpoint, timeout=args.timeout)
    if not client.available():
        env = {"ollama": "OLLAMA_API_KEY", "anthropic": "ANTHROPIC_API_KEY",
               "openai": "OPENAI_API_KEY"}.get(client.provider(), "OLLAMA_API_KEY")
        print(f"error: no {env} for provider {client.provider()!r} "
              f"(looked in the environment and {args.env_file}); "
              "use --dry-run to inspect the request without sending it", file=sys.stderr)
        return 2

    try:
        draft = draft_letter(pack, client, max_tokens=args.max_tokens,
                             timeout=args.timeout, temperature=args.temperature)
    except LlmError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"error: could not read the model's reply: {exc}", file=sys.stderr)
        return 1

    # The repo's client-ready gate is the last word: the same rules that a delivered
    # report must satisfy apply to the text we are about to suggest.
    from saju_ai.validate import Problem

    gate = [Problem(f.code, f"{f.note} :: {f.excerpt}") for f in gate_scan(draft.letter, rendered=True)]
    problems = list(draft.problems) + gate

    if args.json:
        print(json.dumps({
            "letter": draft.letter,
            "features": draft.features,
            "provenance": draft.provenance(),
            "problems": [{"code": p.code, "detail": p.detail} for p in problems],
            "citations": draft.payload.get("citations") or [],
        }, indent=2, ensure_ascii=False))
    else:
        print(f"letter draft — {draft.provider}/{draft.model} · prompt {draft.prompt_version} · "
              f"{len(draft.letter.split())} words · {draft.usage or 'no usage reported'}")
        print("-" * 72)
        print(draft.letter)
        print("-" * 72)
        if draft.features:
            print("features: " + "; ".join(draft.features))
        for citation in draft.payload.get("citations") or []:
            if isinstance(citation, dict):
                print(f"  cites {citation.get('file')}#{citation.get('section')}")
        if problems:
            print(f"\nFLAGGED — {len(problems)} problem(s); do not paste as-is:")
            print(summarise(problems))
        else:
            print("\nCLEAN — every check passed (structure, length, citations, numbers, "
                  "ground rules, client-ready gate). Review before use.")

    if args.out is not None:
        # A suggestion file beside nothing else: the reviewer moves it by hand.
        args.out.write_text(draft.letter + "\n", encoding="utf-8")
        print(f"\nwrote {args.out} (suggestion only — the report is untouched)")

    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
