#!/usr/bin/env python3
"""Suggest crop_x for build_fullbleed.py: where each host's face sits in the side-by-side recording.

Usage:
    python3 face_crop.py raw.mp4 --at 2120 2135 2150      # a few moments when both are on camera

Takes frames, finds skin-coloured pixels in the upper two-thirds of each half and centres
the 608-px 9:16 crop on them. Prints {"L": x, "R": x} for the config. It is a heuristic:
look at one frame of the render to confirm.
"""
import argparse
import json
import subprocess

import numpy as np


def frame(path, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", path, "-frames:v", "1", "-vf", "scale=960:540",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(540, 960, 3).astype(np.float32)


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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video"); ap.add_argument("--at", type=float, nargs="+", required=True)
    a = ap.parse_args()
    print(json.dumps({"crop_x": suggest(a.video, a.at)}))


if __name__ == "__main__":
    main()
