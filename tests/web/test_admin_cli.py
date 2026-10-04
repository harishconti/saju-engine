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


# ---- final fix wave C --------------------------------------------------------

def _draft(cli):
    store, iid = _add(cli)
    generate_draft(store, iid, store.files_root)
    return store, iid


def _fake_pdf(tmp_path, body=b"%PDF-1.4 polished"):
    f = tmp_path / "polished-src.pdf"
    f.write_bytes(body)
    return f


def test_attach_copies_pdf_and_blocks_regenerate(cli, tmp_path, capsys):
    store, iid = _draft(cli)
    src = _fake_pdf(tmp_path)
    assert cli.main(["attach", str(iid), str(src)]) == 0
    row = store.get_intake(iid)
    dest = Path(row["pdf_path"])
    assert dest == (store.files_root / str(iid) / "report.pdf").resolve() or dest.samefile(store.files_root / str(iid) / "report.pdf")
    assert dest.read_bytes() == src.read_bytes() and row["polished"] is True
    capsys.readouterr()
    assert cli.main(["regenerate", str(iid)]) == 1
    assert "--force" in capsys.readouterr().err
    assert dest.read_bytes() == src.read_bytes()
    assert cli.main(["regenerate", str(iid), "--force"]) == 0
    assert store.get_intake(iid)["polished"] is False


def test_attach_requires_draft_ready_and_a_pdf(cli, tmp_path, capsys):
    store, iid = _add(cli)  # status received
    assert cli.main(["attach", str(iid), str(_fake_pdf(tmp_path))]) == 1
    store2, iid2 = _draft(cli)
    bad = tmp_path / "x.txt"
    bad.write_text("not a pdf")
    assert cli.main(["attach", str(iid2), str(bad)]) == 1
    assert cli.main(["attach", str(iid2), str(tmp_path / "missing.pdf")]) == 1
    assert store2.get_intake(iid2)["polished"] is False


def test_revoke_and_reissue(cli, capsys):
    store, iid = _draft(cli)
    assert cli.main(["approve", str(iid), "--base-url", "https://x.test"]) == 0
    t1 = capsys.readouterr().out.strip().rsplit("/", 1)[1]
    assert cli.main(["reissue", str(iid), "--base-url", "https://x.test"]) == 0
    t2 = capsys.readouterr().out.strip().rsplit("/", 1)[1]
    assert t1 != t2 and store.resolve_token(t1) is None and store.resolve_token(t2)["id"] == iid
    assert cli.main(["revoke", str(iid)]) == 0
    assert store.resolve_token(t2) is None
    assert store.get_intake(iid)["status"] == "draft_ready"
    assert cli.main(["revoke", str(iid)]) == 1          # not approved any more
    assert cli.main(["reissue", str(iid), "--base-url", "https://x.test"]) == 1
    assert cli.main(["approve", str(iid), "--base-url", "https://x.test"]) == 0  # can re-approve


def test_approve_base_url_env_and_no_localhost_default(cli, monkeypatch, capsys):
    store, iid = _draft(cli)
    monkeypatch.delenv("SAJU_PUBLIC_URL", raising=False)
    assert cli.main(["approve", str(iid)]) == 2
    assert "SAJU_PUBLIC_URL" in capsys.readouterr().err
    assert store.get_intake(iid)["status"] == "draft_ready"  # nothing was issued
    monkeypatch.setenv("SAJU_PUBLIC_URL", "https://pub.test/")
    assert cli.main(["approve", str(iid)]) == 0
    assert capsys.readouterr().out.startswith("https://pub.test/report/")


def test_rotate_reencrypts_with_first_key(cli, monkeypatch, capsys):
    from cryptography.fernet import Fernet
    store, iid = _add(cli)
    old = __import__("os").environ["SAJU_INTAKE_KEY"]
    new = generate_key()
    monkeypatch.setenv("SAJU_INTAKE_KEY", f"{new},{old}")
    assert cli.main(["show", str(iid)]) == 0           # old rows still decrypt
    assert cli.main(["rotate"]) == 0
    assert "1 intake" in capsys.readouterr().out
    monkeypatch.setenv("SAJU_INTAKE_KEY", new)          # old key dropped
    assert cli.main(["show", str(iid)]) == 0
    assert '"name": "N"' in capsys.readouterr().out
    assert Fernet(new.encode())
