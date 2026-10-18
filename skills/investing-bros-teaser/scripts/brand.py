#!/usr/bin/env python3
"""Investing Bros brand assets for promo video: palette, logo, fonts, frames.

Shared by investing-bros-shorts and investing-bros-teaser (identical copies).

Usage:
    python3 brand.py logo  COVER.jpg OUT_logo.png [--box navy|dark|x0,y0,x1,y1]
                                                       # cut the wordmark out of the show cover (default: navy cover)
    python3 brand.py fonts HEEBO_VARIABLE.ttf OUT_DIR  # static Heebo SemiBold/ExtraBold/Black
    python3 brand.py fonts heebo-hebrew-wght-normal.woff2 heebo-latin-wght-normal.woff2 OUT_DIR
                                                       # fallback: @fontsource-variable/heebo subsets, merged
    python3 brand.py frame vertical LOGO.png OUT.png   # 1080x1920 shorts frame
    python3 brand.py frame panel-left LOGO.png OUT.png # 1920x1080 teaser, panel left (host video right)
    python3 brand.py frame panel-right LOGO.png OUT.png

Needs Pillow + numpy (frames, logo) and fontTools (fonts).

Why fonts: Google ships Heebo only as a variable font. libass renders a variable
font at its default weight, so captions come out thin. Instancing static
weights with distinct family names ("Heebo ExtraBold") fixes that; pass the
folder to the ass filter with fontsdir=.
"""
import sys

# Palette (from the navy/gold show cover; investing-bros-show -> Brand).
BLACK = (7, 9, 8)
ACCENT = (245, 183, 31)           # house accent gold #F5B71F — key words, rules, pills
ACCENT_DEEP = (122, 90, 14)       # bands
NAVY_GLOW = (10, 22, 48)          # background glow behind the logo
WHITE = (255, 255, 255)


def ass_colour(rgb) -> str:
    """ASS colours are &HAABBGGRR."""
    r, g, b = rgb
    return f"&H00{b:02X}{g:02X}{r:02X}"


# Vertical (1080x1920) layout, safe for the Reels / Shorts / TikTok UI:
# top ~140 px and bottom ~400 px are covered by app chrome, right ~170 px by buttons.
VERTICAL = {
    "size": (1080, 1920),
    "logo_y": 140, "logo_w": 250,
    "headline_margin_v": 262,       # top-anchored headline under the logo
    "video_y": 470,                 # host video (1080 wide) starts here
    "caption_margin_v": 400,        # bottom-anchored captions sit above the UI zone
    "caption_margin_l": 110, "caption_margin_r": 170,
}

# Teaser (1920x1080): one host's half of the side-by-side recording at native
# size (960x1080) next to a branded panel with logo, label, captions and name.
PANEL = {
    "size": (1920, 1080),
    "logo_y": 95, "logo_w": 380,
    "label_y": 268, "caption_y": 610, "name_y": 985,
}


# Where the "אחים להשקעות" wordmark sits on each cover, as fractions (x0, y0, x1, y1).
LOGO_BOXES = {
    "navy": (0.215, 0.115, 0.785, 0.415),   # current cover: Media Resources/אחים-להשקעות-cover-1400.jpg
    "dark": (160 / 900, 635 / 900, 750 / 900, 830 / 900),   # retired dark cover
}
LOGO_MAX_H = {"vertical": 100, "panel": 160}  # the wordmark is two lines; cap its height, not just its width


def _drop_specks(mask, min_px: int):
    """Indices of mask pixels that belong to blobs smaller than min_px (stars behind the wordmark)."""
    import numpy as np
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    small = []
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        stack, blob = [(y0, x0)], []
        seen[y0, x0] = True
        while stack:
            y, x = stack.pop()
            blob.append((y, x))
            for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True
                    stack.append((yy, xx))
        if len(blob) < min_px:
            small.extend(blob)
    return small


def extract_logo(cover_path: str, out_path: str, box=LOGO_BOXES["navy"], min_speck: int = 400) -> None:
    """Cut the 'אחים להשקעות' wordmark out of a square show cover with a soft alpha.

    box is (x0, y0, x1, y1) as fractions of the cover (LOGO_BOXES has the known covers).
    Opaque blobs smaller than min_speck pixels (stars, grain) are removed. Check the
    result on black before using it.
    """
    import numpy as np
    from PIL import Image
    src = Image.open(cover_path).convert("RGB")
    w, h = src.size
    crop = src.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    a = np.asarray(crop).astype(np.float32)
    bg = np.median(a[:20, :20].reshape(-1, 3), axis=0)
    alpha = np.clip((np.sqrt(((a - bg) ** 2).sum(axis=2)) - 25) / 35, 0, 1)
    for y, x in _drop_specks(alpha > 0.15, min_speck):
        alpha[y, x] = 0
    green = a[:, :, 1] > a[:, :, 0] + 15
    a[green] = np.clip(a[green] * 1.35, 0, 255)      # lift an emerald wordmark (old dark cover) for screens
    logo = Image.fromarray(np.dstack([a, alpha * 255]).astype(np.uint8), "RGBA")
    logo.crop(logo.getbbox()).save(out_path)


