"""P4 Task 3: app flow with the review queue (route functions called directly)."""
from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

import pytest
from fastapi import BackgroundTasks, HTTPException

from saju_web.store import generate_key

APP_PATH = Path(__file__).resolve().parents[2] / "tools" / "client_intake_app.py"


def load_app():
    spec = importlib.util.spec_from_file_location("client_intake_app_flow", APP_PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture
def app_mod(monkeypatch, tmp_path):
    monkeypatch.setenv("SAJU_INTAKE_KEY", generate_key())
    monkeypatch.setenv("SAJU_INTAKE_DIR", str(tmp_path))
    return load_app()


def single(**over):
    kw = dict(name="Test Person", dob="1990-06-15", birth_time="10:00", location="Seoul",
              utc_offset="9", email="t@example.com", gender="F", marriage_status="single",
              tier="essential", main_concern="", timezone="")
    kw.update(over)
    return kw


def run(mod, bg=None, **kw):
    return asyncio.run(mod.generate(bg or BackgroundTasks(), **kw))


def test_import_without_key_raises(monkeypatch, tmp_path):
    monkeypatch.delenv("SAJU_INTAKE_KEY", raising=False)
    monkeypatch.setenv("SAJU_INTAKE_DIR", str(tmp_path))
    with pytest.raises(RuntimeError, match="SAJU_INTAKE_KEY"):
        load_app()


@pytest.mark.parametrize("over", [
    {"name": "  "}, {"tier": "bogus"}, {"gender": "X"}, {"dob": "1990-02-31"},
    {"birth_time": "25:99"}, {"utc_offset": "", "timezone": ""},
    {"timezone": "Mars/Base", "utc_offset": ""}, {"tier": "deep", "main_concern": ""},
    {"utc_offset": "abc"},
])
def test_invalid_generate_is_400_and_stores_nothing(app_mod, over):
    with pytest.raises(HTTPException) as exc:
        run(app_mod, **single(**over))
    assert exc.value.status_code == 400
    assert app_mod.STORE.list_intakes() == []


def test_sample_returns_pdf_and_is_approved(app_mod):
    resp = run(app_mod, **single(tier="sample"))
    assert Path(resp.path).read_bytes()[:4] == b"%PDF"
    row = app_mod.STORE.list_intakes()[0]
    assert row["status"] == "approved"
    assert Path(resp.path).resolve().is_relative_to(app_mod.FILES_DIR.resolve())


def test_paid_single_is_202_then_draft_ready(app_mod):
    bg = BackgroundTasks()
    resp = run(app_mod, bg, **single(tier="essential"))
    assert resp.status_code == 202
    import json
    body = json.loads(resp.body)
    assert body["status"] == "received" and "human reader" in body["message"]
    assert app_mod.STORE.get_intake(body["intake_id"])["status"] == "received"
    asyncio.run(bg())
    row = app_mod.STORE.get_intake(body["intake_id"])
    assert row["status"] == "draft_ready" and Path(row["pdf_path"]).exists()
    # PII is not in plaintext in the sqlite file
    assert b"Test Person" not in app_mod.STORE.db_path.read_bytes()


def test_compat_basic_is_202(app_mod):
    bg = BackgroundTasks()
    resp = asyncio.run(app_mod.compat_generate(
        bg, name_a="A", dob_a="1990-06-15", birth_time_a="10:00", location_a="Seoul",
        utc_offset_a=9.0, gender_a="M", name_b="B", dob_b="1992-03-20", birth_time_b="14:00",
        location_b="Seoul", utc_offset_b=9.0, gender_b="F", email="t@example.com",
        main_concern="", favorable_element_a="", favorable_element_b="",
        timezone_a="", timezone_b="", tier="basic"))
    assert resp.status_code == 202
    asyncio.run(bg())
    assert app_mod.STORE.list_intakes()[0]["status"] == "draft_ready"


def test_failed_generation_stores_class_name_only(app_mod, monkeypatch):
    import saju_web.jobs as jobs

    def boom(*a, **k):
        raise KeyError("secret-name")
    monkeypatch.setattr(jobs, "render_single", boom)
    bg = BackgroundTasks()
    resp = run(app_mod, bg, **single())
    asyncio.run(bg())
    import json
    row = app_mod.STORE.get_intake(json.loads(resp.body)["intake_id"])
    assert row["status"] == "failed" and row["error"] == "KeyError"


def test_report_token_flow(app_mod):
    with pytest.raises(HTTPException) as exc:
        app_mod.report("nope")
    assert exc.value.status_code == 404
    bg = BackgroundTasks()
    import json
    iid = json.loads(run(app_mod, bg, **single()).body)["intake_id"]
    asyncio.run(bg())
    token = app_mod.STORE.issue_token(iid)
    resp = app_mod.report(token)
    assert Path(resp.path).read_bytes()[:4] == b"%PDF"
    # unapproved (received) intake has no token -> same 404
    iid2 = json.loads(run(app_mod, **single()).body)["intake_id"]
    assert app_mod.STORE.get_intake(iid2)["status"] == "received"


def test_cors_hardened(app_mod):
    cors = [m for m in app_mod.app.user_middleware if m.cls.__name__ == "CORSMiddleware"][0]
    assert cors.kwargs["allow_credentials"] is False
    assert cors.kwargs["allow_headers"] == ["Content-Type"]
    assert cors.kwargs["allow_methods"] == ["GET", "POST"]
