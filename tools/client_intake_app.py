#!/usr/bin/env python3
"""FastAPI self-service Saju calculator.

Serves an intake form at `/` and a PDF generation endpoint at `/generate`.
Each request is saved to `candidates_horoscope/intake/` as JSON, and a tiered
premium PDF is computed on demand from the engine.

Usage:
    python3 tools/client_intake_app.py
    # open http://localhost:8080

Dependencies:
    pip install --user --break-system-packages fastapi uvicorn python-multipart

Privacy / deployment note (demo deployment):
    - Intake records (name, DOB, birth time/location, email, main concern) are
      saved as unencrypted JSON files on the local filesystem.
    - PDF generation runs synchronously inside the HTTP worker thread
      (`run_in_threadpool`), holding the connection open until rendering ends.
    - These choices are acceptable for a local demo or trusted single-user
      deployment. A production service should use encrypted storage, a
      background job queue, and email delivery instead of synchronous responses.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone as _timezone
from pathlib import Path
from zoneinfo import ZoneInfo, available_timezones

# Make the local src/ tree importable; user-space site-packages is already on
# sys.path by default, with `$SAJU_SITE` as an explicit override for non-standard
# installs.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
for p in (str(SRC_ROOT), os.environ.get("SAJU_SITE")):
    if p and p not in sys.path:
        sys.path.insert(0, p)

from typing import Optional  # noqa: E402

from fastapi import FastAPI, Form, HTTPException  # noqa: E402
from fastapi.responses import FileResponse, HTMLResponse  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from starlette.concurrency import run_in_threadpool  # noqa: E402

from saju_engine.engine import compute_chart  # noqa: E402
from saju_engine.premium_report import normalize_tier  # noqa: E402
from saju_engine.compat_report import generate_compat_report  # noqa: E402
from saju_html.md_to_saju_pdf import build_pdf  # noqa: E402
from saju_html.md_to_saju_pdf import build_pdf_from_chart  # noqa: E402

app = FastAPI(title="Saju Self-Service Intake")

# Allow the landing-page Next.js app to call /generate and /compat/generate
# directly in development. In production, set SAJU_ALLOWED_ORIGINS to the
# deployed landing-page origin(s) (comma-separated).
_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("SAJU_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

INTAKE_DIR = PROJECT_ROOT / "candidates_horoscope" / "intake"
FORM_PATH = TOOLS_DIR / "client_intake_app.html"
COMPAT_FORM_PATH = TOOLS_DIR / "client_compat_intake_form.html"


def _slugify(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"[^\w\s-]", "", name)
    return re.sub(r"[-\s]+", "-", name) or "candidate"


def _save_intake(payload: dict) -> Path:
    INTAKE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = _slugify(payload.get("name", "candidate"))[:32]
    out = INTAKE_DIR / f"{timestamp}-{slug}.json"
    record = {
        "received_at": datetime.now().isoformat(),
        "source": "client_intake_app",
        "payload": payload,
    }
    out.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def _parse_dob_time(dob: str, birth_time: str) -> tuple[int, int, int, int, int]:
    try:
        d = datetime.strptime(dob, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"Date of birth must be YYYY-MM-DD, got {dob!r}") from exc
    try:
        t = datetime.strptime(birth_time, "%H:%M").time()
    except ValueError as exc:
        raise ValueError(f"Birth time must be HH:MM, got {birth_time!r}") from exc
    return d.year, d.month, d.day, t.hour, t.minute


def _derive_utc_offset(
    dob: str,
    birth_time: str,
    timezone_name: Optional[str],
    fallback_offset: float,
) -> float:
    """Return the UTC offset to use for chart computation.

    If ``timezone_name`` is a recognized IANA zone, compute the exact historical
    UTC offset (including DST) for the given local date/time. Otherwise fall
    back to the user-supplied numeric ``fallback_offset``.
    """
    tz = (timezone_name or "").strip()
    if not tz:
        return fallback_offset
    if tz not in available_timezones():
        # Not a known IANA key — keep the numeric fallback and let the caller
        # decide whether to warn.
        return fallback_offset
    year, month, day, hour, minute = _parse_dob_time(dob, birth_time)
    local_dt = datetime(year, month, day, hour, minute, tzinfo=ZoneInfo(tz))
    offset = local_dt.utcoffset()
    if offset is None:
        return fallback_offset
    return offset.total_seconds() / 3600.0


def _generate_pdf(payload: dict, output_path: Path) -> Path:
    """Run chart computation and PDF generation in the synchronous thread."""
    year, month, day, hour, minute = _parse_dob_time(payload["dob"], payload["birth_time"])
    gender = payload.get("gender")
    if gender not in ("M", "F"):
        raise ValueError("PDF generation requires gender Female or Male so major-luck timing can be computed.")

    tier = normalize_tier(payload.get("tier", "essential"))
    utc_offset = _derive_utc_offset(
        payload["dob"], payload["birth_time"],
        payload.get("timezone"),
        float(payload.get("utc_offset", 5.5)),
    )

    chart = compute_chart(
        name=payload.get("name") or None,
        gender=gender,
        year=year, month=month, day=day,
        hour=hour, minute=minute,
        city=payload.get("location") or None,
        utc_offset=utc_offset,
        use_solar_time=True,
        convention="korean",
    )

    dob_str = f"{payload['dob']}, {payload['birth_time']}, {payload.get('location', '')}"
    day_master_label = f"{chart.day_master} ({chart.day_master_info.get('element', '')} {chart.day_master_info.get('polarity', '')})"

    return build_pdf_from_chart(
        chart, output_path,
        title=f"{payload.get('name', 'Client')} — Saju Reading",
        client=payload.get("name", ""),
        dob=dob_str,
        day_master=day_master_label,
        tier=tier,
    )


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    if not FORM_PATH.exists():
        raise HTTPException(status_code=500, detail="Intake form HTML not found")
    return FORM_PATH.read_text(encoding="utf-8")


@app.post("/generate")
async def generate(
    name: str = Form(...),
    dob: str = Form(...),
    birth_time: str = Form(...),
    location: str = Form(...),
    utc_offset: float = Form(5.5),
    email: str = Form(...),
    gender: str = Form(...),
    marriage_status: str = Form(...),
    tier: str = Form(...),
    main_concern: str = Form(""),
    timezone: str = Form(""),
) -> FileResponse:
    payload = {
        "name": name.strip(),
        "dob": dob.strip(),
        "birth_time": birth_time.strip(),
        "location": location.strip(),
        "utc_offset": str(utc_offset),
        "email": email.strip(),
        "gender": gender,
        "marriage_status": marriage_status,
        "tier": tier,
        "main_concern": main_concern.strip(),
        "timezone": timezone.strip(),
    }

    # Validation
    if not payload["name"]:
        raise HTTPException(status_code=400, detail="Name is required.")
    if tier not in ("sample", "essential", "deep", "spark", "reading", "fullmap"):
        raise HTTPException(status_code=400, detail="Invalid report tier selected.")
    if tier == "deep" and not payload["main_concern"]:
        raise HTTPException(status_code=400, detail="Main concern is required for The Deep Destiny Report tier.")

    _save_intake(payload)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    slug = slugify(name) or "report"
    INTAKE_DIR.mkdir(parents=True, exist_ok=True)
    output_pdf = INTAKE_DIR / f"{timestamp}-{slug}-report.pdf"

    try:
        pdf_path = await run_in_threadpool(_generate_pdf, payload, output_pdf)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {exc}") from exc

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"{slug}-saju-report.pdf",
    )


@app.get("/compat", response_class=HTMLResponse)
def compat_form() -> str:
    if not COMPAT_FORM_PATH.exists():
        raise HTTPException(status_code=500, detail="Compat intake form HTML not found")
    return COMPAT_FORM_PATH.read_text(encoding="utf-8")


@app.post("/compat/generate")
async def compat_generate(
    name_a: str = Form(...),
    dob_a: str = Form(...),
    birth_time_a: str = Form(...),
    location_a: str = Form(...),
    utc_offset_a: float = Form(5.5),
    gender_a: str = Form(...),
    name_b: str = Form(...),
    dob_b: str = Form(...),
    birth_time_b: str = Form(...),
    location_b: str = Form(...),
    utc_offset_b: float = Form(5.5),
    gender_b: str = Form(...),
    email: str = Form(...),
    main_concern: str = Form(""),
    favorable_element_a: str = Form(""),
    favorable_element_b: str = Form(""),
    timezone_a: str = Form(""),
    timezone_b: str = Form(""),
    tier: str = Form("basic"),
) -> FileResponse:
    """Generate a 두 분 궁합 (Compatibility) PDF from two birth charts."""
    payload = {
        "name_a": name_a.strip(),
        "dob_a": dob_a.strip(),
        "birth_time_a": birth_time_a.strip(),
        "location_a": location_a.strip(),
        "utc_offset_a": str(utc_offset_a),
        "gender_a": gender_a,
        "name_b": name_b.strip(),
        "dob_b": dob_b.strip(),
        "birth_time_b": birth_time_b.strip(),
        "location_b": location_b.strip(),
        "utc_offset_b": str(utc_offset_b),
        "gender_b": gender_b,
        "email": email.strip(),
        "main_concern": main_concern.strip(),
        "tier": tier.strip() if tier.strip() in ("basic", "deep") else "basic",
        "favorable_element_a": favorable_element_a.strip(),
        "favorable_element_b": favorable_element_b.strip(),
        "timezone_a": timezone_a.strip(),
        "timezone_b": timezone_b.strip(),
    }
    # Save raw intake.
    INTAKE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    slug_a = slugify(name_a)[:24]
    slug_b = slugify(name_b)[:24]
    intake_path = INTAKE_DIR / f"{timestamp}-compat-{slug_a}-x-{slug_b}.json"
    intake_path.write_text(
        json.dumps({"received_at": datetime.now().isoformat(),
                    "source": "client_intake_app_compat",
                    "payload": payload}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Validate genders so 대운 (major luck) can be computed.
    for prefix, gender in (("a", gender_a), ("b", gender_b)):
        if gender not in ("M", "F"):
            raise HTTPException(status_code=400,
                                detail=f"Gender {prefix.upper()} must be M or F (got {gender!r}).")

    try:
        ya, ma, da, ha, mia = _parse_dob_time(dob_a, birth_time_a)
        yb, mb, db, hb, mib = _parse_dob_time(dob_b, birth_time_b)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    offset_a = _derive_utc_offset(dob_a, birth_time_a, payload.get("timezone_a"), utc_offset_a)
    offset_b = _derive_utc_offset(dob_b, birth_time_b, payload.get("timezone_b"), utc_offset_b)

    chart_a = compute_chart(
        name=name_a or None, gender=gender_a,
        year=ya, month=ma, day=da, hour=ha, minute=mia,
        city=location_a or None, utc_offset=offset_a,
        use_solar_time=True, convention="korean",
    )
    chart_b = compute_chart(
        name=name_b or None, gender=gender_b,
        year=yb, month=mb, day=db, hour=hb, minute=mib,
        city=location_b or None, utc_offset=offset_b,
        use_solar_time=True, convention="korean",
    )

    # Generate markdown + render PDF in a worker thread (charts can be slow).
    # Storage convention (2026-07-06, revised): each pair gets its own subfolder
    # under candidates_horoscope/marriage_compatibility/{slug_a}_{slug_b}/,
    # containing {slug_a}_{slug_b}_compatibility.{md,pdf} for basic and
    # ..._compatibility_deep.{md,pdf} for deep. Raw intake JSON still goes to
    # intake/ for audit.
    MARRIAGE_DIR = PROJECT_ROOT / "candidates_horoscope" / "marriage_compatibility"
    selected_tier = tier.strip() if tier.strip() in ("basic", "deep") else "basic"
    pair_dir = MARRIAGE_DIR / f"{slug_a}_{slug_b}"
    pair_dir.mkdir(parents=True, exist_ok=True)
    name_filename = f"{slug_a}_{slug_b}_compatibility"
    if selected_tier == "deep":
        name_filename += "_deep"
    output_md_path = pair_dir / f"{name_filename}.md"
    output_pdf_path = pair_dir / f"{name_filename}.pdf"

    def _render() -> Path:
        # Use the engine's heuristic 용신 by default, but allow an explicit
        # human-argued override via the form so automated compat does not drift
        # from a reviewed single-chart reading.
        fe_a = favorable_element_a or (
            chart_a.strength_assessment.get("candidate_favorable")
            if chart_a.strength_assessment else None
        )
        fe_b = favorable_element_b or (
            chart_b.strength_assessment.get("candidate_favorable")
            if chart_b.strength_assessment else None
        )
        selected_tier = tier.strip() if tier.strip() in ("basic", "deep") else "basic"
        md = generate_compat_report(
            chart_a, chart_b, name_a=name_a, name_b=name_b,
            favorable_element_a=fe_a or None,
            favorable_element_b=fe_b or None,
            tier=selected_tier,
        )
        output_md_path.write_text(md, encoding="utf-8")
        dob_a_str = f"{dob_a}, {birth_time_a}, {location_a}"
        dob_b_str = f"{dob_b}, {birth_time_b}, {location_b}"
        title = (
            f"Deep Compatibility Reading — {name_a} × {name_b}"
            if selected_tier == "deep"
            else f"Compatibility Reading — {name_a} × {name_b}"
        )
        build_pdf(
            input_md=output_md_path, output_pdf=output_pdf_path,
            title=title,
            client=f"{name_a} ({chart_a.day_master}) · {name_b} ({chart_b.day_master})",
            dob=f"{dob_a_str} · {dob_b_str}",
            day_master=f"{chart_a.day_master}/{chart_b.day_master}",
            tier="compat",
        )
        return output_pdf_path

    try:
        pdf_path = await run_in_threadpool(_render)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate compat PDF: {exc}") from exc

    download_name = f"{slug_a}_{slug_b}_compatibility.pdf"
    if selected_tier == "deep":
        download_name = f"{slug_a}_{slug_b}_compatibility_deep.pdf"
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=download_name,
    )


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    return re.sub(r"[-\s]+", "-", s) or "report"


def main(argv: list[str] | None = None) -> int:
    import uvicorn
    port = int((argv or sys.argv)[1]) if len(argv or sys.argv) > 1 else 8080
    print(f"Starting Saju self-service app at http://localhost:{port}")
    print(f"Intake records will be saved to {INTAKE_DIR}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
