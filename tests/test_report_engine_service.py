#!/usr/bin/env python3
"""Contract tests for the report-engine service (`api/index.py`).

These call the endpoint functions **directly** rather than through `TestClient`.
That is deliberate, for two reasons:

  * The endpoints are plain synchronous functions, so the ASGI layer adds nothing
    except a dependency on starlette/httpx staying version-compatible (the local
    environment has httpx 0.28, whose `Client` no longer accepts `app=`, which
    breaks starlette 0.36's `TestClient`). Testing the logic directly is
    version-proof.
  * Auth failures raise `HTTPException` (which the ASGI layer would turn into a
    response) while validation failures return a `JSONResponse` with the error
    envelope. Asserting on both shapes explicitly documents which is which.

No network and no storage are used. The expensive end-to-end proof — a real
presigned PUT into R2, then download and sha256 compare — is done out of band;
see docs/webapp/05-report-pipeline.md §2.

Why these assertions matter: this service is the boundary between the webapp and
the engine, and its failure modes are quiet. A wrong pillar does not raise; it just
produces a wrong reading. So the chart assertions are on *known-correct facts* taken
from `candidates_horoscope/reports/rm/`, not on shape alone.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.index import (  # noqa: E402
    CONTRACT_VERSION,
    ChartRequest,
    GenerateRequest,
    ScriptRequest,
    chart,
    generate,
    health,
    script,
)

TOKEN = "test-token"
AUTH = f"Bearer {TOKEN}"

RM = {
    "fullName": "Kim Nam-joon",
    "gender": "M",
    "birthDate": "1994-09-12",
    "birthTime": "13:28",
    "timeKnown": True,
    "timezone": "Asia/Seoul",
    "utcOffset": 9,
    "city": "Seoul",
    "latitude": 37.5665,
    "longitude": 126.978,
}


@pytest.fixture(autouse=True)
def _token(monkeypatch):
    monkeypatch.setenv("ENGINE_SERVICE_TOKEN", TOKEN)


def body_of(response) -> dict:
    """The JSON payload of a JSONResponse."""
    return json.loads(response.body)


def chart_request(**overrides) -> ChartRequest:
    return ChartRequest(**{**RM, **overrides})


# ─────────────────────────────── auth ───────────────────────────────


def test_health_requires_a_token():
    with pytest.raises(HTTPException) as exc:
        health(authorization=None)
    assert exc.value.status_code == 401

    with pytest.raises(HTTPException) as exc:
        health(authorization="Bearer wrong")
    assert exc.value.status_code == 401


def test_health_fails_closed_when_unconfigured(monkeypatch):
    monkeypatch.delenv("ENGINE_SERVICE_TOKEN", raising=False)
    with pytest.raises(HTTPException) as exc:
        health(authorization=AUTH)
    assert exc.value.status_code == 503


def test_health_reports_contract_and_fonts():
    payload = body_of(health(authorization=AUTH))
    assert payload["status"] == "ok"
    assert payload["contractVersion"] == CONTRACT_VERSION
    # E1: the renderer must find fonts from the bundle, not only from the system path,
    # or the PDF silently degrades in a serverless function.
    assert payload["fontsDir"], "no DejaVu directory resolved"
    assert payload["engineVersion"] and payload["engineVersion"] != "0.0.0+unknown"


# ─────────────────────────────── /chart facts ───────────────────────────────


def test_chart_returns_the_known_correct_rm_chart():
    payload = body_of(chart(chart_request(), authorization=AUTH))

    assert [(p["stem"], p["branch"]) for p in payload["pillars"]] == [
        ("甲", "戌"), ("癸", "酉"), ("辛", "丑"), ("乙", "未"),
    ]
    assert [p["label"] for p in payload["pillars"]] == ["Year", "Month", "Day", "Hour"]
    assert payload["dayMaster"]["char"] == "辛"
    assert payload["dayMaster"]["element"] == "Metal"
    assert payload["dayMaster"]["polarity"] == "Yin"
    assert payload["strength"]
    assert payload["favorableElement"] == "Water"
    assert payload["favorableProvenance"]


def test_element_balance_percentages_sum_to_100():
    balance = body_of(chart(chart_request(), authorization=AUTH))["elementBalance"]
    assert set(balance) == {"Wood", "Fire", "Earth", "Metal", "Water"}
    assert abs(sum(balance.values()) - 100.0) < 0.5


def test_chart_surfaces_the_hour_boundary_caveat():
    """RM's birth sits seconds from a branch boundary; the reading must say so."""
    caveats = body_of(chart(chart_request(), authorization=AUTH))["caveats"]
    assert any("boundary" in c.lower() for c in caveats), caveats


