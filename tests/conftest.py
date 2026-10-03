"""Shared fixtures. `intake_env` is opt-in (NOT autouse): the self-service app's
import requires SAJU_INTAKE_KEY and must never write into the real
candidates_horoscope/intake/ directory. Web tests activate it via
tests/web/conftest.py; tests/test_client_intake_app.py via `usefixtures`."""
import pytest


@pytest.fixture
def intake_env(monkeypatch, tmp_path_factory):
    from saju_web.store import generate_key

    monkeypatch.setenv("SAJU_INTAKE_KEY", generate_key())
    monkeypatch.setenv("SAJU_INTAKE_DIR", str(tmp_path_factory.mktemp("intake")))
