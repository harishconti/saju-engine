"""Shared fixtures. `intake_env` is opt-in (NOT autouse): the self-service app's
import requires SAJU_INTAKE_KEY and must never write into the real
candidates_horoscope/intake/ directory. Web tests activate it via
tests/web/conftest.py; tests/test_client_intake_app.py via `usefixtures`."""
import os

import pytest

# This machine only has system Chrome (no `playwright install chromium`), so the
# browser-backed PDF tests opt in to it. The gate itself is covered explicitly in
# tests/test_browser_gate.py (which sets/unsets the variable per test).
os.environ.setdefault("SAJU_ALLOW_SYSTEM_CHROME", "1")


@pytest.fixture
def intake_env(monkeypatch, tmp_path_factory):
    from saju_web.store import generate_key

    monkeypatch.setenv("SAJU_INTAKE_KEY", generate_key())
    monkeypatch.setenv("SAJU_INTAKE_DIR", str(tmp_path_factory.mktemp("intake")))
