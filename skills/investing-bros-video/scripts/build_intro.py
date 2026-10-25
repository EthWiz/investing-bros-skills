#!/usr/bin/env python3
"""Build the show intro (8 s, 1920x1080) as a HyperFrames composition, render it
and mux the intro music.

Usage:
    python3 build_intro.py intro.json --project DIR [--render OUT.mp4]

Timeline (seconds, matched to `compose_intro_music.py`):
  0.00  navy paper, two mustard hairlines draw out from the centre
  0.30  the experience line (e.g. `עשור של השקעות`) wipes in right-to-left, large, cream
  0.50  first host rises in on the right, name strip at 0.80
  1.00  second host rises in on the left, name strip at 1.30
  2.70  the line shrinks to its subtitle slot and turns mustard
  3.00  the wordmark (logo-solid.png) lands: upper strip first ...
  3.50  ... then the full wordmark
  3.00-8.00  slow push-in; hold to the end (hard cut into the episode)

intro.json (paths relative to the JSON file):
{
  "fps": 24, "duration": 8.0,
  "line": "עשור של השקעות",
  "logo": "logo-solid.png",                  # investing-bros-brand/assets
  "music": "intro-music.wav",                # compose_intro_music.py output or a supplied track
  "fonts": "fonts/",                         # Heebo-{SemiBold,ExtraBold,Black}.ttf (brand.py fonts)
  "gsap": "gsap.min.js",                     # npm gsap@3 dist/gsap.min.js
  "hosts": [                                  # optional; first entry goes on the right
    {"name": "אמיתי רסקין", "image": "host-amitai-ep08.png"},
    {"name": "נדב רסקין", "image": "host-nadav-ep08.png"}
  ]
}
Host images are transparent cut-outs from one episode's own recording
(investing-bros-brand -> covers). On-screen copy is only the line, the
names and the wordmark: no invented claims.

Render needs Node 18+, `npx hyperframes` and a headless Chrome
(PRODUCER_HEADLESS_SHELL_PATH; see investing-bros-show -> environment).
"""
from __future__ import annotations

import argparse
import html
import json
import os
import random
import shutil
import subprocess
import sys
import zlib

W, H = 1920, 1080
NAVY = (9, 36, 59)
CREAM = (245, 235, 213)
MUSTARD = (216, 165, 46)
HEX = {"navy": "#09243B", "cream": "#F5EBD5", "mustard": "#D8A52E"}

# Layout of the final frame (px on 1920x1080).
LOGO_W, LOGO_TOP = 760, 120
LINE_Y_START, LINE_Y_END = 440, 702        # centre of the experience line
LINE_SIZE, LINE_SCALE_END = 118, 0.54       # px, final scale
HOST_H, HOST_X = 700, (1550, 370)          # host height; centre x for right, left
HOST_BOTTOM = 1080
NAME_SIZE = 46

T = {"rules": 0.0, "line": 0.3, "host": (0.5, 1.0), "name": (0.8, 1.3),
     "line_move": 2.7, "logo": 3.0, "logo_full": 3.5, "push": 3.0}


def q(t: float, fps: int) -> float:
    return round(round(t * fps) / fps, 4)


# --- static assets -----------------------------------------------------------

