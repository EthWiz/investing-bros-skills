#!/usr/bin/env python3
"""Typeset the exact Hebrew title on a vertical Shorts cover (Financial Journal style).

Image models misspell Hebrew, so a Shorts cover is made in two steps: generate the
artwork text-free, then put the title on with this script. Torn-paper strips (line 1
cream, line 2 mustard, slight opposite tilts, white paper fringe), navy Heebo Black
type, an optional `פרק N` pill under the strips and the logo bottom-right.

    python3 make_cover_title.py ART.png "שורט-01-רובוטקסי-cover.jpg" \
        --line1 "מי ינצח" --line2 "במרוץ הרובוטקסי?" --pill "פרק 1" \
        --font fonts/Heebo-Black.ttf --logo logo-solid.png

ART is cropped (never stretched) to 1080x1920. The title block is centred inside the
centre 1080x1080 square (y 420-1500) so 1:1 and 4:5 grid crops keep it; the script
fails if it cannot fit there. --font: static Heebo Black (`brand.py fonts` in
investing-bros-shorts makes it from Google's variable Heebo). Needs Pillow with raqm.
"""
import argparse
import random
import sys

W, H = 1080, 1920
SQUARE = (420, 1500)               # centre 1:1 crop of a 9:16 frame
TITLE_TOP = 440                    # default top of the title block
MAX_TITLE_W = 1010
LOGO_MAX = (260, 170)              # logo box, bottom-right
LOGO_MARGIN = 48
NAVY, CREAM, MUSTARD, PAPER_WHITE = (9, 36, 59), (245, 235, 213), (216, 165, 46), (252, 250, 245)
LINE_PX, PILL_PX = 200, 62
MIN_SCALE = 0.5                    # 100 px type; below this the title is unreadable at thumbnail size


def cover_crop(size, target=(W, H)):
    """Centre crop box that gives the target aspect ratio without stretching."""
    w, h = size
    tw, th = target
    if w * th > h * tw:                        # too wide: trim the sides
        nw = round(h * tw / th)
        x = (w - nw) // 2
        return (x, 0, x + nw, h)
    nh = round(w * th / tw)                    # too tall: trim top and bottom
    y = (h - nh) // 2
    return (0, y, w, y + nh)


def type_scale(strip_widths, width=MAX_TITLE_W):
    """One scale for both strips so the lines keep the same type size. Raises if the
    longest line would shrink the type below MIN_SCALE (100 px)."""
    k = min(1.0, width / max(strip_widths))
    if k < MIN_SCALE:
        raise ValueError(f"title lines too long: type would shrink to {round(LINE_PX * k)} px; "
                         "shorten the hook (about 14 characters a line)")
    return k


