#!/usr/bin/env python3
"""Render an "upgraded" Short config (hook / captions / hyperframes / CTA) over the CLEAN v5 base.

Usage:
  python3 build_amitai_short.py --config CONFIG.json --output short.mp4 \
      [--work /workspace/podcast/ep1/shorts_skilltest/work] [--video IGNORED]

--video is accepted for compatibility but ignored: burned-in inputs (e.g. v7) must not be reused.
The config's base is a clean edit made by make_base.py (same pieces, crop, logo,
speed-adjusted -14 LUFS audio) with no captions/graphics. Reuses strips.py
(torn strips), v5_gfx.py assets (v5_cta.png, v5_end.png) and mg.py easing.
Icons are drawn vectors; emoji are stripped.
"""
import argparse, json, math, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ap = argparse.ArgumentParser(); ap.add_argument("--config", required=True); ap.add_argument("--output", required=True)
ap.add_argument("--video"); ap.add_argument("--work", required=True, help="dir with the clean base mp4, fonts/, logo.png, v5_cta.png, v5_end.png")
A = ap.parse_args(); CFG = json.load(open(A.config, encoding="utf-8")); OUT = os.path.abspath(A.output)
if A.video: print(f"note: ignoring --video {A.video}; building from the clean v5 base", file=sys.stderr)
os.chdir(A.work); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mg import seg, ease_out, ease_back, ease_inout, clamp
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "strips.py")).read().split("def title")[0])          # strip(), NAVY, CREAM, MUST, F
GOLD = (245, 183, 31); WHITE = (255, 255, 255); MUSTARD = (216, 165, 46); RED = (190, 58, 48); YEL = (250, 200, 40)
FPS, Wd, Ht = 24, 1080, 1920
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200d]")
clean = lambda s: re.sub(r"\s+", " ", EMOJI.sub("", s)).strip()
def font(s, w="Black"): return ImageFont.truetype(f"fonts/Heebo-{w}.ttf", s, layout_engine=ImageFont.Layout.RAQM)
def text(d, xy, s, f, fill, anchor="mm", **k): d.text(xy, s, font=f, fill=fill, anchor=anchor, direction="rtl", language="he", **k)

# ---------- static assets ----------
def hook_img():
    h = CFG["hook"]; c = Image.new("RGBA", (Wd, Ht), (0, 0, 0, 0))
    a = strip(h["top_line"], CREAM, 96, 0); b = strip(h["bottom_line"], YEL, 96, 0)
    c.alpha_composite(a, (540 - a.width // 2, 700)); c.alpha_composite(b, (540 - b.width // 2, 700 + a.height - 80)); return c
def tag_img():
    f = font(38, "ExtraBold"); name = CFG["meta"]["speaker"]
    w = int(ImageDraw.Draw(Image.new("L", (1, 1))).textlength(name, font=f, direction="rtl")) + 48
    im = Image.new("RGBA", (w, 64), GOLD + (255,)); text(ImageDraw.Draw(im), (w / 2, 32), name, f, (11, 16, 6)); return im
HOOK = hook_img()
def tag_for(name):
    CFG["meta"]["speaker"] = name; return tag_img()
TAGS = [(a, b, tag_for(n)) for a, b, n in CFG.get("tags", [])] or None
if TAGS is None: TAG = tag_img()
CTA = Image.open("v5_cta.png").convert("RGBA")

# ---------- captions: word-by-word RTL layout, highlight phrases yellow ----------
CF = font(84)
def cap_img(c):
    words = c["text"].split(); nrm = lambda w: w.strip(".,?!:;—\"'()")
    hl = set(nrm(w) for p in c.get("highlight", []) for w in p.split())
    d = ImageDraw.Draw(Image.new("L", (1, 1))); sp = d.textlength(" ", font=CF)
    lines, cur, cw = [], [], 0
    for w in words:
        ww = d.textlength(w, font=CF, direction="rtl")
        if cur and cw + sp + ww > 900: lines.append(cur); cur, cw = [], 0
        cur.append((w, ww)); cw += (sp if cw else 0) + ww
    lines.append(cur)
    im = Image.new("RGBA", (Wd, 130 * len(lines) + 40), (0, 0, 0, 0)); dd = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        tot = sum(w for _, w in ln) + sp * (len(ln) - 1); x = 540 + tot / 2; y = 20 + 130 * i + 65
        for w, ww in ln:                                   # right to left
            dd.text((x - ww / 2, y), w, font=CF, fill=GOLD if nrm(w) in hl else WHITE, anchor="mm", direction="rtl",
                    language="he", stroke_width=6, stroke_fill=(0, 0, 0)); x -= ww + sp
    sh = im.getchannel("A").filter(ImageFilter.GaussianBlur(5)).point(lambda v: v * 0.5)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0)); s2 = Image.new("RGBA", im.size, (0, 0, 0, 255)); s2.putalpha(sh)
    out.alpha_composite(s2, (0, 4)); out.alpha_composite(im); return out
