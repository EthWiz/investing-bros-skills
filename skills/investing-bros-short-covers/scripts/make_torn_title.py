"""Reusable 'cut newspaper' torn-paper title generator (Amitai reference style).
Usage as module:  from make_torn_title import torn_strip, torn_pill, title_block
CLI (ep3 short):  python3 make_torn_title.py ART.jpg OUT.jpg
"""
import sys, random, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import numpy as np
RAQM = ImageFont.Layout.RAQM
RUBIK = "/usr/share/fonts/truetype/sand-box/google/Rubik/Rubik-VariableFont_wght.ttf"
CREAM, MUST, NAVY, WHITE = (246, 238, 222), (245, 183, 31), (17, 27, 48), (252, 250, 245)

def font(size, wght=900):
    f = ImageFont.truetype(RUBIK, size, layout_engine=RAQM)
    try: f.set_variation_by_axes([wght])
    except Exception: pass
    return f

def _torn_mask(w, h, amp, seed):
    rnd = random.Random(seed); pts = []
    def edge(n, f):
        v = 0; out = []
        for i in range(n + 1):
            v = max(-amp, min(amp, v * 0.5 + rnd.uniform(-amp, amp))); out.append(f(i / n, v))
        return out
    m = max(amp * 2, 6)
    pts += edge(int(w / 7), lambda t, v: (m + t * (w - 2 * m), m + v))
    pts += edge(int(h / 7), lambda t, v: (w - m + v, m + t * (h - 2 * m)))
    pts += edge(int(w / 7), lambda t, v: (w - m - t * (w - 2 * m), h - m + v))
    pts += edge(int(h / 7), lambda t, v: (m + v, h - m - t * (h - 2 * m)))
    mk = Image.new("L", (w, h), 0); ImageDraw.Draw(mk).polygon(pts, fill=255); return mk

def _paper(w, h, color, seed, amp=7, fringe=5):
    outer = _torn_mask(w, h, amp, seed)
    inner = outer.filter(ImageFilter.MinFilter(2 * fringe + 1))
    inner = ImageChops.multiply(inner, _torn_mask(w, h, amp * 0.5, seed + 7).filter(ImageFilter.MinFilter(3)))
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 7, (h, w))
    noise = np.array(Image.fromarray(((noise + 128).clip(0, 255)).astype("uint8")).filter(ImageFilter.GaussianBlur(1.2))).astype(float) - 128
    base = np.zeros((h, w, 3)); base[:] = WHITE
    col = np.array(color, float) + noise[..., None]
    a = np.array(inner, float)[..., None] / 255
    rgb = (base + noise[..., None] * 0.5) * (1 - a) + col * a
    img = Image.fromarray(rgb.clip(0, 255).astype("uint8")).convert("RGBA"); img.putalpha(outer); return img

def torn_strip(text, color, size, angle=0, pad=(40, 30), seed=1, wght=900, fg=NAVY, fringe=5):
    f = font(size, wght); d = ImageDraw.Draw(Image.new("L", (1, 1)))
    l, t, r, b = d.textbbox((0, 0), text, font=f, direction="rtl", language="he", anchor="la")
    w, h = int(r - l + 2 * pad[0]), int(b - t + 2 * pad[1])
    p = _paper(w, h, color, seed, fringe=fringe); dd = ImageDraw.Draw(p)
    dd.text((pad[0] - l, pad[1] - t), text, font=f, fill=fg, direction="rtl", language="he", anchor="la")
    return p.rotate(angle, resample=Image.BICUBIC, expand=True)

def shadow(img, off=(6, 8), blur=8, alpha=120):
    s = Image.new("RGBA", (img.width + 40, img.height + 40), (0, 0, 0, 0))
    a = img.getchannel("A").point(lambda v: v * alpha // 255)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); sh.putalpha(a)
    s.alpha_composite(sh, (20 + off[0], 20 + off[1])); s = s.filter(ImageFilter.GaussianBlur(blur))
    s.alpha_composite(img, (20, 20)); return s

def title_block(line1, line2, pill=None, width=1000, seed=3):
    """Returns RGBA block: cream line1 over mustard line2, overlapping, opposite tilts, + white pill."""
    a = torn_strip(line1, CREAM, 200, 1.3, seed=seed)
    b = torn_strip(line2, MUST, 200, -1.2, seed=seed + 1)
    for s in ("a", "b"):
        im = locals()[s]
        if im.width > width: im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
        if s == "a": a = im
        else: b = im
    W = max(a.width, b.width) + 60; ov = int(min(a.height, b.height) * 0.12)
    H = a.height + b.height - ov + 90
    c = Image.new("RGBA", (W + 40, H + 40), (0, 0, 0, 0))
    c.alpha_composite(shadow(a), ((W - a.width) // 2, 0))
    yb = a.height - ov; c.alpha_composite(shadow(b), ((W - b.width) // 2 + 8, yb))
    if pill:
        pp = torn_strip(pill, WHITE, 62, 0, pad=(34, 26), seed=seed + 2, wght=900, fringe=3)
        c.alpha_composite(shadow(pp, (3, 4), 4), ((W - pp.width) // 2, yb + b.height - int(pp.height * 0.45)))
    return c

def ep3_short(art_path, out):
    W, H = 1080, 1920
    art = Image.open(art_path).convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")
    arr = np.array(art); navy = tuple(int(v) for v in np.median(arr[60:200, :, :3].reshape(-1, 3), axis=0))
    d = ImageDraw.Draw(art)
    # paint over old title/pill (y~440-850) with navy, feathered at bottom so sun rays remain
    mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).rectangle([0, 380, W, 860], fill=255); ImageDraw.Draw(mask).rectangle([360, 380, 720, 905], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(12)); art = Image.composite(Image.new("RGBA", (W, H), navy + (255,)), art, mask)
    # old name strip region
    m2 = Image.new("L", (W, H), 0); ImageDraw.Draw(m2).rectangle([255, 1630, 1060, 1760], fill=255)
    art = Image.composite(Image.new("RGBA", (W, H), navy + (255,)), art, m2.filter(ImageFilter.GaussianBlur(6)))
    tb = title_block("דאטה סנטרים", "בחלל?", "פרק 3", width=1010)
    art.alpha_composite(tb, ((W - tb.width) // 2 + 10, 330))
    ns = torn_strip("עם אמתי ונדב רסקין", CREAM, 64, -0.8, pad=(30, 24), seed=11)
    art.alpha_composite(shadow(ns, (4, 5), 5), (290, 1622))
    art.convert("RGB").save(out, quality=92); print(out)

if __name__ == "__main__":
    ep3_short(sys.argv[1], sys.argv[2])
