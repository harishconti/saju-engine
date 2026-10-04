"""System Chrome is only used when SAJU_ALLOW_SYSTEM_CHROME=1 (same output on every machine)."""
import pytest

from saju_html.renderer import PdfBackendUnavailable, _launch_browser


class _Chromium:
    def __init__(self, bundled_ok=False, chrome_ok=True):
        self.calls = []
        self.bundled_ok, self.chrome_ok = bundled_ok, chrome_ok

    def launch(self, **kw):
        self.calls.append(kw)
        ok = self.chrome_ok if kw.get("channel") == "chrome" else self.bundled_ok
        if not ok:
            raise Exception("launch failed")
        return object()


class _PW:
    def __init__(self, **kw):
        self.chromium = _Chromium(**kw)


def test_system_chrome_not_used_by_default(monkeypatch):
    monkeypatch.delenv("SAJU_ALLOW_SYSTEM_CHROME", raising=False)
    pw = _PW()
    with pytest.raises(PdfBackendUnavailable, match="SAJU_ALLOW_SYSTEM_CHROME"):
        _launch_browser(pw)
    assert pw.chromium.calls == [{}]


def test_system_chrome_used_when_allowed(monkeypatch):
    monkeypatch.setenv("SAJU_ALLOW_SYSTEM_CHROME", "1")
    pw = _PW()
    assert _launch_browser(pw) is not None
    assert pw.chromium.calls == [{}, {"channel": "chrome"}]


def test_bundled_chromium_preferred(monkeypatch):
    monkeypatch.setenv("SAJU_ALLOW_SYSTEM_CHROME", "1")
    pw = _PW(bundled_ok=True)
    _launch_browser(pw)
    assert pw.chromium.calls == [{}]
