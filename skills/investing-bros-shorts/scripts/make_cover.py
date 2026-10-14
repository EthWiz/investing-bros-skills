#!/usr/bin/env python3
"""Make the cover image (thumbnail) for one vertical short, sized for Reels / Shorts / TikTok.

Usage:
    python3 make_cover.py --source raw.mp4 --at 857.2 --side L \
        --headline "סוויפט היא בכלל|[לא מערכת תשלומים]" --episode 6 \
        --frame frame_vertical.png --fonts fonts/ OUT-cover.jpg

Output: 1080x1920 JPEG (< 1 MB), the short's own look — brand frame and logo,
the host's close-up from the moment --at (pick a frame with an open, expressive
face, eyes open, mouth not mid-word), a 2–3 line hook headline and a "פרק N" pill.

Crop safety: the headline and the pill sit inside the centre 1080x1080 square
(y 420–1500), so the profile-grid crops keep them — Instagram shows 4:5
(1080x1350) and 1:1 in the grid, TikTok and Shorts show the full 9:16. The logo
sits above the square on purpose (it is on every frame of the short anyway).

--headline: the short's hook, the same faithful paraphrase as its on-screen
headline; | breaks a line, [..] is the gold accent. Needs ffmpeg with libass and Pillow.
"""
import argparse
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brand import ACCENT, VERTICAL, WHITE, ass_colour  # noqa: E402
from clip_captions import rtl  # noqa: E402

W, H = VERTICAL["size"]
VY, VH = 290, 1216                        # host picture, higher than in the short so the face sits in the crop square
ZOOM = 1.15                               # a little tighter than the short: a cover is seen tiny
SQUARE = (420, 1500)                      # centre 1:1 crop of a 9:16 frame
PILL_Y = 1440                             # episode pill centre (its box stays inside the square)
PILL_HALF_H = 51                          # 62 px text + 20 px box border each side
HEAD_GAP = 40                             # space between the headline's last line and the pill
LINE_H = 0.95                             # measured: rendered Heebo Black lines, outline included, per font px
FADE_H = 560                              # dark fade at the bottom of the host picture
EM = "{\\c&H" + ass_colour(ACCENT)[4:] + "&}"
WH = "{\\c&H" + ass_colour(WHITE)[4:] + "&}"


def headline_lines(headline: str):
    lines = [x for x in headline.split("|") if x.strip()]
    if not 1 <= len(lines) <= 3:
        raise ValueError("headline: 1–3 lines")
    for line in lines:
        if len(line.replace("[", "").replace("]", "")) > 18:
            raise ValueError(f"headline line too long for a thumbnail (max ~18 characters): {line}")
    return lines


def headline_box(n_lines: int):
    """(size, top, bottom, centre_y) of the headline block. It is placed by its bottom edge,
    HEAD_GAP above the pill, so a 3-line headline grows upwards instead of into the pill."""
    size = 118 if n_lines <= 2 else 100
    height = n_lines * size * LINE_H
    bottom = PILL_Y - PILL_HALF_H - HEAD_GAP
    top = bottom - height
    return size, top, bottom, round((top + bottom) / 2)


