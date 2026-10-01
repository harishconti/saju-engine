"""Silent-degradation logging for the presentation layer (audit §4.1).

2026-09-14 architecture audit §4.1 found 13 ``except Exception:`` blocks in
the presentation layer that degrade gracefully to a safe placeholder with
**no logging** — a genuine bug there would silently ship a
plausible-looking sentence into a paid client PDF instead of surfacing
anywhere a developer would see it. Every such site now calls
:func:`log_fallback` with a short label before falling back, under the
``saju_engine.fallback`` logger (a dedicated channel so it can be raised to
WARNING/ERROR in production without touching library logging).

Usage::

    try:
        stage = L.twelve_stage(dm, branch)
    except Exception:
        log_fallback("spouse_stage", "twelve_stage failed")
        stage = "—"

The helper never raises: logging is the last thing a fallback path should
be allowed to break.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("saju_engine.fallback")


def log_fallback(site: str, reason: str) -> None:
    """Log a swallowed-exception fallback at WARNING level.

    Args:
        site: a short stable identifier for the call site (module-relative,
            e.g. ``"prose_fillers.spouse_stage"``) so log lines are greppable.
        reason: one short sentence describing what failed.
    """
    try:
        logger.warning("fallback used at %s: %s", site, reason, exc_info=True)
    except Exception:
        # Logging must never break the fallback path itself.
        pass