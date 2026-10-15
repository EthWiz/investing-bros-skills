"""Brand motion-graphic cards (programmatic, Pillow). Card drawn at 2x then downsampled."""
import math, os
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = os.environ.get("HEEBO_FONT", "fonts/Heebo-Variable.ttf")  # Heebo variable font (wght axis; 900 = Black). Not in the repo.
NAVY0 = (0, 4, 28); NAVY1 = (0, 30, 78); CYAN = (0, 163, 255); ORANGE = (255, 140, 0)
GOLD = (245, 183, 31); WHITE = (255, 255, 255); BLOOM = (255, 179, 71)  # GOLD is house accent #F5B71F
CX, CY, CW, CH = 60, 420, 960, 840        # card rect in frame
SS = 2

@lru_cache(None)
def font(size, weight=900):
    f = ImageFont.truetype(FONT, int(size * SS))
    try: f.set_variation_by_axes([weight])
    except Exception: pass
    return f

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def seg(t, a, b): return clamp((t - a) / max(1e-6, b - a))
def ease_out(x): return 1 - (1 - x) ** 3
def ease_inout(x): return 3 * x * x - 2 * x * x * x
def ease_back(x, s=1.7):
    x -= 1; return x * x * ((s + 1) * x + s) + 1

def P(*v): return tuple(int(round(a * SS)) for a in v)

def text_c(d, xy, txt, size, fill, weight=900, anchor="mm", stroke=0, sfill=(0, 0, 0)):
    d.text(P(*xy), txt, font=font(size, weight), fill=fill, anchor=anchor, language="he",
           stroke_width=int(stroke * SS), stroke_fill=sfill)

def glow_layer(img, radius, strength=1.0):
    g = img.filter(ImageFilter.GaussianBlur(radius * SS))
    if strength != 1.0:
        a = g.getchannel("A").point(lambda v: min(255, int(v * strength))); g.putalpha(a)
    return g

def card_base(alpha=1.0):
    W, H = CW * SS, CH * SS
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # vertical navy gradient panel
    grad = Image.new("RGBA", (1, H))
    for y in range(H):
        k = y / H
        c = tuple(int(NAVY1[i] * (1 - k) + NAVY0[i] * k) for i in range(3))
        grad.putpixel((0, y), c + (int(232 * alpha),))
    grad = grad.resize((W, H))
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, W - 1, H - 1], radius=56 * SS, fill=255)
    im.paste(grad, (0, 0), m)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([1, 1, W - 2, H - 2], radius=56 * SS, outline=CYAN + (int(150 * alpha),), width=3 * SS)
    # subtle top sheen
    d.rounded_rectangle([40 * SS, 14 * SS, W - 40 * SS, 18 * SS], radius=2 * SS, fill=(120, 200, 255, int(60 * alpha)))
    return im

# ---------- icons ----------
def car_side(d, cx, cy, s, col=WHITE, a=255, win=CYAN):
    """side-view car centred at cx,cy, width ~ 2.2*s"""
    w = 1.1 * s
    d.rounded_rectangle(P(cx - w, cy - .28 * s, cx + w, cy + .25 * s), radius=int(.22 * s * SS), fill=col + (a,))
    d.polygon([P(cx - .62 * s, cy - .26 * s), P(cx - .32 * s, cy - .62 * s), P(cx + .38 * s, cy - .62 * s), P(cx + .72 * s, cy - .26 * s)], fill=col + (a,))
    d.polygon([P(cx - .5 * s, cy - .3 * s), P(cx - .27 * s, cy - .54 * s), P(cx + .02 * s, cy - .54 * s), P(cx + .02 * s, cy - .3 * s)], fill=win + (a,))
    d.polygon([P(cx + .08 * s, cy - .3 * s), P(cx + .08 * s, cy - .54 * s), P(cx + .35 * s, cy - .54 * s), P(cx + .58 * s, cy - .3 * s)], fill=win + (a,))
    for wx in (-.62, .62):
        d.ellipse(P(cx + wx * s - .26 * s, cy + .02 * s, cx + wx * s + .26 * s, cy + .54 * s), fill=(10, 16, 40, a))
        d.ellipse(P(cx + wx * s - .12 * s, cy + .16 * s, cx + wx * s + .12 * s, cy + .4 * s), fill=(170, 180, 200, a))