def fit_logo(logo, max_w: int, max_h: int):
    """Scale the wordmark to fit max_w x max_h, keeping its aspect ratio."""
    from PIL import Image
    k = min(max_w / logo.width, max_h / logo.height)
    return logo.resize((max(1, round(logo.width * k)), max(1, round(logo.height * k))), Image.LANCZOS)


def _glow(size, centre, radius, colour):
    import numpy as np
    w, h = size
    y, x = np.mgrid[0:h, 0:w]
    g = np.exp(-(((x - centre[0]) / radius[0]) ** 2 + ((y - centre[1]) / radius[1]) ** 2))
    return g[..., None] * np.array(colour, np.float32)


def make_frame(kind: str, logo_path: str, out_path: str) -> None:
    """Background frame the host video and captions are composited onto."""
    import numpy as np
    from PIL import Image, ImageDraw
    if kind == "vertical":
        L = VERTICAL
        w, h = L["size"]
        base = np.zeros((h, w, 3), np.float32) + np.array(BLACK, np.float32)
        base += _glow((w, h), (540, 250), (620, 260), NAVY_GLOW)
        base += _glow((w, h), (540, 1800), (700, 200), (5, 11, 24))
        img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
        logo = fit_logo(Image.open(logo_path), L["logo_w"], LOGO_MAX_H["vertical"])
        img.paste(logo, ((w - logo.width) // 2, L["logo_y"]), logo)
        d = ImageDraw.Draw(img)
        vy, vh = L["video_y"], 1215
        d.rectangle([0, vy - 4, w, vy - 1], fill=ACCENT)
        d.rectangle([0, vy + vh, w, vy + vh + 3], fill=ACCENT)
    elif kind in ("panel-left", "panel-right"):
        L = PANEL
        w, h = L["size"]
        cx = 480 if kind == "panel-left" else 1440
        base = np.zeros((h, w, 3), np.float32) + np.array(BLACK, np.float32)
        base += _glow((w, h), (cx, 430), (520, 430), NAVY_GLOW)
        img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
        logo = fit_logo(Image.open(logo_path), L["logo_w"], LOGO_MAX_H["panel"])
        img.paste(logo, (cx - logo.width // 2, L["logo_y"]), logo)
        d = ImageDraw.Draw(img)
        d.rectangle([958, 0, 961, h], fill=ACCENT)
        d.rectangle([cx - 60, 340, cx + 60, 343], fill=ACCENT)
    else:
        raise ValueError(f"unknown frame kind {kind}")
    img.save(out_path)


FONT_WEIGHTS = {"SemiBold": 600, "ExtraBold": 800, "Black": 900}


def _static(src: str, weight: int, family: str):
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    font = TTFont(src)
    font.flavor = None
    if "fvar" in font:
        font = instantiateVariableFont(font, {"wght": weight}, updateFontNames=False)
    names = font["name"]
    for rec in list(names.names):
        if rec.nameID in (16, 17, 21, 22, 25):
            names.removeNames(nameID=rec.nameID)
    full = family.replace(" ", "")
    for nid, val in ((1, family), (2, "Regular"), (3, f"{full}-static"), (4, family), (6, full)):
        names.setName(val, nid, 3, 1, 0x409)
        names.setName(val, nid, 1, 0, 0)
    font["OS/2"].usWeightClass = 400                   # one face per family: libass must not synthesise bold
    font["OS/2"].fsSelection = (font["OS/2"].fsSelection & ~0b1100001) | 0b1000000   # REGULAR only
    font["head"].macStyle = 0
    return font


def make_fonts(*args):
    """make_fonts(src1[, src2...], out_dir) -> written paths. Each src is the variable Heebo (ttf or woff2);
    several srcs (Hebrew + Latin subsets) are instanced one by one and merged into one font per weight."""
    import os
    import tempfile
    *srcs, out_dir = args
    if not srcs:
        raise ValueError("fonts: give the variable Heebo font (or its subsets) and an output folder")
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for style, weight in FONT_WEIGHTS.items():
        family = f"Heebo {style}"
        out = os.path.join(out_dir, f"Heebo-{style}.ttf")
        if len(srcs) == 1:
            _static(srcs[0], weight, family).save(out)
        else:
            from fontTools.merge import Merger
            with tempfile.TemporaryDirectory() as tmp:
                parts = []
                for i, src in enumerate(srcs):
                    part = os.path.join(tmp, f"{i}.ttf")
                    _static(src, weight, family).save(part)
                    parts.append(part)
                merged = Merger().merge(parts)
                merged.save(out)
                _static(out, weight, family).save(out)     # merge keeps the first part's names; set them again
        written.append(out)
    return written


def main(argv) -> int:
    if len(argv) >= 3 and argv[0] == "logo":
        box = LOGO_BOXES["navy"]
        if len(argv) >= 5 and argv[3] == "--box":
            box = LOGO_BOXES[argv[4]] if argv[4] in LOGO_BOXES else tuple(float(v) for v in argv[4].split(","))
        extract_logo(argv[1], argv[2], box)
    elif len(argv) >= 3 and argv[0] == "fonts":
        print("\n".join(make_fonts(*argv[1:])))
    elif len(argv) >= 4 and argv[0] == "frame":
        make_frame(argv[1], argv[2], argv[3])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
