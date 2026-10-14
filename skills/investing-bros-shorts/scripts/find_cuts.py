#!/usr/bin/env python3
"""Snap proposed cut points to the quietest moment nearby (between words).

Usage:
    python3 find_cuts.py AUDIO.wav --offset 2065 --at 2106.0 2154.4 [--window 0.3]

AUDIO is mono 16 kHz WAV of a window of the episode (ffmpeg -ac 1 -ar 16000);
--offset is the window's start on the source timeline. Prints, per proposed time,
the quietest 20 ms point within +-window and the quiet run around it. Cut inside
the quiet run; if its RMS is high (continuous speech), move the cut.
"""
import argparse
import wave

import numpy as np


def load(path):
    w = wave.open(path)
    return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32), w.getframerate()


def snap(x, sr, offset, t, window=0.3):
    fr = int(0.02 * sr)
    e = np.sqrt(np.convolve(x ** 2, np.ones(fr) / fr, "same"))
    i0, i1 = max(0, int((t - window - offset) * sr)), min(len(e), int((t + window - offset) * sr))
    seg = e[i0:i1]
    j = int(np.argmin(seg))
    q = seg < max(seg.min() * 3, 150)
    lo = hi = j
    while lo > 0 and q[lo - 1]:
        lo -= 1
    while hi < len(q) - 1 and q[hi + 1]:
        hi += 1
    to_t = lambda k: round((i0 + k) / sr + offset, 3)
    return {"at": t, "cut": to_t(j), "quiet": [to_t(lo), to_t(hi)], "rms": int(seg[j]), "speech": int(seg.max())}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio"); ap.add_argument("--offset", type=float, default=0.0)
    ap.add_argument("--at", type=float, nargs="+", required=True); ap.add_argument("--window", type=float, default=0.3)
    a = ap.parse_args()
    x, sr = load(a.audio)
    for t in a.at:
        r = snap(x, sr, a.offset, t, a.window)
        flag = "" if r["rms"] < 200 else "  <- no real pause here, move the cut"
        print(f"{t:.2f} -> cut {r['cut']:.3f}  quiet {r['quiet'][0]:.2f}-{r['quiet'][1]:.2f}  rms {r['rms']}{flag}")


if __name__ == "__main__":
    main()