CAPS = [(c["start"], c["end"], cap_img(c)) for c in CFG["captions"]]

# ---------- vector icons ----------
def ic_warning(d, cx, cy, s, a=255):
    d.polygon([(cx, cy - s), (cx + 1.12 * s, cy + .85 * s), (cx - 1.12 * s, cy + .85 * s)], fill=YEL + (a,))
    d.line([(cx, cy - s), (cx + 1.12 * s, cy + .85 * s), (cx - 1.12 * s, cy + .85 * s), (cx, cy - s)], fill=NAVY + (a,), width=max(2, int(s * .09)), joint="curve")
    d.rounded_rectangle([cx - s * .1, cy - s * .45, cx + s * .1, cy + s * .25], s * .1, fill=NAVY + (a,))
    d.ellipse([cx - s * .12, cy + s * .4, cx + s * .12, cy + s * .64], fill=NAVY + (a,))
def ic_lidar(d, cx, cy, s, t, a=255):
    for k in range(3):                                      # sweeping beams
        ang = t * 3.2 + k * 2.09; L = s * 1.6
        d.polygon([(cx, cy - s * .2), (cx + L * math.cos(ang - .12), cy - s * .2 + L * .45 * math.sin(ang - .12)),
                   (cx + L * math.cos(ang + .12), cy - s * .2 + L * .45 * math.sin(ang + .12))], fill=MUSTARD + (int(a * .35),))
    d.rounded_rectangle([cx - s * .9, cy + s * .25, cx + s * .9, cy + s * .55], s * .12, fill=CREAM + (a,), outline=NAVY + (a,), width=4)  # mount
    d.rounded_rectangle([cx - s * .5, cy - s * .55, cx + s * .5, cy + s * .25], s * .18, fill=CREAM + (a,), outline=NAVY + (a,), width=5)  # puck
    d.rectangle([cx - s * .5, cy - s * .22, cx + s * .5, cy - s * .05], fill=NAVY + (a,))
    ph = (t * 3.2) % (2 * math.pi); d.ellipse([cx + s * .4 * math.cos(ph) - 7, cy - s * .135 - 7, cx + s * .4 * math.cos(ph) + 7, cy - s * .135 + 7], fill=YEL + (a,))
def ic_x(d, cx, cy, s, u, a=255):
    w = int(s * .22)
    if u > 0: d.line([(cx - s, cy - s), (cx - s + 2 * s * min(1, u * 2), cy - s + 2 * s * min(1, u * 2))], fill=RED + (a,), width=w)
    if u > .5: v = (u - .5) * 2; d.line([(cx + s, cy - s), (cx + s - 2 * s * v, cy - s + 2 * s * v)], fill=RED + (a,), width=w)
def ic_camera(d, cx, cy, s, a=255):
    d.rounded_rectangle([cx - s, cy - s * .55, cx + s, cy + s * .7], s * .2, fill=CREAM + (a,), outline=NAVY + (a,), width=5)
    d.rounded_rectangle([cx - s * .45, cy - s * .8, cx + s * .1, cy - s * .5], s * .08, fill=NAVY + (a,))
    d.ellipse([cx - s * .45, cy - s * .38, cx + s * .45, cy + s * .52], fill=NAVY + (a,))
    d.ellipse([cx - s * .25, cy - s * .18, cx + s * .25, cy + s * .32], fill=MUSTARD + (a,))
    d.ellipse([cx - s * .1, cy - s * .08, cx + s * .02, cy + s * .04], fill=CREAM + (a,))
