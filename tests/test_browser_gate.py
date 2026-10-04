"""Browser selection for the HTML/Playwright PDF backend: bundled Chromium is
preferred; a system Google Chrome is used (with a warning) when it is missing,
unless SAJU_ALLOW_SYSTEM_CHROME=0 requires the bundled browser."""
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


def test_system_chrome_used_with_warning_by_default(monkeypatch):
    monkeypatch.delenv("SAJU_ALLOW_SYSTEM_CHROME", raising=False)
    pw = _PW()
    with pytest.warns(UserWarning, match="system Google Chrome"):
        assert _launch_browser(pw) is not None
    assert pw.chromium.calls == [{}, {"channel": "chrome"}]


def test_strict_mode_refuses_system_chrome(monkeypatch):
    monkeypatch.setenv("SAJU_ALLOW_SYSTEM_CHROME", "0")
    pw = _PW()
    with pytest.raises(PdfBackendUnavailable, match="playwright install chromium"):
        _launch_browser(pw)
    assert pw.chromium.calls == [{}]


def test_bundled_chromium_preferred(monkeypatch):
    monkeypatch.delenv("SAJU_ALLOW_SYSTEM_CHROME", raising=False)
    pw = _PW(bundled_ok=True)
    _launch_browser(pw)
    assert pw.chromium.calls == [{}]


def test_no_browser_at_all_raises(monkeypatch):
    monkeypatch.delenv("SAJU_ALLOW_SYSTEM_CHROME", raising=False)
    pw = _PW(chrome_ok=False)
    with pytest.raises(PdfBackendUnavailable):
        _launch_browser(pw)
