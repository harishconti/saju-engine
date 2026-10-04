"""Report-generation jobs for the self-service app (single chart and compat).

``generate_draft`` renders the engine draft PDF for a stored intake and records
the outcome in the store. Failures store only the exception class name in the
plaintext ``error`` column; the traceback frames (never the exception message)
go to the log. Logs must not contain PII.
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from saju_engine.compat_report import generate_compat_report
from saju_engine.engine import compute_chart
from saju_engine.premium_report import normalize_tier
from saju_html.md_to_saju_pdf import build_pdf, build_pdf_from_chart
from saju_web.store import IntakeStore

log = logging.getLogger("saju.jobs")

# Bounds concurrent PDF renders (CPU/RAM); sample sync renders and background drafts share it.
RENDER_SLOTS = threading.BoundedSemaphore(max(1, int(os.environ.get("SAJU_MAX_RENDERS", "2"))))

STALE_AFTER = timedelta(minutes=15)


def is_stale(updated_at: Optional[str], now: Optional[datetime] = None) -> bool:
    """True when a row has sat in received/generating for more than 15 minutes."""
    try:
        ts = datetime.fromisoformat(updated_at)
    except (TypeError, ValueError):
        return False
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return (now or datetime.now(timezone.utc)) - ts > STALE_AFTER


def parse_dob_time(dob: str, birth_time: str) -> tuple[int, int, int, int, int]:
    try:
        d = datetime.strptime(dob, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"Date of birth must be YYYY-MM-DD, got {dob!r}") from exc
    try:
        t = datetime.strptime(birth_time, "%H:%M").time()
    except ValueError as exc:
        raise ValueError(f"Birth time must be HH:MM, got {birth_time!r}") from exc
    return d.year, d.month, d.day, t.hour, t.minute


def derive_offset(dob: str, birth_time: str, timezone_name: Optional[str],
                  fallback_offset: Optional[float]) -> float:
    """UTC offset for chart computation (shared historical/DST-aware logic, N-13).

    Raises ``UnknownTimezone`` (a ValueError) when neither a recognised zone nor
    a numeric fallback is available.
    """
    from saju_engine.timezone import derive_utc_offset

    y, mo, d, h, mi = parse_dob_time(dob, birth_time)
    offset, _from_tz = derive_utc_offset(y, mo, d, h, mi, timezone_name, fallback_offset)
    return offset


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    return re.sub(r"[-\s]+", "-", s) or "report"


def _fallback(raw) -> Optional[float]:
    return float(raw) if raw not in (None, "") else None


def _compute(name: str, birth: dict, gender: str):
    y, mo, d, h, mi = parse_dob_time(birth["dob"], birth["birth_time"])
    offset = derive_offset(birth["dob"], birth["birth_time"], birth.get("timezone"),
                           _fallback(birth.get("utc_offset")))
    return compute_chart(
        name=name or None, gender=gender, year=y, month=mo, day=d, hour=h, minute=mi,
        city=birth.get("location") or None, utc_offset=offset,
        use_solar_time=True, convention="korean",
    )


def render_single(pii: dict, birth: dict, tier: str, out_pdf: Path) -> Path:
    gender = birth.get("gender")
    if gender not in ("M", "F"):
        raise ValueError("PDF generation requires gender Female or Male so major-luck timing can be computed.")
    chart = _compute(pii.get("name", ""), birth, gender)
    name = pii.get("name", "Client")
    dob_str = f"{birth['dob']}, {birth['birth_time']}, {birth.get('location', '')}"
    dm = f"{chart.day_master} ({chart.day_master_info.get('element', '')} {chart.day_master_info.get('polarity', '')})"
    return build_pdf_from_chart(
        chart, out_pdf, title=f"{name} — Saju Reading", client=pii.get("name", ""),
        dob=dob_str, day_master=dm, tier=normalize_tier(tier),
    )


def render_compat(pii: dict, birth: dict, tier: str, out_dir: Path) -> Path:
    a, b = birth["a"], birth["b"]
    name_a, name_b = pii["name_a"], pii["name_b"]
    slug_a, slug_b = slugify(name_a)[:24], slugify(name_b)[:24]
    selected = tier if tier in ("basic", "deep") else "basic"
    base = f"{slug_a}_{slug_b}_compatibility" + ("_deep" if selected == "deep" else "")
    out_md, out_pdf = out_dir / f"{base}.md", out_dir / f"{base}.pdf"
    chart_a = _compute(name_a, a, a["gender"])
    chart_b = _compute(name_b, b, b["gender"])
    # N-7: forward an override only when the form field was actually filled in.
    md = generate_compat_report(
        chart_a, chart_b, name_a=name_a, name_b=name_b,
        favorable_element_a=birth.get("favorable_element_a") or None,
        favorable_element_b=birth.get("favorable_element_b") or None,
        tier=selected,
    )
    out_md.write_text(md, encoding="utf-8")
    title = (f"Deep Compatibility Reading — {name_a} × {name_b}" if selected == "deep"
             else f"Compatibility Reading — {name_a} × {name_b}")
    build_pdf(
        input_md=out_md, output_pdf=out_pdf, title=title,
        client=f"{name_a} ({chart_a.day_master}) · {name_b} ({chart_b.day_master})",
        dob=f"{a['dob']}, {a['birth_time']}, {a.get('location', '')} · "
            f"{b['dob']}, {b['birth_time']}, {b.get('location', '')}",
        day_master=f"{chart_a.day_master}/{chart_b.day_master}", tier="compat",
    )
    return out_pdf


def generate_draft(store: IntakeStore, intake_id: int, files_dir: Path, *,
                   hold_slot: bool = True) -> None:
    """Render the draft PDF for ``intake_id`` into ``files_dir/<id>/``.

    Sets "generating", then "draft_ready" (with pdf_path) or "failed" (error =
    exception class name only). ``files_dir`` must be under ``store.files_root``
    so retention purge can delete the output. Rendering is bounded by
    ``RENDER_SLOTS``; pass ``hold_slot=False`` if the caller already holds one.
    """
    if hold_slot:
        with RENDER_SLOTS:
            _generate(store, intake_id, files_dir)
    else:
        _generate(store, intake_id, files_dir)


def _generate(store: IntakeStore, intake_id: int, files_dir: Path) -> None:
    try:
        was_received = store.get_intake(intake_id)["status"] == "received"
        store.set_status(intake_id, "generating")
    except KeyError:  # row purged before the job ran
        log.warning("draft generation skipped: intake %s no longer exists", intake_id)
        return
    try:
        row = store.get_intake(intake_id)
        out_dir = Path(files_dir) / str(intake_id)
        if was_received and out_dir.exists():
            # Pre-AUTOINCREMENT databases can reuse an id: never inherit old files.
            shutil.rmtree(out_dir, ignore_errors=True)
        out_dir.mkdir(parents=True, exist_ok=True)
        if row["kind"] == "compat":
            pdf = render_compat(row["pii"], row["birth"], row["tier"], out_dir)
        else:
            pdf = render_single(row["pii"], row["birth"], row["tier"],
                                out_dir / "report.pdf")
    except Exception as exc:
        # Exception messages may embed birth data/PII: log class + frames only.
        log.error("draft generation failed for intake %s: %s", intake_id,
                  type(exc).__name__, exc_info=(type(exc), None, exc.__traceback__))
        try:
            store.set_status(intake_id, "failed", error=type(exc).__name__)
        except KeyError:
            log.warning("intake %s vanished during generation", intake_id)
        return
    try:
        store.set_status(intake_id, "draft_ready", pdf_path=str(pdf))
    except KeyError:
        log.warning("intake %s vanished during generation", intake_id)
