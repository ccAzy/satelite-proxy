#!/usr/bin/env python3
"""Generate the WINDOWS-ONLY app icon set (.ico + Square*Logo) from win0.png.

  pip install pillow
  python3 scripts/generate-windows-app-icon.py [source.png]

Source: src-tauri/icons/win0.png by default (512px RGBA; neon face-saturn
tile with a soft BLACK drop shadow baked around it). The shadow is RGB(0,0,0)
with alpha <= ~66 offset toward bottom-right — it must be TRIMMED, not kept:
on light wallpapers / light taskbars it reads as a dark halo and at 16-24px
it mushes the edge. The tile's hard edge (alpha >= 200) is cropped with a
1px allowance for its baked AA, kept at native scale, and re-centered at
~86% of a transparent canvas — the same margin design the cross-platform
set uses (see generate-app-icons.py).

Outputs (Windows platform only — this script never writes icon.png/icns,
the shared 32x32/128x128 pngs, or anything under tray/):
  icons/icon.ico          exe/installer/taskbar icon (BIG; window_icon.rs
                          keeps the SMALL title-bar icons on tray/titlebar-*)
  icons/Square*Logo.png   msi/appx assets (local -Bundle msi builds)
  icons/StoreLogo.png

The .ico recipe is the 2026-09-23 tuning verbatim: 20/28px entries for
125%/175% DPI, entries <=48px are single-step LANCZOS downscales with an
RGB-only unsharp pass (<=32px additionally gamma 0.88 midtone lift — the
neon artwork is a dark planet on a dark tile and reads as mush when merely
resampled); alpha keeps its clean AA.
"""
from __future__ import annotations

import struct
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src-tauri" / "icons"
DEFAULT_SOURCE = OUT / "win0.png"

# Repo-wide margin design: content occupies ~86% of the canvas.
ART_SCALE = 0.86
HARD_ALPHA = 200  # tile edge; the drop shadow never exceeds ~66
AA_ALLOWANCE = 1  # keep the tile's own 1px antialiased edge

_normalized: Image.Image | None = None


def normalized_source() -> Image.Image:
    """win0 with the black drop shadow trimmed, tile centered at 86%."""
    global _normalized
    if _normalized is not None:
        return _normalized
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    im = Image.open(path).convert("RGBA")

    # Trim stray glow noise (alpha < 4), then locate the hard tile edge —
    # thresholding above the shadow's alpha keeps the crop on real artwork.
    a = im.split()[3].point(lambda v: 255 if v >= 4 else 0)
    box = a.getbbox()
    if box:
        im = im.crop(box)
    hard = im.split()[3].point(lambda v: 255 if v >= HARD_ALPHA else 0)
    l, t, r, b = hard.getbbox() or im.getbbox()
    l, t = max(0, l - AA_ALLOWANCE), max(0, t - AA_ALLOWANCE)
    r, b = min(im.size[0], r + AA_ALLOWANCE), min(im.size[1], b + AA_ALLOWANCE)
    # Force square (center-crop the longer axis), keep native resolution.
    side = max(r - l, b - t)
    cx, cy = (l + r) // 2, (t + b) // 2
    l, t = cx - side // 2, cy - side // 2
    tile = im.crop((l, t, l + side, t + side))

    canvas = Image.new("RGBA", (round(side / ART_SCALE),) * 2, (0, 0, 0, 0))
    off = (canvas.size[0] - side) // 2
    canvas.alpha_composite(tile, (off, off))
    _normalized = canvas
    return _normalized


def make(size: int) -> Image.Image:
    """Resample to `size`. Halving steps keep small sizes crisp."""
    im = normalized_source()
    while im.size[0] // 2 >= size:
        im = im.resize((im.size[0] // 2,) * 2, Image.Resampling.LANCZOS)
    if im.size != (size, size):
        im = im.resize((size, size), Image.Resampling.LANCZOS)
    return im


def ico_entry(size: int) -> Image.Image:
    """One .ico entry, tuned for Windows legibility (2026-09 recipe)."""
    if size > 48:
        return make(size)
    im = normalized_source().resize((size, size), Image.Resampling.LANCZOS)
    r, g, b, a = im.split()
    rgb = Image.merge("RGB", (r, g, b))
    if size <= 32:
        rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.4, percent=100, threshold=2))
        rgb = rgb.point(lambda v: int(255 * (v / 255) ** 0.88))
    else:
        rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.2, percent=80, threshold=2))
    return Image.merge("RGBA", (*rgb.split(), a))


def write_ico(path: Path) -> None:
    # 20/28px exist because 125%/175% DPI ask for exactly those sizes.
    sizes = [16, 20, 24, 28, 32, 48, 64, 128, 256]
    entries, blobs = [], []
    for s in sizes:
        buf = BytesIO()
        ico_entry(s).save(buf, format="PNG")
        data = buf.getvalue()
        entries.append((s, len(data)))
        blobs.append(data)
    offset = 6 + 16 * len(sizes)
    header = struct.pack("<HHH", 0, 1, len(sizes))
    dire = body = b""
    for (s, sz), data in zip(entries, blobs):
        w = h = 0 if s >= 256 else s
        dire += struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, sz, offset)
        body += data
        offset += sz
    path.write_bytes(header + dire + body)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, sz in [
        ("Square30x30Logo.png", 30),
        ("Square44x44Logo.png", 44),
        ("Square71x71Logo.png", 71),
        ("Square89x89Logo.png", 89),
        ("Square107x107Logo.png", 107),
        ("Square142x142Logo.png", 142),
        ("Square150x150Logo.png", 150),
        ("Square284x284Logo.png", 284),
        ("Square310x310Logo.png", 310),
        ("StoreLogo.png", 50),
    ]:
        make(sz).save(OUT / name, format="PNG")
    write_ico(OUT / "icon.ico")
    print(f"Windows app icons written -> {OUT}")


if __name__ == "__main__":
    main()