def paper_background(out_path: str, seed: int = 11) -> None:
    """Navy paper: fine grain, soft blotches and a gentle vignette."""
    import numpy as np
    from PIL import Image, ImageFilter
    rng = np.random.default_rng(seed)
    base = np.ones((H, W, 3), np.float32) * np.array(NAVY, np.float32)
    grain = rng.normal(0, 3.2, (H, W, 1))
    blot = Image.fromarray((rng.random((H // 24, W // 24)) * 255).astype("uint8"))
    blot = np.asarray(blot.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(40)), np.float32)
    blot = (blot / 255.0 - 0.5)[..., None] * 9
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    vignette = (1 - 0.28 * np.clip(r - 0.35, 0, 1) ** 1.6)[..., None]
    img = np.clip((base + grain + blot) * vignette, 0, 255).astype("uint8")
    Image.fromarray(img, "RGB").save(out_path)


def paper_strip(text: str, out_path: str, font_path: str, size: int,
                colour=CREAM, tilt: float = -1.0) -> tuple[int, int]:
    """One torn-paper strip with navy Heebo Black type and a soft navy shadow.
    Deterministic (edges seeded from the text). Returns the PNG size."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, features
    if not features.check("raqm"):
        raise RuntimeError("Pillow has no raqm: Hebrew would render left-to-right")
    rng = random.Random(zlib.crc32(text.encode()))
    font = ImageFont.truetype(font_path, size)
    x0, y0, x1, y1 = ImageDraw.Draw(Image.new("L", (8, 8))).textbbox(
        (0, 0), text, font=font, direction="rtl", language="he")
    px, py = round(size * 0.55), round(size * 0.22)
    sw, sh = x1 - x0 + 2 * px, y1 - y0 + 2 * py
    jag = max(3, size // 12)
    edge = ([(x, rng.uniform(0, jag)) for x in range(0, sw + 1, 7)]
            + [(sw - rng.uniform(0, jag), y) for y in range(0, sh + 1, 7)]
            + [(x, sh - rng.uniform(0, jag)) for x in range(sw, -1, -7)]
            + [(rng.uniform(0, jag), y) for y in range(sh, -1, -7)])
    mask = Image.new("L", (sw, sh), 0)
    ImageDraw.Draw(mask).polygon(edge, fill=255)
    grain = np.random.default_rng(zlib.crc32(text.encode())).normal(0, 5, (sh, sw, 1))
    paper = np.clip(np.asarray(Image.new("RGB", (sw, sh), colour), np.float32) + grain, 0, 255)
    strip = Image.fromarray(paper.astype("uint8"), "RGB").convert("RGBA")
    ImageDraw.Draw(strip).text((px - x0, py - y0), text, font=font, fill=NAVY + (255,),
                               direction="rtl", language="he")
    strip.putalpha(mask)
    strip = strip.rotate(tilt, resample=Image.BICUBIC, expand=True)
    pad = 24
    out = Image.new("RGBA", (strip.width + 2 * pad, strip.height + 2 * pad), (0, 0, 0, 0))
    shadow = Image.new("RGBA", strip.size, NAVY + (0,))
    shadow.putalpha(strip.getchannel("A").point(lambda a: a * 120 // 255))
    layer = Image.new("RGBA", out.size, (0, 0, 0, 0))
    layer.paste(shadow, (pad + 5, pad + 8))
    out = Image.alpha_composite(out, layer.filter(ImageFilter.GaussianBlur(7)))
    layer = Image.new("RGBA", out.size, (0, 0, 0, 0))
    layer.paste(strip, (pad, pad))
    out = Image.alpha_composite(out, layer)
    out.save(out_path)
    return out.size


def host_cutout(src: str, out_path: str, height: int = HOST_H) -> tuple[int, int]:
    """Trim a transparent host cut-out to its content and scale it to `height`."""
    from PIL import Image
    im = Image.open(src).convert("RGBA")
    box = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if not box:
        raise ValueError(f"{src}: no opaque pixels (needs a transparent cut-out)")
    if box == (0, 0, im.width, im.height) and im.getchannel("A").getextrema()[0] == 255:
        raise ValueError(f"{src}: no transparency; supply the cut-out PNG, not a frame")
    im = im.crop(box)
    w = round(im.width * height / im.height)
    im.resize((w, height), Image.LANCZOS).save(out_path)
    return w, height


# --- composition -------------------------------------------------------------

def timeline_js(cfg: dict, hosts: list[dict]) -> str:
    fps = cfg.get("fps", 24)
    D = cfg.get("duration", 8.0)
    s = LINE_SCALE_END
    dy = LINE_Y_END - LINE_Y_START
    js = ["const tl=window.gsap.timeline({paused:true});",
          f"tl.fromTo('#rule-r',{{scaleX:0}},{{scaleX:1,duration:0.7,ease:'power2.out'}},{q(T['rules'] + 0.1, fps)});",
          f"tl.fromTo('#rule-l',{{scaleX:0}},{{scaleX:1,duration:0.7,ease:'power2.out'}},{q(T['rules'] + 0.1, fps)});",
          f"tl.fromTo('#line .txt',{{clipPath:'inset(0 0 0 100%)'}},{{clipPath:'inset(0 0 0 0%)',duration:0.6,ease:'power2.inOut'}},{q(T['line'], fps)});",
          f"tl.to('#line',{{y:{dy},scale:{s},duration:0.45,ease:'power3.inOut'}},{q(T['line_move'], fps)});",
          f"tl.to('#line .txt',{{color:'{HEX['mustard']}',duration:0.45,ease:'power2.inOut'}},{q(T['line_move'], fps)});",
          f"tl.to('.rule',{{opacity:0,duration:0.3}},{q(T['line_move'], fps)});",
          f"tl.fromTo('#line .bar',{{scaleX:0}},{{scaleX:1,duration:0.4,ease:'power2.out'}},{q(T['line_move'] + 0.35, fps)});",
          # wordmark: upper strip, then the whole mark
          f"tl.fromTo('#logo',{{opacity:0,scale:1.14,rotation:-2.5,clipPath:'inset(0% 0% 47% 0%)'}},"
          f"{{opacity:1,scale:1,rotation:0,duration:0.24,ease:'power3.out'}},{q(T['logo'], fps)});",
          f"tl.to('#logo',{{clipPath:'inset(0% 0% 0% 0%)',duration:0.2,ease:'power2.out'}},{q(T['logo_full'], fps)});",
          f"tl.fromTo('#logo',{{y:0}},{{y:6,duration:0.08,yoyo:true,repeat:1,ease:'power1.inOut'}},{q(T['logo_full'], fps)});",
          f"tl.fromTo('#world',{{scale:1}},{{scale:1.03,duration:{D - T['push']:.2f},ease:'none'}},{q(T['push'], fps)});"]
    for i, h in enumerate(hosts):
        side = "r" if i == 0 else "l"
        js.append(f"tl.fromTo('#host-{side}',{{opacity:0,y:140}},{{opacity:1,y:0,duration:0.65,ease:'power3.out'}},{q(T['host'][i], fps)});")
        dx = 60 if side == "r" else -60
        js.append(f"tl.fromTo('#name-{side}',{{opacity:0,x:{dx}}},{{opacity:1,x:0,duration:0.4,ease:'power2.out'}},{q(T['name'][i], fps)});")
        js.append(f"tl.fromTo('#host-{side}',{{x:0}},{{x:{-8 if side == 'r' else 8},duration:{D - T['host'][i] - 0.65:.2f},ease:'none'}},{q(T['host'][i] + 0.65, fps)});")
    js.append("window.__timelines=window.__timelines||{};window.__timelines['intro']=tl;")
    return "\n".join(js)


def build_html(cfg: dict, hosts: list[dict], logo_h: int) -> str:
    fps = cfg.get("fps", 24)
    D = cfg.get("duration", 8.0)
    line = html.escape(cfg["line"])
    host_divs = []
    for i, h in enumerate(hosts):
        side = "r" if i == 0 else "l"
        cx = HOST_X[0] if side == "r" else HOST_X[1]
        left = round(cx - h["w"] / 2)
        nl = round(cx - h["name_w"] / 2 + (60 if side == "r" else -60))
        host_divs.append(
            f'<img class="host" id="host-{side}" src="{h["file"]}" alt="" '
            f'style="left:{left}px;top:{HOST_BOTTOM - h["h"]}px;width:{h["w"]}px;height:{h["h"]}px" />')
        host_divs.append(
            f'<img class="name" id="name-{side}" src="{h["name_file"]}" alt="{html.escape(h["name"])}" '
            f'style="left:{nl}px;top:{HOST_BOTTOM - h["name_h"] - 34}px" />')
    return f"""<!doctype html>
<html lang="he">
<head>
<meta charset="utf-8" />
<style>
@font-face{{font-family:'Heebo Black';src:url('fonts/Heebo-Black.ttf') format('truetype');font-display:block}}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;width:{W}px;height:{H}px;overflow:hidden;background:{HEX['navy']}}}
#stage{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:{HEX['navy']}}}
#world{{position:absolute;inset:0;transform-origin:50% 40%}}
#bg{{position:absolute;left:0;top:0;width:{W}px;height:{H}px}}
.rule{{position:absolute;top:{LINE_Y_START}px;height:3px;width:420px;background:{HEX['mustard']};opacity:0.9}}
#rule-r{{left:{W // 2 + 20}px;transform-origin:0 50%}}
#rule-l{{left:{W // 2 - 440}px;transform-origin:100% 50%}}
#line{{position:absolute;left:0;width:{W}px;top:{LINE_Y_START - LINE_SIZE}px;height:{LINE_SIZE * 2}px;
  display:flex;align-items:center;justify-content:center;gap:48px;transform-origin:50% 50%}}
