#!/usr/bin/env python3
"""Cosmic Saju report engine — a stateless FastAPI service.

Endpoints (all bearer-authenticated with one shared token):

    POST /health     readiness probe
    POST /chart      derive a chart summary, no render
    POST /generate   compute + render a PDF and PUT it to a presigned URL

Deliberate constraints — see docs/webapp/05-report-pipeline.md §1:

  * **No database.** User, order and price concepts do not exist here. It is
    handed birth data and overrides; it does not know who is paying.
  * **No storage credentials.** The caller presigns one PUT URL; that is the
    only way bytes leave the process. The PDF never crosses a response body.
  * **No persistent state.** A temp directory is fine; durable state is not.
  * **Never log PII.** Exception *messages* can embed birth data (the engine's
    own `saju_web/jobs.py` documents this), so only the class name is logged and
    only a class name crosses the wire.

Deployment note: the Vercel project's Root Directory is the **repository root**,
so this file lives at `api/index.py` and `src/` is importable. Using
`services/report-engine/` as the root would hide `src/` from the function bundle,
which is why the layout differs from the original plan.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Make the repository's src/ tree importable — the same convention tools/*.py uses.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from saju_engine.compat_report import generate_compat_report  # noqa: E402
from saju_engine.engine import compute_chart  # noqa: E402
from saju_engine.premium_report import generate_premium_report, normalize_tier  # noqa: E402
from saju_engine.report_data import _ELEMENT_ASSOCIATIONS  # noqa: E402
from saju_engine.strength import element_balance_pct  # noqa: E402
from saju_engine.timezone import derive_utc_offset  # noqa: E402
from saju_engine.yongsin import favorable_element  # noqa: E402
from saju_html.audio_script import build_audio_script, chunk_for_tts, script_stats  # noqa: E402
from saju_html.chart_input import prepare_chart_render  # noqa: E402
from saju_html.md_to_saju_pdf import build_pdf  # noqa: E402

try:  # pragma: no cover - version reporting is best-effort
    from saju_engine import __version__ as ENGINE_VERSION
except Exception:  # noqa: BLE001
    ENGINE_VERSION = "unknown"

# `saju_engine.__version__` comes from installed package metadata, which does not
# exist on a serverless host (the source tree is present, not pip-installed). Fall
# back to pyproject.toml so the version recorded against every report is real.
if not ENGINE_VERSION or ENGINE_VERSION.startswith("0.0.0"):  # pragma: no cover
    try:
        import tomllib

        with open(PROJECT_ROOT / "pyproject.toml", "rb") as _fh:
            ENGINE_VERSION = tomllib.load(_fh)["project"]["version"]
    except Exception:  # noqa: BLE001 - version is cosmetic; never fail a render for it
        pass

log = logging.getLogger("saju.report_engine")

# Bumped whenever the request/response shape changes. The webapp sends its
# expectation and a mismatch is rejected rather than silently mis-rendered.
CONTRACT_VERSION = 1

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_VALID_GENDERS = ("M", "F")
_KINDS = ("single", "compat")
_SINGLE_TIERS = ("sample", "essential", "deep", "spark", "reading", "fullmap")
_COMPAT_TIERS = ("basic", "deep")

app = FastAPI(title="Cosmic Saju report engine", version=ENGINE_VERSION)


# ─────────────────────────────── errors ───────────────────────────────


def _fail(status: int, code: str, message: str) -> JSONResponse:
    """The error envelope. `message` must never contain birth data."""
    return JSONResponse(status_code=status, content={"error": message, "code": code})


# ─────────────────────────────── auth ───────────────────────────────


def _authorize(authorization: Optional[str]) -> None:
    expected = (os.environ.get("ENGINE_SERVICE_TOKEN") or "").strip()
    if not expected:
        # Fail closed: an unauthenticated engine is worse than a dark one.
        raise HTTPException(status_code=503, detail="Engine is not configured")
    provided = ""
    if authorization and authorization.lower().startswith("bearer "):
        provided = authorization[7:].strip()
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


# ─────────────────────────────── request models ───────────────────────────────


class ProfileIn(BaseModel):
    """Birth data. Mirrors `EngineProfile` in apps/web/src/lib/engine.ts."""

    fullName: str = ""
    gender: str
    birthDate: str
    birthTime: str = "12:00"
    timeKnown: bool = True
    timezone: Optional[str] = None
    utcOffset: Optional[float] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ChartRequest(ProfileIn):
    """`POST /chart` — a flat profile plus the contract version."""

    contractVersion: int = CONTRACT_VERSION


class GenerateRequest(BaseModel):
    """`POST /generate` — mirrors `EnginePayload` in apps/web/src/lib/engine.ts."""

    contractVersion: int = CONTRACT_VERSION
    kind: str
    tier: str
    uploadUrl: str
    # Optional: where to PUT the source markdown. Storing it is what lets the audio
    # script be derived from the artefact that was actually approved, instead of being
    # recomputed later (an engine deploy in between could change the words).
    mdUploadUrl: Optional[str] = None
    # Optional: where to PUT the **web document** — the reading the client opens, as one
    # self-contained HTML file. Rendered from the same markdown as the PDF, so the two can
    # never disagree. Single-chart only for now (the compat reading has its own renderer).
    htmlUploadUrl: Optional[str] = None
    profileA: ProfileIn
    profileB: Optional[ProfileIn] = None
    favorableOverrideA: Optional[str] = None
    favorableOverrideB: Optional[str] = None


class ScriptRequest(BaseModel):
    """`POST /script` — turn an approved report's markdown into a spoken script.

    The markdown is sent in the body rather than recomputed here on purpose: the script
    must be a derivation of the text a human approved, not of whatever the engine would
    produce today.
    """

    contractVersion: int = CONTRACT_VERSION
    markdown: str


# ─────────────────────────────── validation ───────────────────────────────


class BirthData:
    """Validated, engine-ready birth data. Construction raises 422 on bad input."""

    def __init__(self, profile: ProfileIn) -> None:
        if profile.gender not in _VALID_GENDERS:
            raise _http(422, "INVALID_GENDER", "Gender must be Male or Female — major-luck direction needs it.")
        if not _DATE_RE.match(profile.birthDate or ""):
            raise _http(422, "INVALID_BIRTH_DATE", "Date of birth must be YYYY-MM-DD.")
        if profile.timeKnown and not _TIME_RE.match(profile.birthTime or ""):
            raise _http(422, "INVALID_BIRTH_TIME", "Birth time must be HH:MM on a 24-hour clock.")

        # E2: `sajupy` geocodes a city name through Nominatim ONLY when longitude
        # is absent (sajupy/core.py:406). A live geocode would be a network call
        # with a usage policy and a silent fallback that CHANGES THE CHART, so we
        # refuse rather than fall back. The webapp resolves coordinates once, at
        # profile creation, from a bundled table.
        if profile.longitude is None:
            raise _http(
                422,
                "MISSING_LONGITUDE",
                "A longitude is required so solar-time correction is exact. Resolve the birthplace "
                "before requesting a chart.",
            )

        if not profile.timezone and profile.utcOffset is None:
            raise _http(422, "MISSING_TIMEZONE", "A timezone or UTC offset is required.")

        year, month, day = (int(p) for p in profile.birthDate.split("-"))
        hour, minute = (int(p) for p in (profile.birthTime or "12:00").split(":"))

        try:
            offset, from_timezone = derive_utc_offset(
                year, month, day, hour, minute, profile.timezone, profile.utcOffset
            )
        except Exception as exc:  # noqa: BLE001 - unknown zone etc.
            raise _http(422, "UNKNOWN_TIMEZONE", "That timezone could not be resolved.") from exc

        self.year, self.month, self.day = year, month, day
        self.hour, self.minute = hour, minute
        self.utc_offset = offset
        self.from_timezone = from_timezone
        self.gender = profile.gender
        self.name = (profile.fullName or "").strip() or "Client"
        self.city = (profile.city or "").strip() or None
        self.timezone = profile.timezone
        self.longitude = profile.longitude
        self.time_known = bool(profile.timeKnown)

    def compute(self, *, reference_year: Optional[int] = None):
        """A fully-derived Chart. `city` is passed for the record only — longitude wins."""
        return compute_chart(
            name=self.name,
            gender=self.gender,
            year=self.year,
            month=self.month,
            day=self.day,
            hour=self.hour,
            minute=self.minute,
            city=self.city,
            longitude=self.longitude,
            utc_offset=self.utc_offset,
            use_solar_time=True,
            convention="korean",
        )

    @property
    def dob_label(self) -> str:
        """`12 September 1994, 13:28, Seoul` — the cover's birth line."""
        try:
            from datetime import date as _date

            pretty = _date(self.year, self.month, self.day).strftime("%-d %B %Y")
        except Exception:  # noqa: BLE001 - %-d is glibc-specific
            pretty = f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
        clock = f"{self.hour:02d}:{self.minute:02d}" if self.time_known else "time unknown"
        return ", ".join(p for p in (pretty, clock, self.city or "") if p)


