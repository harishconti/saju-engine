#!/usr/bin/env python3
"""Build the web-font subsets the reading embeds, from the families the app uses.

The webapp gets its type from a Google Fonts `<link>`. A delivered reading cannot do that:
it has to be a single self-contained file, and a Google request would also tell a third
party when a client opened their report. So the faces travel *inside* the file, subsetted
to the glyphs a report actually sets.

Three families, matching `apps/web/src/app/layout.tsx` and the tokens in
`apps/web/src/app/globals.css`:

    Inter              variable (wght + opsz) — body, headings, UI
    Cormorant Garamond variable (wght)        — display headings, the cover
    IBM Plex Mono      static 400             — eyebrows, labels, table headers

Inter's italic is *not* embedded, on purpose: the app does not load one either, so the
browser synthesises the same oblique here as it does there.

    python3 tools/build-web-fonts.py            # regenerate into src/saju_html/fonts/
    python3 tools/build-web-fonts.py --check     # verify coverage; change nothing

Regenerate when the app changes its font stack, or when a report needs a glyph the
subsets do not carry — `tests/test_web_report.py` asserts the families still match the
app's tokens, and `--check` reports any missing glyph.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = REPO_ROOT / "src" / "saju_html" / "fonts"
RAW = "https://raw.githubusercontent.com/google/fonts/main"

# family, source path, output filename, CSS weight range
FACES = (
    ("Inter", f"{RAW}/ofl/inter/Inter%5Bopsz,wght%5D.ttf",
     "Inter-web.woff2", "100 900"),
    ("Cormorant Garamond", f"{RAW}/ofl/cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf",
     "CormorantGaramond-web.woff2", "300 700"),
    ("IBM Plex Mono", f"{RAW}/ofl/ibmplexmono/IBMPlexMono-Regular.ttf",
     "IBMPlexMono-web.woff2", "400"),
)
LICENCES = (
    ("Inter", f"{RAW}/ofl/inter/OFL.txt"),
    ("Cormorant Garamond", f"{RAW}/ofl/cormorantgaramond/OFL.txt"),
    ("IBM Plex Mono", f"{RAW}/ofl/ibmplexmono/OFL.txt"),
)

# Where report *prose* lives. `.csv`/`.json` are deliberately out: the engine's data tables
# are not set on a page, and including them would drag in thousands of ideographs.
SCAN_DIRS = ("knowledge", "src", "tests", "candidates_horoscope", "docs")
SCAN_SUFFIXES = (".py", ".md", ".html", ".txt")

# The Latin text of a report: ASCII, Latin-1, and the punctuation an editorial document uses
# (dashes, curly quotes, the middle dot, ellipsis), plus the block glyphs the element table's
# "Presence" column is drawn with. Emoji and CJK are *excluded* so they keep falling back to
# the reader's own colour-emoji and CJK fonts — forcing them into a text face would replace
# the app's colour emoji with monochrome outlines.
RANGES = (
    (0x20, 0x7E), (0xA0, 0xFF),          # ASCII, Latin-1
    (0x2010, 0x2015), (0x2018, 0x201D), (0x2020, 0x2022), (0x2026, 0x2026),
    (0x2030, 0x2030), (0x2032, 0x2033), (0x2039, 0x203A), (0x2044, 0x2044),
    (0x20AC, 0x20AC), (0x2122, 0x2122), (0x2190, 0x2193), (0x2212, 0x2212),
    (0x2217, 0x2217), (0x2248, 0x2248), (0x2264, 0x2265),
    (0x2580, 0x259F),                    # block elements — the "Presence" bars
    (0x25A0, 0x25CF), (0x2605, 0x2606), (0x2713, 0x2713),
)

LATIN_CHAR_RE = re.compile(
    "["
    "\u0020-\u007e\u00a0-\u00ff"
    "\u2010-\u2015\u2018-\u201d\u2020-\u2022\u2026\u2030\u2032-\u2033"
    "\u2039-\u203a\u2044\u20ac\u2122\u2190-\u2193\u2212\u2217\u2248"
    "\u2264-\u2265\u2580-\u259f\u25a0-\u25cf\u2605-\u2606\u2713"
    "]"
)


def collect_codepoints() -> set:
    """Every glyph a report can set, from the corpus plus the ranges above."""
    codepoints = set()
    for low, high in RANGES:
        codepoints.update(range(low, high + 1))
    found: set = set()
    for directory in SCAN_DIRS:
        root = REPO_ROOT / directory
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
                continue
            if "__pycache__" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            found.update(LATIN_CHAR_RE.findall(text))
    codepoints.update(ord(char) for char in found)
    print(f"  repo Latin glyphs found: {len(found)} distinct")
    return codepoints


def download(url: str, destination: Path) -> Path:
    if destination.exists() and destination.stat().st_size > 0:
        print(f"  cached {destination.name}")
        return destination
    print(f"  downloading {url.rsplit('/', 1)[-1]}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310 - fixed URL
        destination.write_bytes(response.read())
    return destination


def build(codepoints: set, workdir: Path, *, check: bool) -> int:
    from fontTools import subset
    from fontTools.ttLib import TTFont

    missing = 0
    for family, url, filename, _weight in FACES:
        target = FONT_DIR / filename
        if check:
            if not target.exists():
                print(f"  MISSING {filename}")
                missing += 1
                continue
            source = download(url, workdir / Path(url).name.replace("%5B", "[").replace("%5D", "]")
                              .replace(",", "_"))
            drawable = set(TTFont(str(source)).getBestCmap())
            undrawable = [c for c in codepoints if c not in drawable]
            if undrawable:
                print(f"  {filename}: {len(undrawable)} glyphs the face itself lacks "
                      f"(they fall back to the reader's fonts)")
            absent = sorted(c for c in codepoints if c in drawable
                            and c not in set(TTFont(str(target)).getBestCmap()))
            if absent:
                print(f"  {filename}: {len(absent)} glyphs uncovered "
                      f"(e.g. {''.join(chr(c) for c in absent[:10])})")
                missing += 1
            else:
                print(f"  {filename}: covers all {len(codepoints)} glyphs")
            continue

        source = download(url, workdir / Path(url).name.replace("%5B", "[").replace("%5D", "]")
                          .replace(",", "_"))
        font = TTFont(str(source))
        drawable = set(font.getBestCmap())
        undrawable = sorted(c for c in codepoints if c not in drawable)
        options = subset.Options()
        # `layout_features="*"` keeps kerning and the `calt`/`liga` behaviour the app gets;
        # the variable axes are kept (this is a subset, not an instance), so one file serves
        # every weight the tokens ask for.
        options.layout_features = ["*"]
        options.name_IDs = ["*"]
        options.notdef_outline = True
        options.recalc_bounds = True
        options.drop_tables += ["DSIG"]
        subsetter = subset.Subsetter(options=options)
        subsetter.populate(unicodes=sorted(codepoints))
        subsetter.subset(font)
        font.flavor = "woff2"
        target.parent.mkdir(parents=True, exist_ok=True)
        font.save(str(target))
        note = f" — {len(undrawable)} glyphs the face does not have" if undrawable else ""
        print(f"  wrote {filename}: {target.stat().st_size // 1024} KB{note}")
        if undrawable:
            print(f"    outside the face (fall back to the reader's fonts): "
                  f"{''.join(chr(c) for c in undrawable[:12])}")

    licence = FONT_DIR / "LICENSE-WebFonts.txt"
    if not check and not licence.exists():
        parts = ["The three webfaces embedded in the delivered reading are redistributed "
                 "under the SIL Open Font License 1.1. Their notices follow.\n"]
        for family, url in LICENCES:
            path = download(url, workdir / f"OFL-{family.split()[0]}.txt")
            parts.append(f"\n{'=' * 78}\n{family}\n{'=' * 78}\n\n"
                         + path.read_text(encoding="utf-8").strip() + "\n")
        licence.write_text("".join(parts), encoding="utf-8")
        print(f"  wrote {licence.name}")
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="verify the bundled subsets cover the report's glyphs")
    parser.add_argument("--workdir", default="/tmp/opencode",
                        help="where to cache the downloaded source fonts")
    args = parser.parse_args()

    codepoints = collect_codepoints()
    print(f"  subsetting to {len(codepoints)} glyphs (Latin, punctuation, block elements)")
    missing = build(codepoints, Path(args.workdir), check=args.check)
    if args.check and missing:
        print("  FAIL: rebuild with: python3 tools/build-web-fonts.py")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
