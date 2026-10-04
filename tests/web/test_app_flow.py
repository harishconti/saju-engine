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


def test_missing_browser_is_actionable_failure(app_mod, monkeypatch, caplog):
    import json
    import logging

    import saju_html.renderer as renderer

    def no_browser(*a, **k):
        raise RuntimeError("Executable doesn't exist for Test Person 1990-06-15")
    monkeypatch.setattr(renderer, "html_to_pdf", no_browser)
    monkeypatch.delenv("SAJU_PDF_FALLBACK", raising=False)
    monkeypatch.delenv("SAJU_PDF_BACKEND", raising=False)
    bg = BackgroundTasks()
    resp = run(app_mod, bg, **single(tier="essential"))
    with caplog.at_level(logging.ERROR, logger="saju.jobs"):
        asyncio.run(bg())
    iid = json.loads(resp.body)["intake_id"]
    row = app_mod.STORE.get_intake(iid)
    assert row["status"] == "failed" and row["error"] == "PdfBackendUnavailable"
    assert not row.get("pdf_path")
    assert not list((app_mod.FILES_DIR / str(iid)).glob("*.pdf"))
    assert "playwright install chromium" in caplog.text
    assert "Test Person" not in caplog.text and "1990-06-15" not in caplog.text


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


# ---- review fix round 1 ------------------------------------------------------

BAD_OFFSETS = ["nan", "inf", "-inf", "99", "-30", "1e308"]


@pytest.mark.parametrize("off", BAD_OFFSETS)
def test_single_rejects_bad_offset(app_mod, off):
    with pytest.raises(HTTPException) as exc:
        run(app_mod, **single(utc_offset=off))
    assert exc.value.status_code == 400
    assert app_mod.STORE.list_intakes() == []


def _compat(mod, **over):
    kw = dict(name_a="A", dob_a="1990-06-15", birth_time_a="10:00", location_a="Seoul",
              utc_offset_a=9.0, gender_a="M", name_b="B", dob_b="1992-03-20",
              birth_time_b="14:00", location_b="Seoul", utc_offset_b=9.0, gender_b="F",
              email="t@example.com", main_concern="", favorable_element_a="",
              favorable_element_b="", timezone_a="", timezone_b="", tier="basic")
    kw.update(over)
    return asyncio.run(mod.compat_generate(BackgroundTasks(), **kw))


@pytest.mark.parametrize("off", [float("nan"), float("inf"), 99.0, -30.0, 1e308])
@pytest.mark.parametrize("who", ["a", "b"])
def test_compat_rejects_bad_offset(app_mod, off, who):
    with pytest.raises(HTTPException) as exc:
        _compat(app_mod, **{f"utc_offset_{who}": off})
    assert exc.value.status_code == 400
    assert app_mod.STORE.list_intakes() == []


def test_offset_boundaries_accepted(app_mod):
    assert run(app_mod, **single(utc_offset="-12")).status_code == 202
    assert run(app_mod, **single(utc_offset="14")).status_code == 202


@pytest.mark.parametrize("over", [
    {"name": "x" * 121}, {"location": "x" * 121}, {"email": "x" * 255},
    {"main_concern": "x" * 2001},
])
def test_single_field_length_limits(app_mod, over):
    with pytest.raises(HTTPException) as exc:
        run(app_mod, **single(**over))
    assert exc.value.status_code == 400
    assert app_mod.STORE.list_intakes() == []


@pytest.mark.parametrize("over", [
    {"name_a": "x" * 121}, {"name_b": "x" * 121}, {"location_a": "x" * 121},
    {"email": "x" * 255}, {"main_concern": "x" * 2001},
])
def test_compat_field_length_limits(app_mod, over):
    with pytest.raises(HTTPException) as exc:
        _compat(app_mod, **over)
    assert exc.value.status_code == 400
    assert app_mod.STORE.list_intakes() == []


def test_limits_at_boundary_accepted(app_mod):
    resp = run(app_mod, **single(name="x" * 120, main_concern="y" * 2000))
    assert resp.status_code == 202


def test_unknown_paid_style_tier_is_queued_not_sync(app_mod, monkeypatch):
    # Fail-safe: anything but "sample" is queued for review, never rendered inline.
    monkeypatch.setattr(app_mod, "SINGLE_TIERS", app_mod.SINGLE_TIERS + ("future",))
    resp = run(app_mod, **single(tier="future"))
    assert resp.status_code == 202
    assert app_mod.STORE.list_intakes()[0]["status"] == "received"


