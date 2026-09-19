#!/usr/bin/env python3
"""Render the market_research/ markdown files to HTML.

Produces:
  - market_research_html/combined.html  (single combined report with TOC)
  - market_research_html/<NN>-<slug>.html  (one HTML per MD file)

Styling matches the Saju brand: clean serif body, dark navy headings,
element-color accents (Fire/Wood/etc not relevant here — uses a single
brand accent + good typography).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from datetime import date

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "misc" / "market_research"
DST = ROOT / "misc" / "market_research_html"

DOCS = [
    ("02-market-size-and-demand.md",   "Market Size & Demand",                  "02"),
    ("03-competitor-landscape.md",     "Competitor Landscape",                  "03"),
    ("04-feature-demand.md",           "Feature Demand & Codebase Gaps",        "04"),
    ("05-audience-demographics.md",    "Audience Demographics",                 "05"),
    ("06-monetization-strategy.md",    "Monetization Strategy",                 "06"),
    ("07-app-platform-decision.md",    "App Platform Decision",                 "07"),
    ("08-marketing-strategy.md",       "Marketing Strategy",                    "08"),
    ("09-product-roadmap.md",          "Product Roadmap",                       "09"),
    ("10-risks-and-do-not-do.md",      "Risks & Do-Not-Do",                     "10"),
    ("11-financial-model.md",          "Financial Model",                       "11"),
    ("12-feasibility-verdict.md",      "Feasibility Verdict — Final Go / No-Go","12"),
    ("13-architecture-saju-web-cosmicid.md", "Architecture — Backend × Vercel × Cosmic ID","13"),
]

md = MarkdownIt("gfm-like", {"html": True, "linkify": False, "typographer": True})
md.enable(["table", "strikethrough"])


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def render(md_text: str) -> str:
    return md.render(md_text)


def html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def collect_ids(html: str) -> list[str]:
    return re.findall(r'<h([1-3]) id="([^"]+)"', html)


def rewrite_anchors(html: str, prefix: str) -> str:
    """Prefix every generated id so headings are unique per file when combined.

    Also rewrite internal markdown links that pointed to <slug>#anchor>.
    """
    def add_prefix(m: re.Match) -> str:
        level, anchor = m.group(1), m.group(2)
        return f'<h{level} id="{prefix}-{anchor}"'

    return re.sub(r'<h([1-3]) id="([^"]+)"', add_prefix, html)


CSS = """
:root {
  --brand: #2b3a55;
  --brand-soft: #4a5d7e;
  --accent: #b48a3a;
  --bg: #fbfaf6;
  --bg-soft: #f3efe6;
  --ink: #1d2330;
  --ink-soft: #4a5060;
  --rule: #d9d3c4;
  --code-bg: #efe9da;
  --table-stripe: #f6f1e3;
  --max-w: 880px;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: "Iowan Old Style", "Palatino Linotype", "Cambria", "Georgia", serif;
  color: var(--ink);
  background: var(--bg);
  line-height: 1.55;
  font-size: 17px;
}
.wrap {
  max-width: var(--max-w);
  margin: 0 auto;
  padding: 56px 32px 96px;
}
header.cover {
  border-bottom: 2px solid var(--brand);
  padding-bottom: 28px;
  margin-bottom: 40px;
}
header.cover .eyebrow {
  font-family: "Helvetica Neue", "Inter", system-ui, sans-serif;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-size: 12px;
  color: var(--accent);
  font-weight: 600;
}
header.cover h1 {
  font-family: "Iowan Old Style", "Palatino Linotype", "Cambria", "Georgia", serif;
  font-size: 38px;
  line-height: 1.15;
  margin: 8px 0 12px;
  color: var(--brand);
}
header.cover .sub {
  color: var(--ink-soft);
  font-size: 16px;
  font-style: italic;
}
header.cover .meta {
  margin-top: 18px;
  font-family: "Helvetica Neue", "Inter", system-ui, sans-serif;
  font-size: 13px;
  color: var(--ink-soft);
  letter-spacing: 0.04em;
}
nav.toc {
  background: var(--bg-soft);
  border: 1px solid var(--rule);
  border-left: 4px solid var(--brand);
  padding: 22px 28px 24px;
  margin: 0 0 48px;
  border-radius: 2px;
}
nav.toc h2 {
  font-family: "Helvetica Neue", "Inter", system-ui, sans-serif;
  font-size: 13px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--brand-soft);
  margin: 0 0 14px;
  font-weight: 600;
}
nav.toc ol {
  margin: 0;
  padding-left: 22px;
  font-family: "Helvetica Neue", "Inter", system-ui, sans-serif;
  font-size: 14.5px;
}
nav.toc li { margin: 5px 0; }
nav.toc a { color: var(--brand); text-decoration: none; }
nav.toc a:hover { text-decoration: underline; }
nav.toc .doc-num {
  display: inline-block;
  width: 28px;
  color: var(--accent);
  font-weight: 600;
}
h1, h2, h3, h4 {
  font-family: "Iowan Old Style", "Palatino Linotype", "Cambria", "Georgia", serif;
  color: var(--brand);
  line-height: 1.25;
  margin: 1.6em 0 0.6em;
}
h1 { font-size: 30px; border-bottom: 1px solid var(--rule); padding-bottom: 0.25em; }
h2 { font-size: 24px; }
h3 { font-size: 19px; color: var(--brand-soft); }
h4 { font-size: 16px; color: var(--brand-soft); text-transform: uppercase; letter-spacing: 0.05em; }
p { margin: 0.6em 0 1em; }
a { color: var(--brand); }
ul, ol { padding-left: 24px; }
li { margin: 4px 0; }
strong { color: var(--ink); }
em { color: var(--ink-soft); }
hr { border: none; border-top: 1px solid var(--rule); margin: 2.5em 0; }
code {
  background: var(--code-bg);
  padding: 1px 6px;
  border-radius: 3px;
  font-family: "SF Mono", "Consolas", "Menlo", monospace;
  font-size: 0.92em;
}
pre {
  background: var(--code-bg);
  padding: 14px 16px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 14px;
  border-left: 3px solid var(--accent);
}
pre code { background: none; padding: 0; }
blockquote {
  border-left: 3px solid var(--accent);
  margin: 1.2em 0;
  padding: 4px 16px;
  color: var(--ink-soft);
  background: var(--bg-soft);
  font-style: italic;
}
table {
  border-collapse: collapse;
  width: 100%;
  margin: 1.2em 0;
  font-size: 14.5px;
  font-family: "Helvetica Neue", "Inter", system-ui, sans-serif;
}
th, td {
  border: 1px solid var(--rule);
  padding: 8px 12px;
  text-align: left;
  vertical-align: top;
}
th {
  background: var(--brand);
  color: #fbfaf6;
  font-weight: 600;
  letter-spacing: 0.02em;
}
tbody tr:nth-child(even) { background: var(--table-stripe); }
.footnote-ref { font-size: 0.8em; vertical-align: super; }
.footnotes { margin-top: 3em; border-top: 1px solid var(--rule); padding-top: 1em; font-size: 14px; }
footer.foot {
  margin-top: 64px;
  padding-top: 20px;
  border-top: 1px solid var(--rule);
  font-family: "Helvetica Neue", "Inter", system-ui, sans-serif;
  font-size: 12px;
  color: var(--ink-soft);
  letter-spacing: 0.04em;
  text-align: center;
}
@media print {
  body { background: white; font-size: 11pt; }
  .wrap { padding: 24px; max-width: none; }
  nav.toc { page-break-after: always; }
  h1, h2 { page-break-after: avoid; }
  table { page-break-inside: avoid; }
}
"""


def page_html(title: str, body_html: str, *, with_toc: list[tuple[str, str, str]] | None = None,
              cover_meta: str | None = None) -> str:
    toc_html = ""
    if with_toc:
        items = "\n".join(
            f'      <li><span class="doc-num">{num}.</span> <a href="#{anchor}">{label}</a></li>'
            for label, anchor, num in with_toc
        )
        toc_html = f"""
