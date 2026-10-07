"""Optional email delivery of private report links (D2).

The self-service flow stores the client's email (encrypted) at intake. Once the
owner approves an order, the private ``/report/<token>`` link can be emailed to
the client instead of copied by hand. Email is strictly opt-in: if SMTP is not
configured, ``is_configured()`` is False and callers fall back to printing the
link (the pre-D2 behaviour).

Configuration (all read at send time, so env can change without a re-import):
    SAJU_SMTP_HOST       SMTP server host (required to enable)
    SAJU_SMTP_PORT       port (default 587)
    SAJU_SMTP_USER       username (optional; enables login)
    SAJU_SMTP_PASSWORD   password (optional; enables login)
    SAJU_SMTP_FROM       From: address (default = SAJU_SMTP_USER or noreply@localhost)
    SAJU_SMTP_STARTTLS   "1"/"true" to use STARTTLS (default: on when port != 465)

No PII is logged here; the caller logs only the outcome.
"""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Optional


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def is_configured() -> bool:
    """True when enough SMTP config is present to attempt a send."""
    return bool(_env("SAJU_SMTP_HOST"))


def _starttls_default(port: int) -> bool:
    raw = _env("SAJU_SMTP_STARTTLS")
    if raw:
        return raw.lower() in ("1", "true", "yes", "on")
    return port != 465


def build_message(link: str, to: str, *, subject: Optional[str] = None) -> EmailMessage:
    """A plain-text delivery email carrying the private link."""
    sender = _env("SAJU_SMTP_FROM") or _env("SAJU_SMTP_USER") or "noreply@localhost"
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject or "Your Saju reading is ready"
    msg.set_content(
        "Your reading has been prepared and reviewed.\n\n"
        f"Download it privately here (keep this link to yourself):\n{link}\n\n"
        "This link is personal and can be revoked; do not forward it.\n"
    )
    return msg


def send_report_link(link: str, to: str, *, subject: Optional[str] = None,
                     timeout: float = 15.0) -> bool:
    """Send ``link`` to ``to``. Returns True on success, False if unsent/unconfigured.

    Never raises: a delivery problem is reported via the boolean so the owner
    can still copy the printed link, and no exception text can leak PII.
    """
    if not is_configured() or not to:
        return False
    port = int(_env("SAJU_SMTP_PORT", "587") or "587")
    user = _env("SAJU_SMTP_USER")
    password = _env("SAJU_SMTP_PASSWORD")
    msg = build_message(link, to, subject=subject)
    try:
        if port == 465:
            with smtplib.SMTP_SSL(_env("SAJU_SMTP_HOST"), port, timeout=timeout) as s:
                if user:
                    s.login(user, password)
                s.send_message(msg)
        else:
            with smtplib.SMTP(_env("SAJU_SMTP_HOST"), port, timeout=timeout) as s:
                if _starttls_default(port):
                    s.starttls()
                if user:
                    s.login(user, password)
                s.send_message(msg)
        return True
    except Exception:  # noqa: BLE001 — delivery must never crash the CLI
        return False
