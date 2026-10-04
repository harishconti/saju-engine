# P4 — Web Hardening (single calendar, encrypted intake store, paid-order review queue) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Source:** audit `/mnt/data2/git_repos/research-engine/output/2026-10-01/saju-engine-audit-2026-10-01.md` §3 S8a/S8d/S8e/S8f, §8 Phase 1, §9 C3/C4; leftover from Wave A: `/generate` saves intake before validating.

**User decisions (2026-10-03):**
1. **Paid orders are queued for review.** Paid tiers (essential, deep, legacy spark/reading/fullmap, compat basic/deep) are saved, an engine draft PDF is generated in the background, and the client gets "received — we'll email your reviewed report". The owner approves each order with a CLI command that issues a private download link. The free `sample` tier still downloads instantly.
2. **SQLite + encrypted PII.** One SQLite file (WAL). Name, email and main concern are encrypted with a key from the `SAJU_INTAKE_KEY` environment variable (Fernet, `cryptography` package added to the `web` extras). Birth data stays plain so charts can be recomputed. A retention command deletes intakes and their files older than N days (default 180).
3. **One calendar.** 세운/월운 transit pillars use the engine's own solar-term table (`data/solar_terms.csv`) instead of sajupy's calendar.

**Goal:** Make the self-service app keep the promise its form makes (human review before paid delivery), stop storing client PII in plaintext JSON forever, close the remaining request-handling gaps (validate-before-save, CORS, bind address, no synchronous PDF rendering for paid orders), and remove the second clock from the engine.

**Architecture:** A new small package `src/saju_web/` holds the web-side logic so it is importable and testable without FastAPI: `store.py` (SQLite + Fernet), `jobs.py` (draft generation from a stored intake), `tokens.py` (download tokens). `tools/client_intake_app.py` stays the FastAPI entry point and becomes thin. `tools/intake_admin.py` is the owner CLI (list / approve / purge). The calendar change is confined to `src/saju_engine/sewoon.py`.

**Tech Stack:** Python 3.10–3.12, FastAPI (BackgroundTasks), sqlite3 (stdlib), `cryptography` (Fernet), pytest.

## Global Constraints