def _http(status: int, code: str, message: str) -> HTTPException:
    """An HTTPException carrying machine-readable detail for the caller."""
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def _error_code(exc: HTTPException) -> str:
    detail = exc.detail
    if isinstance(detail, dict):
        return str(detail.get("code") or "ENGINE_REJECTED")
    return "ENGINE_REJECTED"


def _error_message(exc: HTTPException) -> str:
    detail = exc.detail
    if isinstance(detail, dict):
        return str(detail.get("message") or "The engine rejected this request.")
    return str(detail)


# ─────────────────────────────── chart summary ───────────────────────────────


def _caveats(chart) -> List[str]:
    """Confidence notes, taken from the engine's own report text.

    Generating the one-page sample and lifting its `> ⚠` blockquotes means the
    dashboard shows exactly the wording the client PDF will use — no second copy
    of the doctrine to drift.
    """
    try:
        md = generate_premium_report(chart, tier="sample", generation_date=None)
    except Exception:  # noqa: BLE001 - caveats are optional
        return []
    notes: List[str] = []
    for line in md.splitlines():
        stripped = line.strip()
        if stripped.startswith(">") and "⚠" in stripped:
            text = stripped.lstrip("> ").replace("**", "").replace("⚠ ", "").strip()
            # Drop the leading "Hour-boundary note:"-style label's emphasis only.
            if text:
                notes.append(text)
    return notes


