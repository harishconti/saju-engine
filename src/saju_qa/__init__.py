"""Saju QA — optional TypeSafe/Jev classifiers for report compliance and intake triage.

Kept separate from the deterministic ``saju_engine`` core. Requires
``TYPESAFE_API_KEY``; standard library only.
"""
from __future__ import annotations

from .client import TypesafeClient, TypesafeError
from .compliance import scan_report

__all__ = ["TypesafeClient", "TypesafeError", "scan_report"]
