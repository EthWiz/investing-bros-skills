#!/usr/bin/env python3
"""Check a rendered short before handing it back: length, loudness, peak, the first second, and a frame strip.

Usage:
    python3 check_short.py short.mp4 [--frames 8]      # writes short_strip.jpg next to it

Prints duration, integrated loudness (target about -14 LUFS) and true peak (below -1 dB),
and checks the opening and the ending: frame 1 is not black or fading in, speech starts
within 0.4 s, and the short doesn't trail off in more than 1 s of silence. Length outside
15-60 s fails; outside the 20-45 s target is a note to explain in the hand-back.
Then LOOK at the strip: captions right-to-left and inside the safe zone, the right host
on screen, nothing over the face, the hook readable on the first frame.
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


LIMIT, TARGET = (15, 60), (20, 45)
DARK_FRAME = 25            # mean luma (0-255) below this reads as a black frame
LEAD_SILENCE, TAIL_SILENCE = 0.4, 1.0


def luma(path, t):
    """Mean luma of the frame at time t."""
    log = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1",
                          "-vf", "signalstats,metadata=print", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.findall(r"YAVG=(-?[\d.]+)", log)
    return float(m[-1]) if m else 0.0


def silences(path, noise_db=-35, min_len=0.3):
    """[(start, end)] stretches of silence; an open one at the end runs to None."""
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", f"silencedetect=n={noise_db}dB:d={min_len}",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: (-?[\d.]+)", log)]
    return [(s, ends[i] if i < len(ends) else None) for i, s in enumerate(starts)]


def opening_problems(d, first_luma, later_luma, quiet):
    """The first second has to hook: a visible frame and speech straight away; no dead air at the end."""
    out = []
    if first_luma < DARK_FRAME:
        out.append(f"frame 1 is nearly black (luma {first_luma:.0f}); open on the host, not a fade or a title card")
    elif later_luma and first_luma < 0.6 * later_luma:
        out.append(f"frame 1 is much darker than 0.5 s in ({first_luma:.0f} vs {later_luma:.0f}); remove the fade-in")
    for s, e in quiet:
        if s <= 0.05 and (e if e is not None else d) > LEAD_SILENCE:
            out.append(f"{(e if e is not None else d):.1f} s of silence before the first word; start on the word")
        if (e is None or e >= d - 0.05) and d - s > TAIL_SILENCE:
            out.append(f"{d - s:.1f} s of silence at the end; cut right after the payoff")
    return out


def problems(d, lufs, peak):
    out = []
    if not LIMIT[0] <= d <= LIMIT[1]:
        out.append(f"duration {d:.1f} s is outside {LIMIT[0]}–{LIMIT[1]} s")
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
    bad = problems(d, lufs, peak) + opening_problems(d, luma(a.video, 0), luma(a.video, min(0.5, d / 2)),
                                                     silences(a.video))
    for p in bad:
        print("warning:", p)
    if LIMIT[0] <= d <= LIMIT[1] and not TARGET[0] <= d <= TARGET[1]:
        print(f"note: {d:.1f} s is outside the {TARGET[0]}–{TARGET[1]} s target; say why in the hand-back")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