def ic_check(d, cx, cy, s, u, a=255):
    p = [(cx - s, cy), (cx - s * .3, cy + s * .7), (cx + s, cy - s * .7)]
    if u > 0: d.line([p[0], (p[0][0] + (p[1][0] - p[0][0]) * min(1, u * 2), p[0][1] + (p[1][1] - p[0][1]) * min(1, u * 2))], fill=MUSTARD + (a,), width=int(s * .3), joint="curve")
    if u > .5: v = (u - .5) * 2; d.line([p[1], (p[1][0] + (p[2][0] - p[1][0]) * v, p[1][1] + (p[2][1] - p[1][1]) * v)], fill=MUSTARD + (a,), width=int(s * .3), joint="curve")
def ic_bars(d, cx, cy, s, t, a=255):
    hs = [1.0, .72, .48, .28]
    for i, h in enumerate(hs):
        u = ease_back(seg(t, .15 + .12 * i, .45 + .12 * i)); hh = s * 1.6 * h * u
        x = cx - s * .95 + i * s * .62
        if hh > 2: d.rectangle([x - s * .24, cy + s * .8 - hh, x + s * .24, cy + s * .8], fill=CREAM + (a,), outline=NAVY + (a,), width=4)
    u = ease_out(seg(t, .7, 1.2))
    if u > 0:
        x0, y0 = cx - s * .95, cy - s * 1.0; x1, y1 = x0 + (cx + s * 1.0 - x0) * u, y0 + (cy + s * .1 - y0) * u
        d.line([(x0, y0), (x1, y1)], fill=MUSTARD + (a,), width=int(s * .14))
        ang = math.atan2(y1 - y0, x1 - x0); L = s * .32
        d.polygon([(x1 + L * math.cos(ang), y1 + L * math.sin(ang)), (x1 + L * .7 * math.cos(ang + 2.2), y1 + L * .7 * math.sin(ang + 2.2)),
                   (x1 + L * .7 * math.cos(ang - 2.2), y1 + L * .7 * math.sin(ang - 2.2))], fill=MUSTARD + (a,))
def car(d, cx, cy, s, a=255):
    d.rounded_rectangle([cx - s, cy - s * .2, cx + s, cy + s * .3], s * .18, fill=CREAM + (a,), outline=NAVY + (a,), width=3)
    d.polygon([(cx - s * .55, cy - s * .2), (cx - s * .3, cy - s * .55), (cx + s * .35, cy - s * .55), (cx + s * .65, cy - s * .2)], fill=CREAM + (a,), outline=NAVY + (a,))
    for wx in (-.55, .55): d.ellipse([cx + wx * s - s * .2, cy + s * .12, cx + wx * s + s * .2, cy + s * .52], fill=NAVY + (a,))
LABEL = {}
def ic_car_front(d, cx, cy, s, t, a=255):          # robotaxi, front view, camera "eyes"
    d.rounded_rectangle([cx - s * 1.2, cy - s * .1, cx + s * 1.2, cy + s * .6], s * .25, fill=CREAM + (a,), outline=NAVY + (a,), width=5)
    d.polygon([(cx - s * .85, cy - s * .1), (cx - s * .55, cy - s * .65), (cx + s * .55, cy - s * .65), (cx + s * .85, cy - s * .1)], fill=CREAM + (a,), outline=NAVY + (a,))
    d.polygon([(cx - s * .62, cy - s * .15), (cx - s * .45, cy - s * .55), (cx + s * .45, cy - s * .55), (cx + s * .62, cy - s * .15)], fill=NAVY + (a,))
    g = .6 + .4 * math.sin(t * 4)
    for ex in (-.75, .75): d.ellipse([cx + ex * s - s * .17, cy + s * .1, cx + ex * s + s * .17, cy + s * .44], fill=NAVY + (a,)); d.ellipse([cx + ex * s - s * .09, cy + s * .18, cx + ex * s + s * .09, cy + s * .36], fill=YEL + (int(a * g),))
    for wx in (-.9, .9): d.rounded_rectangle([cx + wx * s - s * .18, cy + s * .55, cx + wx * s + s * .18, cy + s * .85], s * .06, fill=NAVY + (a,))