def test_lucky_cues_come_from_the_engine_table():
    cues = body_of(chart(chart_request(), authorization=AUTH))["luckyCues"]
    assert cues["direction"] == "north"  # Water
    assert "black" in cues["colors"]
    assert cues["numbers"] == ["1", "6"]


# ─────────────────────────────── /chart rejections ───────────────────────────────


@pytest.mark.parametrize(
    "field, value, code",
    [
        ("gender", "X", "INVALID_GENDER"),
        ("birthDate", "12/09/1994", "INVALID_BIRTH_DATE"),
        ("birthTime", "1:28 PM", "INVALID_BIRTH_TIME"),
    ],
)
def test_chart_rejects_bad_input(field, value, code):
    response = chart(chart_request(**{field: value}), authorization=AUTH)
    assert response.status_code == 422
    assert body_of(response)["code"] == code


def test_chart_refuses_to_geocode_when_longitude_is_missing():
    """E2: never fall back to a live Nominatim lookup — it silently changes the chart."""
    response = chart(chart_request(longitude=None), authorization=AUTH)
    assert response.status_code == 422
    assert body_of(response)["code"] == "MISSING_LONGITUDE"


def test_chart_requires_a_timezone_or_offset():
    response = chart(chart_request(timezone=None, utcOffset=None), authorization=AUTH)
    assert response.status_code == 422
    assert body_of(response)["code"] == "MISSING_TIMEZONE"


def test_chart_rejects_a_wrong_contract_version():
    response = chart(chart_request(contractVersion=99), authorization=AUTH)
    assert response.status_code == 422
    assert body_of(response)["code"] == "CONTRACT_VERSION_MISMATCH"


# ─────────────────────────────── /generate ───────────────────────────────


def generate_request(**overrides) -> GenerateRequest:
    payload = {
        "contractVersion": CONTRACT_VERSION,
        "kind": "single",
        "tier": "deep",
        "uploadUrl": "http://127.0.0.1:9/never-listens",
        "profileA": RM,
    }
    payload.update(overrides)
    return GenerateRequest(**payload)


def test_generate_requires_auth():
    with pytest.raises(HTTPException) as exc:
        generate(generate_request(), authorization=None)
    assert exc.value.status_code == 401


def test_generate_rejects_a_wrong_contract_version():
    response = generate(generate_request(contractVersion=99), authorization=AUTH)
    assert response.status_code == 422
    assert body_of(response)["code"] == "CONTRACT_VERSION_MISMATCH"


def test_generate_rejects_an_unknown_kind():
    response = generate(generate_request(kind="triple"), authorization=AUTH)
    assert response.status_code == 422
    assert body_of(response)["code"] == "INVALID_KIND"


def test_generate_rejects_a_tier_that_does_not_belong_to_the_kind():
    response = generate(generate_request(tier="basic"), authorization=AUTH)
    assert response.status_code == 422
    assert body_of(response)["code"] == "INVALID_TIER"

    response = generate(
        generate_request(kind="compat", tier="essential", profileB=RM), authorization=AUTH
    )
    assert response.status_code == 422
    assert body_of(response)["code"] == "INVALID_TIER"


def test_generate_requires_two_people_for_a_compatibility_reading():
    response = generate(generate_request(kind="compat", tier="deep"), authorization=AUTH)
    assert response.status_code == 422
    assert body_of(response)["code"] == "COMPAT_NEEDS_TWO_PROFILES"


