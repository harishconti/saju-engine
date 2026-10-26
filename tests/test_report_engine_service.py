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
    _validate_upload_url,
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
    # The upload allowlist fails closed. Give the suite a small, explicit one; tests that
    # exercise the missing-allowlist path delete it themselves.
    monkeypatch.setenv("SAJU_UPLOAD_HOSTS", "pdf.test,md.test,html.test,127.0.0.1")
    monkeypatch.delenv("R2_ENDPOINT", raising=False)
    monkeypatch.delenv("SAJU_UPLOAD_BUCKET", raising=False)


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


def test_generate_renders_the_reading_when_asked(monkeypatch):
    """With `htmlUploadUrl`, the engine PUTs the web document beside the PDF.

    The web document is the artefact the client reads and can save as one file; it is rendered
    from the same markdown as the PDF, so the two cannot disagree about a word.
    """
    import api.index as svc

    uploaded: dict = {}

    def fake_upload(artifact, url, *, content_type="application/pdf", timeout=60.0):
        uploaded[str(url)] = (artifact.read_bytes(), content_type)

    monkeypatch.setattr(svc, "_upload", fake_upload)
    response = generate(
        generate_request(uploadUrl="https://pdf.test/put", mdUploadUrl="https://md.test/put",
                         htmlUploadUrl="https://html.test/put"),
        authorization=AUTH,
    )
    assert response.status_code == 200, body_of(response)

    body = body_of(response)
    assert set(uploaded) == {"https://pdf.test/put", "https://md.test/put", "https://html.test/put"}

    document, content_type = uploaded["https://html.test/put"]
    assert content_type.startswith("text/html")
    assert document.startswith(b"<!DOCTYPE html")
    # Self-contained and private, which is what makes it safe to serve and to download.
    assert b"noindex" in document
    assert b"<script" not in document and b"<link " not in document
    assert b'name="viewport"' in document
    # Integrity metadata for the reading travels with the PDF's.
    assert body["htmlBytes"] == len(document)
    assert body["htmlSha256"] and len(body["htmlSha256"]) == 64


def test_generate_renders_the_reading_for_a_compatibility_report(monkeypatch):
    """A compatibility order gets the same reading a single-chart order gets.

    The two-chart reading renders through the very same `build_pdf` /
    `markdown_to_html(web=True)` as every other tier — `md_to_saju_compat_pdf.py` is a thin wrapper
    over that renderer — so there was never a reason to withhold the web document. But the engine
    returned `html_path=None` for `kind="compat"`, and the webapp did not ask for one either, so the
    compat product shipped a PDF and no reading. Owner, 2026-10-17: *"I see html reports essential and
    deep but not in comparability reports."*
    """
    import api.index as svc

    uploaded: dict = {}

    def fake_upload(artifact, url, *, content_type="application/pdf", timeout=60.0):
        uploaded[str(url)] = (artifact.read_bytes(), content_type)

    monkeypatch.setattr(svc, "_upload", fake_upload)
    response = generate(
        generate_request(kind="compat", tier="basic",
                         profileB={**RM, "fullName": "Arun", "gender": "F",
                                   "birthDate": "1992-03-20", "birthTime": "14:00"},
                         uploadUrl="https://pdf.test/put",
                         htmlUploadUrl="https://html.test/put"),
        authorization=AUTH,
    )
    assert response.status_code == 200, body_of(response)

    body = body_of(response)
    assert set(uploaded) == {"https://pdf.test/put", "https://html.test/put"}
    document, content_type = uploaded["https://html.test/put"]
    assert content_type.startswith("text/html")
    assert document.startswith(b"<!DOCTYPE html")
    # Self-contained and private, exactly like the single-chart reading.
    assert b"noindex" in document
    assert b"<script" not in document and b"<link " not in document
    assert b'name="viewport"' in document
    # It really is the two-chart document: both partners and the composite score are in it.
    assert "Kim Nam-joon" in document.decode("utf-8")
    assert "Arun" in document.decode("utf-8")
    assert "Compatibility Reading" in document.decode("utf-8")
    # Integrity metadata travels with the PDF's, so a caller can tell "not uploaded" from "not asked".
    assert body["htmlBytes"] == len(document)
    assert body["htmlSha256"] and len(body["htmlSha256"]) == 64