def chip_icon(d, cx, cy, s, a=255):
    d.rounded_rectangle(P(cx - s, cy - s, cx + s, cy + s), radius=int(.25 * s * SS), outline=CYAN + (a,), width=int(5 * SS), fill=(0, 40, 90, a))
    for k in (-.5, 0, .5):
        for (x0, y0, x1, y1) in [(cx + k * s, cy - s, cx + k * s, cy - 1.35 * s), (cx + k * s, cy + s, cx + k * s, cy + 1.35 * s),
                                 (cx - s, cy + k * s, cx - 1.35 * s, cy + k * s), (cx + s, cy + k * s, cx + 1.35 * s, cy + k * s)]:
            d.line(P(x0, y0, x1, y1), fill=CYAN + (a,), width=int(5 * SS))
    d.text(P(cx, cy), "AI", font=font(s * .9), fill=WHITE + (a,), anchor="mm")

def robot_icon(d, cx, cy, s, a=255):
    """humanoid robot (Optimus-like), height ~3.2*s, cy = centre"""
    top = cy - 1.6 * s
    d.rounded_rectangle(P(cx - .42 * s, top, cx + .42 * s, top + .7 * s), radius=int(.25 * s * SS), fill=(230, 236, 245, a))
    d.rounded_rectangle(P(cx - .32 * s, top + .22 * s, cx + .32 * s, top + .42 * s), radius=int(.1 * s * SS), fill=(10, 20, 50, a))
    d.rounded_rectangle(P(cx - .25 * s, top + .27 * s, cx + .25 * s, top + .37 * s), radius=int(.05 * s * SS), fill=CYAN + (a,))
    d.rectangle(P(cx - .1 * s, top + .7 * s, cx + .1 * s, top + .82 * s), fill=(150, 160, 180, a))
    d.rounded_rectangle(P(cx - .6 * s, top + .82 * s, cx + .6 * s, top + 1.9 * s), radius=int(.22 * s * SS), fill=(230, 236, 245, a))
    d.rounded_rectangle(P(cx - .2 * s, top + 1.05 * s, cx + .2 * s, top + 1.3 * s), radius=int(.06 * s * SS), fill=CYAN + (a,))
    for sx in (-1, 1):
        d.rounded_rectangle(P(cx + sx * .66 * s - .14 * s, top + .88 * s, cx + sx * .66 * s + .14 * s, top + 1.85 * s), radius=int(.12 * s * SS), fill=(200, 208, 222, a))
        d.rounded_rectangle(P(cx + sx * .28 * s - .17 * s, top + 1.95 * s, cx + sx * .28 * s + .17 * s, top + 3.15 * s), radius=int(.12 * s * SS), fill=(200, 208, 222, a))

def pin(d, x, y, s, col, a=255):
    d.ellipse(P(x - s, y - 2.4 * s, x + s, y - .4 * s), fill=col + (a,))
    d.polygon([P(x - .8 * s, y - 1.1 * s), P(x + .8 * s, y - 1.1 * s), P(x, y)], fill=col + (a,))
    d.ellipse(P(x - .4 * s, y - 1.8 * s, x + .4 * s, y - 1.0 * s), fill=NAVY0 + (a,))

def coin(d, x, y, r, a=255):
    d.ellipse(P(x - r, y - r, x + r, y + r), fill=(200, 120, 0, a))
    d.ellipse(P(x - r * .86, y - r * .9, x + r * .86, y + r * .82), fill=GOLD + (a,))
    d.text(P(x, y), "₪", font=font(r * 1.1, 800), fill=(130, 70, 0, a), anchor="mm")

def bez(p0, p1, p2, p3, u):
    return tuple((1 - u) ** 3 * p0[i] + 3 * (1 - u) ** 2 * u * p1[i] + 3 * (1 - u) * u * u * p2[i] + u ** 3 * p3[i] for i in range(2))

