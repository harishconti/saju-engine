#!/usr/bin/env python3
"""UI/UX audit — measures every page against the bar stated in docs/webapp/06-frontend-ux.md.

Why it exists: that page sets an explicit acceptance bar — no horizontal body scroll at 390 / 768 /
1440, zero hydration warnings, axe clean on every screen, ≥44 px touch targets, one `<h1>`, both themes.
Every one of those is *measurable*, so none of them should be a matter of opinion. This runs the
measurements in a real browser instead of reading the markup and guessing.

The a11y engine is `axe-core` (a devDependency of apps/web, so the audit and any future e2e gate use
the same version).

Usage
-----
    # public pages only
    python3 tools/audit-ui.py

    # include the pages behind the login (creates no data; it signs in with the given account)
    AUDIT_EMAIL=you@example.com AUDIT_PASSWORD='…' python3 tools/audit-ui.py

Authenticated runs need an existing account. Audit a throwaway one rather than your own, and delete it
afterwards (`neon neon-auth user delete <id>` — see docs/webapp/09-operations.md).

Requires: `python3 -m playwright install chromium` (or a system Chrome, used as a fallback), and
`npm install` in apps/web so `axe-core/axe.min.js` is present.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
AXE = ROOT / "apps/web/node_modules/axe-core/axe.min.js"
BASE = os.environ.get("AUDIT_BASE_URL", "https://www.cosmicsaju.com")
# `--strict` turns the audit into a gate: overflow, axe, hydration and sub-44px *controls* fail it.
# Text links and the deliberately bare /login are not failures — see docs/webapp/06.
STRICT = "--strict" in sys.argv

VIEWPORTS = [("mobile", 390, 844), ("tablet", 768, 1024), ("desktop", 1440, 900)]
# The bar requires both themes to render on every screen, so each viewport is measured twice.
SCHEMES = ["dark", "light"] if os.environ.get("AUDIT_SCHEMES", "dark,light") == "dark,light" else [os.environ["AUDIT_SCHEMES"]]
PUBLIC = ["/", "/sample", "/login", "/privacy", "/terms", "/refund-policy"]
AUTHED = [
    "/dashboard",
    "/dashboard/profiles",
    "/dashboard/reports",
    "/dashboard/orders",
    "/dashboard/account",
    "/reports/new",
    "/admin",
]

# Deliberate and known: Turnstile runs at TURNSTILE_MODE=log and cannot solve a challenge under
# automation. Counting it as a page defect would drown the real findings.
NOISE = ("challenges.cloudflare.com", "turnstile", "data:,", "no available adapters")


def _overflow(pg):
    return pg.evaluate(
        """() => {
      const vw = window.innerWidth, out = [];
      // An element inside an overflow-x: auto/scroll ancestor is *meant* to overflow.
      const scrollable = (el) => {
        for (let p = el.parentElement; p; p = p.parentElement)
          if (/(auto|scroll)/.test(getComputedStyle(p).overflowX)) return true;
        return false;
      };
      for (const el of document.querySelectorAll('body *')) {
        const r = el.getBoundingClientRect();
        if (!r.width || !r.height) continue;
        if (r.right > vw + 1 && !scrollable(el)) {
          out.push({ tag: el.tagName.toLowerCase(), cls: String(el.className).slice(0, 50),
                     right: Math.round(r.right), text: (el.textContent || '').trim().slice(0, 36) });
          if (out.length >= 4) break;
        }
      }
      return out;
    }"""
    )


def _targets(pg):
    """Controls below the 44 px bar. Inline links inside prose are exempt by WCAG, and are filtered out."""
    return pg.evaluate(
        """() => {
      const out = [];
      for (const el of document.querySelectorAll('a[href], button, select, [role=tab]')) {
        const r = el.getBoundingClientRect();
        if (!r.width || !r.height) continue;
        const s = getComputedStyle(el);
        if (s.visibility === 'hidden' || s.display === 'none') continue;
        // Inline link: a link whose parent has non-link text siblings is prose, not a control.
        const inline =
          el.tagName === 'A' &&
          el.parentElement &&
          el.parentElement.textContent.trim().length > el.textContent.trim().length + 8;
        if (inline) continue;
        if (r.height < 44 || r.width < 44) {
          // A control is a button, tab or select. A text link is governed by the WCAG 2.5.8 spacing
          // exception instead (its target may be small provided neighbours are far enough apart), so it
          // is reported separately rather than counted as a defect — see docs/webapp/06.
          const control = el.tagName !== 'A';
          out.push({ kind: control ? 'control' : 'text-link', tag: el.tagName.toLowerCase(),
                     h: Math.round(r.height), w: Math.round(r.width),
                     text: (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 34) });
          if (out.length >= 8) break;
        }
      }
      return out;
    }"""
    )


def _axe(pg):
    pg.add_script_tag(content=AXE.read_text())
    return pg.evaluate(
        """async () => {
      const r = await window.axe.run(document, { resultTypes: ['violations'] });
      return r.violations.map(v => ({ id: v.id, impact: v.impact, n: v.nodes.length,
        target: (v.nodes[0]?.target || []).join(' ').slice(0, 76) }));
    }"""
    )


def measure(pg, path, label):
    console, errors = [], []
    pg.on("console", lambda m: console.append(m.text[:130]))
    pg.on("pageerror", lambda e: errors.append(str(e)[:130]))
    resp = pg.goto(BASE + path, wait_until="load", timeout=60_000)
    pg.wait_for_timeout(2500)

    noise = [c for c in console + errors if any(n in c.lower() for n in NOISE)]
    real = [c for c in console + errors if not any(n in c.lower() for n in NOISE)]
    return {
        "path": path,
        "vp": label,
        "status": resp.status if resp else 0,
        "ovf": _overflow(pg),
        "targets": _targets(pg),
        "h1": pg.evaluate("document.querySelectorAll('h1').length"),
        "shell": pg.evaluate("!!document.querySelector('header, nav, [aria-label=Dashboard]')"),
        "hydration": [c for c in real if "hydrat" in c.lower() or "did not match" in c.lower()][:2],
        "errors": real[:4],
        "noise": len(noise),
        "axe": _axe(pg),
    }


def sign_in(ctx, email, password):
    pg = ctx.new_page()
    pg.goto(BASE + "/login", wait_until="load", timeout=60_000)
    pg.fill("#email", email)
    pg.fill("#password", password)
    pg.click("button[type=submit]")
    pg.wait_for_url("**/dashboard**", timeout=30_000)
    pg.close()


def main() -> int:
    if not AXE.exists():
        print(f"  axe-core not found at {AXE}\n  run `npm install` in apps/web first.", file=sys.stderr)
        return 2

    email, password = os.environ.get("AUDIT_EMAIL"), os.environ.get("AUDIT_PASSWORD")
    pages = PUBLIC + (AUTHED if email and password else [])
    rows = []

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()

        if email and password:
            auth_ctx = browser.new_context(viewport={"width": 1280, "height": 900})
            sign_in(auth_ctx, email, password)
            cookies = auth_ctx.cookies()
            auth_ctx.close()
        else:
            cookies = None

        for label, w, h in VIEWPORTS:
            for scheme in SCHEMES:
                ctx = browser.new_context(viewport={"width": w, "height": h}, color_scheme=scheme)
                if cookies:
                    ctx.add_cookies(cookies)
                for path in pages:
                    pg = ctx.new_page()
                    try:
                        rows.append(measure(pg, path, f"{label}/{scheme}"))
                    except Exception as err:  # a page that cannot be measured is itself a finding
                        rows.append({"path": path, "vp": f"{label}/{scheme}", "error": str(err)[:120]})
                    pg.close()
                ctx.close()
        browser.close()

    print(f"\n=== {BASE} — {'public + authenticated' if cookies else 'public pages only'} ===")
    print(f"  {'page':28s} {'vp':8s} {'st':4s} {'ovf':4s} {'<44px':6s} {'h1':3s} {'shell':6s} {'hyd':4s} {'axe':4s}")
    for r in rows:
        if "error" in r:
            print(f"  {r['path']:28s} {r['vp']:8s} ERROR {r['error'][:56]}")
            continue
        print(
            f"  {r['path']:28s} {r['vp']:8s} {r['status']:<4d} {len(r['ovf']):<4d} "
            f"{len(r['targets']):<6d} {r['h1']:<3d} {('y' if r['shell'] else 'NO'):6s} "
            f"{len(r['hydration']):<4d} {len(r['axe']):<4d}"
        )

    print("\n=== FINDINGS ===")
    seen: set = set()
    for r in rows:
        if "error" in r:
            continue
        vp, path = r["vp"], r["path"]
        if r["ovf"] and (path, "ovf") not in seen:
            seen.add((path, "ovf"))
            print(f"  H-SCROLL  {path} @{vp}: {json.dumps(r['ovf'][:3])}")
        controls = [t for t in r["targets"] if t["kind"] == "control"]
        if controls and (path, "tg") not in seen:
            seen.add((path, "tg"))
            print(f"  CONTROL<44 {path} @{vp}: {json.dumps(controls[:4])}")
        links = [t for t in r["targets"] if t["kind"] == "text-link"]
        if links and (vp.split("/")[0] == "mobile") and (path, "tl") not in seen:
            seen.add((path, "tl"))
            print(f"  text-links<44 {path} @{vp}: {len(links)} (WCAG spacing exception; informal)")
        if r["h1"] != 1 and (path, "h1") not in seen:
            seen.add((path, "h1"))
            print(f"  H1 COUNT  {path}: {r['h1']}")
        if not r["shell"] and (path, "shell") not in seen:
            seen.add((path, "shell"))
            print(f"  NO SHELL  {path} @{vp}")
        if r["hydration"] and (path, "hyd") not in seen:
            seen.add((path, "hyd"))
            print(f"  HYDRATION {path}: {json.dumps(r['hydration'])}")
        for a in r["axe"]:
            key = (path, a["id"])
            if key not in seen:
                seen.add(key)
                print(f"  AXE       {path} @{vp}: {a['id']} ({a['impact']}, {a['n']}) — {a['target']}")

    failures: list[str] = []
    for r in rows:
        if "error" in r:
            failures.append(f"{r['path']} @{r['vp']}: could not be measured — {r['error']}")
            continue
        where = f"{r['path']} @{r['vp']}"
        if r["ovf"]:
            failures.append(f"{where}: horizontal scroll ({len(r['ovf'])} element(s))")
        for a in r["axe"]:
            failures.append(f"{where}: axe {a['id']} ({a['impact']}, {a['n']} node(s))")
        if r["hydration"]:
            failures.append(f"{where}: hydration warning")
        for t in (x for x in r["targets"] if x["kind"] == "control"):
            failures.append(f"{where}: control under 44px — {t['tag']} {t['w']}x{t['h']} {t['text']!r}")

    print(f"\n=== SUMMARY: {len(rows)} page/viewport runs, {len(failures)} blocking issue(s) ===")
    if failures:
        for line in failures[:25]:
            print("  ✗ " + line)
        if len(failures) > 25:
            print(f"  … +{len(failures) - 25} more")
        return 1 if STRICT else 0
    print("  ✓ clean: no overflow, no axe violations, no hydration warnings, no small controls")
    return 0


if __name__ == "__main__":
    sys.exit(main())