def test_a_failed_web_document_upload_still_delivers_the_report(monkeypatch):
    """Best-effort, like the markdown: losing the reading must not lose the order.

    The response says `htmlSha256: null`, so a caller can tell "not uploaded" from "not asked
    for" without guessing.
    """
    import api.index as svc
    from fastapi import HTTPException

    def fake_upload(artifact, url, *, content_type="application/pdf", timeout=60.0):
        if content_type.startswith("text/html"):
            raise HTTPException(status_code=502, detail="storage refused the document")

    monkeypatch.setattr(svc, "_upload", fake_upload)
    response = generate(
        generate_request(uploadUrl="https://pdf.test/put", htmlUploadUrl="https://html.test/put"),
        authorization=AUTH,
    )
    assert response.status_code == 200, body_of(response)
    body = body_of(response)
    assert body["htmlSha256"] is None and body["htmlBytes"] is None
    assert body["sha256"], "the PDF still reported its own integrity metadata"


def test_no_web_document_is_rendered_unless_asked_for(monkeypatch):
    """A caller that does not ask pays nothing for it — and the response says so."""
    import api.index as svc

    uploaded: dict = {}

    def fake_upload(artifact, url, *, content_type="application/pdf", timeout=60.0):
        uploaded[str(url)] = content_type

    monkeypatch.setattr(svc, "_upload", fake_upload)
    response = generate(generate_request(uploadUrl="https://pdf.test/put"), authorization=AUTH)
    assert response.status_code == 200, body_of(response)
    assert list(uploaded) == ["https://pdf.test/put"]
    assert body_of(response)["htmlSha256"] is None


def test_generate_surfaces_an_upload_failure_without_leaking_the_url():
    """The render succeeds; the upload target is unreachable. The error must be clean."""
    response = generate(generate_request(tier="sample"), authorization=AUTH)
    assert response.status_code in (502, 500)
    payload = body_of(response)
    assert payload["code"] in ("UPLOAD_FAILED", "RENDER_FAILED")
    assert "never-listens" not in payload["error"], "the presigned URL leaked into the error message"


# ─────────────────────── upload allowlist (SSRF guard) ───────────────────────


def test_generate_refuses_an_upload_url_on_an_unlisted_host():
    response = generate(generate_request(uploadUrl="https://evil.example/put"), authorization=AUTH)
    assert response.status_code == 422
    payload = body_of(response)
    assert payload["code"] == "UPLOAD_URL_NOT_ALLOWED"
    assert "evil.example" not in payload["error"], "the target host leaked into the error"


def test_generate_refuses_plain_http_to_a_remote_host():
    response = generate(generate_request(uploadUrl="http://pdf.test/put"), authorization=AUTH)
    assert response.status_code == 422
    assert body_of(response)["code"] == "UPLOAD_URL_INSECURE"


def test_generate_refuses_an_upload_url_with_embedded_credentials():
    response = generate(
        generate_request(uploadUrl="https://user:pass@pdf.test/put"), authorization=AUTH
    )
    assert response.status_code == 422
    assert body_of(response)["code"] == "UPLOAD_URL_INVALID"


def test_generate_refuses_a_markdown_upload_to_an_unlisted_host():
    response = generate(
        generate_request(mdUploadUrl="https://evil.example/put"), authorization=AUTH
    )
    assert response.status_code == 422
    assert body_of(response)["code"] == "UPLOAD_URL_NOT_ALLOWED"


def test_generate_fails_closed_without_an_upload_allowlist(monkeypatch):
    monkeypatch.delenv("SAJU_UPLOAD_HOSTS", raising=False)
    monkeypatch.delenv("R2_ENDPOINT", raising=False)
    response = generate(generate_request(uploadUrl="https://pdf.test/put"), authorization=AUTH)
    assert response.status_code == 503
    assert body_of(response)["code"] == "UPLOAD_HOSTS_UNCONFIGURED"


def test_the_r2_endpoint_is_itself_an_allowlist(monkeypatch):
    monkeypatch.delenv("SAJU_UPLOAD_HOSTS", raising=False)
    monkeypatch.setenv("R2_ENDPOINT", "https://account.r2.cloudflarestorage.com")
    assert _validate_upload_url("https://account.r2.cloudflarestorage.com/bucket/x.pdf") is None
    assert _validate_upload_url("https://other.r2.cloudflarestorage.com/bucket/x.pdf") == (
        "UPLOAD_URL_NOT_ALLOWED"
    )