- Test prefix: `PYTHONPATH=src:/home/harish/.local/lib/python3.12/site-packages`
- Baseline: 1474 passed, 5 skipped, 14 xfailed; `tools/run_validation.py` 315 checks (PASS 306, INTERPRETATION 9, FAIL 0); golden snapshots unchanged except where Task 1 explicitly allows.
- Tests call FastAPI route functions directly (`asyncio.run(module.generate(...))`) — this environment's httpx/starlette versions don't agree on `TestClient` (see tests/test_client_intake_app.py). For BackgroundTasks, construct `fastapi.BackgroundTasks()`, pass it in, then `await`/run its tasks explicitly in the test.
- Never log decrypted PII; log intake ids only.
- No email sending in this plan (audit D2) — the approve CLI prints the link for the owner to send.
- Branch: `feat/p4-web-hardening` off `develop`; one commit per task; messages end with a blank line + `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Don't touch `candidates_horoscope/` content other than the intake storage location the app writes to (the user has uncommitted work there); the new SQLite file and PDFs go under `candidates_horoscope/intake/` (already gitignored? — check `.gitignore`; if not ignored, add `candidates_horoscope/intake/*.sqlite*` and `candidates_horoscope/intake/files/` to .gitignore).

---

### Task 1: S8a — 세운/월운 use the engine's solar-term table

**Files:** `src/saju_engine/sewoon.py` (`_load_sajupy_calendar`, `_annual_pillar_for_date`, `_monthly_pillar_for_date`), test `tests/test_sewoon_calendar.py` (new).

**Approach:** Reuse the engine's own term machinery instead of sajupy's day table. `pillars._independent_year_month_pillar(year, month, day, hour, minute, utc_offset)` already derives the year and month pillar from properly timezone-converted 절기 instants (returns `None` outside the table's 1899–2101 range). For a calendar *date* (transit tables have no time), evaluate it at **12:00 KST** (`hour=12, minute=0, utc_offset=9.0`) — the same "midday representative instant" convention a day-granular table implies — and document it.

- [ ] **Step 1: Tests first**
```python
"""S8a (2026-10-01 audit): transit (세운/월운) pillars came from sajupy's
calendar_data.csv while natal/대운 used the engine's own ephemeris
(data/solar_terms.csv) — two clocks in one product. Transit lookups now use
the engine table, evaluated at 12:00 KST for a calendar date."""
from datetime import date, timedelta

from saju_engine import sewoon as SW
from saju_engine.pillars import _independent_year_month_pillar


def test_transit_pillars_match_engine_term_table_at_noon_kst():
    d = date(1990, 1, 1)
    while d < date(2031, 1, 1):
        ref = _independent_year_month_pillar(d.year, d.month, d.day, 12, 0, 9.0)
        assert "".join(SW._annual_pillar_for_date(d.year, d.month, d.day)) == ref["year_pillar"]
        assert "".join(SW._monthly_pillar_for_date(d.year, d.month, d.day)) == ref["month_pillar"]
        d += timedelta(days=1)


def test_sajupy_calendar_no_longer_loaded():
    assert not hasattr(SW, "_load_sajupy_calendar")


def test_out_of_range_fallback_still_works():
    assert SW._annual_pillar_for_date(2150, 1, 10) == SW._annual_pillar(2149)
```
(Check the exact keys `_independent_year_month_pillar` returns — adapt `"year_pillar"`/`"month_pillar"` to the real key names.)

- [ ] **Step 2: Implement** — delete `_load_sajupy_calendar`; in both date functions call `_independent_year_month_pillar(year, month, day, 12, 0, 9.0)` (import inside the function if a cycle appears); on `None` keep the existing out-of-range fallbacks. Comment: `# S8a (2026-10-01 audit): one clock — transit pillars use data/solar_terms.csv (the natal/대운 table), evaluated at 12:00 KST for a calendar date.`
- [ ] **Step 3: Measure drift** — throwaway script (not committed): for every date 1900-01-01…2100-12-31 compare old sajupy pillars vs new; report the count of differing days and confirm every differing date is a 절기 day (or ±1). Put the numbers in the report.
- [ ] **Step 4: Golden** — run `tools/regen_golden.py`; any diff must be a transit pillar for a date on a 절기 day — list each; anything else → fix. Run validation (sewoon fixtures must pass; if one fails, STOP and report — do not edit fixtures).
- [ ] **Step 5: Commit** — `fix(sewoon): S8a transit pillars use the engine solar-term table`

---

### Task 2: `saju_web.store` — SQLite intake store with encrypted PII + retention

**Files:** Create `src/saju_web/__init__.py`, `src/saju_web/store.py`, `tests/web/__init__.py`, `tests/web/test_store.py`; modify `pyproject.toml` (`web` extras: add `"cryptography>=42"`).

**Interfaces (Produces):**
```python
class IntakeStore:
    def __init__(self, db_path: Path, key: bytes): ...      # creates schema; WAL mode
    @classmethod
    def from_env(cls, db_path: Path) -> "IntakeStore": ...  # key from SAJU_INTAKE_KEY; raises RuntimeError with a how-to message if unset/invalid
    def add_intake(self, *, kind: str, tier: str, pii: dict, birth: dict) -> int   # kind ∈ {"single","compat"}; returns id; status "received"
    def get_intake(self, intake_id: int) -> dict             # decrypted: {"id","kind","tier","status","created_at","pii":{...},"birth":{...},"pdf_path","error"}
    def set_status(self, intake_id: int, status: str, *, pdf_path: Optional[str] = None, error: Optional[str] = None) -> None
    def list_intakes(self, status: Optional[str] = None) -> List[dict]   # NO pii in list rows except decrypted name
    def issue_token(self, intake_id: int) -> str             # status must be "draft_ready"; stores sha256(token); sets status "approved"; returns the raw token once
    def resolve_token(self, token: str) -> Optional[dict]    # approved intake for this token, else None
    def purge_older_than(self, days: int, *, now: Optional[datetime] = None) -> int   # deletes rows + their PDF/MD files; returns count
STATUSES = ("received", "generating", "draft_ready", "approved", "failed")
def generate_key() -> str   # Fernet.generate_key().decode()
```
Schema: `intake(id INTEGER PRIMARY KEY, created_at TEXT, kind TEXT, tier TEXT, status TEXT, pii_enc BLOB, birth_json TEXT, pdf_path TEXT, error TEXT, token_sha256 TEXT UNIQUE, approved_at TEXT)`. `pii_enc` = Fernet(json.dumps(pii)). `birth_json` plain (dob, birth_time, location, utc_offset, timezone, gender, marriage_status; compat: a_/b_ prefixed). Thread-safety: one connection per call (`sqlite3.connect(..., timeout=10)`), `PRAGMA journal_mode=WAL` at init.

- [ ] **Step 1: Tests first** (`tests/web/test_store.py`) — roundtrip add/get decrypts PII; raw DB file bytes do not contain the plaintext name/email/concern (open the sqlite file and `assert b"alice@example.com" not in data`); wrong key → `get_intake` raises; `from_env` without the variable raises RuntimeError mentioning `SAJU_INTAKE_KEY`; status transitions; `issue_token` only from `draft_ready`, returns a token that `resolve_token` finds, DB stores only the hash; `purge_older_than(180, now=...)` removes old rows and their files, keeps recent ones; `list_intakes` rows contain no email/concern.
- [ ] **Step 2: Implement.** Skip all tests in `tests/web/` cleanly if `cryptography` is not importable (`pytest.importorskip("cryptography")`); install it locally with `pip install --user --break-system-packages cryptography` if missing and note it in the report.
- [ ] **Step 3: Verify + commit** — `feat(web): S8/C3 SQLite intake store with encrypted PII and retention`

---

### Task 3: Wire the app — validate-before-save, review queue, download tokens, CORS/bind

**Files:** Create `src/saju_web/jobs.py`, `tools/intake_admin.py`, `tests/web/test_app_flow.py`, `tests/web/test_admin_cli.py`; modify `tools/client_intake_app.py`, `tools/client_intake_app.html`, `tools/client_compat_intake_form.html`, `tests/test_client_intake_app.py` (adapt tests that assumed instant PDFs for paid tiers / JSON files in INTAKE_DIR).

**Interfaces:**
```python
# src/saju_web/jobs.py
def generate_draft(store: IntakeStore, intake_id: int, files_dir: Path) -> None
    # sets "generating", computes chart(s) + PDF via the existing app helpers' logic
    # (move _generate_pdf / the compat _render body here, parameterised by the stored
    # birth+pii dicts), writes into files_dir/<id>/, sets "draft_ready" (pdf_path) or
    # "failed" (error = exception class name only; full traceback to the log, no PII).
PAID_TIERS = {"essential", "deep", "spark", "reading", "fullmap", "basic"}   # compat basic/deep are paid; "deep" covers both
```
App behaviour:
- **Both POST routes validate everything first** (required fields, tier, gender, DOB/time parse, offset/timezone, deep-concern rule) and only then write to the store. Invalid → 400, nothing stored (extend the S8c test to `/generate`).
- **Sample tier** (`/generate` with `tier == "sample"`): store the intake, generate the PDF synchronously in the threadpool as today, mark the intake `approved` (no token needed) and return the PDF. The free hook stays instant.
- **Paid tiers** (all other single tiers; both compat tiers): store, schedule `generate_draft` via `BackgroundTasks`, return **202** JSON `{"status": "received", "intake_id": <id>, "message": "Thank you — your reading is being prepared and will be reviewed by a human reader before delivery. We'll email you a private download link."}`.
- **`GET /report/{token}`**: `store.resolve_token(token)` → FileResponse of the approved PDF; unknown/unapproved → 404 (same response for both, no detail).
- Storage: `IntakeStore.from_env(INTAKE_DIR / "intake.sqlite")`, files under `INTAKE_DIR / "files"`. App startup fails fast with the RuntimeError message if `SAJU_INTAKE_KEY` is missing.
- **CORS (S8e):** `allow_credentials=False`, `allow_headers=["Content-Type"]`, methods `["GET","POST"]`; keep env-driven origins.
- **Bind:** `SAJU_HOST` env (default `127.0.0.1`) and port arg as today.
- **Forms:** submit handler branches on response: `application/pdf` → download (sample); `202` JSON → show the message in the status region; errors → message. Make the status regions `role="status" aria-live="polite"` and replace any `alert()` with status text.
- **Admin CLI** `tools/intake_admin.py`: `list [--status S]`, `show <id>` (decrypted, for the owner), `approve <id> [--base-url URL]` (requires `draft_ready`; prints `<base-url>/report/<token>`; default base URL `http://localhost:8080`), `regenerate <id>` (re-runs `generate_draft`), `purge --days N` (default 180), `genkey` (prints a new key). Uses `IntakeStore.from_env`.

- [ ] **Step 1: Tests first** — `tests/web/test_app_flow.py` (set `SAJU_INTAKE_KEY` via monkeypatch to `generate_key()`, point `INTAKE_DIR` at tmp_path, reload the app module): invalid `/generate` → 400 and no rows; sample → PDF response + intake approved; paid single → 202 JSON, row `received`, running the background task → `draft_ready` with an existing PDF; compat basic → 202; `/report/<bad>` → 404; after `issue_token`, `/report/<token>` → the PDF; app module import without the key raises. `tests/web/test_admin_cli.py`: `approve` on `received` fails with a clear message; on `draft_ready` prints a URL containing a token that resolves; `purge` deletes old rows. Update `tests/test_client_intake_app.py` tests that relied on JSON files / instant paid PDFs (keep their intent: N-14 curated-folder protection, N-7 override passthrough, F-10 offsets, S7 prices).
- [ ] **Step 2: Implement** (jobs.py extraction first, then routes, then forms, then CLI).
- [ ] **Step 3: Verify** — full suite, validation, golden unchanged, ruff F. Manual smoke: `SAJU_INTAKE_KEY=$(python3 tools/intake_admin.py genkey) python3 tools/client_intake_app.py 8099` in the background, `curl -F ...` a sample and a paid request, check 200 PDF / 202 JSON, then kill it. Record output in the report.
- [ ] **Step 4: Commit** — `feat(web): S8d/S8f paid-order review queue, download tokens, validate-before-save, CORS/bind hardening`

---

### Task 4: Docs + tracker

- [ ] `CLAUDE.md` "Client Intake": describe the review queue (sample instant; paid → 202 + review), `SAJU_INTAKE_KEY`, `tools/intake_admin.py` commands, retention default; `/saju-client` workflow note: approve via the CLI after reviewing the draft.
- [ ] `README.md`, `docs/openwiki/operations/toolchain-and-testing.md`, `docs/openwiki/products/reports.md`: same, briefly; remove "saved as JSON" wording.
- [ ] `docs/issues_bugs.md`: S8a, S8c (/generate), S8d, S8e, S8f, C3, C4 → FIXED with SHAs; M15 (plaintext intake) → FIXED.
- [ ] `docs/MEMORY.md`: Recent Changes bullet + "Open: email delivery (D2), MoR checkout (D1), deploy (D3)".
- [ ] Full suite + validation; commit `docs: record P4 web hardening`.
