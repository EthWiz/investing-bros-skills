#!/usr/bin/env python3
"""Investing Bros brand assets for promo video: palette, logo, fonts, frames.

Shared by investing-bros-shorts and investing-bros-video (identical copies).

Usage:
    python3 brand.py logo  CURRENT_LOGO.png OUT_logo.png
                                                       # solid newspaper logo (default)
    python3 brand.py logo  COVER.jpg OUT_logo.png --transparent [--box navy|dark|x0,y0,x1,y1]
                                                       # legacy keyed wordmark
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
from pathlib import Path

# Shared deterministic motion palette and font names. Artwork palettes live in
# investing-bros-brand; scripts import these values instead of redefining them.
BLACK = (7, 9, 8)
ACCENT = (245, 183, 31)           # house accent gold #F5B71F — key words, rules, pills
ACCENT_DEEP = (122, 90, 14)       # bands
NAVY_GLOW = (10, 22, 48)          # background glow behind the logo
TITLE_NAVY = (19, 32, 62)          # teaser title outline #13203E
WHITE = (255, 255, 255)
# Financial Journal print palette (investing-bros-brand -> brand-rules.md). Used for the
# Shorts hook strips, which must look different from the white/gold captions.
JOURNAL_NAVY = (9, 36, 59)        # #09243B headline ink, paper shadow
JOURNAL_CREAM = (245, 235, 213)   # #F5EBD5 first strip
JOURNAL_MUSTARD = (216, 165, 46)  # #D8A52E second strip
FONT_SEMIBOLD = "Heebo SemiBold"
FONT_EXTRABOLD = "Heebo ExtraBold"
FONT_BLACK = "Heebo Black"

# Approved 1920x1080 full-frame teaser (v5). Coordinates are top-left canvas
# pixels unless an ASS anchor is noted.
TEASER = {
    "size": (1920, 1080),
    "caption": {"font": FONT_EXTRABOLD, "size": 84, "x": 960, "y": 1000},
    "kicker": {"font": FONT_BLACK, "size": 112, "x": 1862, "y": 22, "outline": 3, "shadow": 5},
    "title": {"font": FONT_BLACK, "size": 72, "x": 1862, "y": 148, "outline": 2.5, "shadow": 4},
    "logo": {"x": 60, "y": 48, "width": 300},
    "caption_plate": (330, 880, 1590, 1060, 150),
    "blur_plate": (380, 890, 1540, 1050, 255),
    "title_plate": (1120, 20, 1910, 250, 120),
    "bottom_plate": (0, 960, 1920, 1080, 60),
}


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

# Full-bleed short (1080x1920): where captions and the hook may sit (centre y, canvas px).
# Captions stay above the bottom ~400 px of app UI (a 100 px line with outline needs
# its centre <= 1470). The paper-strip hook is on screen only ~2.7 s, so by default it
# sits in the centre of the frame (it may cover the face briefly), padded HOOK_GAP below
# the logo's bottom edge and HOOK_GAP above the caption line. Captions go just under
# the chin (face_crop.py suggests caption_y). check_short.py fails a render outside these.
CAPTION_Y_BOUNDS = (1100, 1470)
HOOK_Y_BOUNDS = (300, 1000)
CAPTION_Y_DEFAULT, HOOK_Y_DEFAULT = 1290, 960
LOGO_BOX = (56, 150, 266, 277)    # the full-bleed logo: 210 px wide at (56, 150), logo-solid.png aspect
CAPTION_HALF = 58                 # half the height of a 100-px caption line with its outline
HOOK_GAP = 40                     # minimum clear space between the hook block and logo / captions
HOOK_STRIPS = {"size": 108, "second_scale": 1.1, "pad_x": 34, "pad_y": 14, "overlap": 8,
               "tilt": (-1.2, 1.0), "shadow": (6, 9, 7, 110)}   # shadow dx, dy, blur, alpha


def hook_strips(lines, out_path, font_path, centre_y=HOOK_Y_DEFAULT, size=None):
    """Draw the Shorts hook as torn-paper strips (Financial Journal): line 1 on cream,
    line 2 on mustard (then alternating), navy Heebo Black type, a soft paper shadow.

    Writes a transparent 1080x1920 PNG and returns the block's (top, bottom) in px.
    "[...]" accent markup is ignored: the strip colour is the accent. Deterministic
    (edges are seeded from the text). Needs Pillow with raqm for Hebrew shaping.
    """
    import random
    import zlib
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, features
    if not features.check("raqm"):
        raise RuntimeError("Pillow has no raqm: Hebrew would render left-to-right")
    cfg = HOOK_STRIPS
    size = size or cfg["size"]
    strips = []
    for i, raw in enumerate(lines):
        text = raw.replace("[", "").replace("]", "").strip()
        rng = random.Random(zlib.crc32(f"{i}:{text}".encode()))
        font = ImageFont.truetype(font_path, round(size * (cfg["second_scale"] if i % 2 else 1)))
        probe = ImageDraw.Draw(Image.new("L", (10, 10)))
        x0, y0, x1, y1 = probe.textbbox((0, 0), text, font=font, direction="rtl", language="he")
        w, h = x1 - x0 + 2 * cfg["pad_x"], y1 - y0 + 2 * cfg["pad_y"]
        jag = max(4, size // 13)
        top = [(x, rng.uniform(0, jag)) for x in range(0, w + 1, 9)]
        right = [(w - rng.uniform(0, jag), y) for y in range(0, h + 1, 9)]
        bottom = [(x, h - rng.uniform(0, jag)) for x in range(w, -1, -9)]
        left = [(rng.uniform(0, jag), y) for y in range(h, -1, -9)]
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).polygon(top + right + bottom + left, fill=255)
        colour = JOURNAL_MUSTARD if i % 2 else JOURNAL_CREAM
        grain = np.random.default_rng(zlib.crc32(text.encode())).normal(0, 5, (h, w, 1))
        paper = np.clip(np.asarray(Image.new("RGB", (w, h), colour), np.float32) + grain, 0, 255).astype(np.uint8)
        strip = Image.fromarray(paper, "RGB").convert("RGBA")
        ImageDraw.Draw(strip).text((cfg["pad_x"] - x0, cfg["pad_y"] - y0), text, font=font,
                                   fill=JOURNAL_NAVY + (255,), direction="rtl", language="he")
        strip.putalpha(mask)
        strips.append(strip.rotate(cfg["tilt"][i % 2], resample=Image.BICUBIC, expand=True))
    total = sum(s.height for s in strips) - cfg["overlap"] * (len(strips) - 1)
    y = round(centre_y - total / 2)
    block = (y, y + total)
    canvas = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    dx, dy, blur, alpha = cfg["shadow"]
    for s in strips:
        x = round(540 - s.width / 2)
        shadow = Image.new("RGBA", s.size, JOURNAL_NAVY + (0,))
        shadow.putalpha(s.getchannel("A").point(lambda a: a * alpha // 255))
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        layer.paste(shadow, (x + dx, y + dy))
        canvas = Image.alpha_composite(canvas, layer.filter(ImageFilter.GaussianBlur(blur)))
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        layer.paste(s, (x, y))
        canvas = Image.alpha_composite(canvas, layer)
        y += s.height - cfg["overlap"]
    canvas.save(out_path)
    return block


# Down arrow (Heebo has no arrow glyphs): an ASS vector drawing, 60x70 px, for the end card.
ARROW_ASS = "m 20 0 l 40 0 l 40 36 l 60 36 l 30 70 l 0 36 l 20 36"
CALLOUT = {"size": 58, "pad_x": 30, "pad_y": 12, "arrow": (84, 72), "gap": 10,
           "fade_in": 0.25, "fade_out": 0.3, "bob_hz": 2.0}


def callout_strip(text, out_path, font_path, size=None):
    """A "look down" callout: one cream torn-paper strip with navy Heebo Black type and a
    mustard down arrow (navy edge) under it. Writes a tight transparent PNG, returns (w, h)."""
    import random
    import zlib
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, features
    if not features.check("raqm"):
        raise RuntimeError("Pillow has no raqm: Hebrew would render left-to-right")
    c = CALLOUT
    size = size or c["size"]
    rng = random.Random(zlib.crc32(text.encode()))
    font = ImageFont.truetype(font_path, size)
    x0, y0, x1, y1 = ImageDraw.Draw(Image.new("L", (8, 8))).textbbox((0, 0), text, font=font, direction="rtl", language="he")
    sw, sh = x1 - x0 + 2 * c["pad_x"], y1 - y0 + 2 * c["pad_y"]
    aw, ah = c["arrow"]
    W, H = sw + 24, sh + c["gap"] + ah + 24          # room for the shadow
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    jag = max(3, size // 13)
    edge = ([(x, rng.uniform(0, jag)) for x in range(0, sw + 1, 9)] + [(sw - rng.uniform(0, jag), y) for y in range(0, sh + 1, 9)]
            + [(x, sh - rng.uniform(0, jag)) for x in range(sw, -1, -9)] + [(rng.uniform(0, jag), y) for y in range(sh, -1, -9)])
    ax, ay = (sw - aw) / 2, sh + c["gap"]
    arrow = [(ax + aw * 0.33, ay), (ax + aw * 0.67, ay), (ax + aw * 0.67, ay + ah * 0.5), (ax + aw, ay + ah * 0.5),
             (ax + aw / 2, ay + ah), (ax, ay + ah * 0.5), (ax + aw * 0.33, ay + ah * 0.5)]
    shadow = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(shadow)
    d.polygon([(x + 5, y + 7) for x, y in edge], fill=110)
    d.polygon([(x + 5, y + 7) for x, y in arrow], fill=110)
    img.paste(Image.new("RGBA", (W, H), JOURNAL_NAVY + (255,)), (0, 0), shadow.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(img)
    d.polygon(edge, fill=JOURNAL_CREAM + (255,))
    d.text((c["pad_x"] - x0, c["pad_y"] - y0), text, font=font, fill=JOURNAL_NAVY + (255,), direction="rtl", language="he")
    d.polygon(arrow, fill=JOURNAL_MUSTARD + (255,), outline=JOURNAL_NAVY + (255,), width=3)
    img.save(out_path)
    return W, H


# Teaser (1920x1080): one host's half of the side-by-side recording at native
# size (960x1080) next to a branded panel with logo, label, captions and name.
PANEL = {
    "size": (1920, 1080),
    "logo_y": 95, "logo_w": 380,
    "label_y": 268, "caption_y": 610, "name_y": 985,
}


# Where the "אחים להשקעות" wordmark sits on each cover, as fractions (x0, y0, x1, y1).
LOGO_BOXES = {
    "navy": (0.215, 0.115, 0.785, 0.415),   # archived navy cover
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
    """Legacy colour-keyed wordmark extraction.

    box is (x0, y0, x1, y1) as fractions of the cover (LOGO_BOXES has the known covers).
    Opaque blobs smaller than min_speck pixels (stars, grain) are removed. Check the
    result on black before using it. Do not use this for the current newspaper logo:
    keying navy makes its navy letters transparent; use extract_solid_logo instead.
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