def _chart_summary(chart, override: Optional[str] = None) -> Dict[str, Any]:
    """The shape apps/web/src/lib/chart.ts parses."""
    fe = favorable_element(chart, override)
    cues: Dict[str, Any] = {}
    assoc = _ELEMENT_ASSOCIATIONS.get(fe.element or "")
    if assoc:
        cues = {
            "colors": [c.strip() for c in assoc.get("colors", "").split(",") if c.strip()],
            "direction": assoc.get("direction"),
            "numbers": [n.strip() for n in assoc.get("numbers", "").split(",") if n.strip()],
        }

    return {
        "pillars": [
            {"stem": chart.year.stem, "branch": chart.year.branch, "label": "Year"},
            {"stem": chart.month.stem, "branch": chart.month.branch, "label": "Month"},
            {"stem": chart.day.stem, "branch": chart.day.branch, "label": "Day"},
            {"stem": chart.hour.stem, "branch": chart.hour.branch, "label": "Hour"},
        ],
        "dayMaster": {
            "char": chart.day_master,
            "element": chart.day_master_info.get("element"),
            "polarity": chart.day_master_info.get("polarity"),
        },
        "elementBalance": {k: round(v, 1) for k, v in element_balance_pct(chart).items()},
        "strength": _strength_label(chart),
        "favorableElement": fe.element,
        "favorableProvenance": fe.method,
        "luckyCues": cues,
        "caveats": _caveats(chart),
    }


def _strength_label(chart) -> str:
    """The report's own strength label, so the dashboard cannot disagree with the PDF."""
    try:
        from saju_engine.premium_report import _strength_label as impl

        return impl(chart)
    except Exception:  # noqa: BLE001
        return (chart.strength_assessment or {}).get("verdict", "") or ""


# ─────────────────────────────── rendering ───────────────────────────────


