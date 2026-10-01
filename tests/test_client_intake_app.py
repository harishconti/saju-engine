"""F-3 (2026-09-26 audit): the self-service calculator FastAPI app could not
even be imported (`NameError: name 'TOOLS_DIR' is not defined`), broken since
its introduction on 2026-09-19 despite being marked "done" in CLAUDE.md.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_PATH = PROJECT_ROOT / "tools" / "client_intake_app.py"


def _load_app_module():
    spec = importlib.util.spec_from_file_location("client_intake_app", APP_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_client_intake_app_imports_without_error():
    module = _load_app_module()
    assert module.app is not None


def test_client_intake_app_form_paths_resolve_to_tools_dir():
    module = _load_app_module()
    assert module.TOOLS_DIR == PROJECT_ROOT / "tools"
    assert module.FORM_PATH == PROJECT_ROOT / "tools" / "client_intake_app.html"
    assert module.FORM_PATH.exists()
    assert module.COMPAT_FORM_PATH == PROJECT_ROOT / "tools" / "client_compat_intake_form.html"
    assert module.COMPAT_FORM_PATH.exists()


def test_compat_generate_does_not_forward_raw_candidate_favorable_as_override():
    """N-7 (2026-09-26 audit): a blank favorable_element_a/_b form field used
    to fall back to strength_assessment["candidate_favorable"] — the raw,
    pre-climate 억부 pick — and forward it to generate_compat_report() as a
    favorable_element_a/_b override. compat.py's compat_score() treats ANY
    non-empty value there as an outright reader-confirmed override, bypassing
    the climate merge and mislabeling unreviewed engine output. The fix is to
    only forward the form field itself, verbatim (never a chart's own
    strength_assessment), and let favorable_element() resolve the rest."""
    source = APP_PATH.read_text()
    assert '.get("candidate_favorable")' not in source
    assert "strength_assessment[\"candidate_favorable\"]" not in source
    assert "strength_assessment[\"_raw_unresolved_favorable\"]" not in source


def test_no_module_reads_the_raw_favorable_field_outside_the_permitted_set():
    """2026-09-14 audit §5 item 2, closed form: the raw pick is published
    ONLY as ``_raw_unresolved_favorable`` (no ``candidate_favorable`` alias).
    Four modules had adopted the old name as if it were a public 용신 field, and
    two of them shipped a pre-climate element to clients.

    Permit reads only in the producer (strength.py), the resolver
    (yongsin.py) and the validation harness (validation.py, which compares raw
    vs resolved by design). daeun_overlay.py is the one intentional
    exception: its overlay displays the strength-heuristic pick explicitly and
    is covered by its own note.
    """
    import ast
    import pathlib

    import saju_engine

    RAW = "_raw_unresolved_favorable"
    LEGACY = "candidate_favorable"
    src_root = pathlib.Path(saju_engine.__file__).parent
    # Reads of the raw key are permitted only where the value is used AS the
    # raw diagnostic (or compared against the resolved value on purpose).
    # skeleton.py is included because its snapshot line is explicitly labelled
    # "Raw 억부 candidate (pre-climate, unresolved)" and sits beside the
    # resolved element — the self-flag the underscore prefix exists for.
    permitted = {
        "strength.py", "yongsin.py", "validation.py",
        "daeun_overlay.py", "skeleton.py",
    }

    def _string_accesses(text):
        """Return the string literals used as a subscript key or a .get()/.pop()
        argument — i.e. real field reads, ignoring comments and docstrings."""
        found = []
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
                if isinstance(node.slice.value, str):
                    found.append(node.slice.value)
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in ("get", "pop", "setdefault")
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                found.append(node.args[0].value)
        return found

    offenders = []
    for path in sorted(src_root.glob("*.py")):
        if path.name in permitted:
            continue
        for key in _string_accesses(path.read_text(encoding="utf-8")):
            if key in (RAW, LEGACY):
                offenders.append(f"{path.name}:{key}")
    assert not offenders, (
        f"modules outside {sorted(permitted)} read the raw favorable field: {offenders}. "
        "Client-facing 용신 must come from yongsin.favorable_element(chart)."
    )


def test_compat_generate_never_writes_into_the_curated_deliverable_folder(monkeypatch, tmp_path):
    """N-14 (2026-09-26 audit): /compat/generate used to render straight into
    candidates_horoscope/marriage_compatibility/{slug_a}_{slug_b}/ — the same
    curated folder the manual /saju-client workflow uses for reviewed client
    deliverables. A public request naming a real past client pair silently
    overwrote their actual PDF. It must render into its own scratch directory
    under INTAKE_DIR instead, and never touch the curated folder."""
    import asyncio

    module = _load_app_module()
    monkeypatch.setattr(module, "INTAKE_DIR", tmp_path)
    curated_dir = module.PROJECT_ROOT / "candidates_horoscope" / "marriage_compatibility"
    before = set(curated_dir.rglob("*")) if curated_dir.exists() else set()

    # Call the route function directly (bypassing the ASGI/HTTP layer, which
    # this environment's httpx/starlette versions don't agree on for
    # TestClient) — FastAPI's @app.post decorator returns the plain
    # coroutine function unchanged, so it's callable like any other async def.
    response = asyncio.run(module.compat_generate(
        name_a="N14-Test-A", dob_a="1990-06-15", birth_time_a="10:00",
        location_a="Seoul", utc_offset_a=9.0, gender_a="M",
        name_b="N14-Test-B", dob_b="1992-03-20", birth_time_b="14:00",
        location_b="Seoul", utc_offset_b=9.0, gender_b="F",
        email="test@example.com", main_concern="", favorable_element_a="",
        favorable_element_b="", timezone_a="", timezone_b="", tier="basic",
    ))
    assert Path(response.path).exists()
    after = set(curated_dir.rglob("*")) if curated_dir.exists() else set()
    assert before == after, "compat_generate must never write into the curated deliverable folder"
    assert any(tmp_path.rglob("*compatibility.pdf")), "PDF should render into the scratch INTAKE_DIR instead"


def test_intake_forms_do_not_default_utc_offset_to_india():
    """F-10 (2026-09-26 audit): both self-service intake forms hard-coded
    value="5.5" (India UTC offset) as the pre-filled default, contradicting
    the 2026-09-07 India-to-English-global pivot (CLAUDE.md: "India is a
    Phase-2 PPP experiment only — no India-specific content or funnel
    work"). A client who doesn't overwrite it gets a silently wrong chart.
    """
    for html_path, field_ids in [
        (PROJECT_ROOT / "tools" / "client_intake_app.html", ["utc_offset"]),
        (PROJECT_ROOT / "tools" / "client_compat_intake_form.html", ["utc_offset_a", "utc_offset_b"]),
    ]:
        html = html_path.read_text()
        for field_id in field_ids:
            start = html.index(f'id="{field_id}"')
            tag = html[start:html.index(">", start)]
            assert 'value="5.5"' not in tag, (
                f"{html_path.name}#{field_id} must not default to India's UTC offset: {tag!r}"
            )
