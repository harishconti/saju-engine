#!/usr/bin/env python3
"""Build the TTF Satori needs for the Open Graph image, from the committed woff2 subsets.

Why this exists
---------------
`next/og` renders the OG image with Satori, which accepts **ttf / otf / woff** but *not* woff2 —
verified against the bundled runtime (`node_modules/next/dist/compiled/@vercel/og` contains no
`woff2` handling, and ships a `.ttf` as its own default face). The brand faces in
`src/saju_html/fonts/` are woff2, because that is what the *web* needs, so the OG image needs a
second rendering of the same outline.

It re-derives that from the file already in the repo rather than re-downloading from Google, so the
build has no network dependency and the two cannot drift in anything but format. Subsetting to the
Latin/punctuation set an OG image actually sets keeps it small.

    python3 tools/build-og-fonts.py            # write the TTF
    python3 tools/build-og-fonts.py --check    # verify it covers what the OG image sets
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fontTools import subset  # type: ignore
from fontTools.ttLib import TTFont  # type: ignore
from fontTools.varLib import instancer  # type: ignore

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src" / "saju_html" / "fonts"
# Colocated with the route that reads it, which is the pattern Next documents for local OG fonts —
# and what makes Vercel's output tracing pick it up.
OUT_DIR = REPO_ROOT / "apps" / "web" / "src" / "lib" / "og-fonts"

# family → (source, output ttf, weight to pin or None)
#
# The first two sources are **variable** fonts (Inter carries opsz+wght, Cormorant wght). Satori's
# parser cannot read a variable font — it fails while parsing the static tables it expects, with an
# opaque "Cannot read properties of undefined" during prerender. So each is instanced to a single
# static weight first; that is also why the results are small.
#
# The third is the repo's own Hangul/Hanja subset (already a static TTF). It is needed because the
# shared Day Master card prints the four pillars in Hanja, and the Latin faces carry no CJK — without
# it Satori has no glyph and renders nothing. The subset is 1007 glyphs; restricted to the 22
# stems/branches it costs a few KB.
FACES = (
    ("Cormorant Garamond", SRC_DIR / "CormorantGaramond-web.woff2", "CormorantGaramond-og.ttf", 600, "latin"),
    ("Inter", SRC_DIR / "Inter-web.woff2", "Inter-og.ttf", 400, "latin"),
    ("SajuCJK", SRC_DIR / "SajuCJK-Regular.ttf", "SajuCJK-og.ttf", None, "hanja"),
)

# The Hanja a four-pillars card can print: the ten heavenly stems, the twelve earthly branches, and
# the seal character the site already uses as a mark.
STEMS_BRANCHES = "甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥四"

# ASCII, Latin-1 letters/punctuation, general punctuation (— – ' ' " " … ·), and the
# arrows/box-drawing the layout never uses but a future caption might.
# Coverage for the Latin faces.
UNICODES = (
    "U+0020-007E,U+00A0-00FF,U+2010-2015,U+2018-201D,U+2026,U+00B7,U+2713,U+2014"
)


def build(check_only: bool) -> int:
    missing = [str(src) for _, src, _, _, _ in FACES if not src.exists()]
    if missing:
        print(
            "missing font source(s):\n  " + "\n  ".join(missing)
            + "\n(latin faces: run tools/build-web-fonts.py; hanja: tools/build-cjk-font-subset.py)",
            file=sys.stderr,
        )
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    problems = 0
    for family, src_path, out_name, weight, coverage in FACES:
        out_path = OUT_DIR / out_name

        font = TTFont(str(src_path))

        # Pin every axis: the requested weight on `wght`, each axis's own default elsewhere
        # (Inter also carries `opsz`). Skipped for faces already static.
        if weight is not None and "fvar" in font:
            pinned = {
                axis.axisTag: (weight if axis.axisTag == "wght" else axis.defaultValue)
                for axis in font["fvar"].axes
            }
            font = instancer.instantiateVariableFont(font, pinned, inplace=False, updateFontNames=False)

        options = subset.Options()
        options.flavor = None          # uncompressed TTF, which is what Satori wants
        options.desubroutinize = True
        options.recalc_bounds = True
        options.drop_tables += ["DSIG"]

        if coverage == "hanja":
            unicodes = subset.parse_unicodes(",".join(f"U+{ord(c):04X}" for c in STEMS_BRANCHES))
        else:
            unicodes = subset.parse_unicodes(UNICODES)

        subsetter = subset.Subsetter(options=options)
        subsetter.populate(unicodes=unicodes)
        subsetter.subset(font)

        if check_only:
            covered = set(font.getBestCmap())
            need_chars = STEMS_BRANCHES if coverage == "hanja" else "CosmicSajuYourchartisarithmetic0123456789—·'\""
            # No checkmark in the Latin set on purpose: Cormorant Garamond has none, which is the kind
            # of gap this mode exists to surface (it caught it on the first run).
            gap = sorted({ord(c) for c in need_chars} - covered)
            if gap:
                problems += 1
                print(f"{family}: MISSING {''.join(chr(c) for c in gap)!r}")
            else:
                print(f"{family}: ok ({len(covered)} glyphs, {len(font.keys())} tables)")
            font.close()
            continue

        subset.save_font(font, str(out_path), options)
        font.close()
        print(f"{family}: {src_path.name} → {out_path.relative_to(REPO_ROOT)} ({out_path.stat().st_size:,} bytes)")

    return 1 if problems else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="verify glyph coverage; write nothing")
    args = ap.parse_args()
    return build(args.check)


if __name__ == "__main__":
    sys.exit(main())
