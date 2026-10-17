#!/usr/bin/env python3
"""Build the browser-tab icons from the brand mark.

Why this exists
---------------
The site shipped **no icon at all**. `public/favicon.svg` existed but nothing linked to it, so browsers
fell back to their default request for `/favicon.ico` — which 404s — and every tab showed a generic
globe. Measured on production before the fix:

    /favicon.svg  → 200   (the file was there, unreferenced)
    /favicon.ico  → 404   (what a browser actually asks for)
    <link rel="icon"> in the HTML → absent

The App Router fixes the *declaration* by convention: a file named `favicon.ico`, `icon.png` or
`apple-icon.png` under `src/app/` is served and linked automatically for every page. What it cannot do
is invent the raster files, which is what this script produces.

Notes
-----
* The letter is set in **Cormorant Garamond**, the brand's display face, rather than the SVG's
  `font-family="Georgia,serif"` — a favicon must not depend on which serif the viewer has installed.
  The TTF is the static instance `tools/build-og-fonts.py` already derives.
* Rendered at 4x and downsampled, because a 16x16 icon drawn directly is a smear.
* `apple-icon.png` is drawn **square**: iOS applies its own corner mask, and pre-rounded art gets
  double-rounded.

    python3 tools/build-icons.py            # write the icons
    python3 tools/build-icons.py --check     # verify they render something
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
APP = REPO_ROOT / "apps" / "web" / "src" / "app"
BRAND_FONT = REPO_ROOT / "apps" / "web" / "src" / "lib" / "og-fonts" / "CormorantGaramond-og.ttf"
FALLBACK_FONT = REPO_ROOT / "src" / "saju_html" / "fonts" / "DejaVuSans-Bold.ttf"

BACKGROUND = (8, 8, 15)          # #08080f, the tile behind the mark
GOLD_TOP = (224, 198, 122)       # #E0C67A
GOLD_BOTTOM = (160, 128, 48)     # #A08030
SUPERSAMPLE = 4
BASE = 256                       # master render size; everything else is derived from it


def _gradient(size: int) -> Image.Image:
    """A 45-degree gold gradient, built small (it is smooth) and scaled up."""
    small = 64
    img = Image.new("RGB", (small, small))
    pixels = []
    for y in range(small):
        for x in range(small):
            t = (x + y) / (2 * (small - 1))
            pixels.append(tuple(round(a + (b - a) * t) for a, b in zip(GOLD_TOP, GOLD_BOTTOM)))
    img.putdata(pixels)
    return img.resize((size, size), Image.BICUBIC)


def _font(size: int) -> ImageFont.FreeTypeFont:
    path = BRAND_FONT if BRAND_FONT.exists() else FALLBACK_FONT
    if not path.exists():
        raise SystemExit(
            f"no font: {path} — run tools/build-og-fonts.py (or tools/build-web-fonts.py)",
        )
    return ImageFont.truetype(str(path), size)


def render(size: int, *, rounded: bool) -> Image.Image:
    """One icon at `size` px, supersampled."""
    big = size * SUPERSAMPLE
    canvas = Image.new("RGBA", (big, big), (0, 0, 0, 0))

    # The tile. `apple-icon` is square because iOS masks it itself.
    tile = Image.new("RGBA", (big, big), BACKGROUND + (255,))
    if rounded:
        mask = Image.new("L", (big, big), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, big - 1, big - 1], radius=round(big * 0.22), fill=255)
        tile.putalpha(mask)
    canvas.alpha_composite(tile)

    # The letter, centred on its own bounding box rather than the em box — Cormorant sits high, and
    # baseline-centring leaves the mark visibly low in the tab.
    font = _font(round(big * 0.78))
    glyph_mask = Image.new("L", (big, big), 0)
    draw = ImageDraw.Draw(glyph_mask)
    box = draw.textbbox((0, 0), "S", font=font)
    draw.text(
        ((big - (box[2] - box[0])) / 2 - box[0], (big - (box[3] - box[1])) / 2 - box[1]),
        "S",
        font=font,
        fill=255,
    )
    canvas.paste(_gradient(big), (0, 0), glyph_mask)

    return canvas.resize((size, size), Image.LANCZOS)


def build(check_only: bool) -> int:
    APP.mkdir(parents=True, exist_ok=True)

    if check_only:
        icon = render(32, rounded=True)
        red, _green, _blue, alpha = icon.split()
        # `histogram()` rather than `getdata()`: the latter is deprecated in Pillow 12 and the
        # replacement API is newer than the floor we support.
        opaque = sum(alpha.histogram()[1:])
        # A missing glyph would still be a valid PNG — just a dark tile — so count the *gold* pixels
        # specifically. Not the mean colour over the opaque pixels: the tile covers ~15x the area the
        # letter does, so the average of a correct icon is nearly black (measured: rgb(18,17,19)).
        gold = red.point(lambda v: 255 if v > 120 else 0).histogram()[255]
        print(f"32px icon: {opaque} opaque px, {gold} gold px")
        if opaque < 400 or gold < 20:
            print("the mark is missing or blank — is the brand font present?", file=sys.stderr)
            return 1
        return 0

    master = render(BASE, rounded=True)
    master.save(APP / "icon.png")
    print(f"icon.png        {BASE}x{BASE}  ({ (APP / 'icon.png').stat().st_size:,} bytes)")

    # `favicon.ico` is what a browser requests with no other information, so it must exist.
    master.resize((256, 256), Image.LANCZOS).save(
        APP / "favicon.ico", format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64)]
    )
    print(f"favicon.ico     16/24/32/48/64  ({ (APP / 'favicon.ico').stat().st_size:,} bytes)")

    render(180, rounded=False).save(APP / "apple-icon.png")
    print(f"apple-icon.png  180x180  (square: iOS masks it)  ({ (APP / 'apple-icon.png').stat().st_size:,} bytes)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="verify the mark renders; write nothing")
    args = ap.parse_args()
    return build(args.check)


if __name__ == "__main__":
    sys.exit(main())
