"""Tests for the optional saju_qa classifier package (no network)."""
from __future__ import annotations

import json

import pytest

from saju_qa import TypesafeClient, TypesafeError, scan_report


class _FakeClient:
    """Routes answers off the check keyword in each question."""

    def __init__(self, available=True):
        self._available = available
        self.calls = []

    def available(self):
        return self._available

    def classify(self, state, questions, **kw):
        self.calls.append(questions)
        answers = {}
        for key, q in questions.items():
            text = str(q.get("instructions", {}).get("question", "")).lower()
            if "hedged" in text:
                val = 0.1  # not hedged
            elif "certain" in text or "future" in text:  # predictive / future-oriented
                val = 0.9
            else:
                val = 0.0
            answers[key] = {"type": "noul", "noul": val}
        return {"model": "jev-test", "answers": answers,
                "usage": {"input_tokens": 10, "output_tokens": 5}}


# ── block extraction ──────────────────────────────────────────────────


def test_blocks_skips_headings_tables_and_short():
    from saju_qa.compliance import _blocks

    md = (
        "# Heading\n\n"
        "| A | B |\n|---|---|\n| 1 | 2 |\n\n"
        "Short.\n\n"
        "This is a long enough prose paragraph about the reading tendency and its "
        "possible implications for the coming year."
    )
    blocks = _blocks(md, max_blocks=10)
    assert len(blocks) == 1
    assert "tendency" in blocks[0]


# ── scan_report ───────────────────────────────────────────────────────


def test_scan_flags_predictive_and_unhedged():
    md = "Your career will certainly collapse next year and you will lose everything."
    client = _FakeClient()
    rep = scan_report(md, client=client)
    assert rep["clean"] is False
    assert len(rep["flagged"]) == 1
    assert "predictive" in rep["flagged"][0]["flags"]
    assert "not_hedged" in rep["flagged"][0]["flags"]
    assert len(client.calls) == 1  # all checks batched into ONE call


def test_scan_clean_when_hedged_and_not_predictive():
    class _Clean(_FakeClient):
        def classify(self, state, questions, **kw):
            answers = {}
            for k, q in questions.items():
                text = str(q.get("instructions", {}).get("question", "")).lower()
                if "hedged" in text:
                    val = 1.0
                elif "certain" in text:
                    val = 0.0
                elif "future" in text:
                    val = 0.9
                else:
                    val = 0.0
                answers[k] = {"type": "noul", "noul": val}
            return {"answers": answers, "usage": {"input_tokens": 5, "output_tokens": 1}}

    md = ("You may find that this period tends to favour steady effort rather than "
          "sudden moves, and the reading suggests a gradual shift.")
    rep = scan_report(md, client=_Clean())
    assert rep["clean"] is True
    assert rep["flagged"] == []


def test_scan_raises_without_key():
    with pytest.raises(TypesafeError):
        scan_report("some prose block that is definitely long enough to be scanned.",
                    client=_FakeClient(available=False))


def test_scan_empty_report_is_clean():
    rep = scan_report("# Title\n\n| a | b |\n|---|---|", client=_FakeClient())
    assert rep == {"n_blocks": 0, "clean": True, "flagged": [], "counts": {}, "usage": {}}


# ── client request shape ───────────────────────────────────────────────


def test_client_builds_bearer_request(monkeypatch):
    import saju_qa.client as c

    captured = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps({"model": "jev-1", "answers": {},
                               "usage": {"input_tokens": 1}}).encode()

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["auth"] = req.get_header("Authorization")
        captured["body"] = json.loads(req.data.decode())
        return _Resp()

    monkeypatch.setattr(c.urllib.request, "urlopen", fake_urlopen)
    out = c.TypesafeClient(api_key="ts_test").classify(
        "state", {"q": {"type": "noul", "instructions": "yes?"}})

    assert captured["url"].endswith("/v1/systemone")
    assert captured["auth"] == "Bearer ts_test"
    assert captured["body"]["model"] == "jev-latest"
    assert out["model"] == "jev-1"


def test_client_requires_key(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    with pytest.raises(TypesafeError):
        TypesafeClient().classify("x", {"q": {"type": "noul", "instructions": "?"}})
