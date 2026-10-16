"""Tests for the review-time letter drafter (`saju_ai`).

Two things are being protected here, and they are the reasons this package exists at
all: the pack must carry the chart and *nothing identifying*, and a draft must not be
shown as finished unless it survives the deterministic checks. Both are asserted without
touching a network — the provider call is the one part that is not unit-tested, because
it needs a key; everything the model could get wrong is validated locally.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from saju_ai import (  # noqa: E402
    LlmClient, LlmError, build_messages, build_pack, draft_letter, parse_payload, validate,
)
from saju_ai.pack import LETTER_MAX_WORDS, LETTER_MIN_WORDS  # noqa: E402

CLI = REPO_ROOT / "tools" / "suggest_letter.py"

BIRTH = dict(
    name="RM (Kim Nam-joon)", gender="M", year=1994, month=9, day=12, hour=13,
    minute=28, city="Seoul", longitude=126.978, utc_offset=9,
)
# Only distinctive values: "12" would match ages and stage numbers everywhere and prove
# nothing. These are the strings that must never reach a provider.
PII = ("Kim Nam-joon", "Seoul", "1994", "126.978")


@pytest.fixture(scope="module")
def chart():
    from saju_engine.engine import compute_chart

    return compute_chart(**BIRTH)


@pytest.fixture(scope="module")
def pack(chart):
    from saju_html.chart_input import chart_markdown

    report_md = chart_markdown(chart, "deep", title="Saju Reading")
    return build_pack(chart, report_md, pii_terms=PII)


# ── the pack ─────────────────────────────────────────────────────────────────────

def test_pack_carries_the_chart_facts_the_letter_needs(pack):
    facts = pack.facts
    assert facts["day_master"]["romanised"] and facts["day_master"]["element"]
    assert len(facts["pillars"]) == 4
    for pillar in facts["pillars"]:
        assert pillar["hanja"] and pillar["romanised"]
        assert pillar["stem_element"] and pillar["branch_element"] and pillar["animal"]
    # The day pillar's animal and element are what a day-pillar portrait is built on.
    day = next(p for p in facts["pillars"] if p["position"] == "day")
    assert day["animal"] and day["branch_element"]
    assert facts["favorable_element"]["element"]
    assert facts["dominant_ten_god_classes"], "no ten-god classes"
    # Counts, not just names: the audit caught a report inventing three "dominant"
    # classes while its own table showed one appearing five times.
    assert all("count" in entry for entry in facts["dominant_ten_god_classes"])
    assert facts["daeun"], "no major-luck periods"


def test_pack_carries_no_identifying_information(pack):
    """The client's name, place and birth data must never be sent to a provider."""
    rendered = pack.render()
    assert pack.contains_pii() == []
    for term in PII:
        assert term not in rendered, f"{term!r} leaked into the pack"
    # The report title ("Name — Deep Destiny Report") carries the name, so it must not
    # be in the outline; the first entry is the report's own contents page.
    assert not any("Deep Destiny Report" in s for s in pack.report_sections)
    assert pack.report_sections[0] == "Table of Contents"


def test_pack_is_deterministic(chart):
    from saju_html.chart_input import chart_markdown

    report_md = chart_markdown(chart, "deep", title="Saju Reading")
    first = build_pack(chart, report_md, pii_terms=PII)
    second = build_pack(chart, report_md, pii_terms=PII)
    assert first.render() == second.render()


def test_pack_excerpts_are_citable_slices_of_knowledge(pack):
    assert pack.excerpts, "no doctrine selected"
    for excerpt in pack.excerpts:
        assert (REPO_ROOT / "knowledge" / excerpt.file).exists()
        assert excerpt.text and excerpt.words <= 130
        assert excerpt.id.startswith(excerpt.file + "#")
    # The method and the favourable-element logic are always relevant.
    files = {e.file for e in pack.excerpts}
    assert "09-interpretation-method.md" in files
    assert "03-five-elements.md" in files


def test_prompt_states_the_rules_and_the_output_shape(pack):
    system, user = build_messages(pack)
    assert user == pack.render()
    for phrase in ("JSON only", "EXCERPT", "second person", "must not invent"):
        assert phrase.lower() in system.lower(), f"system prompt lacks {phrase!r}"
    assert '"letter"' in system and '"citations"' in system
    # The gate's own bans are stated in the constraints, in the pack the model reads.
    assert "never mention the engine" in user.lower()
    assert "querent" in user.lower()


# ── validation ────────────────────────────────────────────────────────────────────

def _good_letter(pack) -> dict:
    # This chart's recorded time sits close to an hour boundary, so a valid letter
    # carries the caveat — which is exactly what the validator should insist on.
    body = " ".join(["You"] + ["read"] * 200) + (
        " If the recorded birth time is a few minutes out, the hour pillar changes.")
    return {
        "letter": body,
        "features": ["day pillar", "favourable element"],
        "citations": [{"file": pack.excerpts[0].file, "section": pack.excerpts[0].section}],
    }


