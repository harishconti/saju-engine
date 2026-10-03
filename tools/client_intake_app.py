#!/usr/bin/env python3
"""FastAPI self-service Saju calculator with a paid-order review queue.

Serves intake forms at `/` (single chart) and `/compat` (two charts).

Flow:
    - Both POST routes validate everything first, then store the intake in an
      encrypted SQLite store (`saju_web.store`; name/email/concern are
      Fernet-encrypted with `SAJU_INTAKE_KEY`, birth data stays plain).
    - `sample` (free hook): PDF rendered immediately and returned.
    - Paid tiers: HTTP 202 "received"; an engine draft PDF is generated in the
      background; the owner reviews it and approves with `tools/intake_admin.py`,
      which issues a private link served at `GET /report/{token}`.

Usage:
    SAJU_INTAKE_KEY=$(python3 tools/intake_admin.py genkey) python3 tools/client_intake_app.py [port]
    # SAJU_HOST (default 127.0.0.1) sets the bind address; SAJU_INTAKE_DIR overrides storage.

Never log decrypted PII; only intake ids are logged. Deploy with `umask 077`.
"""
from __future__ import annotations

import logging
import os
import re
import sys
from pathlib import Path

# Make the local src/ tree importable; user-space site-packages is already on
# sys.path by default, with `$SAJU_SITE` as an explicit override for non-standard
# installs.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
for p in (str(SRC_ROOT), os.environ.get("SAJU_SITE")):
    if p and p not in sys.path:
        sys.path.insert(0, p)

from fastapi import BackgroundTasks, FastAPI, Form, HTTPException  # noqa: E402
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from starlette.concurrency import run_in_threadpool  # noqa: E402

from saju_web.jobs import PAID_TIERS, derive_offset, generate_draft  # noqa: E402
from saju_web.store import IntakeStore  # noqa: E402

app = FastAPI(title="Saju Self-Service Intake")
log = logging.getLogger("saju.client_intake_app")

# S8e: no credentials, minimal headers/methods. In production set
# SAJU_ALLOWED_ORIGINS to the deployed landing-page origin(s) (comma-separated).
_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("SAJU_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    expose_headers=["Content-Disposition"],
)

TOOLS_DIR = Path(__file__).resolve().parent
INTAKE_DIR = Path(os.environ.get("SAJU_INTAKE_DIR") or PROJECT_ROOT / "candidates_horoscope" / "intake")
FILES_DIR = INTAKE_DIR / "files"
FORM_PATH = TOOLS_DIR / "client_intake_app.html"
COMPAT_FORM_PATH = TOOLS_DIR / "client_compat_intake_form.html"

# Fails fast with a how-to RuntimeError when SAJU_INTAKE_KEY is missing/invalid.
STORE = IntakeStore.from_env(INTAKE_DIR / "intake.sqlite", FILES_DIR)

SINGLE_TIERS = ("sample", "essential", "deep", "spark", "reading", "fullmap")
RECEIVED_MESSAGE = (
    "Thank you \u2014 your reading is being prepared and will be reviewed by a human "
    "reader before delivery. We'll email you a private download link."
)


def _bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=400, detail=detail)


def _check_birth(dob: str, birth_time: str, tz: str, offset: str, label: str = "") -> None:
    """Validate date/time parse and timezone/offset resolution (no PII in errors)."""
    try:
        fallback = float(offset) if offset else None
    except ValueError:
        raise _bad_request(f"{label}UTC offset must be a number.")
    try:
        derive_offset(dob, birth_time, tz or None, fallback)
    except ValueError as exc:  # includes UnknownTimezone
        raise _bad_request(f"{label}{exc}") from exc


def _accepted(intake_id: int) -> JSONResponse:
    return JSONResponse(
        status_code=202,
        content={"status": "received", "intake_id": intake_id, "message": RECEIVED_MESSAGE},
    )


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    if not FORM_PATH.exists():
        raise HTTPException(status_code=500, detail="Intake form HTML not found")
    return FORM_PATH.read_text(encoding="utf-8")


