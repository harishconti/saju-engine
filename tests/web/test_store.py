"""Tests for saju_web.store (encrypted SQLite intake store)."""
from datetime import datetime, timedelta, timezone

import pytest

pytest.importorskip("cryptography")

from saju_web.store import IntakeStore, generate_key  # noqa: E402

PII = {"name": "Alice Kim", "email": "alice@example.com", "concern": "secret worry about career"}
BIRTH = {"dob": "1990-05-01", "birth_time": "10:30", "location": "Seoul", "utc_offset": "+09:00"}


@pytest.fixture
def store(tmp_path):
    return IntakeStore(tmp_path / "intake.sqlite", generate_key().encode())


def _add(store):
    return store.add_intake(kind="single", tier="essential", pii=PII, birth=BIRTH)


def test_roundtrip_decrypts(store):
    i = _add(store)
    row = store.get_intake(i)
    assert row["pii"] == PII
    assert row["birth"] == BIRTH
    assert row["status"] == "received" and row["kind"] == "single" and row["tier"] == "essential"
    assert row["pdf_path"] is None and row["error"] is None
    assert row["created_at"].endswith("+00:00")


def test_raw_db_has_no_plaintext_pii(tmp_path):
    p = tmp_path / "i.sqlite"
    s = IntakeStore(p, generate_key().encode())
    _add(s)
    data = b"".join(f.read_bytes() for f in tmp_path.glob("i.sqlite*"))
    for needle in (b"alice@example.com", b"Alice Kim", b"secret worry"):
        assert needle not in data
    assert b"1990-05-01" in data  # birth stays plain


def test_wrong_key_raises(tmp_path):
    p = tmp_path / "i.sqlite"
    i = _add(IntakeStore(p, generate_key().encode()))
    with pytest.raises(Exception):
        IntakeStore(p, generate_key().encode()).get_intake(i)


def test_from_env(tmp_path, monkeypatch):
    monkeypatch.delenv("SAJU_INTAKE_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SAJU_INTAKE_KEY"):
        IntakeStore.from_env(tmp_path / "a.sqlite")
    monkeypatch.setenv("SAJU_INTAKE_KEY", "not-a-key")
    with pytest.raises(RuntimeError, match="SAJU_INTAKE_KEY"):
        IntakeStore.from_env(tmp_path / "a.sqlite")
    monkeypatch.setenv("SAJU_INTAKE_KEY", generate_key())
    assert IntakeStore.from_env(tmp_path / "a.sqlite")


def test_status_transitions(store):
    i = _add(store)
    store.set_status(i, "draft_ready", pdf_path="/x.pdf")
    r = store.get_intake(i)
    assert r["status"] == "draft_ready" and r["pdf_path"] == "/x.pdf"
    store.set_status(i, "failed", error="boom")
    assert store.get_intake(i)["error"] == "boom"
    with pytest.raises(ValueError):
        store.set_status(i, "bogus")
    with pytest.raises(ValueError):
        store.add_intake(kind="weird", tier="t", pii={}, birth={})


def test_token_flow(tmp_path):
    p = tmp_path / "i.sqlite"
    s = IntakeStore(p, generate_key().encode())
    i = _add(s)
    with pytest.raises(ValueError):
        s.issue_token(i)  # still "received"
    s.set_status(i, "draft_ready")
    tok = s.issue_token(i)
    assert s.get_intake(i)["status"] == "approved"
    assert s.resolve_token(tok)["id"] == i
    assert s.resolve_token("nope") is None
    data = b"".join(f.read_bytes() for f in tmp_path.glob("i.sqlite*"))
    assert tok.encode() not in data
    with pytest.raises(ValueError):
        s.issue_token(i)  # already approved


def test_list_intakes_minimal_pii(store):
    i = _add(store)
    store.set_status(i, "draft_ready")
    _add(store)
    rows = store.list_intakes()
    assert len(rows) == 2
    assert [r["id"] for r in store.list_intakes("draft_ready")] == [i]
    for r in rows:
        assert r["name"] == "Alice Kim"
        assert "email" not in str(r) and "concern" not in str(r) and "pii" not in r


