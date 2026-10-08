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
headline; | breaks a line, [..] is emerald. Needs ffmpeg with libass and Pillow.
"""
import argparse
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brand import EMERALD, VERTICAL, WHITE, ass_colour  # noqa: E402
from clip_captions import rtl  # noqa: E402

W, H = VERTICAL["size"]
VY, VH = 290, 1216                        # host picture, higher than in the short so the face sits in the crop square
ZOOM = 1.15                               # a little tighter than the short: a cover is seen tiny
SQUARE = (420, 1500)                      # centre 1:1 crop of a 9:16 frame
HEAD_CENTER_Y = 1290                      # headline block centre (below the face, inside the square)
PILL_Y = 1450
FADE_H = 560                              # dark fade at the bottom of the host picture
EM = "{\\c&H" + ass_colour(EMERALD)[4:] + "&}"
WH = "{\\c&H" + ass_colour(WHITE)[4:] + "&}"


def headline_lines(headline: str):
    lines = [x for x in headline.split("|") if x.strip()]
    if not 1 <= len(lines) <= 3:
        raise ValueError("headline: 1–3 lines")
    for line in lines:
        if len(line.replace("[", "").replace("]", "")) > 18:
            raise ValueError(f"headline line too long for a thumbnail (max ~18 characters): {line}")
    return lines


def build_ass(headline: str, episode) -> str:
    lines = headline_lines(headline)
    size = 118 if len(lines) <= 2 else 100
    green = ass_colour(EMERALD)
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
Style: Pill,Heebo ExtraBold,62,&H000B1006,&H000B1006,{green},{green},0,0,0,0,100,100,0,0,3,20,0,5,0,0,0,-1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 1,0:00:00.00,0:00:05.00,Head,,0,0,0,,{{\\pos({W // 2},{HEAD_CENTER_Y})}}{body}
"""
    if episode is not None:
        head += f"Dialogue: 1,0:00:00.00,0:00:05.00,Pill,,0,0,0,,{{\\pos({W // 2},{PILL_Y})}}{rtl(f'פרק {episode}')}\n"
    return head


def gradient_png(path: str) -> None:
    """Dark fade over the lower part of the host picture so the headline reads."""
    from PIL import Image
    h = FADE_H
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--at", type=float, required=True, help="source time of the host frame")
    ap.add_argument("--side", choices=("L", "R", "full"), default="L")
    ap.add_argument("--headline", required=True)
    ap.add_argument("--episode", type=int)
    ap.add_argument("--frame", required=True, help="brand.py frame vertical")
    ap.add_argument("--fonts", required=True, help="folder with static Heebo weights")
    ap.add_argument("out")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        ass = os.path.join(tmp, "cover.ass")
        grad = os.path.join(tmp, "grad.png")
        open(ass, "w", encoding="utf-8").write(build_ass(a.headline, a.episode))
        gradient_png(grad)
        subprocess.run(build_command(a.source, a.at, a.side, a.frame, ass, a.fonts, grad, a.out), check=True)
    size = os.path.getsize(a.out)
    print(f"{a.out}: {W}x{H}, {size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
