#!/usr/bin/env python3
"""Stamp each person's name from a TSV onto a certificate PNG template.

Only third-party dependency:  pip install pillow

Usage:
    python3 make_certificates.py synthetic_data.tsv certificate_template.png
    python3 make_certificates.py data.tsv template.png --font /path/to/Font.ttf --outdir out
"""
import argparse
import csv
import os
import re
import urllib.request

from PIL import Image, ImageDraw, ImageFont

# Great Vibes: an elegant, very legible script font (SIL Open Font License).
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/greatvibes/GreatVibes-Regular.ttf"
DEFAULT_FONT = os.path.join("fonts", "GreatVibes-Regular.ttf")


def get_font_path(user_path):
    """Use the supplied font, else download Great Vibes once and cache it."""
    if user_path:
        return user_path
    if not os.path.exists(DEFAULT_FONT):
        os.makedirs(os.path.dirname(DEFAULT_FONT), exist_ok=True)
        print(f"Downloading font to {DEFAULT_FONT} ...")
        urllib.request.urlretrieve(FONT_URL, DEFAULT_FONT)
    return DEFAULT_FONT


def clean_name(*parts):
    """Join the columns and collapse any runs of whitespace into one space."""
    return " ".join(" ".join(parts).split())


def read_names(tsv_path):
    with open(tsv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader, None)  # skip header row
        for row in reader:
            if any(cell.strip() for cell in row):
                yield clean_name(*row)


def fit_font(draw, text, font_path, start_size, max_width):
    """Largest font size (<= start_size) whose rendered text fits max_width."""
    size = start_size
    while size > 10:
        font = ImageFont.truetype(font_path, size)
        left, _, right, _ = draw.textbbox((0, 0), text, font=font)
        if right - left <= max_width:
            return font
        size -= 2
    return ImageFont.truetype(font_path, 10)


def draw_centered(img, text, font_path, size, max_width, color, dx, dy):
    draw = ImageDraw.Draw(img)
    font = fit_font(draw, text, font_path, size, max_width)
    # Centre on the actual ink bounding box, so script fonts with long
    # swashes/descenders are centred visually rather than by font metrics.
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    w, h = right - left, bottom - top
    x = (img.width - w) / 2 - left + dx
    y = (img.height - h) / 2 - top + dy
    draw.text((x, y), text, font=font, fill=color)


def safe_filename(name):
    return re.sub(r"[^\w\-]+", "_", name).strip("_") or "certificate"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("tsv", help="TSV file: first name, middle initial, last name")
    p.add_argument("template", help="certificate template PNG")
    p.add_argument("--font", help="path to a .ttf/.otf font (default: auto-download Great Vibes)")
    p.add_argument("--outdir", default="certificates")
    p.add_argument("--size", type=int, default=110, help="starting font size in px (shrinks to fit)")
    p.add_argument("--max-width", type=int, default=1000, help="max text width in px")
    p.add_argument("--color", default="#8B1A6B", help="text colour, e.g. '#8B1A6B'")
    p.add_argument("--dx", type=int, default=0, help="nudge horizontally from centre (px)")
    p.add_argument("--dy", type=int, default=0, help="nudge vertically from centre (px)")
    args = p.parse_args()

    font_path = get_font_path(args.font)
    os.makedirs(args.outdir, exist_ok=True)

    for name in read_names(args.tsv):
        img = Image.open(args.template).convert("RGBA")
        draw_centered(img, name, font_path, args.size, args.max_width, args.color, args.dx, args.dy)
        out = os.path.join(args.outdir, safe_filename(name) + ".png")
        img.convert("RGB").save(out)
        print(f"{name!r} -> {out}")


if __name__ == "__main__":
    main()