def test_purge(tmp_path):
    s = IntakeStore(tmp_path / "i.sqlite", generate_key().encode())
    (tmp_path / "files").mkdir(exist_ok=True)
    old_pdf = tmp_path / "files" / "old.pdf"
    old_md = tmp_path / "files" / "old.md"
    new_pdf = tmp_path / "files" / "new.pdf"
    for f in (old_pdf, old_md, new_pdf):
        f.write_text("x")
    old, new = _add(s), _add(s)
    s.set_status(old, "draft_ready", pdf_path=str(old_pdf))
    s.set_status(new, "draft_ready", pdf_path=str(new_pdf))
    now = datetime.now(timezone.utc) + timedelta(days=200)
    # make "new" recent relative to now
    import sqlite3
    with sqlite3.connect(tmp_path / "i.sqlite") as c:
        c.execute("UPDATE intake SET created_at=? WHERE id=?", ((now - timedelta(days=5)).isoformat(), new))
    assert s.purge_older_than(180, now=now) == 1
    assert not old_pdf.exists() and not old_md.exists()
    assert new_pdf.exists()
    assert [r["id"] for r in s.list_intakes()] == [new]
    with pytest.raises(KeyError):
        s.get_intake(old)


def test_set_status_clears_error_on_retry(store):
    i = _add(store)
    store.set_status(i, "failed", error="RuntimeError")
    assert store.get_intake(i)["error"] == "RuntimeError"
    store.set_status(i, "generating")
    assert store.get_intake(i)["error"] is None
    store.set_status(i, "failed", error="X")
    store.set_status(i, "draft_ready", pdf_path="/x.pdf")
    r = store.get_intake(i)
    assert r["error"] is None and r["pdf_path"] == "/x.pdf"


def test_set_status_explicit_none_clears_and_unset_keeps(store):
    i = _add(store)
    store.set_status(i, "draft_ready", pdf_path="/x.pdf")
    store.set_status(i, "failed", error="E")
    assert store.get_intake(i)["pdf_path"] == "/x.pdf"  # kept
    store.set_status(i, "failed", pdf_path=None)
    r = store.get_intake(i)
    assert r["pdf_path"] is None and r["error"] == "E"


def test_set_status_unknown_id_raises(store):
    with pytest.raises(KeyError):
        store.set_status(999, "generating")


def test_set_status_approved_forbidden_and_sample_path(tmp_path):
    s = IntakeStore(tmp_path / "i.sqlite", generate_key().encode())
    i = _add(s)
    with pytest.raises(ValueError, match="issue_token"):
        s.set_status(i, "approved")
    s.mark_approved_without_token(i)
    r = s.get_intake(i)
    assert r["status"] == "approved"
    import sqlite3
    with sqlite3.connect(tmp_path / "i.sqlite") as c:
        row = c.execute("SELECT token_sha256, approved_at FROM intake WHERE id=?", (i,)).fetchone()
    assert row[0] is None and row[1]
    assert s.resolve_token("") is None
    with pytest.raises(KeyError):
        s.mark_approved_without_token(999)


def test_purge_containment_and_missing_files(tmp_path):
    root = tmp_path / "files"
    s = IntakeStore(tmp_path / "i.sqlite", generate_key().encode(), files_root=root)
    outside = tmp_path / "outside.pdf"
    outside.write_text("x")
    inside = root / "in.pdf"
    inside.write_text("x")
    a, b, c = _add(s), _add(s), _add(s)
    s.set_status(a, "draft_ready", pdf_path=str(outside))
    s.set_status(b, "draft_ready", pdf_path=str(root / "gone.pdf"))
    s.set_status(c, "draft_ready", pdf_path=str(inside))
    now = datetime.now(timezone.utc) + timedelta(days=200)
    assert s.purge_older_than(180, now=now) == 3
    assert outside.exists()
    assert not inside.exists()
    assert s.list_intakes() == []


def test_purge_rejects_naive_now(store):
    with pytest.raises(ValueError):
        store.purge_older_than(1, now=datetime(2030, 1, 1))


def test_purge_normalises_tz(store):
    _add(store)
    from datetime import timezone as tz
    now = datetime.now(timezone(timedelta(hours=9))) + timedelta(days=200)
    assert store.purge_older_than(180, now=now) == 1
    assert tz.utc


def test_list_intakes_survives_bad_row(tmp_path):
    p = tmp_path / "i.sqlite"
    s = IntakeStore(p, generate_key().encode())
    a = _add(s)
    b = _add(s)
    import sqlite3
    with sqlite3.connect(p) as c:
        c.execute("UPDATE intake SET pii_enc=? WHERE id=?", (b"garbage", a))
    rows = s.list_intakes()
    assert [r["id"] for r in rows] == [a, b]
    assert rows[0]["name"] is None and rows[1]["name"] == "Alice Kim"


def test_permissions(tmp_path):
    import os
    import stat
    root = tmp_path / "files"
    IntakeStore(tmp_path / "i.sqlite", generate_key().encode(), files_root=root)
    assert stat.S_IMODE(os.stat(tmp_path / "i.sqlite").st_mode) == 0o600
    assert stat.S_IMODE(os.stat(root).st_mode) == 0o700