def test_generate_rejects_bad_birth_data_before_touching_the_upload():
    response = generate(
        generate_request(profileA={k: v for k, v in RM.items() if k != "longitude"}),
        authorization=AUTH,
    )
    assert response.status_code == 422
    assert body_of(response)["code"] == "MISSING_LONGITUDE"


def test_generate_surfaces_an_upload_failure_without_leaking_the_url():
    """The render succeeds; the upload target is unreachable. The error must be clean."""
    response = generate(generate_request(tier="sample"), authorization=AUTH)
    assert response.status_code in (502, 500)
    payload = body_of(response)
    assert payload["code"] in ("UPLOAD_FAILED", "RENDER_FAILED")
    assert "never-listens" not in payload["error"], "the presigned URL leaked into the error message"


# ─────────────────────────────── /script (the audio summary) ───────────────────────────────

APPROVED_MARKDOWN = """## Kiran — Deep Destiny Report

## Chart at a Glance

Day Master: Im (Yang Water, 壬水). Strength: Very Strong.

## Day Master Portrait

You meet the world with the patience of deep water. 丙午 sits in the year.

## Timing: Major Luck & Annual Windows

2026 leans toward your favourable element. 2027 is a year to build.

## Practical Guidance Summary

- Lean into Fire tones.
- Rest in the Metal months.

## Closing Note

Water finds its level. That is the whole of it.

## Sources & Limits

- knowledge/09-interpretation-method.md
"""


def test_script_requires_a_token():
    with pytest.raises(HTTPException) as exc:
        script(ScriptRequest(markdown=APPROVED_MARKDOWN), authorization=None)
    assert exc.value.status_code == 401


def test_script_derives_a_spoken_script_from_the_approved_markdown():
    payload = body_of(script(ScriptRequest(markdown=APPROVED_MARKDOWN), authorization=AUTH))
    spoken = payload["script"]

    assert payload["stats"]["chars"] == len(spoken)
    assert payload["stats"]["words"] > 10
    # Every promised section is narrated...
    for chapter in ("Chart at a Glance", "Day Master Portrait",
                    "Practical Guidance Summary", "Closing Note"):
        assert chapter in spoken
    # ...and reference material is not.
    assert "Sources & Limits" not in spoken
    # Hanja is translated, not deleted: the clause keeps its subject and its meaning.
    assert "Bing O sits in the year." in spoken
    # No markup, no citations, no stray glyphs.
    for marker in ("|", "**", "#", "knowledge/", "壬"):
        assert marker not in spoken


def test_script_returns_chunks_that_fit_a_tts_request():
    payload = body_of(script(ScriptRequest(markdown=APPROVED_MARKDOWN), authorization=AUTH))
    assert payload["chunks"], "expected at least one chunk"
    assert all(len(c) <= 2000 for c in payload["chunks"])


def test_script_is_deterministic():
    first = body_of(script(ScriptRequest(markdown=APPROVED_MARKDOWN), authorization=AUTH))
    second = body_of(script(ScriptRequest(markdown=APPROVED_MARKDOWN), authorization=AUTH))
    assert first["script"] == second["script"]


def test_script_rejects_a_wrong_contract_version():
    response = script(ScriptRequest(contractVersion=99, markdown=APPROVED_MARKDOWN), authorization=AUTH)
    assert response.status_code == 422
    assert body_of(response)["code"] == "CONTRACT_VERSION_MISMATCH"


def test_script_rejects_empty_text():
    response = script(ScriptRequest(markdown="   "), authorization=AUTH)
    assert response.status_code == 422
    assert body_of(response)["code"] == "EMPTY_MARKDOWN"


def test_script_is_empty_when_the_report_promises_no_audio():
    """A compatibility report, say. No audio is the honest answer, not a fallback script."""
    payload = body_of(script(ScriptRequest(markdown="## Career & Wealth\n\nBody.\n"), authorization=AUTH))
    assert payload["script"] == ""
    assert payload["chunks"] == []
    assert payload["stats"]["chars"] == 0
