#!/usr/bin/env python3
"""Make the cover image (thumbnail) for one vertical short, sized for Reels / Shorts / TikTok.

Usage:
    python3 make_cover.py --source raw.mp4 --at 857.2 --side L \
        --headline "סוויפט היא בכלל|[[לא מערכת תשלומים]]" --episode 6 \
        --frame frame_vertical.png --fonts fonts/ --preview OUT-cover.jpg

Pick --at with cover_frames.py (a sheet of candidate frames). Output: 1080x1920 JPEG
(< 1 MB), the short's own look: brand frame and logo, the host's close-up from the
moment --at, a 1-3 line hook headline and a "פרק N" pill. The host picture gets a
little extra contrast and sharpening: a cover is judged at ~150 px wide.

Crop safety: the headline and the pill sit inside the centre 1080x1080 square
(y 420-1500), so every profile-grid crop keeps them: Instagram's grid is 3:4
(1080x1440, since January 2025), TikTok's is about 3:4, YouTube's channel Shorts
tab shows the full 9:16. The logo sits above the square on purpose (it is on every
frame of the short anyway).

--headline: the short's hook, the same faithful paraphrase as its on-screen
headline; | breaks a line, [..] is gold text, a whole line in [[..]] is navy text
on a gold box (the one line that must read at thumbnail size). Aim for 3-6 words.
--preview also writes OUT_preview.png: the cover at feed size, the 3:4 and 1:1 grid
crops and a 120-px thumbnail, side by side. Needs ffmpeg with libass and Pillow.
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
BOX_PAD = 30                              # extra line height for a boxed line (its box border)
MAX_WORDS = 6                             # more than this does not read at thumbnail size
DASHES = ("\u2014", "\u2013")              # never on screen (investing-bros-show -> Hebrew)
GRID_34 = (240, 1680)                     # Instagram / TikTok 3:4 grid crop of a 9:16 cover
GRADE = "eq=contrast=1.08:saturation=1.12,unsharp=5:5:0.6"   # face punch for a tiny thumbnail
EM = "{\\c&H" + ass_colour(ACCENT)[4:] + "&}"
WH = "{\\c&H" + ass_colour(WHITE)[4:] + "&}"


def headline_lines(headline: str):
    lines = [x for x in headline.split("|") if x.strip()]
    if not 1 <= len(lines) <= 3:
        raise ValueError("headline: 1–3 lines")
    if any(d in headline for d in DASHES):
        raise ValueError(f"no em or en dash on screen (use a comma or a plain hyphen): {headline}")
    for line in lines:
        if len(plain(line)) > 18:
            raise ValueError(f"headline line too long for a thumbnail (max ~18 characters): {line}")
    if sum(is_boxed(x) for x in lines) > 1:
        raise ValueError("box one line at most: one focal line reads, two compete")
    return lines


def plain(line: str) -> str:
    return line.replace("[", "").replace("]", "")


def is_boxed(line: str) -> bool:
    t = line.strip()
    return t.startswith("[[") and t.endswith("]]")


def headline_warnings(headline: str):
    words = len(plain(headline.replace("|", " ")).split())
    return [f"headline has {words} words: covers that click say it in {MAX_WORDS} or fewer"] if words > MAX_WORDS else []


def headline_box(n_lines: int, n_boxed: int = 0):
    """(size, top, bottom, centre_y) of the headline block. It is placed by its bottom edge,
    HEAD_GAP above the pill, so a 3-line headline grows upwards instead of into the pill."""
    size = 118 if n_lines <= 2 else 100
    height = n_lines * size * LINE_H + n_boxed * BOX_PAD
    bottom = PILL_Y - PILL_HALF_H - HEAD_GAP
    top = bottom - height
    return size, top, bottom, round((top + bottom) / 2)


def line_centres(lines):
    """Centre y of each headline line, top to bottom (boxed lines get BOX_PAD more room)."""
    size, top, _, _ = headline_box(len(lines), sum(map(is_boxed, lines)))
    out, y = [], top
    for line in lines:
        h = size * LINE_H + (BOX_PAD if is_boxed(line) else 0)
        out.append(round(y + h / 2))
        y += h
    return out


def build_ass(headline: str, episode) -> str:
    lines = headline_lines(headline)
    size = headline_box(len(lines))[0]
    accent = ass_colour(ACCENT)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Head,Heebo Black,{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,6,4,5,60,60,0,-1
Style: Box,Heebo Black,{size},&H000B1006,&H000B1006,{accent},{accent},0,0,0,0,100,100,0,0,3,14,0,5,60,60,0,-1
Style: Pill,Heebo ExtraBold,62,&H000B1006,&H000B1006,{accent},{accent},0,0,0,0,100,100,0,0,3,20,0,5,0,0,0,-1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    for line, y in zip(lines, line_centres(lines)):
        if is_boxed(line):
            head += f"Dialogue: 1,0:00:00.00,0:00:05.00,Box,,0,0,0,,{{\\pos({W // 2},{y})}}{rtl(plain(line))}\n"
        else:
            body = rtl(line).replace("[", EM).replace("]", WH)
            head += f"Dialogue: 1,0:00:00.00,0:00:05.00,Head,,0,0,0,,{{\\pos({W // 2},{y})}}{body}\n"
    if episode is not None:
        head += f"Dialogue: 1,0:00:00.00,0:00:05.00,Pill,,0,0,0,,{{\\pos({W // 2},{PILL_Y})}}{rtl(f'פרק {episode}')}\n"
    return head


def preview(cover: str, out: str) -> None:
    """Side-by-side: feed size, the 3:4 and 1:1 grid crops, and a 120-px thumbnail, on navy."""
    from PIL import Image
    img = Image.open(cover).convert("RGB")
    tiles = [img.resize((270, 480)),
             img.crop((0, GRID_34[0], W, GRID_34[1])).resize((270, 360)),
             img.crop((0, SQUARE[0], W, SQUARE[1])).resize((270, 270)),
             img.resize((120, 213))]
    sheet = Image.new("RGB", (sum(t.width for t in tiles) + 20 * (len(tiles) + 1), 480 + 40), (10, 22, 48))
    x = 20
    for t in tiles:
        sheet.paste(t, (x, 20))
        x += t.width + 20
    sheet.save(out)


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
    fc = (f"[0:v]{crop},scale={zw}:{zh}:force_original_aspect_ratio=increase,crop={W}:{VH}:(iw-{W})/2:(ih-{VH})/3,{GRADE},setpts=0[host];"
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
    fc = (f"[0:v]crop={w}:{h}:{x}:{y},scale={zw}:{zh},crop={W}:{H}:(iw-{W})/2:(ih-{H})/3,setsar=1,{GRADE},setpts=0[host];"
          f"[1:v]setpts=0[gr];[2:v]scale=210:-1,setpts=0[lg];[1:v]vflip,scale={W}:420,setpts=0[top];"
          f"[host][gr]overlay=0:{H - FB_FADE_H}[b0];[b0][top]overlay=0:0[b];[b][lg]overlay=56:150[c];"
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
    ap.add_argument("--preview", action="store_true", help="also write OUT_preview.png (feed size, grid crops, tiny thumbnail)")
    ap.add_argument("out")
    a = ap.parse_args()
    for w in headline_warnings(a.headline):
        print("warning:", w)
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
    if a.preview:
        pv = os.path.splitext(a.out)[0] + "_preview.png"
        preview(a.out, pv)
        print(f"{pv}: look at it; the headline must read in the 120-px thumbnail")
    return 0


if __name__ == "__main__":
    sys.exit(main())
