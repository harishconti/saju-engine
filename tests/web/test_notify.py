"""D2: optional SMTP email delivery of private report links."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from saju_web import notify
from saju_web.jobs import generate_draft
from saju_web.store import generate_key

CLI_PATH = Path(__file__).resolve().parents[2] / "tools" / "intake_admin.py"


def test_is_configured_false_without_host(monkeypatch):
    monkeypatch.delenv("SAJU_SMTP_HOST", raising=False)
    assert notify.is_configured() is False
    assert notify.send_report_link("http://x/report/t", "a@b.com") is False


def test_build_message_has_link_and_subject(monkeypatch):
    monkeypatch.setenv("SAJU_SMTP_FROM", "reader@cosmicsaju.com")
    msg = notify.build_message("https://x.test/report/tok", "client@example.com")
    assert msg["To"] == "client@example.com"
    assert msg["From"] == "reader@cosmicsaju.com"
    assert "Saju" in msg["Subject"]
    assert "https://x.test/report/tok" in msg.get_content()


def test_starttls_default_port(monkeypatch):
    monkeypatch.delenv("SAJU_SMTP_STARTTLS", raising=False)
    assert notify._starttls_default(587) is True
    assert notify._starttls_default(465) is False


class FakeSMTP:
    """Minimal SMTP capture; records the message and whether TLS/login ran."""

    instances = []

    def __init__(self, host, port, timeout=None):
        self.host, self.port = host, port
        self.sent = []
        self.tls = False
        self.logged_in = False
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def starttls(self):
        self.tls = True

    def login(self, user, password):
        self.logged_in = True

    def send_message(self, msg):
        self.sent.append(msg)


def test_send_report_link_uses_starttls_and_login(monkeypatch):
    FakeSMTP.instances.clear()
    monkeypatch.setattr(notify.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setenv("SAJU_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SAJU_SMTP_PORT", "587")
    monkeypatch.setenv("SAJU_SMTP_USER", "u")
    monkeypatch.setenv("SAJU_SMTP_PASSWORD", "p")
    assert notify.send_report_link("https://x/report/tok", "c@e.com") is True
    inst = FakeSMTP.instances[-1]
    assert inst.tls is True and inst.logged_in is True
    assert inst.sent and inst.sent[0]["To"] == "c@e.com"


def test_send_report_link_returns_false_on_error(monkeypatch):
    def boom(*a, **k):
        raise OSError("connection refused")

    monkeypatch.setattr(notify.smtplib, "SMTP", boom)
    monkeypatch.setenv("SAJU_SMTP_HOST", "smtp.example.com")
    assert notify.send_report_link("https://x/report/tok", "c@e.com") is False


# ── CLI integration: approve emails when configured, prints-only otherwise ──

@pytest.fixture
def cli(monkeypatch, tmp_path):
    monkeypatch.setenv("SAJU_INTAKE_KEY", generate_key())
    monkeypatch.setenv("SAJU_INTAKE_DIR", str(tmp_path))
    spec = importlib.util.spec_from_file_location("intake_admin_n", CLI_PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _approved_draft(cli):
    store = cli._store()
    iid = store.add_intake(
        kind="single", tier="essential",
        pii={"name": "N", "email": "client@example.com", "main_concern": ""},
        birth={"dob": "1990-06-15", "birth_time": "10:00", "location": "Seoul",
               "utc_offset": "9", "timezone": "", "gender": "F"})
    generate_draft(store, iid, store.files_root)
    return store, iid


def test_approve_prints_link_when_smtp_unconfigured(cli, capsys, monkeypatch):
    monkeypatch.delenv("SAJU_SMTP_HOST", raising=False)
    _, iid = _approved_draft(cli)
    assert cli.main(["approve", str(iid), "--base-url", "https://x.test"]) == 0
    out = capsys.readouterr().out
    assert "https://x.test/report/" in out
    assert "emailed" not in out


def test_approve_emails_when_configured(cli, capsys, monkeypatch):
    FakeSMTP.instances.clear()
    monkeypatch.setattr(notify.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setenv("SAJU_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SAJU_SMTP_PORT", "587")
    _, iid = _approved_draft(cli)
    assert cli.main(["approve", str(iid), "--base-url", "https://x.test"]) == 0
    out = capsys.readouterr().out
    assert "https://x.test/report/" in out
    assert "emailed the private link" in out
    assert FakeSMTP.instances[-1].sent  # actually sent
    # the recipient address must never be printed
    assert "client@example.com" not in out
