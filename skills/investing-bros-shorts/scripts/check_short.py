#!/usr/bin/env python3
"""Check a rendered short before handing it back: length, loudness, peak, and a frame strip to look at.

Usage:
    python3 check_short.py short.mp4 [--frames 8]      # writes short_strip.jpg next to it

Prints duration, integrated loudness (target about -14 LUFS) and true peak (below -1 dB),
with a warning for anything outside the house limits. Then LOOK at the strip: captions
right-to-left and inside the safe zone, the right host on screen, nothing over the face.
"""
import argparse
import re
import subprocess
import sys


def probe(path):
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                             capture_output=True, text=True, check=True).stdout)
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", log)[-1])
    peak = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", log)[-1])
    return d, lufs, peak


def problems(d, lufs, peak):
    out = []
    if not 30 <= d <= 60:
        out.append(f"duration {d:.1f} s is outside 30–60 s")
    if abs(lufs + 14) > 1.5:
        out.append(f"loudness {lufs} LUFS is not about -14")
    if peak > -1.0:
        out.append(f"true peak {peak} dB is above -1 dB")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video"); ap.add_argument("--frames", type=int, default=8)
    a = ap.parse_args()
    d, lufs, peak = probe(a.video)
    strip = re.sub(r"\.[^.]+$", "", a.video) + "_strip.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-vf", f"fps={a.frames}/{d:.3f},scale=270:480,tile={a.frames}x1",
                    "-frames:v", "1", strip], check=True)
    print(f"{a.video}: {d:.2f} s, {lufs} LUFS, peak {peak} dB -> {strip}")
    bad = problems(d, lufs, peak)
    for p in bad:
        print("warning:", p)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
