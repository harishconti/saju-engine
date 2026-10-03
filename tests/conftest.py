"""Suite-wide env for the self-service app: its import requires SAJU_INTAKE_KEY
and must never write into the real candidates_horoscope/intake/ directory."""
import pytest


@pytest.fixture(autouse=True)
def _intake_env(monkeypatch, tmp_path_factory):
    from saju_web.store import generate_key

    monkeypatch.setenv("SAJU_INTAKE_KEY", generate_key())
    monkeypatch.setenv("SAJU_INTAKE_DIR", str(tmp_path_factory.mktemp("intake")))