def test_the_r2_endpoint_allows_virtual_hosted_bucket_urls(monkeypatch):
    # The webapp's S3 client presigns virtual-hosted style: the bucket is a subdomain of the
    # endpoint, not a path segment. Setting R2_ENDPOINT alone must cover those URLs.
    monkeypatch.delenv("SAJU_UPLOAD_HOSTS", raising=False)
    monkeypatch.setenv("R2_ENDPOINT", "https://account.r2.cloudflarestorage.com")
    assert _validate_upload_url("https://bucket.account.r2.cloudflarestorage.com/x.pdf") is None
    assert _validate_upload_url("https://a.b.account.r2.cloudflarestorage.com/x.pdf") == (
        "UPLOAD_URL_NOT_ALLOWED"
    )
    assert _validate_upload_url("https://bucket.other.r2.cloudflarestorage.com/x.pdf") == (
        "UPLOAD_URL_NOT_ALLOWED"
    )


def test_generate_scopes_uploads_to_the_configured_bucket(monkeypatch):
    monkeypatch.setenv("SAJU_UPLOAD_BUCKET", "saju-engine-dev")
    assert _validate_upload_url("https://pdf.test/saju-engine-dev/reports/x.pdf") is None
    assert _validate_upload_url("https://pdf.test/other-bucket/x.pdf") == "UPLOAD_PATH_NOT_ALLOWED"


def test_bucket_scope_accepts_a_virtual_hosted_bucket(monkeypatch):
    monkeypatch.delenv("SAJU_UPLOAD_HOSTS", raising=False)
    monkeypatch.setenv("R2_ENDPOINT", "https://account.r2.cloudflarestorage.com")
    monkeypatch.setenv("SAJU_UPLOAD_BUCKET", "saju-engine-dev")
    assert _validate_upload_url(
        "https://saju-engine-dev.account.r2.cloudflarestorage.com/reports/x.pdf"
    ) is None
    assert _validate_upload_url(
        "https://other-bucket.account.r2.cloudflarestorage.com/reports/x.pdf"
    ) == "UPLOAD_PATH_NOT_ALLOWED"


# ─────────────────────── request-size and field bounds ───────────────────────


def test_script_request_caps_markdown_length():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ScriptRequest(markdown="x" * 1_000_001)


def test_profile_rejects_out_of_range_coordinates():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ChartRequest(**{**RM, "longitude": 200})
    with pytest.raises(ValidationError):
        ChartRequest(**{**RM, "latitude": -91})


def test_body_size_middleware_rejects_an_oversized_content_length():
    import asyncio

    from api.index import DEFAULT_MAX_REQUEST_BYTES, MaxBodySizeMiddleware

    seen = {"ran": False}
    sent = []

    async def app(scope, receive, send):  # pragma: no cover - must not be reached
        seen["ran"] = True

    async def receive():  # pragma: no cover - must not be reached
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http",
        "headers": [(b"content-length", str(DEFAULT_MAX_REQUEST_BYTES + 1).encode())],
    }
    asyncio.run(MaxBodySizeMiddleware(app)(scope, receive, send))

    assert seen["ran"] is False
    assert sent[0]["status"] == 413
    assert json.loads(sent[1]["body"])["code"] == "REQUEST_TOO_LARGE"


def test_body_size_middleware_counts_a_chunked_body():
    import asyncio

    from api.index import DEFAULT_MAX_REQUEST_BYTES, MaxBodySizeMiddleware

    seen = {"ran": False}
    sent = []

    async def app(scope, receive, send):  # pragma: no cover - must not be reached
        seen["ran"] = True
        await receive()

    async def receive():
        return {
            "type": "http.request",
            "body": b"x" * (DEFAULT_MAX_REQUEST_BYTES + 1),
            "more_body": False,
        }

    async def send(message):
        sent.append(message)

    asyncio.run(MaxBodySizeMiddleware(app)({"type": "http", "headers": []}, receive, send))

    # No content-length, so the app is entered and the limit is enforced while it reads:
    # that is the path this test exists for.
    assert seen["ran"] is True
    assert sent[0]["status"] == 413
    assert json.loads(sent[1]["body"])["code"] == "REQUEST_TOO_LARGE"



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
