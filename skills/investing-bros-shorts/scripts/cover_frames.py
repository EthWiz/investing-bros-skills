#!/usr/bin/env python3
"""Contact sheet of candidate cover frames for one short, so --at for make_cover.py is picked by looking.

Usage:
    python3 cover_frames.py raw.mp4 --from 2106 --to 2154 --side R [--n 12] OUT_frames.jpg
    python3 cover_frames.py nadav.mp4 --from 2106 --to 2154 --crop 656,0,1215,2160 OUT_frames.jpg

Writes a 4-column sheet of N frames evenly spread over the window, each cropped like the
cover (the host's half, or the full-screen --crop) and labelled with its SOURCE time.
Pass that time to make_cover.py --at.

Pick the frame that will win the click at thumbnail size:
- a clear emotion that fits the hook (surprise, a smile, a raised eyebrow, a pointing hand),
- eyes open and toward the camera or the other host, mouth not mid-word,
- the face big and sharp; no motion blur, no hand over the face.
"""
import argparse
import subprocess
import sys

COLS = 4


def times(t0: float, t1: float, n: int):
    """n source times spread over [t0, t1], away from the very edges."""
    if t1 <= t0 or n < 1:
        raise ValueError("need --to after --from and n >= 1")
    step = (t1 - t0) / n
    return [round(t0 + step * (i + 0.5), 2) for i in range(n)]


def crop_filter(side=None, crop=None) -> str:
    if crop:
        x, y, w, h = crop
        return f"crop={w}:{h}:{x}:{y}"
    if side == "L":
        return "crop=iw/2:ih:0:0"
    if side == "R":
        return "crop=iw/2:ih:iw/2:0"
    return "null"


def build_command(source, ts, crop_vf, out, tile_w=270, tile_h=480, font=None) -> list:
    """One seek per candidate (fast on long recordings), each tile labelled with its source time."""
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for t in ts:
        cmd += ["-ss", f"{t:.2f}", "-i", source]
    fc, ff = "", (f":fontfile='{font}'" if font else "")
    for i, t in enumerate(ts):
        fc += (f"[{i}:v]trim=end_frame=1,{crop_vf},scale={tile_w}:{tile_h}:force_original_aspect_ratio=increase,"
               f"crop={tile_w}:{tile_h},drawbox=y=ih-40:w=iw:h=40:color=black@0.6:t=fill,"
               f"drawtext=text='{t:.2f}':x=10:y=h-32:fontsize=26:fontcolor=white{ff}[f{i}];")
    rows = -(-len(ts) // COLS)
    pad = rows * COLS - len(ts)
    for j in range(pad):
        fc += f"color=c=black:s={tile_w}x{tile_h}:d=0.04,trim=end_frame=1[p{j}];"
    fc += "".join(f"[f{i}]" for i in range(len(ts))) + "".join(f"[p{j}]" for j in range(pad))
    fc += f"xstack=inputs={rows * COLS}:layout=" + "|".join(
        f"{(k % COLS) * tile_w}_{(k // COLS) * tile_h}" for k in range(rows * COLS)) + ":fill=black[out]"
    return cmd + ["-filter_complex", fc, "-map", "[out]", "-frames:v", "1", "-q:v", "3", out]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("--from", dest="t0", type=float, required=True)
    ap.add_argument("--to", dest="t1", type=float, required=True)
    ap.add_argument("--side", choices=("L", "R", "full"), default="full")
    ap.add_argument("--crop", help="x,y,w,h: the full-screen crop, as in the short's config")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--font", help="a .ttf for the time labels (e.g. fonts/Heebo-SemiBold.ttf) if ffmpeg has no default font")
    ap.add_argument("out")
    a = ap.parse_args()
    ts = times(a.t0, a.t1, a.n)
    crop = [int(v) for v in a.crop.split(",")] if a.crop else None
    subprocess.run(build_command(a.source, ts, crop_filter(a.side, crop), a.out, font=a.font), check=True)
    print(f"{a.out}: {len(ts)} frames, {', '.join(f'{t:.2f}' for t in ts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