def build_ass(headline: str, episode) -> str:
    lines = headline_lines(headline)
    size, _, _, centre_y = headline_box(len(lines))
    accent = ass_colour(ACCENT)
    body = "\\N".join(rtl(x).replace("[", EM).replace("]", WH) for x in lines)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Head,Heebo Black,{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,6,4,5,60,60,0,-1
Style: Pill,Heebo ExtraBold,62,&H000B1006,&H000B1006,{accent},{accent},0,0,0,0,100,100,0,0,3,20,0,5,0,0,0,-1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 1,0:00:00.00,0:00:05.00,Head,,0,0,0,,{{\\pos({W // 2},{centre_y})}}{body}
"""
    if episode is not None:
        head += f"Dialogue: 1,0:00:00.00,0:00:05.00,Pill,,0,0,0,,{{\\pos({W // 2},{PILL_Y})}}{rtl(f'פרק {episode}')}\n"
    return head


def gradient_png(path: str, h: int = FADE_H) -> None:
    """Dark fade over the lower part of the host picture so the headline reads."""
    from PIL import Image
    img = Image.new("RGBA", (W, h))
    px = img.load()
    for y in range(h):
        a = int(255 * min(1.0, (y / h) ** 0.8 * 1.15))
        for x in range(W):
            px[x, y] = (7, 9, 8, a)
    img.save(path)


def build_command(source, at, side, frame, ass, fonts, grad, out) -> list:
    crop = "crop=iw/2:ih:0:0" if side == "L" else ("crop=iw/2:ih:iw/2:0" if side == "R" else "crop=iw:ih:0:0")
    esc = lambda p: p.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")  # noqa: E731
    # setpts=0 on every input: a seeked video frame and two stills must line up on one timestamp
    zw, zh = int(W * ZOOM) // 2 * 2, int(VH * ZOOM) // 2 * 2
    fc = (f"[0:v]{crop},scale={zw}:{zh}:force_original_aspect_ratio=increase,crop={W}:{VH}:(iw-{W})/2:(ih-{VH})/3,setpts=0[host];"
          f"[1:v]setpts=0[bg];[2:v]setpts=0[gr];"
          f"[bg][host]overlay=0:{VY}[b];[b][gr]overlay=0:{VY + VH - FADE_H}[c];"
          f"[c]ass='{esc(ass)}':fontsdir='{esc(fonts)}',format=yuvj420p[out]")
    return ["ffmpeg", "-v", "error", "-y", "-ss", f"{at:.3f}", "-i", source, "-i", frame, "-i", grad,
            "-filter_complex", fc, "-map", "[out]", "-frames:v", "1", "-q:v", "2", out]


FB_FADE_H = 900                            # full-screen cover: fade from y=1020 to the bottom


def build_command_fullbleed(source, at, crop, logo, ass, fonts, grad, out) -> list:
    """House-style cover: the host full-screen (same crop as build_fullbleed.py), logo top-left."""
    esc = lambda p: p.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")  # noqa: E731
    x, y, w, h = crop
    zw, zh = int(W * ZOOM) // 2 * 2, int(H * ZOOM) // 2 * 2
    fc = (f"[0:v]crop={w}:{h}:{x}:{y},scale={zw}:{zh},crop={W}:{H}:(iw-{W})/2:(ih-{H})/3,setsar=1,setpts=0[host];"
          f"[1:v]setpts=0[gr];[2:v]scale=210:-1,setpts=0[lg];"
          f"[host][gr]overlay=0:{H - FB_FADE_H}[b];[b][lg]overlay=56:150[c];"
          f"[c]ass='{esc(ass)}':fontsdir='{esc(fonts)}',format=yuvj420p[out]")
    return ["ffmpeg", "-v", "error", "-y", "-ss", f"{at:.3f}", "-i", source, "-i", grad, "-i", logo,
            "-filter_complex", fc, "-map", "[out]", "-frames:v", "1", "-q:v", "2", out]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--at", type=float, required=True, help="source time of the host frame")
    ap.add_argument("--side", choices=("L", "R", "full"), default="L")
    ap.add_argument("--headline", required=True)
    ap.add_argument("--episode", type=int)
    ap.add_argument("--style", choices=("split", "fullbleed"), default="split",
                    help="fullbleed = house style (matches build_fullbleed.py): host full-screen, logo top-left")
    ap.add_argument("--crop", help="fullbleed: x,y,w,h of the 9:16 host crop in the source (as in the short's config)")
    ap.add_argument("--logo", help="fullbleed: logo.png (brand.py logo)")
    ap.add_argument("--frame", help="split: brand.py frame vertical")
    ap.add_argument("--fonts", required=True, help="folder with static Heebo weights")
    ap.add_argument("out")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        ass = os.path.join(tmp, "cover.ass")
        grad = os.path.join(tmp, "grad.png")
        open(ass, "w", encoding="utf-8").write(build_ass(a.headline, a.episode))
        if a.style == "fullbleed":
            if not (a.crop and a.logo):
                ap.error("--style fullbleed needs --crop and --logo")
            gradient_png(grad, FB_FADE_H)
            crop = [int(v) for v in a.crop.split(",")]
            subprocess.run(build_command_fullbleed(a.source, a.at, crop, a.logo, ass, a.fonts, grad, a.out), check=True)
        else:
            if not a.frame:
                ap.error("--style split needs --frame")
            gradient_png(grad)
            subprocess.run(build_command(a.source, a.at, a.side, a.frame, ass, a.fonts, grad, a.out), check=True)
    size = os.path.getsize(a.out)
    print(f"{a.out}: {W}x{H}, {size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
