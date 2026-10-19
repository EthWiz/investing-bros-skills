#!/usr/bin/env python3
"""Suggest the framing and the caption / hook positions for build_fullbleed.py.

Usage:
    python3 face_crop.py raw.mp4 --at 2120 2135 2150      # side-by-side recording: crop_x per host
    python3 face_crop.py source.mp4 --at 1116 1140 1174 --crop 418,0,405,720
                                                          # one-host frame (e.g. Zoom speaker view):
                                                          # your 9:16 crop box in source pixels

Side-by-side: takes frames, finds skin-coloured pixels in the upper two-thirds of each
half and centres the 608-px 9:16 crop on them; prints {"crop_x": {"L": x, "R": x}}.
With OpenCV installed (pip install opencv-python-headless) it also finds the face in
each crop, maps it to the 1080x1920 short and suggests "caption_y" (just under the chin)
and "hook_y" (the brief hook in the frame centre, moved up only if it would run into the
captions), clamped to brand.CAPTION_Y_BOUNDS and brand.HOOK_Y_BOUNDS, with a warning when
the face is too big for the captions to clear. These are
heuristics: look at one frame of the render to confirm (hands in shot pull them off).
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brand import CAPTION_HALF, CAPTION_Y_BOUNDS, HOOK_GAP, HOOK_STRIPS, HOOK_Y_BOUNDS, HOOK_Y_DEFAULT  # noqa: E402

HOOK_HALF = round(HOOK_STRIPS["size"] * 1.45)   # half a two-strip hook block (~290 px)


def frame(path, t, w=960, h=540, gray=False):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", path, "-frames:v", "1", "-vf", f"scale={w}:{h}",
                          "-f", "rawvideo", "-pix_fmt", "gray" if gray else "rgb24", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint8)
    return a.reshape(h, w) if gray else a.reshape(h, w, 3).astype(np.float32)


def skin_centre_x(half):
    r, g, b = half[..., 0], half[..., 1], half[..., 2]
    cr = 0.5 * r - 0.4187 * g - 0.0813 * b + 128
    cb = -0.1687 * r - 0.3313 * g + 0.5 * b + 128
    m = (cr > 135) & (cr < 175) & (cb > 85) & (cb < 135)
    m[int(half.shape[0] * 0.66):] = False          # ignore hands/arms low in the frame
    xs = np.nonzero(m)[1]
    return float(np.median(xs)) if len(xs) > 200 else half.shape[1] / 2


def suggest(path, times):
    out = {}
    for side, sl in (("L", slice(0, 480)), ("R", slice(480, 960))):
        cx = np.median([skin_centre_x(frame(path, t)[:, sl]) for t in times]) * 2   # back to 960-px half
        out[side] = int(min(max(cx - 304, 0), 960 - 608))
    return out


def video_size(path):
    s = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout
    w, h = (int(x) for x in s.strip().split(",")[:2])
    return w, h


def face_boxes(path, times, crop, size):
    """Face boxes (x0, y0, x1, y1) in 1080x1920 short pixels, one per frame where a face was found."""
    try:
        import cv2
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    except (ImportError, AttributeError):
        return None
    W, H = size
    sw, sh = 640, round(640 * H / W)
    k = W / sw
    cx, cy, cw, ch = crop
    boxes = []
    for t in times:
        faces = cascade.detectMultiScale(frame(path, t, sw, sh, gray=True), 1.05, 3, minSize=(sw // 12, sw // 12))
        inside = [(x * k, y * k, w * k, h * k) for x, y, w, h in faces if cx <= (x + w / 2) * k <= cx + cw]
        if inside:
            x, y, w, h = max(inside, key=lambda f: f[2])
            sx, sy = 1080 / cw, 1920 / ch
            boxes.append(((x - cx) * sx, (y - cy) * sy, (x + w - cx) * sx, (y + h - cy) * sy))
    return boxes


def place(boxes):
    """caption_y / hook_y for the median face box, clamped to the brand bounds."""
    x0, y0, x1, y1 = (float(np.median([b[i] for b in boxes])) for i in range(4))
    cap = round(min(max(y1 + CAPTION_HALF + 15, CAPTION_Y_BOUNDS[0]), CAPTION_Y_BOUNDS[1]))
    hook = round(min(max(min(HOOK_Y_DEFAULT, cap - CAPTION_HALF - HOOK_GAP - HOOK_HALF), HOOK_Y_BOUNDS[0]),
                     HOOK_Y_BOUNDS[1]))
    warn = []
    if cap - CAPTION_HALF < y1:
        warn.append(f"chin at y~{y1:.0f}: captions at the lowest allowed {cap} still overlap the chin/neck")
    return {"face_box": [round(v) for v in (x0, y0, x1, y1)], "caption_y": cap, "hook_y": hook, "warnings": warn}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video"); ap.add_argument("--at", type=float, nargs="+", required=True)
    ap.add_argument("--crop", help="x,y,w,h of the 9:16 crop in source pixels (one-host frame)")
    a = ap.parse_args()
    size = video_size(a.video)
    if a.crop:
        crops = {"crop": [int(v) for v in a.crop.split(",")]}
        out = {}
    else:
        cx = suggest(a.video, a.at)
        out = {"crop_x": cx}
        sx = size[0] / 1920
        crops = {s: [round((cx[s] + (960 if s == "R" else 0)) * sx), 0, round(608 * sx), size[1]] for s in "LR"}
    for key, crop in crops.items():
        boxes = face_boxes(a.video, a.at, crop, size)
        if boxes is None:
            out["note"] = "install opencv-python-headless for caption_y / hook_y suggestions"
            break
        if boxes:
            out["layout" if key == "crop" else f"layout_{key}"] = place(boxes)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
