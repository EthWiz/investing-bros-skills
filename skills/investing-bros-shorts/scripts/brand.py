#!/usr/bin/env python3
"""Investing Bros brand assets for promo video: palette, logo, fonts, frames.

Shared by investing-bros-shorts and investing-bros-teaser (identical copies).

Usage:
    python3 brand.py logo  COVER.jpg OUT_logo.png      # cut the wordmark out of the dark cover
    python3 brand.py fonts HEEBO_VARIABLE.ttf OUT_DIR  # static Heebo SemiBold/ExtraBold/Black
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

# Palette (from the dark show cover: black, emerald, white).
BLACK = (7, 9, 8)
EMERALD = (31, 191, 122)          # #1FBF7A — bright enough for text on video
EMERALD_DEEP = (14, 92, 63)       # glows/bands
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


def extract_logo(cover_path: str, out_path: str, box=(160 / 900, 635 / 900, 750 / 900, 830 / 900)) -> None:
    """Cut the 'אחים להשקעות' wordmark out of the dark square cover with a soft alpha.

    box is (x0, y0, x1, y1) as fractions of the cover; the default fits the dark
    cover's wordmark. Check the result on black before using it.
    """
    import numpy as np
    from PIL import Image
    src = Image.open(cover_path).convert("RGB")
    w, h = src.size
    crop = src.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    a = np.asarray(crop).astype(np.float32)
    bg = np.median(a[:20, :20].reshape(-1, 3), axis=0)
    alpha = np.clip((np.sqrt(((a - bg) ** 2).sum(axis=2)) - 25) / 35, 0, 1)
    green = a[:, :, 1] > a[:, :, 0] + 15
    a[green] = np.clip(a[green] * 1.35, 0, 255)      # lift the emerald line for screens
    logo = Image.fromarray(np.dstack([a, alpha * 255]).astype(np.uint8), "RGBA")
    logo.crop(logo.getbbox()).save(out_path)


def make_fonts(variable_ttf: str, out_dir: str) -> list:
    """Write static Heebo SemiBold (600), ExtraBold (800) and Black (900)."""
    from pathlib import Path
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    out = []
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    for weight, label in ((600, "SemiBold"), (800, "ExtraBold"), (900, "Black")):
        font = instancer.instantiateVariableFont(TTFont(variable_ttf), {"wght": weight})
        family = f"Heebo {label}"
        for rec in font["name"].names:
            if rec.nameID in (1, 4, 16):
                rec.string = family
            elif rec.nameID in (2, 17):
                rec.string = "Regular"
            elif rec.nameID == 6:
                rec.string = family.replace(" ", "") + "-Regular"
        path = f"{out_dir}/Heebo-{label}.ttf"
        font.save(path)
        out.append(path)
    return out


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
        base += _glow((w, h), (540, 250), (620, 260), (8, 48, 30))
        base += _glow((w, h), (540, 1800), (700, 200), (4, 26, 16))
        img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
        logo = Image.open(logo_path)
        lw = L["logo_w"]
        logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
        img.paste(logo, ((w - lw) // 2, L["logo_y"]), logo)
        d = ImageDraw.Draw(img)
        vy, vh = L["video_y"], 1215
        d.rectangle([0, vy - 4, w, vy - 1], fill=EMERALD)
        d.rectangle([0, vy + vh, w, vy + vh + 3], fill=EMERALD)
    elif kind in ("panel-left", "panel-right"):
        L = PANEL
        w, h = L["size"]
        cx = 480 if kind == "panel-left" else 1440
        base = np.zeros((h, w, 3), np.float32) + np.array(BLACK, np.float32)
        base += _glow((w, h), (cx, 430), (520, 430), (8, 52, 32))
        img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
        logo = Image.open(logo_path)
        lw = L["logo_w"]
        logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
        img.paste(logo, (cx - lw // 2, L["logo_y"]), logo)
        d = ImageDraw.Draw(img)
        d.rectangle([958, 0, 961, h], fill=EMERALD)
        d.rectangle([cx - 60, 340, cx + 60, 343], fill=EMERALD)
    else:
        raise ValueError(f"unknown frame kind {kind}")
    img.save(out_path)


def main(argv) -> int:
    if len(argv) >= 3 and argv[0] == "logo":
        extract_logo(argv[1], argv[2])
    elif len(argv) >= 3 and argv[0] == "fonts":
        print("\n".join(make_fonts(argv[1], argv[2])))
    elif len(argv) >= 4 and argv[0] == "frame":
        make_frame(argv[1], argv[2], argv[3])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
