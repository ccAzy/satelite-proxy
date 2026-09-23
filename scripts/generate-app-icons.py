#!/usr/bin/env python3
"""Generate the Satelite app icon set (PNGs / .ico / .icns).

  pip install pillow
  python3 scripts/generate-app-icons.py

Everything (icon.png / .ico / Square*Logo) is resampled from
assets/icon/ic_launcher-web.png (1024px rounded tile; corners are baked
into the source alpha, content centered at ~86% of the canvas — when
swapping in a new source, trim alpha<4 glow noise, force-square the
content, then center it at that ratio). The .icns writer is pure Python
(PNG payloads), so no iconutil / macOS needed.

The .icns payloads use a FULL-BLEED variant (make_mac_icon): macOS 26
Tahoe masks every app icon with the system squircle and plates any
transparent margin with a light/white backdrop, so the source's 14%
transparent margin showed up as a white ring. The variant scales the
tile to ~96% of the canvas over an opaque dark base (color sampled from
the tile) and applies its own 15% corner rounding — tighter than the
system mask, so the mask always lands on opaque pixels (also fine on
older macOS, which shows the 15%-rounded dark tile as-is).

Windows / Linux outputs (ico, Square*, pngs) keep the source's rounded
transparent-margin design — those platforms render transparency natively.

Tray icons live in generate-tray-icons.py — this script never touches them.
"""
from __future__ import annotations

import struct
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src-tauri" / "icons"
APP_ICON_SOURCE = ROOT / "assets" / "icon" / "ic_launcher-web.png"

# macOS full-bleed variant: dark base sampled from the tile body, art
# footprint and own-corner radius (kept well under the ~22% system mask).
MAC_ICON_BG = (9, 10, 13, 255)
MAC_ART_SCALE = 0.96
MAC_CORNER_RATIO = 0.15

_APP_ICON_SRC: Image.Image | None = None
_MAC_ICON_1024: Image.Image | None = None


def app_icon_source() -> Image.Image:
    global _APP_ICON_SRC
    if _APP_ICON_SRC is None:
        _APP_ICON_SRC = Image.open(APP_ICON_SOURCE).convert("RGBA")
    return _APP_ICON_SRC


def make_app_icon(size: int) -> Image.Image:
    """Resample the source tile to `size`. Halving steps keep small sizes crisp."""
    im = app_icon_source()
    while im.size[0] // 2 >= size:
        im = im.resize((im.size[0] // 2,) * 2, Image.Resampling.LANCZOS)
    if im.size != (size, size):
        im = im.resize((size, size), Image.Resampling.LANCZOS)
    return im


def _rounded_mask(size: int, radius: float, ss: int = 4) -> Image.Image:
    big = size * ss
    m = Image.new("L", (big, big), 0)
    ImageDraw.Draw(m).rounded_rectangle(
        [0, 0, big - 1, big - 1], radius=radius * ss, fill=255
    )
    return m.resize((size, size), Image.Resampling.LANCZOS)


def mac_icon_1024() -> Image.Image:
    """Full-bleed macOS variant: opaque dark tile, own 15% corner rounding.

    The source tile keeps its designed proportions; the painted base only
    fills the outer margin + corners so the system squircle mask never
    reveals its backdrop plate (macOS 26 Tahoe behavior).
    """
    global _MAC_ICON_1024
    if _MAC_ICON_1024 is None:
        art = app_icon_source()
        bbox = art.split()[3].getbbox()
        if bbox:
            art = art.crop(bbox)
        hi = 1024
        target = int(round(hi * MAC_ART_SCALE))
        scaled = art.resize((target, target), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (hi, hi), MAC_ICON_BG)
        off = (hi - target) // 2
        canvas.alpha_composite(scaled, (off, off))
        canvas.putalpha(_rounded_mask(hi, hi * MAC_CORNER_RATIO))
        _MAC_ICON_1024 = canvas
    return _MAC_ICON_1024


def make_mac_icon(size: int) -> Image.Image:
    """Resample the full-bleed variant to `size` (halving keeps sizes crisp)."""
    im = mac_icon_1024()
    while im.size[0] // 2 >= size:
        im = im.resize((im.size[0] // 2,) * 2, Image.Resampling.LANCZOS)
    if im.size != (size, size):
        im = im.resize((size, size), Image.Resampling.LANCZOS)
    return im


def _ico_entry(size: int) -> Image.Image:
    """One .ico entry, tuned for Windows title-bar legibility (2026-09).

    Entries <=48px are single-step LANCZOS downscales from the 1024 source
    with a mild unsharp pass on RGB only (alpha keeps its clean AA) and,
    for <=32px, a slight midtone lift — the neon artwork is a dark planet
    on a dark tile with soft glow and reads as mush when merely resampled
    at 16-24px. Bigger entries keep the plain make_app_icon pipeline.
    """
    if size > 48:
        return make_app_icon(size)
    im = app_icon_source().resize((size, size), Image.Resampling.LANCZOS)
    r, g, b, a = im.split()
    rgb = Image.merge("RGB", (r, g, b))
    if size <= 32:
        rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.4, percent=100, threshold=2))
        rgb = rgb.point(lambda v: int(255 * (v / 255) ** 0.88))
    else:
        rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.2, percent=80, threshold=2))
    return Image.merge("RGBA", (*rgb.split(), a))


def write_ico(path: Path) -> None:
    # 20/28px exist because 125%/175% DPI title bars ask for exactly those
    # sizes — without them Windows rescales a neighboring entry and the
    # title-bar icon looks blurry.
    sizes = [16, 20, 24, 28, 32, 48, 64, 128, 256]
    entries, blobs = [], []
    for s in sizes:
        buf = BytesIO()
        _ico_entry(s).save(buf, format="PNG")
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


def write_icns() -> None:
    """Pure-Python .icns: PNG payloads for the modern retin@2x types."""
    types = [
        ("ic11", 32),   # 16x16@2x
        ("ic12", 64),   # 32x32@2x
        ("ic07", 128),  # 128x128
        ("ic13", 256),  # 128x128@2x
        ("ic08", 256),  # 256x256
        ("ic14", 512),  # 256x256@2x
        ("ic09", 512),  # 512x512
        ("ic10", 1024), # 512x512@2x
    ]
    body = b""
    for typ, s in types:
        buf = BytesIO()
        make_mac_icon(s).save(buf, format="PNG")
        blob = buf.getvalue()
        body += typ.encode("ascii") + struct.pack(">I", len(blob) + 8) + blob
    (OUT / "icon.icns").write_bytes(b"icns" + struct.pack(">I", len(body) + 8) + body)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    make_app_icon(1024).save(OUT / "icon.png", format="PNG")
    for name, sz in [
        ("32x32.png", 32),
        ("128x128.png", 128),
        ("128x128@2x.png", 256),
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
        make_app_icon(sz).save(OUT / name, format="PNG")

    write_ico(OUT / "icon.ico")
    write_icns()
    print(f"App icons written → {OUT}")


if __name__ == "__main__":
    main()
