#!/usr/bin/env python3
"""Lightweight intake server for the Saju client intake form.

Serves `tools/client_intake_form.html` and accepts POST /submit, saving each
submission as a JSON file under `candidates_horoscope/intake/`.

Usage:
    python3 tools/client_intake_server.py
    # open http://localhost:8080 in a browser
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INTAKE_DIR = PROJECT_ROOT / "candidates_horoscope" / "intake"
FORM_PATH = PROJECT_ROOT / "tools" / "client_intake_form.html"


def _slugify(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"[^\w\s-]", "", name)
    return re.sub(r"[-\s]+", "-", name) or "candidate"


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        print(f"[{datetime.now().isoformat()}] {fmt % args}")

    def _send_json(self, status: int, data: dict) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str) -> None:
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self._send_file(FORM_PATH, "text/html; charset=utf-8")
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/submit":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(raw) if raw.strip().startswith("{") else {
                k: v for k, v in (pair.split("=", 1) for pair in raw.split("&") if "=" in pair)
            }
            payload = {k: unquote(v).strip() for k, v in payload.items()}
        except Exception as exc:
            self._send_json(400, {"ok": False, "error": f"Invalid payload: {exc}"})
            return

        required = {"name", "dob", "birth_time", "location", "email", "gender", "marriage_status", "tier"}
        missing = required - set(payload.keys())
        if missing:
            self._send_json(400, {"ok": False, "error": f"Missing fields: {sorted(missing)}"})
            return

        if payload.get("tier") == "deep" and not payload.get("main_concern", "").strip():
            self._send_json(400, {"ok": False, "error": "Main concern is required for The Deep Destiny Report tier."})
            return

        INTAKE_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        slug = _slugify(payload["name"])[:32]
        out_path = INTAKE_DIR / f"{timestamp}-{slug}.json"
        record = {
            "received_at": datetime.now().isoformat(),
            "source": "client_intake_form",
            "payload": payload,
        }
        out_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")

        print(f"Saved intake: {out_path}")
        self._send_json(200, {"ok": True, "saved": str(out_path)})


def main(argv: list[str] | None = None) -> int:
    port = int((argv or sys.argv)[1]) if len(argv or sys.argv) > 1 else 8080
    server = HTTPServer(("0.0.0.0", port), _Handler)
    print(f"Serving Saju intake form at http://localhost:{port}")
    print(f"Submissions will be saved to {INTAKE_DIR}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