@app.post("/generate")
async def generate(
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    dob: str = Form(...),
    birth_time: str = Form(...),
    location: str = Form(...),
    # N-13: no default offset. A blank offset is only valid when `timezone` is given.
    utc_offset: str = Form(""),
    email: str = Form(...),
    gender: str = Form(...),
    marriage_status: str = Form(...),
    tier: str = Form(...),
    main_concern: str = Form(""),
    timezone: str = Form(""),
):
    name, dob, birth_time = name.strip(), dob.strip(), birth_time.strip()
    location, utc_offset, timezone = location.strip(), utc_offset.strip(), timezone.strip()
    main_concern = main_concern.strip()

    # S8d: validate EVERYTHING before anything is stored.
    if not name:
        raise _bad_request("Name is required.")
    if not email.strip():
        raise _bad_request("Email is required.")
    if not timezone and not utc_offset:
        raise _bad_request("Provide an IANA timezone or a UTC offset (no default is assumed).")
    if tier not in SINGLE_TIERS:
        raise _bad_request("Invalid report tier selected.")
    if gender not in ("M", "F"):
        raise _bad_request("Gender must be Female or Male so major-luck timing can be computed.")
    if tier == "deep" and not main_concern:
        raise _bad_request("Main concern is required for The Deep Destiny Report tier.")
    _check_birth(dob, birth_time, timezone, utc_offset)

    intake_id = STORE.add_intake(
        kind="single", tier=tier,
        pii={"name": name, "email": email.strip(), "main_concern": main_concern},
        birth={"dob": dob, "birth_time": birth_time, "location": location,
               "utc_offset": utc_offset, "timezone": timezone, "gender": gender,
               "marriage_status": marriage_status},
    )

    if tier in PAID_TIERS:
        background_tasks.add_task(generate_draft, STORE, intake_id, FILES_DIR)
        return _accepted(intake_id)

    # Free sample: render now, approve without a token, return the PDF.
    await run_in_threadpool(generate_draft, STORE, intake_id, FILES_DIR)
    row = STORE.get_intake(intake_id)
    if row["status"] != "draft_ready":
        # N-14: never echo exception text; generate_draft already logged it.
        raise HTTPException(status_code=500, detail="Failed to generate report. Please try again.")
    STORE.mark_approved_without_token(intake_id)
    return FileResponse(
        path=row["pdf_path"], media_type="application/pdf",
        filename=f"{slugify(name)}-saju-report.pdf",
    )


@app.get("/report/{token}")
def report(token: str):
    row = STORE.resolve_token(token)
    if row is None or not row["pdf_path"] or not Path(row["pdf_path"]).is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(
        path=row["pdf_path"], media_type="application/pdf",
        filename=Path(row["pdf_path"]).name,
    )


@app.get("/compat", response_class=HTMLResponse)
def compat_form() -> str:
    if not COMPAT_FORM_PATH.exists():
        raise HTTPException(status_code=500, detail="Compat intake form HTML not found")
    return COMPAT_FORM_PATH.read_text(encoding="utf-8")


@app.post("/compat/generate")
async def compat_generate(
    background_tasks: BackgroundTasks,
    name_a: str = Form(...),
    dob_a: str = Form(...),
    birth_time_a: str = Form(...),
    location_a: str = Form(...),
    utc_offset_a: float = Form(...),
    gender_a: str = Form(...),
    name_b: str = Form(...),
    dob_b: str = Form(...),
    birth_time_b: str = Form(...),
    location_b: str = Form(...),
    utc_offset_b: float = Form(...),
    gender_b: str = Form(...),
    email: str = Form(...),
    main_concern: str = Form(""),
    favorable_element_a: str = Form(""),
    favorable_element_b: str = Form(""),
    timezone_a: str = Form(""),
    timezone_b: str = Form(""),
    tier: str = Form("basic"),
):
    """Queue a 두 분 궁합 (Compatibility) report; the owner reviews before delivery."""
    # S8c/S8d: validate BEFORE persisting.
    for prefix, gender in (("A", gender_a), ("B", gender_b)):
        if gender not in ("M", "F"):
            raise _bad_request(f"Gender {prefix} must be M or F (got {gender!r}).")
    if not name_a.strip() or not name_b.strip():
        raise _bad_request("Both names are required.")
    if not email.strip():
        raise _bad_request("Email is required.")
    _check_birth(dob_a.strip(), birth_time_a.strip(), timezone_a.strip(), str(utc_offset_a), "Partner A: ")
    _check_birth(dob_b.strip(), birth_time_b.strip(), timezone_b.strip(), str(utc_offset_b), "Partner B: ")

    selected_tier = tier.strip() if tier.strip() in ("basic", "deep") else "basic"
    intake_id = STORE.add_intake(
        kind="compat", tier=selected_tier,
        pii={"name_a": name_a.strip(), "name_b": name_b.strip(), "email": email.strip(),
             "main_concern": main_concern.strip()},
        birth={
            "a": {"dob": dob_a.strip(), "birth_time": birth_time_a.strip(),
                  "location": location_a.strip(), "utc_offset": str(utc_offset_a),
                  "timezone": timezone_a.strip(), "gender": gender_a},
            "b": {"dob": dob_b.strip(), "birth_time": birth_time_b.strip(),
                  "location": location_b.strip(), "utc_offset": str(utc_offset_b),
                  "timezone": timezone_b.strip(), "gender": gender_b},
            "favorable_element_a": favorable_element_a.strip(),
            "favorable_element_b": favorable_element_b.strip(),
        },
    )
    # N-14: renders go to files/<id>/ under the store, never the curated
    # candidates_horoscope/marriage_compatibility/ folder.
    background_tasks.add_task(generate_draft, STORE, intake_id, FILES_DIR)
    return _accepted(intake_id)


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    return re.sub(r"[-\s]+", "-", s) or "report"


def main(argv: list[str] | None = None) -> int:
    import uvicorn
    args = argv if argv is not None else sys.argv
    port = int(args[1]) if len(args) > 1 else 8080
    host = os.environ.get("SAJU_HOST", "127.0.0.1")
    print(f"Starting Saju self-service app at http://{host}:{port}")
    print(f"Intake store: {INTAKE_DIR}")
    uvicorn.run(app, host=host, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
