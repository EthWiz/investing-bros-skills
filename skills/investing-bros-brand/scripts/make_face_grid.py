#!/usr/bin/env python3
"""Labelled review grid of one host's face stills, for the operator's face picks.

  make_face_grid.py RECORDING OUT_DIR --host amitai --side left --prefix A \
      --score-json amitai-scores.json [--pick 10 --gap 30]
  make_face_grid.py RECORDING OUT_DIR --host nadav --side right --prefix N \
      --times 09:59.4 34:51.3 ...

Times come from face_score.py (its --json output, or the MM:SS.s lines it prints).
Writes OUT_DIR/<ID>.jpg (the host's half of the frame at full size),
OUT_DIR/grid-<host>-<PREFIX>.jpg (numbered tiles with their times) and
OUT_DIR/manifest-<host>-<PREFIX>.json (id -> host, t_sec), the input of
record_face_picks.py. The prefix is the round id: a second round for the same host
gets a new prefix (episode 9: A, then B for Amitai), so no round overwrites another.
An existing manifest for the same host and prefix is refused unless --force.
The stills are real frames, untouched. Keep them out of the repo.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess


def parse_time(s: str) -> float:
    """'MM:SS.s', 'H:MM:SS.s' or plain seconds -> seconds."""
    sec = 0.0
    for part in str(s).strip().split(":"):
        sec = sec * 60 + float(part)
    return round(sec, 3)


def pick_times(score_json: dict, n: int, gap: float) -> list[float]:
    """Top-n frame times by score from face_score.py --json, at least gap s apart, in time order."""
    rows = sorted(((f["score"], f["t"]) for f in score_json["frames"].values()), key=lambda x: -x[0])
    out: list[float] = []
    for _, t in rows:
        if all(abs(t - u) >= gap for u in out):
            out.append(t)
        if len(out) == n:
            break
    return sorted(out)


def grid_shape(n: int, cols: int | None = None) -> tuple[int, int]:
    cols = cols or min(5, max(1, n))
    return cols, math.ceil(n / cols)


def fmt(t: float) -> str:
    return f"{int(t // 60):02d}:{t % 60:04.1f}"


def out_names(host: str, prefix: str) -> dict:
    """Per-round file names: host AND prefix, so a second round never overwrites the first."""
    return {"grid": f"grid-{host}-{prefix}.jpg", "manifest": f"manifest-{host}-{prefix}.json"}


def extract(recording: str, t: float, side: str, out: str) -> None:
    crop = {"left": ["-vf", "crop=iw/2:ih:0:0"], "right": ["-vf", "crop=iw/2:ih:iw/2:0"], "full": []}[side]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", recording, "-frames:v", "1",
                    *crop, "-q:v", "1", out], check=True)


def build_grid(paths: list[str], labels: list[str], out: str, tile_w: int = 384) -> None:
    from PIL import Image, ImageDraw, ImageFont

    ims = [Image.open(p).convert("RGB") for p in paths]
    th = round(tile_w * ims[0].height / ims[0].width)
    cols, rows = grid_shape(len(ims))
    bar = 44
    sheet = Image.new("RGB", (cols * tile_w, rows * (th + bar)), "white")
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default(size=30)
    except TypeError:  # Pillow < 10.1
        font = ImageFont.load_default()
    for k, (im, lab) in enumerate(zip(ims, labels)):
        x, y = (k % cols) * tile_w, (k // cols) * (th + bar)
        sheet.paste(im.resize((tile_w, th)), (x, y + bar))
        d.text((x + 8, y + 6), lab, fill="black", font=font)
    sheet.save(out, quality=90)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("recording")
    ap.add_argument("out_dir")
    ap.add_argument("--host", required=True, help="amitai or nadav (show spelling)")
    ap.add_argument("--side", choices=["left", "right", "full"], required=True)
    ap.add_argument("--prefix", required=True, help="id letter(s), e.g. A for Amitai, N for Nadav")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--score-json", help="face_score.py --json output for this host")
    g.add_argument("--times", nargs="+", help="MM:SS.s times (as face_score.py prints them)")
    ap.add_argument("--pick", type=int, default=10)
    ap.add_argument("--gap", type=float, default=30.0)
    ap.add_argument("--force", action="store_true", help="replace this host's round with the same prefix")
    a = ap.parse_args(argv)
    if not a.prefix.isalnum():
        ap.error("--prefix must be letters/digits (it names the files and the still ids)")
    names = out_names(a.host, a.prefix)
    man_path = os.path.join(a.out_dir, names["manifest"])
    if os.path.exists(man_path) and not a.force:
        ap.error(f"{man_path} exists: use a new --prefix for a new round (or --force to redo this one)")

    if a.score_json:
        with open(a.score_json) as fh:
            times = pick_times(json.load(fh), a.pick, a.gap)
    else:
        times = [parse_time(t) for t in a.times]
    os.makedirs(a.out_dir, exist_ok=True)
    items, paths, labels = {}, [], []
    for k, t in enumerate(times, 1):
        sid = f"{a.prefix}{k}"
        p = os.path.join(a.out_dir, sid + ".jpg")
        extract(a.recording, t, a.side, p)
        items[sid] = {"host": a.host, "t_sec": t}
        paths.append(p)
        labels.append(f"{sid}  {fmt(t)}")
    grid = os.path.join(a.out_dir, names["grid"])
    build_grid(paths, labels, grid)
    man = {"recording": os.path.basename(a.recording), "host": a.host, "side": a.side,
           "prefix": a.prefix, "grid": names["grid"], "items": items}
    with open(man_path, "w") as fh:
        json.dump(man, fh, indent=1, ensure_ascii=False)
    print(grid)
    for sid, it in items.items():
        print(sid, fmt(it["t_sec"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