def ic_route(d, cx, cy, s, t, a=255):                # A -> B, car travels the dashed path (right to left, RTL)
    A, B = (cx + s * 1.4, cy + s * .35), (cx - s * 1.4, cy - s * .35); u = ease_inout(seg(t, .3, 2.0))
    for k in range(14):
        if k % 2: continue
        p0 = k / 14; p1 = (k + 1) / 14
        if p0 > ease_out(seg(t, 0, .5)): break
        d.line([(A[0] + (B[0] - A[0]) * p0, A[1] + (B[1] - A[1]) * p0), (A[0] + (B[0] - A[0]) * p1, A[1] + (B[1] - A[1]) * p1)], fill=CREAM + (a,), width=8)
    for P_, col in ((A, CREAM), (B, YEL)):
        d.ellipse([P_[0] - s * .16, P_[1] - s * .16, P_[0] + s * .16, P_[1] + s * .16], fill=col + (a,), outline=NAVY + (a,), width=4)
    car(d, A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u - s * .3, s * .42, a)
def ic_brain(d, cx, cy, s, t, a=255):                 # machine thinking: chip with pulsing traces
    d.rounded_rectangle([cx - s * .7, cy - s * .7, cx + s * .7, cy + s * .7], s * .15, fill=CREAM + (a,), outline=NAVY + (a,), width=6)
    d.rounded_rectangle([cx - s * .38, cy - s * .38, cx + s * .38, cy + s * .38], s * .08, fill=NAVY + (a,))
    for k in (-.4, 0, .4):
        for (x0, y0, x1, y1) in ((cx + k * s, cy - s * .7, cx + k * s, cy - s * 1.05), (cx + k * s, cy + s * .7, cx + k * s, cy + s * 1.05),
                                 (cx - s * .7, cy + k * s, cx - s * 1.05, cy + k * s), (cx + s * .7, cy + k * s, cx + s * 1.05, cy + k * s)):
            d.line([(x0, y0), (x1, y1)], fill=CREAM + (a,), width=8)
    pu = (t * 1.5) % 1; d.ellipse([cx - s * .2 * (1 + pu), cy - s * .2 * (1 + pu), cx + s * .2 * (1 + pu), cy + s * .2 * (1 + pu)], outline=YEL + (int(a * (1 - pu)),), width=6)
    d.ellipse([cx - s * .12, cy - s * .12, cx + s * .12, cy + s * .12], fill=YEL + (a,))
def ic_robot(d, cx, cy, s, t, a=255):                 # humanoid robot rising in
    k = ease_back(seg(t, 0, .5)); cy = cy + s * .4 * (1 - k); top = cy - s * 1.2
    d.rounded_rectangle([cx - s * .38, top, cx + s * .38, top + s * .6], s * .2, fill=CREAM + (a,), outline=NAVY + (a,), width=5)
    d.rounded_rectangle([cx - s * .28, top + s * .2, cx + s * .28, top + s * .36], s * .08, fill=NAVY + (a,))
    d.rounded_rectangle([cx - s * .2, top + s * .24, cx + s * .2, top + s * .32], s * .04, fill=YEL + (a,))
    d.rounded_rectangle([cx - s * .55, top + s * .7, cx + s * .55, top + s * 1.65], s * .2, fill=CREAM + (a,), outline=NAVY + (a,), width=5)
    for sx in (-1, 1):
        d.rounded_rectangle([cx + sx * s * .68 - s * .12, top + s * .75, cx + sx * s * .68 + s * .12, top + s * 1.55], s * .1, fill=CREAM + (a,), outline=NAVY + (a,), width=4)
        d.rounded_rectangle([cx + sx * s * .25 - s * .14, top + s * 1.7, cx + sx * s * .25 + s * .14, top + s * 2.4], s * .1, fill=CREAM + (a,), outline=NAVY + (a,), width=4)
def ic_house(d, cx, cy, s, t, a=255):
    k = ease_back(seg(t, 0, .5)); s = s * (.6 + .4 * k)
    d.polygon([(cx - s * 1.1, cy - s * .1), (cx, cy - s * 1.0), (cx + s * 1.1, cy - s * .1)], fill=YEL + (a,), outline=NAVY + (a,))
    d.rectangle([cx - s * .85, cy - s * .1, cx + s * .85, cy + s * .9], fill=CREAM + (a,), outline=NAVY + (a,), width=5)
    d.rectangle([cx - s * .2, cy + s * .35, cx + s * .2, cy + s * .9], fill=NAVY + (a,))
    for wx in (-.55, .55): d.rectangle([cx + wx * s - s * .15, cy + s * .1, cx + wx * s + s * .15, cy + s * .4], fill=NAVY + (a,))
