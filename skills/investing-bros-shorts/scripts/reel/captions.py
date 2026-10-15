import os
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FONT = os.environ.get("HEEBO_FONT", "fonts/Heebo-Variable.ttf")  # Heebo variable font (wght axis; 900 = Black). Not in the repo.
GOLD = (245, 183, 31, 255); WHITE = (255, 255, 255, 255)  # house accent #F5B71F
CAP_Y = 1490          # caption centre line (77.6% of 1920): below chin, above the yellow bar (1654)
MAXW = 980

@lru_cache(None)
def font(size):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_axes([900]); return f

def render_chunk(words, active, size=96):
    """words in reading order; laid out right-to-left. Returns RGBA image (tight + margin)."""
    while True:
        f = font(size); stroke = max(6, size // 9)
        d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
        ws = [d0.textlength(w, font=f, direction="rtl", language="he") for w in words]
        gap = size * 0.28
        total = sum(ws) + gap * (len(words) - 1)
        if total + 2 * stroke <= MAXW or size <= 60: break
        size -= 4
    pad = stroke + 24
    Wd, Ht = int(total + 2 * pad), int(size * 1.45 + 2 * pad)
    im = Image.new("RGBA", (Wd, Ht), (0, 0, 0, 0))
    base_y = pad + size * 0.72
    x = Wd - pad
    pos = []
    for w, wd in zip(words, ws):
        pos.append((x - wd, w)); x -= wd + gap
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    for (px, w) in pos:
        sd.text((px, base_y + 6), w, font=f, anchor="ls", fill=(0, 0, 0, 170), direction="rtl", language="he", stroke_width=stroke + 2, stroke_fill=(0, 0, 0, 170))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)))
    d = ImageDraw.Draw(im)
    for i, (px, w) in enumerate(pos):
        d.text((px, base_y), w, font=f, anchor="ls", fill=GOLD if i == active else WHITE, direction="rtl", language="he",
               stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    return im
