#!/usr/bin/env python3
"""End-to-end smoke: does the DEPLOYED engine produce a reading for a compatibility order?

Signs R2 PUT/GET/DELETE URLs itself (SigV4, stdlib only — no boto3), points the live engine at a
throwaway prefix, then fetches the objects back and checks them: both artefacts really arrived, the
document is the two-chart one, it is self-contained and private, and it passes the client-ready gate.
Everything it creates is deleted at the end.

Usage: python3 smoke_compat_reading.py [basic|deep]
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ENV: dict[str, str] = {}
for line in (ROOT / "apps/web/.env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        ENV[k.strip()] = v.strip().strip('"').strip("'")

ENDPOINT = ENV["R2_ENDPOINT"].rstrip("/")
BUCKET = ENV["R2_BUCKET"]
REGION = ENV.get("R2_REGION") or "auto"
ACCESS = ENV["R2_ACCESS_KEY_ID"]
SECRET = ENV["R2_SECRET_ACCESS_KEY"]


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


def presign(method: str, key: str, expires: int = 900) -> str:
    """A presigned URL for one object. Signs `host` only, so the engine may send Content-Type."""
    now = datetime.now(timezone.utc)
    stamp, day = now.strftime("%Y%m%dT%H%M%SZ"), now.strftime("%Y%m%d")
    host = urllib.parse.urlparse(ENDPOINT).netloc
    scope = f"{day}/{REGION}/s3/aws4_request"
    query = {
        "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
        "X-Amz-Credential": f"{ACCESS}/{scope}",
        "X-Amz-Date": stamp,
        "X-Amz-Expires": str(expires),
        "X-Amz-SignedHeaders": "host",
    }
    canonical_query = "&".join(
        f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}"
        for k, v in sorted(query.items())
    )
    canonical_request = "\n".join([
        method,
        f"/{BUCKET}/{urllib.parse.quote(key, safe='/')}",
        canonical_query,
        f"host:{host}\n",
        "host",
        "UNSIGNED-PAYLOAD",
    ])
    to_sign = "\n".join([
        "AWS4-HMAC-SHA256", stamp, scope,
        hashlib.sha256(canonical_request.encode()).hexdigest(),
    ])
    k = _sign(f"AWS4{SECRET}".encode(), day)
    for part in (REGION, "s3", "aws4_request"):
        k = _sign(k, part)
    signature = hmac.new(k, to_sign.encode(), hashlib.sha256).hexdigest()
    return f"{ENDPOINT}/{BUCKET}/{key}?{canonical_query}&X-Amz-Signature={signature}"


def post(url: str, payload: dict, token: str) -> tuple[int, dict]:
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        try:
            return exc.code, json.loads(body)
        except Exception:
            return exc.code, {"raw": body[:400]}


def fetch(url: str) -> bytes | None:
    try:
        with urllib.request.urlopen(url, timeout=120) as response:
            return response.read()
    except urllib.error.HTTPError:
        return None


def delete(url: str) -> int:
    request = urllib.request.Request(url, method="DELETE")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code


PROFILE_A = {
    "fullName": "Smoke Alpha", "gender": "F", "birthDate": "1992-03-20",
    "birthTime": "14:00", "timeKnown": True, "timezone": "Asia/Seoul",
    "utcOffset": 9, "city": "Seoul", "latitude": 37.5665, "longitude": 126.978,
}
PROFILE_B = {
    "fullName": "Smoke Beta", "gender": "M", "birthDate": "1978-04-02",
    "birthTime": "23:00", "timeKnown": True, "timezone": "Asia/Seoul",
    "utcOffset": 9, "city": "Seoul", "latitude": 37.5665, "longitude": 126.978,
}


def main() -> int:
    tier = sys.argv[1] if len(sys.argv) > 1 else "basic"
    if tier not in ("basic", "deep"):
        print("  tier must be basic or deep")
        return 2

    stamp = time.strftime("%Y%m%d-%H%M%S")
    prefix = f"smoke/compat-{tier}-{stamp}"
    keys = {kind: f"{prefix}.{kind}" for kind in ("pdf", "md", "html")}
    urls = {kind: presign("PUT", key) for kind, key in keys.items()}
    gets = {kind: presign("GET", key) for kind, key in keys.items()}
    deletes = {kind: presign("DELETE", key) for kind, key in keys.items()}

    engine = ENV["ENGINE_URL"].rstrip("/")
    print(f"  engine   : {engine}")
    print(f"  tier     : compat/{tier}")
    print(f"  prefix   : {prefix}")
    print("  asking the deployed engine for a compatibility reading with htmlUploadUrl …\n")

    started = time.monotonic()
    status, body = post(f"{engine}/generate", {
        "contractVersion": 1,
        "kind": "compat",
        "tier": tier,
        "uploadUrl": urls["pdf"],
        "mdUploadUrl": urls["md"],
        "htmlUploadUrl": urls["html"],
        "profileA": PROFILE_A,
        "profileB": PROFILE_B,
        "favorableOverrideA": None,
        "favorableOverrideB": None,
    }, ENV["ENGINE_SERVICE_TOKEN"])
    elapsed = time.monotonic() - started

    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, ok, detail))

    check("engine returned 200", status == 200, f"HTTP {status} {body.get('code') or ''}")
    if status != 200:
        print(f"  ✗ HTTP {status}: {json.dumps(body)[:400]}")
        for kind in ("pdf", "md", "html"):
            delete(deletes[kind])
        return 1

    check("PDF bytes reported", bool(body.get("bytes")), f"{body.get('bytes')} bytes, {body.get('pages')} pages")
    # THE ASSERTION THIS SMELL TEST EXISTS FOR.
    check("htmlSha256 is set (the reading was rendered AND uploaded)",
          bool(body.get("htmlSha256")), str(body.get("htmlSha256"))[:16] + "…")
    check("htmlBytes is set", bool(body.get("htmlBytes")), f"{body.get('htmlBytes')} bytes")

    pdf = fetch(gets["pdf"])
    document = fetch(gets["html"])
    markdown = fetch(gets["md"])
    check("PDF object really stored", bool(pdf and pdf.startswith(b"%PDF")), f"{len(pdf or b'')} bytes")
    check("markdown object really stored", bool(markdown and markdown.startswith(b"#")),
          f"{len(markdown or b'')} bytes")
    check("reading object really stored",
          bool(document and document.startswith(b"<!DOCTYPE html")), f"{len(document or b'')} bytes")

    if document:
        text = document.decode("utf-8", errors="replace")
        check("it is the two-chart document (both partners named)",
              "Smoke Alpha" in text and "Smoke Beta" in text)
        check("titled as a compatibility reading", "Compatibility Reading" in text)
        check("private (noindex)", "noindex" in text)
        check("no scripts and no external stylesheets",
              "<script" not in text and "<link " not in text)
        check("viewport present", 'name="viewport"' in text)
        faces = text.count("data:font/woff2")
        check("faces embedded for offline reading", faces >= 3, f"{faces} woff2 faces")
        external = sorted({
            u for u in (
                "fonts.googleapis", "fonts.gstatic", "cdn.", "unpkg", "jsdelivr",
            ) if u in text
        })
        check("no third-party references", not external, ", ".join(external) or "none")

        # The same gate the reviewer runs, over the artefact the client would open.
        sys.path.insert(0, str(ROOT / "tools"))
        from qa_client_ready import _html_text, scan  # noqa: PLC0415

        findings = scan(_html_text(text), source="html", rendered=True, name="Smoke Alpha", tier="compat")
        codes = sorted({f.code for f in findings})
        check("passes the client-ready gate", not findings, ", ".join(codes) or "CLEAN")

    print(f"  done in {elapsed:.1f}s\n")
    for name, ok, detail in checks:
        print(f"    {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))

    for kind in ("pdf", "md", "html"):
        delete(deletes[kind])
    print(f"\n  cleaned up {prefix}.*")

    return 0 if all(ok for _, ok, _ in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
