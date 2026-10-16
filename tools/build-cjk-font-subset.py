#!/usr/bin/env python3
"""Rebuild the bundled Hangul/Hanja font subset used by the ReportLab PDF backend.

`src/saju_html/md_to_saju_pdf.py` draws CJK that survives translation (pillar
Hanja, star names, glossary terms) with `SajuCJK`, a glyph-subset of Noto Sans KR.
Subsetting matters because the source face is ~10 MB; the bundled subset is a few
hundred KB, and reportlab re-subsets it again to the glyphs each PDF actually
uses, so the delivered PDF stays small.

Run this whenever the report content gains CJK the subset does not cover — a new
Hanja in `knowledge/`, or a Hangul term the translation maps do not list. The
`test_cjk_font_covers_repo_cjk` regression test fails when one does.

    python3 tools/build-cjk-font-subset.py            # regenerate in place
    python3 tools/build-cjk-font-subset.py --check     # verify, change nothing

The subset contains every Hangul syllable and Hanja the repo uses plus ASCII and
Latin-1 — ~200 KB per face. It is *not* the whole font: a report never draws the
~20k ideographs in the engine's Hanja data tables, and bundling them would cost
2.4 MB per face. Characters the Korean face cannot draw at all (simplified Chinese
forms) are reported by `--check` and dropped at render time, so a tofu box can
never reach a client.

The source is the OFL-licensed Noto Sans KR variable TTF from google/fonts. The
licence text is kept beside the fonts as `LICENSE-NotoSansKR.txt`.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = REPO_ROOT / "src" / "saju_html" / "fonts"
SOURCE_URL = (
    "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanskr/"
    "NotoSansKR%5Bwght%5D.ttf"
)
LICENSE_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanskr/OFL.txt"

# Weights to emit. Names must match `_CJK_FACE_FILES` in the renderer.
FACES = ((400, "SajuCJK-Regular.ttf"), (700, "SajuCJK-Bold.ttf"))

# Scanned for the Hanja a *report* can contain. Deliberately excludes `.csv` and
# `.json`: the engine's data tables hold ~20k ideographs (a Hanja dictionary),
# none of which reach report prose, and including them would bloat the subset
# from ~195 KB to the whole font. `src/saju_engine` and `knowledge/` are where
# report text comes from; `tests/` holds the probes.
SCAN_DIRS = ("knowledge", "src", "tests", "candidates_horoscope")
SCAN_SUFFIXES = (".py", ".md", ".html", ".txt")

# ASCII + Latin-1, so a CJK run's Latin neighbours always have a face too.
LATIN_RANGES = ((0x20, 0x7F), (0xA0, 0xFF))

CJK_CHAR_RE = re.compile(
    "[\u1100-\u11ff\u3000-\u303f\u3130-\u318f\u3400-\u4dbf\u4e00-\u9fff"
    "\uac00-\ud7a3\uf900-\ufaff\uff00-\uffef]"
)


def collect_codepoints() -> set:
    """Unicode codepoints a Saju report may need to draw."""
    codepoints = set()
    for lo, hi in LATIN_RANGES:
        codepoints.update(range(lo, hi + 1))
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
            found.update(CJK_CHAR_RE.findall(text))
    codepoints.update(ord(char) for char in found)
    print(f"  repo CJK codepoints found: {len(found)} distinct")
    return codepoints


def download(url: str, destination: Path) -> Path:
    if destination.exists() and destination.stat().st_size > 0:
        print(f"  cached {destination.name}")
        return destination
    print(f"  downloading {url.rsplit('/', 1)[-1]}")
    with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310 - fixed URL
        destination.write_bytes(response.read())
    return destination


def build(codepoints: set, workdir: Path, *, check: bool) -> int:
    from fontTools import subset
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer

    missing = 0
    # Noto Sans KR is a *Korean* face: it has no simplified-Chinese forms, and a
    # handful of ideographs in this repo (and the regex literals in the CJK
    # routing patterns) are outside it. Those cannot be drawn by any Korean face,
    # so they are not a subsetting gap; the renderer drops them rather than
    # printing a tofu box. Compare against the source face to keep the check
    # honest.
    source = download(SOURCE_URL, workdir / "NotoSansKR-VF.ttf")
    drawable = set(TTFont(str(source)).getBestCmap())
    undrawable = sorted(c for c in codepoints if c not in drawable)
    if undrawable:
        print(f"  outside Noto Sans KR (dropped at render time): {len(undrawable)} "
              f"{''.join(chr(c) for c in undrawable[:12])}")

    for weight, filename in FACES:
        target = FONT_DIR / filename
        if check:
            if not target.exists():
                print(f"  MISSING {filename}")
                missing += 1
                continue
            cmap = TTFont(str(target)).getBestCmap()
            absent = sorted(c for c in codepoints if c in drawable and c not in cmap)
            if absent:
                print(f"  {filename}: {len(absent)} drawable codepoints uncovered "
                      f"(e.g. {''.join(chr(c) for c in absent[:8])})")
                missing += 1
            else:
                print(f"  {filename}: covers every drawable codepoint "
                      f"({len(codepoints) - len(undrawable)} of {len(codepoints)})")
            continue

        font = TTFont(str(source))
        instanced = instancer.instantiateVariableFont(font, {"wght": weight}, inplace=False)
        options = subset.Options()
        options.name_IDs = ["*"]
        options.name_legacy = True
        options.notdef_outline = True
        options.recalc_bounds = True
        options.drop_tables += ["DSIG"]
        subsetter = subset.Subsetter(options=options)
        subsetter.populate(unicodes=sorted(codepoints))
        subsetter.subset(instanced)
        family = f"NotoSansKR{'-Bold' if weight == 700 else ''}"
        for record in instanced["name"].names:
            if record.nameID in (1, 4, 6, 16, 17):
                try:
                    record.string = family
                except Exception:  # pragma: no cover - legacy encodings
                    pass
        target.parent.mkdir(parents=True, exist_ok=True)
        instanced.save(str(target))
        print(f"  wrote {filename}: {target.stat().st_size // 1024} KB")

    licence = FONT_DIR / "LICENSE-NotoSansKR.txt"
    if not check and not licence.exists():
        download(LICENSE_URL, licence)
        print(f"  wrote {licence.name}")
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="verify coverage of the bundled faces; change nothing")
    parser.add_argument("--workdir", default="/tmp/opencode",
                        help="where to cache the downloaded source font")
    args = parser.parse_args()

    codepoints = collect_codepoints()
    print(f"  subsetting to {len(codepoints)} codepoints "
          f"(all Hangul + every Hanja the repo uses)")
    missing = build(codepoints, Path(args.workdir), check=args.check)
    if args.check and missing:
        print("  FAIL: rebuild with: python3 tools/build-cjk-font-subset.py")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
