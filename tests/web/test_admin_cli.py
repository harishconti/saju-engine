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