def _fill_holes(mask):
    """Return a boolean mask with enclosed transparent holes filled (Pillow only)."""
    import numpy as np
    from PIL import Image, ImageDraw
    h, w = mask.shape
    padded = Image.new("L", (w + 2, h + 2), 0)
    padded.paste(Image.fromarray((mask * 255).astype("uint8")), (1, 1))
    ImageDraw.floodfill(padded, (0, 0), 128, thresh=0)
    a = np.asarray(padded)[1:-1, 1:-1]
    return a != 128


def _largest_component(mask):
    """Keep the largest 4-connected foreground component."""
    import numpy as np
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    largest = []
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        seen[y0, x0] = True
        stack, blob = [(y0, x0)], []
        while stack:
            y, x = stack.pop()
            blob.append((y, x))
            for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True
                    stack.append((yy, xx))
        if len(blob) > len(largest):
            largest = blob
    out = np.zeros_like(mask, dtype=bool)
    if largest:
        yy, xx = zip(*largest)
        out[yy, xx] = True
    return out


def extract_solid_logo(source_path: str, out_path: str) -> None:
    """Extract the current torn-paper logo while keeping its navy letters opaque.

    Tuned for Media Resources/Investing-bros-logo.png. The source is the square
    newspaper cover: the logo occupies its upper 59%, with the yellow strip
    extending lower than the cream strip.
    """
    import numpy as np
    from PIL import Image, ImageFilter
    src = Image.open(source_path).convert("RGB")
    crop_h = round(src.height * 740 / 1254)
    yellow_from = round(src.height * 640 / 1254)
    rgb = np.asarray(src)[:crop_h].astype(np.float32)
    r, _, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    paper = rgb.mean(axis=2) > 120
    yellow = (r - b > 90) & (r > 170)
    paper[yellow_from:] = yellow[yellow_from:]
    # Opening drops isolated newspaper texture before filling letter counters.
    opened = Image.fromarray((paper * 255).astype("uint8")).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    keep = _largest_component(_fill_holes(np.asarray(opened) > 0))
    alpha = Image.fromarray((keep * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(0.7))
    logo = Image.fromarray(rgb.astype("uint8"), "RGB").convert("RGBA")
    logo.putalpha(alpha)
    bbox = logo.getbbox()
    if not bbox:
        raise ValueError("could not find the torn-paper logo in the supplied image")
    logo.crop(bbox).save(out_path)


def make_fonts(variable_path: str, out_dir: str) -> list:
    """Instance the variable Heebo font into libass-safe static weights."""
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    made = []
    for weight, label in ((600, "SemiBold"), (800, "ExtraBold"), (900, "Black")):
        font = instantiateVariableFont(TTFont(variable_path), {"wght": weight}, inplace=False)
        family = f"Heebo {label}"
        names = font["name"]
        for platform, encoding, language in ((3, 1, 0x409), (1, 0, 0)):
            names.setName(family, 1, platform, encoding, language)
            names.setName("Regular", 2, platform, encoding, language)
            names.setName(f"{family} Regular", 4, platform, encoding, language)
            names.setName(f"Heebo-{label}", 6, platform, encoding, language)
        path = out / f"Heebo-{label}.ttf"
        font.save(path)
        made.append(str(path))
    return made


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


def main(argv) -> int:
    if len(argv) >= 3 and argv[0] == "logo":
        if "--transparent" not in argv:
            extract_solid_logo(argv[1], argv[2])
        else:
            box = LOGO_BOXES["navy"]
            if "--box" in argv:
                value = argv[argv.index("--box") + 1]
                box = LOGO_BOXES[value] if value in LOGO_BOXES else tuple(float(v) for v in value.split(","))
            extract_logo(argv[1], argv[2], box)
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
