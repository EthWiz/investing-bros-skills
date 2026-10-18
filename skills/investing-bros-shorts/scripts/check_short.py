#!/usr/bin/env python3
"""Check a rendered short before handing it back: length, loudness, peak, dead air, and frames to look at.

Usage:
    python3 check_short.py short.mp4 [--frames 8]      # writes short_strip.jpg and short_hook.jpg next to it

Prints duration, integrated loudness (target about -14 LUFS), true peak (below -1 dB) and any
pause of PAUSE_S or more (dead air loses viewers; the house style has no silences), with a
warning for anything outside the house limits. Then LOOK at:
- short_hook.jpg, the frame at HOOK_AT s: it is what a viewer sees before deciding to stay, and the
  frame to pick in the YouTube app's thumbnail picker when there is no custom thumbnail. The hook
  title must be fully on screen and readable, the host's face clear.
- the strip: captions right-to-left and inside the safe zone, the right host on screen, nothing over the face.
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


PAUSE_S = 0.6          # a gap in speech this long is dead air in a short
HOOK_AT = 0.5          # the hook title has popped in by then


def pauses(log, duration, min_s=PAUSE_S, edge=0.3):
    """Silences (start, end) from an ffmpeg silencedetect log, ignoring the first and last `edge` seconds."""
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: (-?[\d.]+)", log)]
    ends += [duration] * (len(starts) - len(ends))
    return [(a, b) for a, b in zip(starts, ends) if b - a >= min_s and a > edge and b < duration - edge]


def problems(d, lufs, peak):
    out = []
    if not 30 <= d <= 60:
        out.append(f"duration {d:.1f} s is outside 30-60 s")
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
    stem = re.sub(r"\.[^.]+$", "", a.video)
    strip, hook = stem + "_strip.jpg", stem + "_hook.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-vf", f"fps={a.frames}/{d:.3f},scale=270:480,tile={a.frames}x1",
                    "-frames:v", "1", strip], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{HOOK_AT}", "-i", a.video, "-frames:v", "1", "-q:v", "3", hook], check=True)
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", a.video, "-af", f"silencedetect=noise=-35dB:d={PAUSE_S}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    print(f"{a.video}: {d:.2f} s, {lufs} LUFS, peak {peak} dB -> {strip}, {hook}")
    bad = problems(d, lufs, peak)
    bad += [f"dead air {b - x:.1f} s at {x:.1f} s: cut it" for x, b in pauses(log, d)]
    for p in bad:
        print("warning:", p)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