#line .txt{{font-family:'Heebo Black';font-size:{LINE_SIZE}px;line-height:1;color:{HEX['cream']};
  white-space:nowrap;padding:0 8px;background:{HEX['navy']};text-shadow:0 6px 18px rgba(0,0,0,0.35)}}
#line .bar{{width:180px;height:6px;background:{HEX['mustard']}}}
#line .bar.r{{transform-origin:0 50%}}
#line .bar.l{{transform-origin:100% 50%}}
#logo{{position:absolute;left:{(W - LOGO_W) // 2}px;top:{LOGO_TOP}px;width:{LOGO_W}px;height:{logo_h}px;
  filter:drop-shadow(0 10px 18px rgba(4,14,26,0.55));transform-origin:50% 40%;opacity:0}}
.host{{position:absolute;filter:drop-shadow(0 12px 26px rgba(4,14,26,0.6));opacity:0}}
.name{{position:absolute;opacity:0}}
</style>
</head>
<body>
<div id="stage" data-composition-id="intro" data-start="0" data-duration="{D:.4f}" data-fps="{fps}" data-width="{W}" data-height="{H}">
<div id="world">
<img id="bg" src="bg.png" alt="" />
<div class="rule" id="rule-r"></div>
<div class="rule" id="rule-l"></div>
{chr(10).join(host_divs)}
<img id="logo" src="logo.png" alt="אחים להשקעות" />
<div id="line" dir="rtl"><div class="bar l"></div><div class="txt">{line}</div><div class="bar r"></div></div>
</div>
<script src="vendor/gsap.min.js"></script>
<script>
(function(){{
{timeline_js(cfg, hosts)}
}})();
</script>
</div>
</body>
</html>
"""


def stage(cfg_path: str, project: str) -> dict:
    from PIL import Image
    base = os.path.dirname(os.path.abspath(cfg_path))
    cfg = json.load(open(cfg_path, encoding="utf-8"))
    p = lambda k: os.path.join(base, k)  # noqa: E731
    pub = os.path.join(project, "public")
    for d in ("fonts", "vendor", "hosts"):
        os.makedirs(os.path.join(pub, d), exist_ok=True)
    black = os.path.join(p(cfg["fonts"]), "Heebo-Black.ttf")
    shutil.copy(black, os.path.join(pub, "fonts", "Heebo-Black.ttf"))
    shutil.copy(p(cfg["gsap"]), os.path.join(pub, "vendor", "gsap.min.js"))
    shutil.copy(p(cfg["logo"]), os.path.join(pub, "logo.png"))
    lw, lh = Image.open(p(cfg["logo"])).size
    logo_h = round(LOGO_W * lh / lw)
    paper_background(os.path.join(pub, "bg.png"))
    hosts = []
    for i, h in enumerate(cfg.get("hosts", [])[:2]):
        f = f"hosts/host-{i}.png"
        w, hh = host_cutout(p(h["image"]), os.path.join(pub, f))
        nf = f"hosts/name-{i}.png"
        nw, nh = paper_strip(h["name"], os.path.join(pub, nf), black, NAME_SIZE,
                             tilt=(-1.2 if i == 0 else 1.0))
        hosts.append({"name": h["name"], "file": f, "w": w, "h": hh,
                      "name_file": nf, "name_w": nw, "name_h": nh})
    with open(os.path.join(pub, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(build_html(cfg, hosts, logo_h))
    cfg["_music"] = p(cfg["music"]) if cfg.get("music") else None
    return cfg


def render(cfg: dict, project: str, out: str) -> None:
    fps = cfg.get("fps", 24)
    D = cfg.get("duration", 8.0)
    silent = os.path.join(project, "intro-silent.mp4")
    subprocess.run(["npx", "--yes", "hyperframes", "render", "public", "-o", os.path.abspath(silent),
                    "--fps", str(fps)], cwd=project, check=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", silent]
    if cfg.get("_music"):
        cmd += ["-i", cfg["_music"], "-map", "0:v:0", "-map", "1:a:0",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
            "-r", str(fps), "-t", f"{D:.3f}", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print(f"wrote {out}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build (and render) the show intro.")
    ap.add_argument("config")
    ap.add_argument("--project", required=True)
    ap.add_argument("--render", metavar="OUT.mp4")
    a = ap.parse_args(argv)
    cfg = stage(a.config, a.project)
    print(f"staged {a.project}/public ({len(cfg.get('hosts', []))} host(s))")
    if a.render:
        render(cfg, a.project, a.render)
    return 0


if __name__ == "__main__":
    sys.exit(main())
