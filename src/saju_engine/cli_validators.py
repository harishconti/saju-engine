"""Shared argparse type-validators for CLI/renderer entry points.

Every entry point that accepts a raw ``--utc-offset`` from the command line
must use ``utc_offset_float`` so the [-12, 14] range check can't drift out of
sync between ``cli.py`` and the PDF renderers (see docs audit I1, 2026-09-20).
"""
from __future__ import annotations

import argparse


def utc_offset_float(s: str) -> float:
    try:
        v = float(s)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"utc-offset must be a number, got {s!r}") from exc
    if not -12 <= v <= 14:
        raise argparse.ArgumentTypeError(f"utc-offset must be in [-12, 14], got {v}")
    return v