def title_position(block_size, top=TITLE_TOP):
    """Top-left of the title block, centred horizontally. Raises if it leaves the square."""
    bw, bh = block_size
    if bw > W:
        raise ValueError(f"title block is {bw}px wide, wider than the {W}px cover")
    if top < SQUARE[0] or top + bh > SQUARE[1]:
        raise ValueError(f"title block y {top}-{top + bh} leaves the centre square {SQUARE[0]}-{SQUARE[1]}; "
                         "shorten the lines or lower --top")
    return ((W - bw) // 2, top)


def logo_position(logo_size):
    lw, lh = logo_size
    return (W - LOGO_MARGIN - lw, H - LOGO_MARGIN - lh)


def _font(path, size):
    from PIL import ImageFont
    f = ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
    family, _style = f.getname()
    if "Heebo" not in family:
        raise ValueError(f"Heebo is the only allowed typeface, got {family!r}")
    try:
        f.set_variation_by_axes([900])         # a variable Heebo: force Black
    except Exception:
        pass
    return f


def _torn_mask(w, h, amp, seed):
    from PIL import Image, ImageDraw
    rnd = random.Random(seed)
    m = max(amp * 2, 6)

    def edge(n, f):
        v, out = 0, []
        for i in range(n + 1):
            v = max(-amp, min(amp, v * 0.5 + rnd.uniform(-amp, amp)))
            out.append(f(i / n, v))
        return out
    pts = edge(int(w / 7), lambda t, v: (m + t * (w - 2 * m), m + v))
    pts += edge(int(h / 7), lambda t, v: (w - m + v, m + t * (h - 2 * m)))
    pts += edge(int(w / 7), lambda t, v: (w - m - t * (w - 2 * m), h - m + v))
    pts += edge(int(h / 7), lambda t, v: (m + v, h - m - t * (h - 2 * m)))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    return mask


def _paper(w, h, color, seed, amp=7, fringe=5):
    import numpy as np
    from PIL import Image, ImageChops, ImageFilter
    outer = _torn_mask(w, h, amp, seed)
    inner = outer.filter(ImageFilter.MinFilter(2 * fringe + 1))
    inner = ImageChops.multiply(inner, _torn_mask(w, h, amp * 0.5, seed + 7).filter(ImageFilter.MinFilter(3)))
    noise = np.random.default_rng(seed).normal(0, 7, (h, w))
    noise = np.array(Image.fromarray((noise + 128).clip(0, 255).astype("uint8"))
                     .filter(ImageFilter.GaussianBlur(1.2))).astype(float) - 128
    a = np.array(inner, float)[..., None] / 255
    rgb = (np.array(PAPER_WHITE, float) + noise[..., None] * 0.5) * (1 - a) + (np.array(color, float) + noise[..., None]) * a
    img = Image.fromarray(rgb.clip(0, 255).astype("uint8")).convert("RGBA")
    img.putalpha(outer)
    return img


def torn_strip(text, color, font_path, size, angle=0.0, pad=(40, 30), seed=1, fringe=5):
    from PIL import Image, ImageDraw
    f = _font(font_path, size)
    l, t, r, b = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox(
        (0, 0), text, font=f, direction="rtl", language="he", anchor="la")
    w, h = int(r - l + 2 * pad[0]), int(b - t + 2 * pad[1])
    p = _paper(w, h, color, seed, fringe=fringe)
    ImageDraw.Draw(p).text((pad[0] - l, pad[1] - t), text, font=f, fill=NAVY,
                           direction="rtl", language="he", anchor="la")
    return p.rotate(angle, resample=Image.BICUBIC, expand=True)


def shadow(img, off=(6, 8), blur=8, alpha=120):
    from PIL import Image, ImageFilter
    s = Image.new("RGBA", (img.width + 40, img.height + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh.putalpha(img.getchannel("A").point(lambda v: v * alpha // 255))
    s.alpha_composite(sh, (20 + off[0], 20 + off[1]))
    s = s.filter(ImageFilter.GaussianBlur(blur))
    s.alpha_composite(img, (20, 20))
    return s


def title_block(line1, line2, font_path, pill=None, width=MAX_TITLE_W, seed=3):
    """Cream line 1 over mustard line 2, overlapping with opposite tilts, plus a white pill."""
    from PIL import Image
    strips = [torn_strip(text, color, font_path, LINE_PX, angle, seed=s)
              for text, color, angle, s in ((line1, CREAM, 1.3, seed), (line2, MUSTARD, -1.2, seed + 1))]
    k = type_scale([im.width for im in strips], width)
    a, b = [im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS) if k < 1 else im
            for im in strips]
    bw = max(a.width, b.width) + 60
    overlap = int(min(a.height, b.height) * 0.12)
    bh = a.height + b.height - overlap + 90
    block = Image.new("RGBA", (bw + 40, bh + 40), (0, 0, 0, 0))
    block.alpha_composite(shadow(a), ((bw - a.width) // 2, 0))
    yb = a.height - overlap
    block.alpha_composite(shadow(b), ((bw - b.width) // 2 + 8, yb))
    if pill:
        pp = torn_strip(pill, PAPER_WHITE, font_path, PILL_PX, 0, pad=(34, 26), seed=seed + 2, fringe=3)
        block.alpha_composite(shadow(pp, (3, 4), 4), ((bw - pp.width) // 2, yb + b.height - int(pp.height * 0.45)))
    return block.crop(block.getbbox())


def make_cover(art_path, out_path, line1, line2, font_path, pill=None, logo_path=None, top=TITLE_TOP):
    from PIL import Image, features
    if not features.check("raqm"):
        raise RuntimeError("Pillow has no raqm: Hebrew would render left-to-right")
    art = Image.open(art_path).convert("RGB")
    art = art.crop(cover_crop(art.size)).resize((W, H), Image.LANCZOS).convert("RGBA")
    block = title_block(line1, line2, font_path, pill)
    art.alpha_composite(block, title_position(block.size, top))
    if logo_path:
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail(LOGO_MAX, Image.LANCZOS)
        art.alpha_composite(logo, logo_position(logo.size))
    art.convert("RGB").save(out_path, "JPEG", quality=92)
    return out_path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("art")
    ap.add_argument("out")
    ap.add_argument("--line1", required=True, help="cream strip (topic)")
    ap.add_argument("--line2", required=True, help="mustard strip (question)")
    ap.add_argument("--pill", help="e.g. 'פרק 3'; omit for no pill")
    ap.add_argument("--font", required=True, help="Heebo Black .ttf")
    ap.add_argument("--logo", help="logo PNG for the bottom-right (brand assets/logo-solid.png)")
    ap.add_argument("--top", type=int, default=TITLE_TOP, help="top of the title block in px")
    a = ap.parse_args(argv)
    try:
        print(make_cover(a.art, a.out, a.line1, a.line2, a.font, a.pill, a.logo, a.top))
    except (ValueError, RuntimeError) as e:
        print(f"FAIL {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