def _render_single(profile: ProfileIn, tier: str, out_pdf: Path,
                   override: Optional[str],
                   wants_html: bool = False) -> Tuple[Path, Path, Optional[int], Optional[Path]]:
    """Mirrors `saju_web/jobs.render_single`, with the tier normalised and the override threaded."""
    data = BirthData(profile)
    chart = data.compute()
    resolved = normalize_tier(tier)
    day_master = (
        f"{chart.day_master} "
        f"({chart.day_master_info.get('element', '')} {chart.day_master_info.get('polarity', '')})"
    )
    title = f"{data.name} — Saju Reading"
    kwargs = prepare_chart_render(
        chart,
        out_pdf,
        title=title,
        client=data.name,
        dob=data.dob_label,
        day_master=day_master,
        tier=resolved,
        favorable_override=override,  # E3
    )
    pages: list = []
    pdf = build_pdf(output_pdf=out_pdf, title=title, tier=resolved, pages_out=pages, **kwargs)

    html_path: Optional[Path] = None
    if wants_html:
        # The web document (the reading) beside the PDF, from the same markdown, so the two
        # artefacts cannot disagree about a word. Self-contained: inline CSS and SVG.
        from saju_html.renderer import markdown_to_html

        document = markdown_to_html(
            Path(kwargs["input_md"]).read_text(encoding="utf-8"),
            title=title,
            client=kwargs.get("client", ""),
            dob=kwargs.get("dob", ""),
            day_master=kwargs.get("day_master", ""),
            report_id=kwargs.get("report_id", ""),
            tier=resolved,
            web=True,
        )
        html_path = out_pdf.with_suffix(".html")
        html_path.write_text(document, encoding="utf-8")
    return pdf, Path(kwargs["input_md"]), (pages[0] if pages else None), html_path