<nav class="toc">
  <h2>Contents</h2>
  <ol>
{items}
  </ol>
</nav>
"""
    cover = ""
    if cover_meta:
        cover = f"""
<header class="cover">
  <div class="eyebrow">Market Research · {cover_meta}</div>
  <h1>{html_escape(title)}</h1>
</header>
"""
    else:
        cover = f"""
<header class="cover">
  <div class="eyebrow">Market Research</div>
  <h1>{html_escape(title)}</h1>
</header>
"""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html_escape(title)}</title>
  <style>{CSS}</style>
</head>
<body>
  <div class="wrap">
    {cover}
    {toc_html}
    <main>
{body_html}
    </main>
    <footer class="foot">
      Saju market research · generated {date.today().isoformat()} · /
      <a href="https://github.com/anthropics/skills">no external dependencies beyond markdown-it-py</a>
    </footer>
  </div>
</body>
</html>
"""


def main() -> int:
    DST.mkdir(exist_ok=True)
    # Pre-render each file, prefixed so anchor ids are unique when combined.
    rendered: list[tuple[str, str, str, str, str]] = []  # (filename, title, num, slug, body)
    for fname, title, num in DOCS:
        src = SRC / fname
        text = src.read_text(encoding="utf-8")
        # strip the first H1 (# Title) — we use it as cover/heading
        body_md = re.sub(r"^#\s+.+?\n", "", text, count=1)
        body_html = render(body_md)
        prefix = f"d{num}"
        body_html = rewrite_anchors(body_html, prefix)
        slug = slugify(fname.replace(".md", ""))
        rendered.append((fname, title, num, slug, body_html))

    # Per-file HTML
    for fname, title, num, slug, body_html in rendered:
        # Per-file TOC: show all docs as a nav strip
        toc = [
            (r[1], f"../{r[3]}.html", r[2]) for r in rendered
        ]
        # Render a self-referential combined file at the top
        out = page_html(
            title,
            body_html,
            cover_meta=f"Document {num} of 11",
        )
        # add simple in-file nav (prev/next)
        idx = int(num) - 2
        prev_link = ""
        next_link = ""
        if idx > 0:
            prev = rendered[idx - 1]
            prev_link = f'<a href="{prev[3]}.html">← Doc {prev[2]}: {html_escape(prev[1])}</a>'
        if idx < len(rendered) - 1:
            nxt = rendered[idx + 1]
            next_link = f'<a href="{nxt[3]}.html">Doc {nxt[2]}: {html_escape(nxt[1])} →</a>'
        nav_strip = f"""
<nav class="toc" style="margin-top:48px;font-size:14px;">
  <div style="display:flex;justify-content:space-between;gap:12px;">
    <div>{prev_link}</div>
    <div><a href="combined.html">↑ Combined report</a></div>
    <div>{next_link}</div>
  </div>
</nav>
"""
        out = out.replace("</main>", f"{nav_strip}</main>")
        (DST / f"{slug}.html").write_text(out, encoding="utf-8")
        print(f"wrote {slug}.html")

    # Combined HTML
    sections = []
    toc_entries = []
    for fname, title, num, slug, body_html in rendered:
        sections.append(f"""
<section id="d{num}-top">
  <header class="cover" style="margin-top:48px;">
    <div class="eyebrow">Document {num} of 11 · <a href="{slug}.html">standalone version</a></div>
    <h1>{num} · {html_escape(title)}</h1>
  </header>
  {body_html}
</section>
""")
        toc_entries.append((f"{num} · {title}", f"d{num}-top", num))

    # Cover for the combined doc
    cover_meta = "11 documents · 12 Jun 2026"
    combined_body = "\n".join(sections)
    combined_out = page_html(
        "Korean Saju — Market Research",
        combined_body,
        with_toc=toc_entries,
        cover_meta=cover_meta,
    )
    (DST / "combined.html").write_text(combined_out, encoding="utf-8")
    print("wrote combined.html")

    # Also a tiny index.html that redirects to combined
    (DST / "index.html").write_text(
        """<!doctype html>
<meta http-equiv="refresh" content="0; url=combined.html">
<title>Saju market research</title>
<p>Redirecting to <a href="combined.html">combined.html</a>…</p>
""",
        encoding="utf-8",
    )
    print("wrote index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