# ---------- the three cards ----------
def mg_fsd(t, dur):
    im = card_base(); lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    h = ease_out(seg(t, 0.1, 0.45))
    text_c(d, (CW / 2, 105 - 30 * (1 - h)), "FSD", 128, CYAN + (int(255 * h),))
    text_c(d, (CW / 2, 220 - 30 * (1 - h)), "הרכב נוהג לבד", 72, WHITE + (int(255 * h),))
    A, B = (170, 720), (790, 420)
    c1, c2 = (560, 800), (380, 380)
    # faint dashed full route
    dr = ease_out(seg(t, 0.3, 0.7)); n = 60
    for i in range(n):
        if i % 2: continue
        u0, u1 = i / n, (i + 1) / n
        if u0 > dr: break
        d.line([P(*bez(A, c1, c2, B, u0)), P(*bez(A, c1, c2, B, min(u1, dr)))], fill=CYAN + (140,), width=6 * SS)
    # progress (orange) + car
    pr = 0.9 * ease_inout(seg(t, 0.55, dur - 0.55))
    pts = [P(*bez(A, c1, c2, B, k / 80 * pr)) for k in range(81)]
    tr = Image.new("RGBA", im.size, (0, 0, 0, 0)); td = ImageDraw.Draw(tr)
    if pr > 0.005:
        td.line(pts, fill=ORANGE + (255,), width=14 * SS, joint="curve")
    lay.alpha_composite(glow_layer(tr, 10, 1.6)); lay.alpha_composite(tr)
    d = ImageDraw.Draw(lay)
    pa = ease_back(seg(t, 0.25, 0.55)); pb = ease_back(seg(t, 0.45, 0.75))
    arrived = seg(t, dur - 0.6, dur - 0.4)
    if pa > 0: pin(d, A[0], A[1], 34 * pa, CYAN)
    if pb > 0: pin(d, B[0], B[1], 34 * pb, tuple(int(CYAN[i] * (1 - arrived) + GOLD[i] * arrived) for i in range(3)))
    if arrived > 0:
        rr = 30 + 60 * seg(t, dur - 0.6, dur - 0.1); ra = int(230 * (1 - seg(t, dur - 0.6, dur - 0.1)))
        d.ellipse(P(B[0] - rr, B[1] - 48 - rr, B[0] + rr, B[1] - 48 + rr), outline=GOLD + (ra,), width=5 * SS)
    la = int(255 * seg(t, 0.4, 0.7))
    text_c(d, (A[0], A[1] + 50), "מקצה", 52, WHITE + (la,), 800)
    text_c(d, (B[0], B[1] + 50), "לקצה", 52, tuple(int(WHITE[i] * (1 - arrived) + GOLD[i] * arrived) for i in range(3)) + (la,), 800)
    # car sprite (side view, rotated along path)
    if pr > 0.0:
        u = max(pr, 0.001); p = bez(A, c1, c2, B, u); q = bez(A, c1, c2, B, min(1, u + 0.01))
        ang = math.degrees(math.atan2(-(q[1] - p[1]), q[0] - p[0]))
        sp = Image.new("RGBA", P(200, 140), (0, 0, 0, 0)); car_side(ImageDraw.Draw(sp), 100, 80, 56)
        sp = sp.rotate(ang, resample=Image.Resampling.BICUBIC, expand=True)
        a = seg(t, 0.5, 0.7)
        if a < 1: sp.putalpha(sp.getchannel("A").point(lambda v: int(v * a)))
        lay.alpha_composite(sp, (int(p[0] * SS - sp.width / 2), int((p[1] - 20) * SS - sp.height / 2)))
    im.alpha_composite(lay); return im

