"""P4 Task 3: owner CLI (tools/intake_admin.py)."""
from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from saju_web.jobs import generate_draft
from saju_web.store import generate_key

CLI_PATH = Path(__file__).resolve().parents[2] / "tools" / "intake_admin.py"


@pytest.fixture
def cli(monkeypatch, tmp_path):
    monkeypatch.setenv("SAJU_INTAKE_KEY", generate_key())
    monkeypatch.setenv("SAJU_INTAKE_DIR", str(tmp_path))
    spec = importlib.util.spec_from_file_location("intake_admin_t", CLI_PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _add(cli):
    store = cli._store()
    iid = store.add_intake(
        kind="single", tier="essential", pii={"name": "N", "email": "e@x.com", "main_concern": ""},
        birth={"dob": "1990-06-15", "birth_time": "10:00", "location": "Seoul",
               "utc_offset": "9", "timezone": "", "gender": "F"})
    return store, iid


def test_genkey_prints_valid_key(cli, capsys):
    assert cli.main(["genkey"]) == 0
    from cryptography.fernet import Fernet
    Fernet(capsys.readouterr().out.strip().encode())


def test_approve_requires_draft_ready(cli, capsys):
    _, iid = _add(cli)
    assert cli.main(["approve", str(iid)]) == 1
    assert "draft_ready" in capsys.readouterr().err


def test_approve_prints_resolving_link(cli, capsys):
    store, iid = _add(cli)
    generate_draft(store, iid, store.files_root)
    assert cli.main(["approve", str(iid), "--base-url", "https://x.test/"]) == 0
    url = capsys.readouterr().out.strip()
    assert url.startswith("https://x.test/report/")
    assert store.resolve_token(url.rsplit("/", 1)[1])["id"] == iid


def test_list_show_regenerate(cli, capsys):
    store, iid = _add(cli)
    assert cli.main(["regenerate", str(iid)]) == 0
    assert "draft_ready" in capsys.readouterr().out
    assert cli.main(["list", "--status", "draft_ready"]) == 0
    assert str(iid) in capsys.readouterr().out
    assert cli.main(["show", str(iid)]) == 0
    assert "e@x.com" in capsys.readouterr().out
    assert cli.main(["show", "999"]) == 1


def test_purge_deletes_old_rows(cli, capsys):
    store, iid = _add(cli)
    generate_draft(store, iid, store.files_root)
    pdf = Path(store.get_intake(iid)["pdf_path"])
    # Backdate the row.
    conn = store._conn()
    conn.execute("UPDATE intake SET created_at=?",
                 ((datetime.now(timezone.utc) - timedelta(days=400)).isoformat(),))
    conn.commit()
    conn.close()
    assert cli.main(["purge", "--days", "180"]) == 0
    assert "purged 1" in capsys.readouterr().out
    assert store.list_intakes() == [] and not pdf.exists()


def test_missing_key_is_clear_error(cli, monkeypatch, capsys):
    monkeypatch.delenv("SAJU_INTAKE_KEY")
    assert cli.main(["list"]) == 2
    assert "SAJU_INTAKE_KEY" in capsys.readouterr().err


def test_list_flags_stale_generating(cli, capsys):
    import sqlite3
    store, iid = _add(cli)
    fresh = _add(cli)[1]
    store.set_status(iid, "generating")
    store.set_status(fresh, "generating")
    old = (datetime.now(timezone.utc) - timedelta(minutes=16)).isoformat()
    conn = sqlite3.connect(store.db_path)
    conn.execute("UPDATE intake SET updated_at=? WHERE id=?", (old, iid))
    conn.commit()
    conn.close()
    assert cli.main(["list"]) == 0
    lines = {l.split("\t")[0]: l for l in capsys.readouterr().out.splitlines()}
    assert "STALE" in lines[str(iid)]
    assert "STALE" not in lines[str(fresh)]


def _age(store, iid, minutes):
    import sqlite3
    old = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
    conn = sqlite3.connect(store.db_path)
    conn.execute("UPDATE intake SET updated_at=? WHERE id=?", (old, iid))
    conn.commit()
    conn.close()


def test_list_flags_stale_received(cli, capsys):
    store, iid = _add(cli)
    fresh = _add(cli)[1]
    _age(store, iid, 16)
    assert cli.main(["list"]) == 0
    lines = {l.split("\t")[0]: l for l in capsys.readouterr().out.splitlines()}
    assert "STALE" in lines[str(iid)] and "STALE" not in lines[str(fresh)]


def test_regenerate_refuses_live_generating_unless_force(cli, capsys):
    store, iid = _add(cli)
    store.set_status(iid, "generating")
    assert cli.main(["regenerate", str(iid)]) == 1
    assert "generating" in capsys.readouterr().err
    assert store.get_intake(iid)["status"] == "generating"
    assert cli.main(["regenerate", str(iid), "--force"]) == 0
    assert store.get_intake(iid)["status"] == "draft_ready"
    # stale generating is allowed without --force
    store.set_status(iid, "generating")
    _age(store, iid, 20)
    assert cli.main(["regenerate", str(iid)]) == 0
