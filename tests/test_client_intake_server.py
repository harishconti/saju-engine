"""N-14 (2026-09-26 audit): client_intake_server.py decoded form bodies with
`unquote`, not `unquote_plus` — `+` encodes a space in
application/x-www-form-urlencoded bodies, so "John Doe" was stored as
"John+Doe".
"""
from __future__ import annotations

import http.client
import importlib.util
import json
import threading
from http.server import HTTPServer
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVER_PATH = PROJECT_ROOT / "tools" / "client_intake_server.py"


def _load_server_module():
    spec = importlib.util.spec_from_file_location("client_intake_server", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_submit_decodes_plus_as_space_in_form_body(tmp_path, monkeypatch):
    module = _load_server_module()
    monkeypatch.setattr(module, "INTAKE_DIR", tmp_path)

    httpd = HTTPServer(("127.0.0.1", 0), module._Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        body = (
            "name=John+Doe&dob=1990-01-01&birth_time=10%3A00&location=Seoul"
            "&email=a%40b.com&gender=M&marriage_status=single&tier=essential"
        )
        conn = http.client.HTTPConnection(*httpd.server_address)
        conn.request(
            "POST", "/submit", body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded",
                     "Content-Length": str(len(body))},
        )
        resp = conn.getresponse()
        result = json.loads(resp.read())
        assert result["ok"] is True
        saved = json.loads(Path(result["saved"]).read_text(encoding="utf-8"))
        assert saved["payload"]["name"] == "John Doe"
        assert saved["payload"]["birth_time"] == "10:00"
        assert saved["payload"]["email"] == "a@b.com"
    finally:
        httpd.shutdown()
        thread.join(timeout=5)