def ic_bars_up(d, cx, cy, s, t, a=255):
    hs = [.28, .48, .72, 1.0]
    for i, h in enumerate(hs):
        u = ease_back(seg(t, .15 + .12 * i, .45 + .12 * i)); hh = s * 1.6 * h * u; x = cx - s * .95 + i * s * .62
        if hh > 2: d.rectangle([x - s * .24, cy + s * .8 - hh, x + s * .24, cy + s * .8], fill=CREAM + (a,), outline=NAVY + (a,), width=4)
    u = ease_out(seg(t, .7, 1.2))
    if u > 0:
        x0, y0 = cx - s * 1.0, cy + s * .1; x1, y1 = x0 + (cx + s * .95 - x0) * u, y0 + (cy - s * 1.0 - y0) * u
        d.line([(x0, y0), (x1, y1)], fill=YEL + (a,), width=int(s * .14)); ang = math.atan2(y1 - y0, x1 - x0); L = s * .32
        d.polygon([(x1 + L * math.cos(ang), y1 + L * math.sin(ang)), (x1 + L * .7 * math.cos(ang + 2.2), y1 + L * .7 * math.sin(ang + 2.2)),
                   (x1 + L * .7 * math.cos(ang - 2.2), y1 + L * .7 * math.sin(ang - 2.2))], fill=YEL + (a,))
def ic_clock(d, cx, cy, s, t, a=255):                  # parked-car share of the day: a pie that fills to the stated pct
    pct = LABEL.get("pct", 95) / 100; u = ease_inout(seg(t, .2, 1.4))
    d.ellipse([cx - s, cy - s, cx + s, cy + s], fill=CREAM + (a,), outline=NAVY + (a,), width=6)
    if u > 0: d.pieslice([cx - s * .88, cy - s * .88, cx + s * .88, cy + s * .88], -90, -90 + 360 * pct * u, fill=YEL + (a,))
    d.ellipse([cx - s * .1, cy - s * .1, cx + s * .1, cy + s * .1], fill=NAVY + (a,))
def ic_two_cars(d, cx, cy, s, t, a=255):
    k1 = ease_back(seg(t, 0, .4)); k2 = ease_back(seg(t, .3, .7))
    if k1 > 0: car(d, cx + s * .65, cy, s * .55 * k1 + 1, a)
    if k2 > 0: car(d, cx - s * .65, cy, s * .55 * k2 + 1, a)
VIS = {"car_front": ic_car_front, "route": ic_route, "brain": ic_brain, "robot": ic_robot, "house": ic_house,
       "bars_up": ic_bars_up, "bars_down": ic_bars, "clock": ic_clock, "two_cars": ic_two_cars}

# ---- ep3 icons (data centers in space) ----
def sun(d, cx, cy, r, t, a=255):
    for k in range(10):
        ang = k * math.pi / 5 + t * .6; r0, r1 = r * 1.25, r * (1.6 + .12 * math.sin(t * 5 + k))
        d.line([(cx + r0 * math.cos(ang), cy + r0 * math.sin(ang)), (cx + r1 * math.cos(ang), cy + r1 * math.sin(ang))], fill=YEL + (a,), width=max(3, int(r * .16)))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=YEL + (a,), outline=NAVY + (a,), width=4)
def ic_sun_ozone(d, cx, cy, s, t, a=255):            # sun -> beams; earth's atmosphere layer filters them, space side gets full
    sun(d, cx, cy - s * .75, s * .32, t, a)
    u = ease_out(seg(t, .2, .9))
    for bx in (-.8, 0, .8):
        y1 = cy - s * .3 + s * 1.1 * u
        d.line([(cx + bx * s, cy - s * .3), (cx + bx * s, y1)], fill=YEL + (a,), width=10)
    k = ease_back(seg(t, .5, 1.0))
    if k > 0:
        d.chord([cx - s * 1.9, cy + s * .55, cx + s * 1.9, cy + s * 2.6], 180, 360, fill=(70, 120, 160, int(a * .55)))   # atmosphere
        d.chord([cx - s * 1.7, cy + s * .8, cx + s * 1.7, cy + s * 2.8], 180, 360, fill=CREAM + (a,), outline=NAVY + (a,))  # earth