def test_validate_accepts_a_grounded_draft(pack):
    assert validate(_good_letter(pack), pack) == []


def test_validate_rejects_an_unknown_citation(pack):
    payload = _good_letter(pack)
    payload["citations"] = [{"file": "knowledge/99-invented.md", "section": "Nope"}]
    codes = {p.code for p in validate(payload, pack)}
    assert "CITATION_UNKNOWN" in codes


@pytest.mark.parametrize("mutate,expected", [
    (lambda p: p.update(letter="You are strong."), "LENGTH"),
    (lambda p: p.update(letter=" ".join(["You"] * 200) + " in 2031."), "INVENTED_NUMBER"),
    (lambda p: p.update(letter=" ".join(["You"] * 200) + " This is guaranteed."), "GROUND_RULE"),
    (lambda p: p.update(letter=" ".join(["You"] * 200) + " The engine computed it."), "MACHINERY"),
    (lambda p: p.update(letter=" ".join(["One", "reads"] * 100)), "NOT_SECOND_PERSON"),
    (lambda p: p.update(citations=[]), "CITATION_MISSING"),
    (lambda p: p.update(features=["only one"]), "FEATURE_COUNT"),
])
def test_validate_catches_each_failure(pack, mutate, expected):
    payload = _good_letter(pack)
    mutate(payload)
    assert expected in {p.code for p in validate(payload, pack)}


def test_birth_time_note_is_required_when_the_chart_is_a_knife_edge(pack):
    """The audit's own spec for this page: it must carry the birth-time caveat."""
    import copy

    uncertain = copy.deepcopy(pack)
    uncertain.facts["hour_uncertainty"] = {"primary_hour_pillar": "辛丑", "distance_seconds": 41}
    with_note = _good_letter(uncertain)
    assert "MISSING_BIRTH_TIME_NOTE" not in {p.code for p in validate(with_note, uncertain)}

    without_note = dict(with_note, letter=with_note["letter"].split(" If the recorded")[0])
    assert "MISSING_BIRTH_TIME_NOTE" in {p.code for p in validate(without_note, uncertain)}


def test_validate_catches_a_favourable_element_that_is_not_the_charts(pack):
    """The letter may not name a favourable element the chart does not have."""
    allowed = {pack.facts["favorable_element"]["element"],
               pack.facts["favorable_element"]["supporting"]}
    wrong = next(e for e in ("Wood", "Fire", "Earth", "Metal", "Water") if e not in allowed)
    payload = _good_letter(pack)
    payload["letter"] += f" The favourable element here is {wrong}."
    codes = {p.code for p in validate(payload, pack)}
    assert "ELEMENT_MISMATCH" in codes

    ok = _good_letter(pack)
    ok["letter"] += f" The favourable element here is {pack.facts['favorable_element']['element']}."
    assert "ELEMENT_MISMATCH" not in {p.code for p in validate(ok, pack)}


def test_validate_catches_a_method_claim_the_chart_does_not_make(pack):
    """A claim about *which method governs* must match the chart's own method."""
    payload = _good_letter(pack)
    payload["letter"] += (" Because the climate is extreme, the climate-balance reading "
                          "takes priority over the strength reading.")
    codes = {p.code for p in validate(payload, pack)}
    if "climate" in pack.facts["favorable_element"]["method"]:
        pytest.skip("this chart's method is climate-based; the claim is legitimate")
    assert "METHOD_MISMATCH" in codes


@pytest.mark.parametrize("phrase,expected", [
    ("a few minutes out", False),          # a hedge, not a measurement
    ("the next hour pillar", False),       # a term of art on this page
    ("about a minute and a half from the boundary", True),   # rounds 41 seconds away
    ("roughly 12 minutes later", True),    # a number the facts do not carry
    ("half an hour", True),
])
def test_validate_catches_invented_time_measurements(pack, phrase, expected):
    payload = _good_letter(pack)
    payload["letter"] += f" {phrase}."
    flagged = "UNSUPPORTED_DURATION" in {p.code for p in validate(payload, pack)}
    assert flagged is expected, phrase


def test_word_bounds_are_the_audits_own():
    assert (LETTER_MIN_WORDS, LETTER_MAX_WORDS) == (140, 280)


# ── the provider call ─────────────────────────────────────────────────────────────

@pytest.fixture
def no_keys(monkeypatch):
    for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "SAJU_LLM_MODEL", "SAJU_LLM_PROVIDER"):
        monkeypatch.delenv(name, raising=False)


def test_client_is_unavailable_without_a_key(no_keys):
    client = LlmClient()
    assert not client.available()
    # Ollama is the default provider; the error must name that provider's variable.
    with pytest.raises(LlmError, match="OLLAMA_API_KEY"):
        client.complete("system", "user")


