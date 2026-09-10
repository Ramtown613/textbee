#!/usr/bin/env python3
"""
Generate the Android launcher icons in branding/assets/android from
branding/assets/logo.png: the ram with the word SMS under it, so the icon
reads as the SMS app at a glance and not just as the shul's logo.

Run from the repo root whenever the logo or the wording changes:

    python3 branding/make_icons.py

Needs Pillow and a bold TrueType font (Arial Bold on Windows, DejaVu Sans
Bold on Linux; pass another with --font). apply.py copies the result into
the Android source tree at build time.
"""
import argparse
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUT = ASSETS / "android"

NAVY = (0x2F, 0x43, 0x5B, 255)
PARCH = (0xFA, 0xF7, 0xF2, 255)
WORD = "SMS"

# dp sizes per density bucket: legacy icon 48dp, adaptive foreground 108dp.
DENSITIES = {"mdpi": 1.0, "hdpi": 1.5, "xhdpi": 2.0, "xxhdpi": 3.0, "xxxhdpi": 4.0}

FONT_CANDIDATES = [
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]


def load_font(path: str | None, px: int) -> ImageFont.FreeTypeFont:
    for p in ([path] if path else []) + FONT_CANDIDATES:
        if p and pathlib.Path(p).is_file():
            return ImageFont.truetype(p, px)
    sys.exit("no bold TrueType font found; pass --font")


def fit_font(path: str | None, text: str, width: int, height: int) -> ImageFont.FreeTypeFont:
    """Largest size whose rendered text fits in width x height."""
    lo, hi = 4, height * 2
    best = load_font(path, lo)
    while lo <= hi:
        mid = (lo + hi) // 2
        f = load_font(path, mid)
        l, t, r, b = f.getbbox(text)
        if r - l <= width and b - t <= height:
            best, lo = f, mid + 1
        else:
            hi = mid - 1
    return best


def compose(size: int, content: float, ram: Image.Image, font_path: str | None) -> Image.Image:
    """
    Transparent square of `size` px. The ram and the word share a centred
    content box `content` * size wide; ram on top, word underneath.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    box = int(size * content)
    gap = max(1, round(size * 0.02))
    word_h = int(box * 0.30)
    ram_h = box - word_h - gap

    r = ram.copy()
    r.thumbnail((box, ram_h), Image.LANCZOS)
    top = (size - box) // 2
    img.alpha_composite(r, ((size - r.width) // 2, top + (ram_h - r.height) // 2))

    font = fit_font(font_path, WORD, box, word_h)
    l, t, rgt, b = font.getbbox(WORD)
    d = ImageDraw.Draw(img)
    x = (size - (rgt - l)) // 2 - l
    y = top + ram_h + gap + (word_h - (b - t)) // 2 - t
    d.text((x, y), WORD, font=font, fill=NAVY)
    return img


def rounded(img: Image.Image, radius_frac: float, circle: bool = False) -> Image.Image:
    """Parchment background under `img`, clipped to a rounded square or a circle."""
    size = img.width
    bg = Image.new("RGBA", (size, size), PARCH)
    bg.alpha_composite(img)
    mask = Image.new("L", (size * 4, size * 4), 0)
    d = ImageDraw.Draw(mask)
    if circle:
        d.ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    else:
        d.rounded_rectangle((0, 0, size * 4 - 1, size * 4 - 1), radius=int(size * 4 * radius_frac), fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    bg.putalpha(mask)
    return bg


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", help="path to a bold .ttf")
    args = ap.parse_args()

    logo = Image.open(ASSETS / "logo.png").convert("RGBA")
    logo = logo.crop(logo.getbbox())  # trim transparent margins

    for dens, scale in DENSITIES.items():
        d = OUT / f"mipmap-{dens}"
        d.mkdir(parents=True, exist_ok=True)
        legacy = int(48 * scale)
        fg = int(108 * scale)
        # Adaptive foreground: launchers mask the outer third, so the artwork
        # stays inside the middle ~60%.
        compose(fg, 0.60, logo, args.font).save(d / "ic_launcher_foreground.png")
        # Legacy icons for launchers without adaptive support.
        art = compose(legacy, 0.80, logo, args.font)
        rounded(art, 0.20).save(d / "ic_launcher.png")
        rounded(art, 0.5, circle=True).save(d / "ic_launcher_round.png")
        print(f"{dens}: legacy {legacy}px, foreground {fg}px")


if __name__ == "__main__":
    main()