def ic_sun_half(d, cx, cy, s, t, a=255):              # 12 of 24 hours of sun: half-filled day dial with a sun
    u = ease_inout(seg(t, .2, 1.2))
    d.ellipse([cx - s, cy - s, cx + s, cy + s], fill=CREAM + (a,), outline=NAVY + (a,), width=6)
    if u > 0: d.pieslice([cx - s * .88, cy - s * .88, cx + s * .88, cy + s * .88], -90, -90 + 180 * u, fill=YEL + (a,))
    for k in range(12):
        ang = k * math.pi / 6; d.line([(cx + s * .9 * math.cos(ang), cy + s * .9 * math.sin(ang)), (cx + s * .98 * math.cos(ang), cy + s * .98 * math.sin(ang))], fill=NAVY + (a,), width=5)
    d.ellipse([cx - s * .1, cy - s * .1, cx + s * .1, cy + s * .1], fill=NAVY + (a,))
def solar(d, cx, cy, w, h, a=255):
    d.rectangle([cx - w, cy - h, cx + w, cy + h], fill=NAVY + (a,), outline=CREAM + (a,), width=4)
    for i in range(1, 4): d.line([(cx - w + 2 * w * i / 4, cy - h), (cx - w + 2 * w * i / 4, cy + h)], fill=CREAM + (a,), width=2)
    d.line([(cx - w, cy), (cx + w, cy)], fill=CREAM + (a,), width=2)
def ic_panel_sun(d, cx, cy, s, t, a=255):            # solar panel turns until it faces the sun head-on
    sx, sy = cx + s * 1.3, cy - s * .3; sun(d, sx, sy, s * .34, t, a)
    u = ease_inout(seg(t, .2, 1.2)); px, py = cx - s * .9, cy + s * .1
    w = s * (.25 + .55 * u)                          # panel opens toward the viewer as it turns to the sun
    solar(d, px, py, w, s * .75, a)
    if u > .95:
        for k in (-.5, 0, .5): d.line([(sx - s * .5, sy + k * s * .5), (px + w + 12, py + k * s * 1.2)], fill=YEL + (int(a * .85),), width=7)
def sat(d, cx, cy, s, a=255):
    solar(d, cx - s * 1.0, cy, s * .55, s * .28, a); solar(d, cx + s * 1.0, cy, s * .55, s * .28, a)
    d.rounded_rectangle([cx - s * .38, cy - s * .38, cx + s * .38, cy + s * .38], s * .1, fill=CREAM + (a,), outline=NAVY + (a,), width=4)
    d.ellipse([cx - s * .1, cy - s * .1, cx + s * .1, cy + s * .1], fill=YEL + (a,))
def ic_sats(d, cx, cy, s, t, a=255):                 # "lots and lots" of compute satellites filling space
    pos = [(0, 0), (-1.75, -.95), (1.75, -.95), (-1.75, .95), (1.75, .95)]
    for i, (x, y) in enumerate(pos):
        k = ease_back(seg(t, .12 * i, .12 * i + .35))
        if k > 0: sat(d, cx + x * s, cy + y * s * .85, s * (.5 if i else .62) * k + 1, a)
def ic_rack(d, cx, cy, s, t, a=255):                 # data center rack lifting off the ground
    k = ease_inout(seg(t, .2, 1.4)); y = cy - s * .6 * k
    d.line([(cx - s * 1.4, cy + s * .95), (cx + s * 1.4, cy + s * .95)], fill=CREAM + (a,), width=6)
    d.rounded_rectangle([cx - s * .6, y - s * .85, cx + s * .6, y + s * .85], s * .08, fill=CREAM + (a,), outline=NAVY + (a,), width=6)
    for i in range(5):
        yy = y - s * .7 + i * s * .3; d.rectangle([cx - s * .48, yy, cx + s * .48, yy + s * .2], fill=NAVY + (a,))
        d.ellipse([cx + s * .3, yy + s * .06, cx + s * .38, yy + s * .14], fill=YEL + (int(a * (.5 + .5 * math.sin(t * 6 + i))),))