def test_client_requires_an_explicit_model(no_keys, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client = LlmClient()
    assert client.available()
    with pytest.raises(LlmError, match="SAJU_LLM_MODEL"):
        client.complete("system", "user")


def test_client_rejects_an_unknown_provider(no_keys):
    with pytest.raises(LlmError, match="unknown provider"):
        LlmClient(provider="gemini", api_key="x", model="m").complete("s", "u")


def test_parse_payload_survives_fences_and_preamble():
    assert parse_payload('```json\n{"letter": "hi"}\n```') == {"letter": "hi"}
    assert parse_payload('Sure! Here you go:\n{"letter": "hi", "features": []}') == {
        "letter": "hi", "features": []}
    with pytest.raises(ValueError):
        parse_payload("no json here")
    # Nested objects and braces inside strings must not end the scan early.
    nested = '{"letter": "a {brace} inside", "citations": [{"file": "f", "section": "s"}]}'
    assert parse_payload(nested)["letter"] == "a {brace} inside"


class _FakeClient(LlmClient):
    """A provider that answers with a canned payload — the orchestration test."""

    def __init__(self, payload):
        super().__init__(provider="anthropic", api_key="test", model="test-model")
        self._payload = payload

    def complete(self, system, user, **kwargs):
        from saju_ai.client import Completion

        return Completion(text=json.dumps(self._payload), provider="anthropic",
                          model="test-model", usage={"input_tokens": 1})


def test_draft_letter_validates_what_the_model_returned(pack):
    from saju_ai.letter import Draft

    payload = _good_letter(pack)
    draft = draft_letter(pack, _FakeClient(payload))
    assert isinstance(draft, Draft)
    assert draft.ok, draft.problems
    assert draft.features == payload["features"]
    assert draft.provenance()["model"] == "test-model"
    assert draft.letter.startswith("You")


def test_a_truncated_reply_says_so_rather_than_failing_to_parse(pack):
    """A reasoning model that runs out of budget returns half a JSON object.

    That showed up as "unterminated JSON object" — true but useless. It now names the
    cause and the fix, because the fix is one flag.
    """
    from saju_ai.client import Completion
    from saju_ai.letter import draft_letter

    class _Truncating(LlmClient):
        def __init__(self):
            super().__init__(provider="anthropic", api_key="t", model="m")

        def complete(self, system, user, **kwargs):
            return Completion(text='{"letter": "You were born', provider="ollama", model="m",
                              usage={"completion_tokens": 8000}, finish_reason="length")

    with pytest.raises(LlmError, match="raise --max-tokens"):
        draft_letter(pack, _Truncating())


def test_client_reports_the_finish_reason_and_the_ollama_default(no_keys, monkeypatch):
    """The default provider is Ollama, and its model id is the verified one."""
    from saju_ai.client import OLLAMA_DEFAULT_MODEL

    monkeypatch.setenv("OLLAMA_API_KEY", "test-key")
    client = LlmClient()
    assert client.provider() == "ollama"
    assert client.model() == OLLAMA_DEFAULT_MODEL == "deepseek-v4.1-flash"
    assert client.endpoint() == "https://ollama.com/v1/chat/completions"
    # An explicit model always wins, including a variant tag.
    assert LlmClient(model="deepseek-v4-pro:0813").model() == "deepseek-v4-pro:0813"


# ── the CLI ───────────────────────────────────────────────────────────────────────

def _cli(*extra, env=None, env_file="/nonexistent/.env"):
    """Run the CLI offline.

    `--env-file` is pinned to a path that does not exist on purpose: the tool's default
    is `apps/web/.env`, which holds a real key on this machine, and a test must never be
    able to reach the network.
    """
    return subprocess.run(
        [sys.executable, str(CLI), "--from-chart", "--name", BIRTH["name"], "--gender", "M",
         "--birth-year", "1994", "--birth-month", "9", "--birth-day", "12",
         "--birth-hour", "13", "--birth-minute", "28", "--city", "Seoul",
         "--longitude", "126.978", "--utc-offset", "9", "--env-file", env_file, *extra],
        capture_output=True, text=True, env=env or {**os.environ}, cwd=str(REPO_ROOT))


def test_cli_dry_run_prints_the_request_and_sends_nothing(no_keys):
    result = _cli("--dry-run")
    assert result.returncode == 0, result.stderr
    assert "## FACTS" in result.stdout and "## CONSTRAINTS" in result.stdout
    assert "no request was made" in result.stdout
    assert "Kim Nam-joon" not in result.stdout and "Seoul" not in result.stdout


def test_cli_refuses_without_a_key_and_says_what_to_do(no_keys):
    result = _cli()
    assert result.returncode == 2
    assert "OLLAMA_API_KEY" in result.stderr and "--dry-run" in result.stderr


def test_cli_json_mode_reports_problems_without_a_draft(no_keys):
    """`--json` is for tooling; without a key it must still fail cleanly, not crash."""
    result = _cli("--json")
    assert result.returncode == 2
    assert "error:" in result.stderr
