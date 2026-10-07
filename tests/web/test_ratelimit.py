"""P4-ratelimit: per-IP sliding-window limiter + declared body-size cap."""
from __future__ import annotations

import pytest

from saju_web.ratelimit import RateLimiter, body_too_large


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def advance(self, dt: float):
        self.t += dt


def test_allows_up_to_limit_then_blocks():
    clock = FakeClock()
    rl = RateLimiter(limit=3, window=60, clock=clock)
    assert [rl.allow("1.2.3.4")[0] for _ in range(3)] == [True, True, True]
    ok, retry = rl.allow("1.2.3.4")
    assert ok is False
    assert 0 < retry <= 60


def test_other_keys_are_independent():
    rl = RateLimiter(limit=1, window=60, clock=FakeClock())
    assert rl.allow("a")[0] is True
    assert rl.allow("b")[0] is True
    assert rl.allow("a")[0] is False


def test_window_slides():
    clock = FakeClock()
    rl = RateLimiter(limit=2, window=60, clock=clock)
    assert rl.allow("x")[0] and rl.allow("x")[0]
    assert rl.allow("x")[0] is False
    clock.advance(61)
    assert rl.allow("x")[0] is True  # old hits expired


def test_limit_zero_disables():
    rl = RateLimiter(limit=0, window=60, clock=FakeClock())
    assert all(rl.allow("x")[0] for _ in range(1000))


def test_retry_after_counts_down():
    clock = FakeClock()
    rl = RateLimiter(limit=1, window=60, clock=clock)
    rl.allow("x")
    clock.advance(20)
    ok, retry = rl.allow("x")
    assert ok is False and retry == pytest.approx(40, abs=0.01)


@pytest.mark.parametrize("length,max_bytes,expected", [
    ("100", 65536, False),
    ("70000", 65536, True),
    (None, 65536, False),
    ("", 65536, False),
    ("not-a-number", 65536, False),
    ("70000", 0, False),  # cap disabled
])
def test_body_too_large(length, max_bytes, expected):
    assert body_too_large(length, max_bytes) is expected


def test_from_env_defaults(monkeypatch):
    from saju_web.ratelimit import from_env
    monkeypatch.delenv("SAJU_RATE_LIMIT", raising=False)
    monkeypatch.delenv("SAJU_RATE_WINDOW", raising=False)
    monkeypatch.delenv("SAJU_MAX_BODY_BYTES", raising=False)
    rl, max_body = from_env()
    assert rl.limit == 20 and max_body == 65536


# ── middleware integration (driven as raw ASGI; TestClient is incompatible
#    with this environment's starlette/httpx versions) ──────────────────────

async def _run_asgi(app, *, method="POST", ip="1.2.3.4", content_length=None):
    scope = {"type": "http", "method": method, "headers": [], "client": (ip, 1234)}
    if content_length is not None:
        scope["headers"].append((b"content-length", str(content_length).encode()))
    statuses = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(msg):
        if msg["type"] == "http.response.start":
            statuses.append(msg["status"])

    await app(scope, receive, send)
    return statuses[-1] if statuses else None


async def _ok_app(scope, receive, send):
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"ok"})


@pytest.fixture
def app_mod():
    import importlib.util
    from pathlib import Path

    app_path = Path(__file__).resolve().parents[2] / "tools" / "client_intake_app.py"
    spec = importlib.util.spec_from_file_location("app_rl", app_path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_middleware_blocks_after_limit(app_mod):
    import asyncio

    app_mod._RATE_LIMITER.limit = 2
    app_mod._RATE_LIMITER._hits.clear()
    mw = app_mod.RateLimitMiddleware(_ok_app)
    assert asyncio.run(_run_asgi(mw, ip="9.9.9.9")) == 200
    assert asyncio.run(_run_asgi(mw, ip="9.9.9.9")) == 200
    assert asyncio.run(_run_asgi(mw, ip="9.9.9.9")) == 429


def test_middleware_rejects_oversized_body(app_mod):
    import asyncio

    app_mod._RATE_LIMITER._hits.clear()
    mw = app_mod.RateLimitMiddleware(_ok_app)
    assert asyncio.run(_run_asgi(mw, ip="8.8.8.8", content_length=10**7)) == 413


def test_middleware_ignores_get(app_mod):
    import asyncio

    app_mod._RATE_LIMITER.limit = 0  # would block POSTs if it applied
    app_mod._RATE_LIMITER._hits.clear()
    mw = app_mod.RateLimitMiddleware(_ok_app)
    assert asyncio.run(_run_asgi(mw, method="GET", ip="7.7.7.7")) == 200