def mg_robotaxi(t, dur):
    im = card_base(); lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    # chips: right = סייברקאב (enters ~0.85s, synced to the word), left = FSD (~1.45s)
    def chip_box(cx, label, k, icon):
        if k <= 0: return
        a = int(255 * clamp(k * 1.5)); off = (1 - k) * 160 * (1 if cx > CW / 2 else -1)
        x = cx + off
        d.rounded_rectangle(P(x - 200, 60, x + 200, 330), radius=34 * SS, fill=(0, 30, 70, int(a * .9)), outline=CYAN + (a,), width=3 * SS)
        icon(x, 160, a)
        text_c(d, (x, 278), label, 58, WHITE + (a,), 800)
    k1 = ease_back(seg(t, 0.35, 0.75)); k2 = ease_back(seg(t, 0.95, 1.35))
    chip_box(CW - 245, "סייברקאב", k1, lambda x, y, a: car_side(d, x, y + 14, 74, a=a))
    chip_box(245, "FSD", k2, lambda x, y, a: chip_icon(d, x, y, 50, a))
    pk = ease_back(seg(t, 1.2, 1.5))
    if pk > 0: text_c(d, (CW / 2, 195), "+", 120 * pk, GOLD + (255,))
    # arrow down
    ar = ease_out(seg(t, 1.45, 1.75))
    if ar > 0:
        y0, y1 = 352, 352 + 95 * ar
        d.line(P(CW / 2, y0, CW / 2, y1), fill=CYAN + (255,), width=10 * SS)
        if ar > .6: d.polygon([P(CW / 2 - 30, y1 - 10), P(CW / 2 + 30, y1 - 10), P(CW / 2, y1 + 26)], fill=CYAN + (255,))
    rk = ease_back(seg(t, 1.65, 2.05))
    if rk > 0:
        g = Image.new("RGBA", im.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        w2 = 400 * rk; h2 = 150 * rk; cy = 625
        gd.rounded_rectangle(P(CW / 2 - w2, cy - h2, CW / 2 + w2, cy + h2), radius=40 * SS, fill=(40, 26, 0, 235), outline=GOLD + (255,), width=4 * SS)
        lay.alpha_composite(glow_layer(g, 18, 0.9)); lay.alpha_composite(g); d = ImageDraw.Draw(lay)
        text_c(d, (CW / 2, cy - 40 * rk), "רובוטקסי", 124 * rk, GOLD + (255,))
        text_c(d, (CW / 2, cy + 82 * rk), "רכב שמרוויח בשבילך", 58 * rk, WHITE + (255,), 700)
        for i, (cx, ph) in enumerate([(CW - 110, 0.0), (110, 0.12), (CW - 170, 0.3), (170, 0.42)]):
            u = seg(t, 1.95 + ph, 2.65 + ph)
            if 0 < u < 1:
                y = 790 - 280 * ease_out(u); a = int(255 * (1 - u ** 3))
                coin(d, cx, y, 44, a)
    im.alpha_composite(lay); return im

def mg_optimus(t, dur):
    im = card_base(); lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    h = ease_out(seg(t, 0.05, 0.4))
    text_c(d, (CW / 2, 92 - 25 * (1 - h)), "מפה להצלחה", 76, CYAN + (int(255 * h),), 900)
    # grid
    gx0, gx1, gy0, gy1 = 80, CW - 80, 200, 760
    for k in range(5):
        y = gy0 + (gy1 - gy0) * k / 4
        d.line(P(gx0, y, gx1, y), fill=(0, 163, 255, int(40 * h)), width=2 * SS)
    nodes = [(130, 700, "FSD"), (330, 600, None), (420, 640, None), (560, 500, "סייברקאב"), (720, 300, "אופטימוס")]
    LAB = {0: (130, 765), 3: (680, 545), 4: (560, 250)}
    # zigzag line: up, small dip, up, up
    pr = ease_inout(seg(t, 0.3, dur - 0.85)) * (len(nodes) - 1)
    ln = Image.new("RGBA", im.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(ln)
    pts = [P(*nodes[0][:2])]
    for i in range(1, len(nodes)):
        u = clamp(pr - (i - 1))
        if u <= 0: break
        x = nodes[i - 1][0] + (nodes[i][0] - nodes[i - 1][0]) * u
        y = nodes[i - 1][1] + (nodes[i][1] - nodes[i - 1][1]) * u
        pts.append(P(x, y))
    if len(pts) > 1:
        ld.line(pts, fill=ORANGE + (255,), width=14 * SS, joint="curve")
        bl = glow_layer(ln, 16, 1.3)
        tint = Image.new("RGBA", im.size, BLOOM + (0,)); tint.putalpha(bl.getchannel("A")); lay.alpha_composite(tint)
        lay.alpha_composite(ln)
        # arrowhead at the head of the line
        hx, hy = pts[-1][0] / SS, pts[-1][1] / SS; px, py = pts[-2][0] / SS, pts[-2][1] / SS
        ang = math.atan2(hy - py, hx - px)
        if pr > 0.15:
            L = 40; Wd = 26
            tip = (hx + math.cos(ang) * 22, hy + math.sin(ang) * 22)
            b1 = (tip[0] - math.cos(ang) * L - math.sin(ang) * Wd, tip[1] - math.sin(ang) * L + math.cos(ang) * Wd)
            b2 = (tip[0] - math.cos(ang) * L + math.sin(ang) * Wd, tip[1] - math.sin(ang) * L - math.cos(ang) * Wd)
            d = ImageDraw.Draw(lay); d.polygon([P(*tip), P(*b1), P(*b2)], fill=(252, 228, 144, 255))
    d = ImageDraw.Draw(lay)
    for i, (x, y, lab) in enumerate(nodes):
        k = ease_back(seg(pr, i - 0.3, i)) if i else ease_back(seg(t, 0.25, 0.5))
        if k <= 0 or lab is None: continue
        r = 16 * k
        g = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse(P(x - r * 2.2, y - r * 2.2, x + r * 2.2, y + r * 2.2), fill=BLOOM + (200,))
        lay.alpha_composite(glow_layer(g, 10)); d = ImageDraw.Draw(lay)
        d.ellipse(P(x - r, y - r, x + r, y + r), fill=(255, 245, 210, 255))
        last = (i == len(nodes) - 1)
        text_c(d, LAB[i], lab, 54 if not last else 66, (GOLD if last else WHITE) + (int(255 * clamp(k)),), 800 if not last else 900, stroke=4, sfill=NAVY0)
    # robot rises in at the top node
    rk = ease_back(seg(t, dur - 0.95, dur - 0.55))
    if rk > 0:
        rl = Image.new("RGBA", im.size, (0, 0, 0, 0)); robot_icon(ImageDraw.Draw(rl), 840, 330 + 40 * (1 - rk), 66 * rk, int(255 * clamp(rk)))
        g = glow_layer(rl, 14, 0.8); tint = Image.new("RGBA", im.size, CYAN + (0,)); tint.putalpha(g.getchannel("A"))
        lay.alpha_composite(tint); lay.alpha_composite(rl)
    im.alpha_composite(lay); return im

KINDS = {"fsd": mg_fsd, "robotaxi": mg_robotaxi, "optimus": mg_optimus}

def render_card(kind, t, dur):
    """returns (card RGBA at 1x, position xy, overall alpha, bg_dim 0..1)"""
    card = KINDS[kind](t, dur).resize((CW, CH), Image.Resampling.LANCZOS)
    tin = ease_back(seg(t, 0.0, 0.32), 1.3); tout = ease_out(seg(t, dur - 0.25, dur))
    sc = (0.86 + 0.14 * tin) * (1 - 0.06 * tout)
    alpha = clamp(seg(t, 0, 0.18)) * (1 - tout)
    if abs(sc - 1) > 1e-3:
        card = card.resize((max(1, int(CW * sc)), max(1, int(CH * sc))), Image.Resampling.BILINEAR)
    x = int(CX + (CW - card.width) / 2); y = int(CY + (CH - card.height) / 2 + 40 * (1 - tin))
    bg = clamp(seg(t, 0, 0.22)) * (1 - clamp(seg(t, dur - 0.22, dur)))
    return card, (x, y), alpha, bg