def _render_compat(
    profile_a: ProfileIn, profile_b: ProfileIn, tier: str, out_dir: Path,
    override_a: Optional[str], override_b: Optional[str],
    wants_html: bool = False,
) -> Tuple[Path, Path, Optional[int], Optional[Path]]:
    """Mirrors `saju_web/jobs.render_compat`."""
    data_a, data_b = BirthData(profile_a), BirthData(profile_b)
    chart_a, chart_b = data_a.compute(), data_b.compute()
    selected = tier if tier in _COMPAT_TIERS else "basic"

    def _slug(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-") or "partner"

    base = f"{_slug(data_a.name)[:24]}_{_slug(data_b.name)[:24]}_compatibility"
    if selected == "deep":
        base += "_deep"
    out_md, out_pdf = out_dir / f"{base}.md", out_dir / f"{base}.pdf"

    markdown = generate_compat_report(
        chart_a,
        chart_b,
        name_a=data_a.name,
        name_b=data_b.name,
        favorable_element_a=override_a or None,
        favorable_element_b=override_b or None,
        tier=selected,
    )
    out_md.write_text(markdown, encoding="utf-8")

    title = (
        f"Deep Compatibility Reading — {data_a.name} × {data_b.name}"
        if selected == "deep"
        else f"Compatibility Reading — {data_a.name} × {data_b.name}"
    )
    pages: list = []
    # One report ID for both artefacts. The renderer would derive exactly this string itself (as does
    # the ReportLab backend), so passing it changes nothing about the PDF — it just means the reading
    # and the PDF cannot disagree about the ID printed in the footer.
    report_id = f"CID-{out_pdf.stem}-{date.today().strftime('%Y%m%d')}"
    pdf = build_pdf(
        input_md=out_md,
        output_pdf=out_pdf,
        title=title,
        client=f"{data_a.name} ({chart_a.day_master}) · {data_b.name} ({chart_b.day_master})",
        dob=f"{data_a.dob_label} · {data_b.dob_label}",
        day_master=f"{chart_a.day_master}/{chart_b.day_master}",
        tier="compat",
        report_id=report_id,
        pages_out=pages,
    )
    html_path: Optional[Path] = None
    if wants_html:
        # The same renderer and the same web mode a single-chart reading uses: the compat markdown is
        # just markdown, so `markdown_to_html(web=True)` gives the two-chart reading the same screen
        # artefact — self-contained, inline CSS and SVG, no external requests. (This used to be
        # withheld on the belief that the compat product rendered through a separate renderer with no
        # web mode; it does not — `md_to_saju_compat_pdf.py` wraps this very `build_pdf`.)
        from saju_html.renderer import markdown_to_html

        document = markdown_to_html(
            out_md.read_text(encoding="utf-8"),
            title=title,
            client=f"{data_a.name} ({chart_a.day_master}) · {data_b.name} ({chart_b.day_master})",
            dob=f"{data_a.dob_label} · {data_b.dob_label}",
            day_master=f"{chart_a.day_master}/{chart_b.day_master}",
            report_id=report_id,
            tier="compat",
            web=True,
        )
        html_path = out_pdf.with_suffix(".html")
        html_path.write_text(document, encoding="utf-8")
    return pdf, out_md, (pages[0] if pages else None), html_path


def _upload(artifact: Path, upload_url: str, *, content_type: str = "application/pdf",
            timeout: float = 60.0) -> None:
    """PUT a rendered artefact to the caller's presigned URL. Stdlib only."""
    body = artifact.read_bytes()
    request = urllib.request.Request(
        upload_url, data=body, method="PUT", headers={"Content-Type": content_type}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status not in (200, 201, 204):
                raise _http(502, "UPLOAD_FAILED", "The rendered PDF could not be stored.")
    except urllib.error.HTTPError as exc:
        log.error("upload rejected by storage: HTTP %s", exc.code)  # status only, never the URL
        raise _http(502, "UPLOAD_FAILED", "The rendered PDF could not be stored.") from exc


# ─────────────────────────────── endpoints ───────────────────────────────


@app.post("/health")
def health(authorization: Optional[str] = Header(None)) -> JSONResponse:
    """Readiness. Cheap: no engine work, just configuration and imports."""
    _authorize(authorization)
    fonts = None
    try:
        from saju_html.md_to_saju_pdf import _DEJAVU_DIR

        fonts = str(_DEJAVU_DIR) if _DEJAVU_DIR else None
    except Exception:  # noqa: BLE001
        pass
    return JSONResponse(
        {
            "status": "ok",
            "engineVersion": ENGINE_VERSION,
            "contractVersion": CONTRACT_VERSION,
            "fontsDir": fonts,
        }
    )


@app.post("/chart")
def chart(request: ChartRequest, authorization: Optional[str] = Header(None)) -> JSONResponse:
    """Derive the chart summary only — no render, no upload.

    Called when a profile is created so the dashboard and the order flow can show
    the four pillars for confirmation BEFORE any payment."""
    _authorize(authorization)
    if request.contractVersion != CONTRACT_VERSION:
        return _fail(422, "CONTRACT_VERSION_MISMATCH", "This engine speaks contract version "
                     f"{CONTRACT_VERSION}, but the request asked for {request.contractVersion}.")
    try:
        data = BirthData(request)
        summary = _chart_summary(data.compute(), None)
    except HTTPException as exc:
        return _fail(exc.status_code, _error_code(exc), _error_message(exc))
    except Exception as exc:  # noqa: BLE001
        log.error("chart failed for intake: %s", type(exc).__name__)
        return _fail(500, "CHART_FAILED", "The chart could not be derived.")
    return JSONResponse(summary)


@app.post("/script")
def script(request: ScriptRequest, authorization: Optional[str] = Header(None)) -> JSONResponse:
    """Derive the spoken-word audio script from an approved report's markdown.

    Deterministic and side-effect free — no model, no clock, no upload. Returns an empty
    script when the text promises no audio summary, which is how the caller learns there
    is nothing to narrate."""
    _authorize(authorization)
    if request.contractVersion != CONTRACT_VERSION:
        return _fail(422, "CONTRACT_VERSION_MISMATCH", "This engine speaks contract version "
                     f"{CONTRACT_VERSION}, but the request asked for {request.contractVersion}.")
    if not request.markdown.strip():
        return _fail(422, "EMPTY_MARKDOWN", "No report text was supplied.")

    try:
        spoken = build_audio_script(request.markdown)
    except Exception as exc:  # noqa: BLE001
        log.error("script derivation failed: %s", type(exc).__name__)
        return _fail(500, "SCRIPT_FAILED", "The audio script could not be derived.")

    return JSONResponse(
        {
            "script": spoken,
            "chunks": chunk_for_tts(spoken) if spoken else [],
            "stats": script_stats(spoken) if spoken else {"chars": 0, "words": 0, "estimatedSeconds": 0},
            "engineVersion": ENGINE_VERSION,
        }
    )


@app.post("/generate")
def generate(request: GenerateRequest, authorization: Optional[str] = Header(None)) -> JSONResponse:
    """Compute, render, upload. Returns integrity metadata, never the PDF itself."""
    _authorize(authorization)

    if request.contractVersion != CONTRACT_VERSION:
        return _fail(422, "CONTRACT_VERSION_MISMATCH", "This engine speaks contract version "
                     f"{CONTRACT_VERSION}, but the request asked for {request.contractVersion}.")
    if request.kind not in _KINDS:
        return _fail(422, "INVALID_KIND", f"kind must be one of {list(_KINDS)}.")
    if not request.uploadUrl:
        return _fail(422, "MISSING_UPLOAD_URL", "An uploadUrl is required.")
    if request.kind == "compat" and request.profileB is None:
        return _fail(422, "COMPAT_NEEDS_TWO_PROFILES", "A compatibility reading needs two people.")
    if request.kind == "single" and request.tier not in _SINGLE_TIERS:
        return _fail(422, "INVALID_TIER", f"Unknown single-chart tier {request.tier!r}.")
    if request.kind == "compat" and request.tier not in _COMPAT_TIERS:
        return _fail(422, "INVALID_TIER", f"Unknown compatibility tier {request.tier!r}.")

    started = time.monotonic()
    html_digest: Optional[str] = None
    html_size: Optional[int] = None
    try:
        with tempfile.TemporaryDirectory(prefix="saju-render-") as tmp:
            out_dir = Path(tmp)
            if request.kind == "compat":
                pdf, markdown_path, page_count, html_path = _render_compat(
                    request.profileA, request.profileB, request.tier, out_dir,
                    request.favorableOverrideA, request.favorableOverrideB,
                    wants_html=bool(request.htmlUploadUrl),
                )
            else:
                pdf, markdown_path, page_count, html_path = _render_single(
                    request.profileA, request.tier, out_dir / "report.pdf",
                    request.favorableOverrideA,
                    wants_html=bool(request.htmlUploadUrl),
                )
            digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
            size = pdf.stat().st_size
            _upload(pdf, request.uploadUrl)
            if request.htmlUploadUrl and html_path is not None:
                # Best-effort, like the markdown: the reading failing to upload must not
                # lose the report. The response says so, so the caller can retry the
                # document without re-rendering the PDF.
                try:
                    document = html_path.read_bytes()
                    _upload(html_path, request.htmlUploadUrl,
                            content_type="text/html; charset=utf-8")
                    html_digest = hashlib.sha256(document).hexdigest()
                    html_size = len(document)
                except HTTPException:
                    log.error("web document upload failed; the PDF is still delivered")
            if request.mdUploadUrl:
                # Best-effort: a missing markdown only costs the audio and the audit
                # trail, never the client's report.
                try:
                    _upload(markdown_path, request.mdUploadUrl, content_type="text/markdown")
                except HTTPException:
                    log.error("source markdown upload failed; report still delivered")
    except HTTPException as exc:
        return _fail(exc.status_code, _error_code(exc), _error_message(exc))
    except Exception as exc:  # noqa: BLE001
        # Exception messages can embed birth data — log the class and frames only.
        log.error("render failed: %s", type(exc).__name__,
                  exc_info=(type(exc), None, exc.__traceback__))
        return _fail(500, "RENDER_FAILED", "The report could not be rendered.")

    return JSONResponse(
        {
            "sha256": digest,
            "bytes": size,
            # The rendered page count, so the review console can show the real figure rather than an
            # em dash. Null when the backend cannot report it (the HTML/Playwright renderer);
            # production renders with ReportLab.
            "pages": page_count,
            # Integrity metadata for the web document (the reading), null when it was not
            # requested or could not be uploaded. The PDF fields above are unaffected.
            "htmlSha256": html_digest,
            "htmlBytes": html_size,
            "engineVersion": ENGINE_VERSION,
            "durationMs": int((time.monotonic() - started) * 1000),
        }
    )
