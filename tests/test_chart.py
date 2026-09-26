"""Tests for the Chart dataclass and serialization."""
from __future__ import annotations

import json

import pytest

from saju_engine.chart import Chart
from saju_engine.engine import compute_chart


def test_to_json_round_trip():
    chart = compute_chart(
        gender="F",
        year=1993, month=12, day=11,
        hour=2, minute=45,
        longitude=79.32,
        utc_offset=5.5,
    )
    text = chart.to_json()
    data = json.loads(text)
    assert data["day_master"] == chart.day_master
    assert data["birth_date"] == chart.birth_date


def test_to_json_raises_on_non_serializable():
    chart = compute_chart(
        gender="F",
        year=1993, month=12, day=11,
        hour=2, minute=45,
        longitude=79.32,
        utc_offset=5.5,
    )
    # Inject a non-JSON-serializable object to ensure strict serialization fails loudly.
    object.__setattr__(chart, "name", object())  # name is a string field normally
    with pytest.raises(TypeError):
        chart.to_json()


def test_to_dict_daeun_entries_match_daeun_period_dict():
    """F-14 (2026-09-26 audit): `to_dict()`'s inline daeun-period comprehension
    duplicated `_daeun_period_dict()`'s exact shape — a DRY violation of the
    same shape that caused E-3 (the two copies could silently drift apart).
    Every to_dict()["daeun"] entry must equal `_daeun_period_dict()`'s output
    for that period.
    """
    chart = compute_chart(
        gender="F", year=1993, month=12, day=11, hour=2, minute=45,
        longitude=79.32, utc_offset=5.5,
    )
    data = chart.to_dict()
    for period, entry in zip(chart.daeun, data["daeun"]):
        assert entry == chart._daeun_period_dict(period)


def test_to_dict_has_no_duplicate_reference_date_key():
    """F-14 (2026-09-26 audit): `to_dict()` emitted the "reference_date" key
    twice (harmless since both were the same value, but a DRY violation)."""
    import inspect
    from saju_engine.chart import Chart

    src = inspect.getsource(Chart.to_dict)
    assert src.count('"reference_date"') == 1


def test_chart_logical_clusters():
    """Chart exposes birth/natal/luck/reference clusters without duplicating storage."""
    chart = compute_chart(
        name="Cluster Test", gender="F",
        year=1993, month=12, day=11,
        hour=2, minute=45,
        longitude=79.32, utc_offset=5.5,
    )
    assert chart.birth.name == chart.name
    assert chart.birth.gender == chart.gender
    assert chart.natal.day.stem == chart.day.stem
    assert chart.natal.pillars == chart.pillars
    assert chart.luck.daeun == chart.daeun
    assert chart.reference.reference_date == chart.reference_date
    # JSON output shape is unchanged.
    data = json.loads(chart.to_json())
    assert data["day_master"] == chart.day_master
    assert data["birth_date"] == chart.birth_date