VIS.update({"sun_ozone": ic_sun_ozone, "sun_half": ic_sun_half, "panel_sun": ic_panel_sun, "sats": ic_sats, "rack": ic_rack})
def ic_scale(d, cx, cy, s, t, a=255):
    n = 1 + int(ease_out(seg(t, .2, 1.4)) * 11)
    for i in range(n):
        r, c = divmod(i, 4); car(d, cx + s * 1.05 - c * s * .7, cy - s * .55 + r * s * .55, s * .28, a)
    k = ease_back(seg(t, .5, .9))
    if k > 0 and LABEL.get("multiplier"):
        f = font(int(64 * k)); d.text((cx, cy + s * 1.15), LABEL["multiplier"], font=f, fill=YEL + (a,), anchor="mm")

# ---------- hyperframe panel ----------
PX, PW, PH = 40, 1000, 700; PY = (1920 - PH) // 2 - 40   # large, centred (v9); captions stay below
def panel_base():
    im = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
    m = Image.new("L", (PW, PH), 0); dm = ImageDraw.Draw(m); import random; random.seed(3)
    pts = [(x, 6 + random.uniform(-4, 4)) for x in range(0, PW + 1, 40)] + [(PW - 6 + random.uniform(-3, 3), y) for y in range(0, PH, 60)] \
        + [(x, PH - 6 + random.uniform(-4, 4)) for x in range(PW, -1, -40)] + [(6 + random.uniform(-3, 3), y) for y in range(PH, 0, -60)]
    dm.polygon(pts, fill=235); paper = Image.new("RGBA", (PW, PH), NAVY + (255,))
    noise = Image.effect_noise((PW, PH), 14).convert("L").point(lambda v: v // 6)
    paper = Image.composite(Image.new("RGBA", (PW, PH), (40, 70, 95, 255)), paper, noise); paper.putalpha(m)
    sh = Image.new("RGBA", (PW, PH), (0, 0, 0, 255)); sh.putalpha(m.filter(ImageFilter.GaussianBlur(8)).point(lambda v: v // 2))
    im.alpha_composite(sh, (0, 0)); im.alpha_composite(paper); return im
PANEL = panel_base()
_strip_cache = {}
def tstrip(s, bg, size):
    k = (s, bg, size)
    if k not in _strip_cache: _strip_cache[k] = strip(s, bg, size, 0)
    return _strip_cache[k]
def draw_step(lay, hf, i, lt, a):
    st = hf["steps"][i]; d = ImageDraw.Draw(lay); title, sub = clean(st["title"]), clean(st["subtitle"])
    split = hf["layout"] == "split_comparison" and i == len(hf["steps"]) - 1
    ka = int(255 * a); k = ease_out(seg(lt, 0, .4))
    ts = tstrip(title, CREAM, 84 if len(title) < 18 else 72)
    sw = ts.copy(); sw.putalpha(sw.getchannel("A").point(lambda v: int(v * a * k)))
    subc = CREAM + (int(255 * a * clamp(seg(lt, .25, .6))),)
    if not split:
        icx, icy = PW / 2, 220
        if st.get("visual") in VIS: LABEL['pct'] = st.get('pct', 95); VIS[st["visual"]](d, icx, icy, 150, lt, ka)
        elif hf["layout"] == "split_comparison":
            if i == 0: q = ease_back(seg(lt, 0, .45), 2); ic_warning(d, icx, icy - 10, 150 * q + 1, ka)
            elif i == 1: ic_lidar(d, icx, icy, 170, lt, ka); ic_x(d, icx, icy, 115, ease_out(seg(lt, 1.2, 1.7)), ka)
        else:
            if st.get("visual") == "bars_down": ic_bars(d, icx, icy, 150, lt, ka)
            else: LABEL['multiplier'] = st.get('multiplier'); ic_scale(d, icx, icy - 20, 150, lt, ka)
        lay.alpha_composite(sw, (int(PW / 2 - sw.width / 2), int(440 + 25 * (1 - k))))
        text(d, (PW / 2, 620), sub, font(52, "SemiBold"), subc)
    else:
        lay.alpha_composite(sw, (int(PW / 2 - sw.width / 2), 40))
        d.line([(PW / 2, 200), (PW / 2, 540)], fill=CREAM + (ka // 2,), width=4)
        ic_lidar(d, PW * .75, 340, 120, lt, ka); ic_x(d, PW * .75, 340, 85, 1, ka)
        text(d, (PW * .75, 515), "LiDAR", font(64, "ExtraBold"), CREAM + (ka,))
        q = ease_back(seg(lt, .2, .6)); ic_camera(d, PW * .25, 340, 105 * q + 1, ka); ic_check(d, PW * .25 + 110, 255, 52, ease_out(seg(lt, .6, 1.0)), ka)
        text(d, (PW * .25, 515), "מצלמות", font(64, "ExtraBold"), CREAM + (ka,))
        text(d, (PW / 2, 625), sub, font(50, "SemiBold"), subc)
def hyper(fr, t):
    for hf in CFG["hyperframes"]:
        if not (hf["start"] <= t < hf["end"]): continue
        lt0 = t - hf["start"]; dur = hf["end"] - hf["start"]
        tin = ease_back(seg(lt0, 0, .35), 1.3); tout = ease_out(seg(lt0, dur - .3, dur))
        lay = PANEL.copy(); steps = hf["steps"]
        i = max(j for j, s in enumerate(steps) if s["at"] <= t + 1e-6)
        x = clamp(seg(t - steps[i]["at"], 0, .3)) if i else 1      # crossfade from previous step
        if i and x < 1: draw_step(lay, hf, i - 1, t - steps[i - 1]["at"], 1 - x)
        draw_step(lay, hf, i, t - steps[i]["at"], x)
        sc = (0.9 + .1 * tin) * (1 - .05 * tout); al = clamp(seg(lt0, 0, .2)) * (1 - tout)
        p = lay.resize((int(PW * sc), int(PH * sc)), Image.BICUBIC)
        if al < 1: p.putalpha(p.getchannel("A").point(lambda v: int(v * al)))
        fr.alpha_composite(p, (int(PX + (PW - p.width) / 2), int(PY + (PH - p.height) / 2 + 30 * (1 - tin))))
        return True
    return False

# ---------- compose ----------
base = CFG.get("base", "ep1_lidar_clean.mp4")
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", base]))
N = int(round(dur * FPS)); hk = CFG["hook"]; cta = CFG["cta_overlay"]
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", base, "-f", "rawvideo", "-pix_fmt", "rgba", "-"], stdout=subprocess.PIPE)
body = "v8_body.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{Wd}x{Ht}", "-r", str(FPS), "-i", "-",
                        "-i", base, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-g", str(FPS),
                        "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", body], stdin=subprocess.PIPE)
for n in range(N):
    raw = dec.stdout.read(Wd * Ht * 4)
    if len(raw) < Wd * Ht * 4: break
    t = n / FPS; fr = Image.frombytes("RGBA", (Wd, Ht), raw)
    if hk["start"] <= t < hk["end"]:
        a = 1 - clamp(seg(t, hk["end"] - .3, hk["end"]))
        h = HOOK if a >= 1 else HOOK.copy(); 
        if a < 1: h.putalpha(h.getchannel("A").point(lambda v: int(v * a)))
        fr.alpha_composite(h)
    if TAGS:
        for a_, b_, im_ in TAGS:
            if a_ <= t < b_: fr.alpha_composite(im_, (1024 - im_.width, 150))
    elif t < cta["start"] - 0.1: fr.alpha_composite(TAG, (1024 - TAG.width, 150))
    shown = hyper(fr, t)
    if True:                                   # v9: captions always on, below the panel
        for s, e, im in CAPS:
            if s <= t < e: fr.alpha_composite(im, (0, 1480 - im.height // 2)); break
    if cta["start"] <= t < cta["end"]: fr.alpha_composite(CTA)
    enc.stdin.write(fr.tobytes())
enc.stdin.close(); enc.wait(); dec.wait()
# end card: v5_end.png (title = meta.outro_question, already rendered in v5_gfx.py), 3 s silent, hard cut
if not os.path.exists("end3.mp4"):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", "24", "-i", "v5_end.png", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                    "-t", "3", "-vf", "format=yuv420p", "-c:v", "libx264", "-c:a", "aac", "-shortest", "end3.mp4"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", body, "-i", "end3.mp4", "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]",
                "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-g", "24", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", OUT], check=True)
layout_path = os.path.splitext(OUT)[0] + "_layout.json"
json.dump({"duration": dur + 3.0, "silent_endcard_seconds": 3.0, "hook_style": "approved-v5"},
          open(layout_path, "w"))
print(OUT)
