import pytest


@pytest.fixture(autouse=True)
def _web_intake_env(intake_env):
    """Every test under tests/web gets a throwaway key + intake dir."""
