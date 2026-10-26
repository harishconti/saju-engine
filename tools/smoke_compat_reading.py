#!/usr/bin/env python3
"""End-to-end smoke: does the DEPLOYED engine produce a reading for a compatibility order?

Signs R2 PUT/GET/DELETE URLs itself (SigV4, stdlib only — no boto3), points the live engine at a
throwaway prefix, then fetches the objects back and checks them: both artefacts really arrived, the
document is the two-chart one, it is self-contained and private, and it passes the client-ready gate.
Everything it creates is deleted at the end.

The URLs are **virtual-hosted** (`https://{bucket}.{endpoint-host}/{key}`), exactly like
`apps/web/src/lib/r2.ts`, which builds its S3 client without `forcePathStyle`. That is the only
shape the engine is ever sent in production, so it is the only shape worth smoking.

Engine project environment this exercises (set on the deployed Vercel engine, not here):

  SAJU_UPLOAD_HOSTS    optional, comma-separated extra upload hosts. `R2_ENDPOINT` alone is
                       enough, because the engine also accepts `{bucket}.{R2_ENDPOINT host}`.
                       **Empty is fatal**: the engine refuses every render with
                       `UPLOAD_HOSTS_UNCONFIGURED` (see `/health`, which reports
                       `uploadAllowlist`). This is the state the tool exists to catch.
  R2_ENDPOINT          the S3 endpoint; its host anchors the allowlist.
  SAJU_UPLOAD_BUCKET   optional; when set, pins uploads to that bucket (host label or path).

Credentials for this script (from the process environment, or `apps/web/.env` as a fallback —
the file is parsed, never `source`d):

  R2_ENDPOINT, R2_BUCKET, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_REGION (optional,
  default `auto`), ENGINE_URL, ENGINE_SERVICE_TOKEN

A missing value is fatal and named: a smoke that cannot run must fail, not pass.

Usage: python3 smoke_compat_reading.py [basic|deep]
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / "apps/web/.env"


@dataclass(frozen=True)
class R2Config:
    """What the signer needs. The names are the webapp's own (`R2_*`)."""

    endpoint: str
    bucket: str
    access_key_id: str
    secret_access_key: str
    region: str = "auto"

    @property
    def host(self) -> str:
        """The virtual-hosted host the webapp's S3 client uses: `{bucket}.{endpoint host}`."""
        return f"{self.bucket}.{urllib.parse.urlsplit(self.endpoint).netloc}"


def read_env_file(path: Path) -> dict[str, str]:
    """Parse a dotenv file. A missing file is an empty mapping — CI supplies the environment."""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip().strip('"').strip("'")
    return values


def load_config(
    environ: Mapping[str, str] | None = None, env_file: Path | None = None
) -> tuple[R2Config, str, str]:
    """Return `(r2 config, engine url, engine token)`.

    The process environment wins, so GitHub Actions can pass the same names as secrets;
    `apps/web/.env` is the local fallback. Never `source` the file — parsing it keeps the
    values out of the shell's environment (and out of any child process it spawns).
    """
    file_values = read_env_file(env_file if env_file is not None else ENV_FILE)
    live = os.environ if environ is None else environ

    def get(name: str) -> str:
        value = (live.get(name) or file_values.get(name) or "").strip()
        if not value:
            raise SystemExit(
                f"  missing {name} — set it in the environment or {ENV_FILE} "
                "(never `source` the file)"
            )
        return value

    cfg = R2Config(
        endpoint=get("R2_ENDPOINT").rstrip("/"),
        bucket=get("R2_BUCKET"),
        access_key_id=get("R2_ACCESS_KEY_ID"),
        secret_access_key=get("R2_SECRET_ACCESS_KEY"),
        region=(live.get("R2_REGION") or file_values.get("R2_REGION") or "auto").strip(),
    )
    return cfg, get("ENGINE_URL").rstrip("/"), get("ENGINE_SERVICE_TOKEN")


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


def presign(method: str, key: str, cfg: R2Config, expires: int = 900) -> str:
    """A presigned URL for one object, virtual-hosted — exactly like the webapp.

    `src/lib/r2.ts` presigns `https://{bucket}.{endpoint-host}/{key}` (the S3 client is built
    without `forcePathStyle`). The engine's allowlist accepts that shape — one extra DNS label
    on the `R2_ENDPOINT` host — so this is the URL to smoke. Signing path-style would test a
    target production never uses, and would have passed while a real render failed
    (AU-03, 2026-10-26 audit). Signs `host` only, so the engine may send Content-Type.
    """
    now = datetime.now(timezone.utc)
    stamp, day = now.strftime("%Y%m%dT%H%M%SZ"), now.strftime("%Y%m%d")
    host = cfg.host
    scope = f"{day}/{cfg.region}/s3/aws4_request"
    quoted_key = urllib.parse.quote(key, safe="/")
    query = {
        "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
        "X-Amz-Credential": f"{cfg.access_key_id}/{scope}",
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
        f"/{quoted_key}",
        canonical_query,
        f"host:{host}\n",
        "host",
        "UNSIGNED-PAYLOAD",
    ])
    to_sign = "\n".join([
        "AWS4-HMAC-SHA256", stamp, scope,
        hashlib.sha256(canonical_request.encode()).hexdigest(),
    ])
    k = _sign(f"AWS4{cfg.secret_access_key}".encode(), day)
    for part in (cfg.region, "s3", "aws4_request"):
        k = _sign(k, part)
    signature = hmac.new(k, to_sign.encode(), hashlib.sha256).hexdigest()
    scheme = urllib.parse.urlsplit(cfg.endpoint).scheme or "https"
    return f"{scheme}://{host}/{quoted_key}?{canonical_query}&X-Amz-Signature={signature}"


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

    cfg, engine, token = load_config()

    stamp = time.strftime("%Y%m%d-%H%M%S")
    prefix = f"smoke/compat-{tier}-{stamp}"
    keys = {kind: f"{prefix}.{kind}" for kind in ("pdf", "md", "html")}
    urls = {kind: presign("PUT", key, cfg) for kind, key in keys.items()}
    gets = {kind: presign("GET", key, cfg) for kind, key in keys.items()}
    deletes = {kind: presign("DELETE", key, cfg) for kind, key in keys.items()}

    print(f"  engine   : {engine}")
    print(f"  storage  : {cfg.host}")
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
    }, token)
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
