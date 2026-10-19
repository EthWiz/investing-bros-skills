#!/usr/bin/env python3
"""Check a rendered short before handing it back: length, loudness, peak, the first second, and a frame strip.

Usage:
    python3 check_short.py short.mp4 [--frames 8]      # writes short_strip.jpg next to it

Prints duration, integrated loudness (target about -14 LUFS) and true peak (below -1 dB),
and checks the opening and the ending: frame 1 is not black or fading in, speech starts
within 0.4 s, and the short doesn't trail off in more than 1 s of silence. Length outside
15-60 s fails; outside the 20-45 s target is a note to explain in the hand-back.
If NAME_layout.json from build_fullbleed.py sits next to the video (or --layout is
given), the caption and hook positions must be inside brand.CAPTION_Y_BOUNDS and
brand.HOOK_Y_BOUNDS, and the hook block must keep brand.HOOK_GAP below the logo and above
the captions.
Then LOOK at the strip: captions right-to-left and inside the safe zone, the right host
on screen, nothing over the face, the hook readable on the first frame.
"""
import argparse
import json
import os
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


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brand import CAPTION_HALF, CAPTION_Y_BOUNDS, HOOK_GAP, HOOK_Y_BOUNDS, LOGO_BOX  # noqa: E402

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


def layout_problems(lay):
    """Caption and hook positions recorded by build_fullbleed.py, against the brand bounds."""
    out = []
    lo, hi = CAPTION_Y_BOUNDS
    if not lo <= lay.get("caption_y", lo) <= hi:
        out.append(f"caption_y {lay['caption_y']} is outside {lo}-{hi}; captions must clear the UI and the hook band")
    if lay.get("hook_style", "strips") == "strips":
        lo, hi = HOOK_Y_BOUNDS
        if not lo <= lay.get("hook_y", lo) <= hi:
            out.append(f"hook_y {lay['hook_y']} is outside the top band {lo}-{hi}")
        box = lay.get("hook_box")
        if box and box[0] < LOGO_BOX[3] + HOOK_GAP:
            out.append(f"hook starts at y={box[0]}: it needs {HOOK_GAP} px clear below the logo (bottom {LOGO_BOX[3]})")
        cap = lay.get("caption_y")
        if box and cap and box[1] > cap - CAPTION_HALF - HOOK_GAP:
            out.append(f"hook ends at y={box[1]}: it needs {HOOK_GAP} px clear above the captions (caption_y {cap})")
    for c in lay.get("callouts", []):
        (top, bottom), (t0, t1) = c["box"], c["window"]
        cap = lay.get("caption_y", CAPTION_Y_BOUNDS[1])
        if top < LOGO_BOX[3] + HOOK_GAP or bottom > cap - CAPTION_HALF - HOOK_GAP:
            out.append(f"callout y {top}-{bottom} needs {HOOK_GAP} px clear of the logo and the captions")
        end = lay.get("endcard_start", lay["duration"] - 2.8 if lay.get("duration") else None)
        if t0 < 2.7 or (end is not None and t1 > end + 0.31):     # 0.3 s crossfade into the card is fine
            out.append(f"callout {t0}-{t1} s overlaps the hook or the end card")
    if lay.get("endcard_box"):
        top, bottom = lay["endcard_box"]
        if top < LOGO_BOX[1] or bottom > CAPTION_Y_BOUNDS[1] + CAPTION_HALF:
            out.append(f"end card y {top}-{bottom} leaves the safe zone (y {LOGO_BOX[1]}-{CAPTION_Y_BOUNDS[1] + CAPTION_HALF})")
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
    ap.add_argument("--layout", help="NAME_layout.json from build_fullbleed.py (default: next to the video)")
    a = ap.parse_args()
    d, lufs, peak = probe(a.video)
    strip = re.sub(r"\.[^.]+$", "", a.video) + "_strip.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-vf", f"fps={a.frames}/{d:.3f},scale=270:480,tile={a.frames}x1",
                    "-frames:v", "1", strip], check=True)
    print(f"{a.video}: {d:.2f} s, {lufs} LUFS, peak {peak} dB -> {strip}")
    bad = problems(d, lufs, peak) + opening_problems(d, luma(a.video, 0), luma(a.video, min(0.5, d / 2)),
                                                     silences(a.video))
    lay_path = a.layout or re.sub(r"\.[^.]+$", "", a.video) + "_layout.json"
    if os.path.exists(lay_path):
        lay = json.load(open(lay_path))
        print(f"layout: caption_y {lay.get('caption_y')}, hook_y {lay.get('hook_y')} ({lay.get('hook_style')})")
        bad += layout_problems(lay)
    elif a.layout:
        bad.append(f"layout file {a.layout} not found")
    for p in bad:
        print("warning:", p)
    if LIMIT[0] <= d <= LIMIT[1] and not TARGET[0] <= d <= TARGET[1]:
        print(f"note: {d:.1f} s is outside the {TARGET[0]}–{TARGET[1]} s target; say why in the hand-back")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