def test_report_refuses_pdf_outside_files_root(app_mod, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside") / "secret.pdf"
    outside.write_bytes(b"%PDF-1.4 secret")
    import json
    iid = json.loads(run(app_mod, **single()).body)["intake_id"]
    app_mod.STORE.set_status(iid, "draft_ready", pdf_path=str(outside))
    token = app_mod.STORE.issue_token(iid)
    with pytest.raises(HTTPException) as exc:
        app_mod.report(token)
    assert exc.value.status_code == 404


def test_failure_log_has_no_exception_message(app_mod, monkeypatch, caplog):
    import logging
    import saju_web.jobs as jobs

    def boom(*a, **k):
        raise ValueError("PII-" + "SECRET-1990-06-15")  # built at runtime
    monkeypatch.setattr(jobs, "render_single", boom)
    bg = BackgroundTasks()
    run(app_mod, bg, **single())
    with caplog.at_level(logging.ERROR, logger="saju.jobs"):
        asyncio.run(bg())
    text = caplog.text
    assert "ValueError" in text and "boom" in text  # class + frames
    assert "PII-SECRET" not in text


# ---- final fix wave A --------------------------------------------------------

def test_purge_removes_whole_order_dir_after_real_render(app_mod):
    import json
    from datetime import datetime, timedelta, timezone
    bg = BackgroundTasks()
    iid = json.loads(run(app_mod, bg, **single(name="Zebediah Quux")).body)["intake_id"]
    asyncio.run(bg())
    d = app_mod.FILES_DIR / str(iid)
    assert d.is_dir() and any(d.iterdir())
    future = datetime.now(timezone.utc) + timedelta(days=400)
    assert app_mod.STORE.purge_older_than(180, now=future) == 1
    assert not d.exists()
    for f in app_mod.FILES_DIR.rglob("*"):
        if f.is_file():
            assert b"Zebediah" not in f.read_bytes()


def test_generate_draft_on_purged_row_is_quiet(app_mod):
    from saju_web.jobs import generate_draft
    generate_draft(app_mod.STORE, 9999, app_mod.FILES_DIR)  # no raise


def test_stale_dir_removed_before_render_of_received_row(app_mod):
    from saju_web.jobs import generate_draft
    iid = app_mod.STORE.add_intake(kind="single", tier="essential",
                                   pii={"name": "N", "email": "e@x.io", "main_concern": ""},
                                   birth={"dob": "1990-06-15", "birth_time": "10:00",
                                          "location": "Seoul", "utc_offset": "9",
                                          "timezone": "", "gender": "F"})
    stale = app_mod.FILES_DIR / str(iid)
    stale.mkdir(parents=True)
    (stale / "old-client.md").write_text("old")
    generate_draft(app_mod.STORE, iid, app_mod.FILES_DIR)
    assert not (stale / "old-client.md").exists()


def test_access_log_filter_redacts_report_token(app_mod):
    import logging
    rec = logging.LogRecord("uvicorn.access", logging.INFO, "", 0,
                            '%s - "%s %s HTTP/%s" %d',
                            ("127.0.0.1:1", "GET", "/report/SECRETTOKEN123", "1.1", 200), None)
    assert app_mod.RedactReportTokens().filter(rec)
    out = rec.getMessage()
    assert "SECRETTOKEN123" not in out and "/report/[redacted]" in out
    assert "/generate" in app_mod.redact_report_tokens("POST /generate")


# ---- final fix wave B --------------------------------------------------------

def test_queue_cap_503_single_and_compat(app_mod, monkeypatch):
    monkeypatch.setenv("SAJU_MAX_QUEUE", "2")
    assert run(app_mod, **single()).status_code == 202
    assert run(app_mod, **single()).status_code == 202
    with pytest.raises(HTTPException) as exc:
        run(app_mod, **single())
    assert exc.value.status_code == 503 and "lot of requests" in exc.value.detail
    with pytest.raises(HTTPException) as exc:
        _compat(app_mod)
    assert exc.value.status_code == 503
    assert len(app_mod.STORE.list_intakes()) == 2
    # the free sample is not subject to the queue cap
    assert Path(run(app_mod, **single(tier="sample")).path).exists()


def test_sample_503_when_no_render_slot(app_mod, monkeypatch):
    import threading
    monkeypatch.setattr(app_mod.jobs, "RENDER_SLOTS", threading.BoundedSemaphore(1))
    monkeypatch.setattr(app_mod, "SAMPLE_SLOT_WAIT", 0.05)
    app_mod.jobs.RENDER_SLOTS.acquire()
    with pytest.raises(HTTPException) as exc:
        run(app_mod, **single(tier="sample"))
    assert exc.value.status_code == 503


@pytest.mark.parametrize("over", [
    {"marriage_status": "complicated"}, {"marriage_status": ""},
    {"email": "not-an-email"}, {"email": "a@b"}, {"email": "a b@c.io"},
])
def test_single_enum_and_email_validation(app_mod, over):
    with pytest.raises(HTTPException) as exc:
        run(app_mod, **single(**over))
    assert exc.value.status_code == 400
    assert app_mod.STORE.list_intakes() == []


def test_marriage_status_is_encrypted(app_mod):
    import json
    iid = json.loads(run(app_mod, **single(marriage_status="widowed")).body)["intake_id"]
    row = app_mod.STORE.get_intake(iid)
    assert row["pii"]["marriage_status"] == "widowed"
    assert "marriage_status" not in row["birth"]
    assert b"widowed" not in app_mod.STORE.db_path.read_bytes()


@pytest.mark.parametrize("over", [
    {"favorable_element_a": "Wind"}, {"favorable_element_b": "Gold"},
    {"tier": "premium"}, {"email": "nope"},
])
def test_compat_validation(app_mod, over):
    with pytest.raises(HTTPException) as exc:
        _compat(app_mod, **over)
    assert exc.value.status_code == 400
    assert app_mod.STORE.list_intakes() == []


def test_compat_element_case_insensitive_and_normalised(app_mod):
    _compat(app_mod, favorable_element_a="wATER", favorable_element_b="")
    row = app_mod.STORE.get_intake(app_mod.STORE.list_intakes()[0]["id"])
    assert row["birth"]["favorable_element_a"] == "Water"


def test_compat_offset_optional_with_timezone(app_mod):
    _compat(app_mod, utc_offset_a="", utc_offset_b="", timezone_a="Asia/Seoul",
            timezone_b="Asia/Seoul")
    assert len(app_mod.STORE.list_intakes()) == 1
    with pytest.raises(HTTPException) as exc:
        _compat(app_mod, utc_offset_a="", timezone_a="")
    assert exc.value.status_code == 400


def test_requeue_pending_recovers_received_and_stale_generating(app_mod):
    import sqlite3
    from datetime import datetime, timedelta, timezone
    st = app_mod.STORE
    mk = lambda: st.add_intake(kind="single", tier="essential",
                               pii={"name": "N", "email": "e@x.io", "main_concern": ""},
                               birth={"dob": "1990-06-15", "birth_time": "10:00", "location": "Seoul",
                                      "utc_offset": "9", "timezone": "", "gender": "F"})
    rec, stale, live, done = mk(), mk(), mk(), mk()
    st.set_status(stale, "generating"); st.set_status(live, "generating")
    st.set_status(done, "draft_ready", pdf_path="x")
    old = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
    with sqlite3.connect(st.db_path) as c:
        c.execute("UPDATE intake SET updated_at=? WHERE id=?", (old, stale))
    jobs_run = []
    ids = app_mod.requeue_pending(spawn=lambda fn: jobs_run.append(fn))
    assert sorted(ids) == sorted([rec, stale])
    for fn in jobs_run:
        fn()
    assert st.get_intake(rec)["status"] == "draft_ready"
    assert st.get_intake(stale)["status"] == "draft_ready"
    assert st.get_intake(live)["status"] == "generating"


def test_render_slots_bound_concurrency(app_mod, monkeypatch):
    import threading, time
    import saju_web.jobs as jobs
    monkeypatch.setattr(jobs, "RENDER_SLOTS", threading.BoundedSemaphore(1))
    cur = {"n": 0, "max": 0}
    lock = threading.Lock()

    def slow(*a, **k):
        with lock:
            cur["n"] += 1; cur["max"] = max(cur["max"], cur["n"])
        time.sleep(0.1)
        with lock:
            cur["n"] -= 1
        raise RuntimeError("stop")
    monkeypatch.setattr(jobs, "render_single", slow)
    ids = [json_id(run(app_mod, **single())) for _ in range(3)]
    ts = [threading.Thread(target=jobs.generate_draft, args=(app_mod.STORE, i, app_mod.FILES_DIR)) for i in ids]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert cur["max"] == 1


def json_id(resp):
    import json
    return json.loads(resp.body)["intake_id"]
