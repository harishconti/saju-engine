"""In-app per-IP rate limiting and request body-size cap (P4-ratelimit).

A reverse proxy should still enforce these at deploy time (D3); this is a
defence-in-depth default for the self-service app so a single IP cannot exhaust
the render queue. Pure stdlib so the ``saju_web`` package stays import-light.

Configuration (read by ``from_env``):
    SAJU_RATE_LIMIT      max requests per window per IP (default 20; 0 disables)
    SAJU_RATE_WINDOW     window length in seconds (default 60)
    SAJU_MAX_BODY_BYTES  max POST body bytes (default 65536; 0 disables)
"""
from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque
from typing import Callable, Deque, Dict, Tuple


class RateLimiter:
    """Thread-safe sliding-window per-key limiter.

    ``allow(key)`` returns ``(True, 0.0)`` when the request is permitted, or
    ``(False, retry_after_seconds)`` when the key has exceeded ``limit`` calls
    within ``window`` seconds. ``limit <= 0`` disables limiting. ``clock`` is
    injectable for deterministic tests.
    """

    def __init__(self, limit: int, window: float,
                 clock: Callable[[], float] = time.monotonic):
        self.limit = limit
        self.window = window
        self._clock = clock
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> Tuple[bool, float]:
        if self.limit <= 0:
            return True, 0.0
        now = self._clock()
        cutoff = now - self.window
        with self._lock:
            q = self._hits[key]
            while q and q[0] <= cutoff:
                q.popleft()
            if len(q) >= self.limit:
                return False, max(0.0, self.window - (now - q[0]))
            q.append(now)
            return True, 0.0


def body_too_large(content_length: str | None, max_bytes: int) -> bool:
    """True when a POST ``Content-Length`` exceeds ``max_bytes`` (0 = no cap).

    A missing or non-numeric length is allowed here (the framework will stream
    it); the cap is a fast rejection for declared-oversized bodies.
    """
    if max_bytes <= 0 or not content_length:
        return False
    try:
        return int(content_length) > max_bytes
    except ValueError:
        return False


def from_env() -> Tuple[RateLimiter, int]:
    """Build ``(RateLimiter, max_body_bytes)`` from the environment."""
    def _int(name: str, default: int) -> int:
        try:
            return int(os.environ.get(name, str(default)))
        except ValueError:
            return default
    try:
        window = float(os.environ.get("SAJU_RATE_WINDOW", "60"))
    except ValueError:
        window = 60.0
    limiter = RateLimiter(_int("SAJU_RATE_LIMIT", 20), window)
    max_body = _int("SAJU_MAX_BODY_BYTES", 65536)
    return limiter, max_body
