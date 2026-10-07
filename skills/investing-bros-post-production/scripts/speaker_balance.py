#!/usr/bin/env python3
"""Check whether the two hosts are at the same level — before and after leveling.

Usage:
    python3 speaker_balance.py AUDIO --a 120:180 --b 300:360 [--a ...] [--b ...]
    python3 speaker_balance.py AUDIO --spread

--a / --b   time ranges (seconds, START:END) where only host A / only host B talks.
            Pick 2–3 ranges per host from the transcript (a monologue each).
--spread    no ranges: report the spread between quiet and loud speech in the
            file (10th vs 90th percentile of 3 s windows that contain speech).
            A spread above ~10 dB on a two-host talk usually means one host is
            much quieter.

Exits 1 when the hosts differ by more than --max-diff dB (default 3), so it can
gate a pipeline. Needs ffmpeg and numpy.
"""
import argparse
import subprocess
import sys

import numpy as np

SR = 16000


def load(path: str) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", path, "-vn", "-ac", "1", "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def rms_db(x: np.ndarray) -> float:
    return float(20 * np.log10(np.sqrt(np.mean(np.square(x, dtype=np.float64))) + 1e-9))


def speech_db(x: np.ndarray, win: float = 0.1, gate_db: float = -45.0) -> float:
    """Level of the speech in x: RMS over 100 ms frames louder than the gate."""
    n = int(win * SR)
    frames = x[: len(x) // n * n].reshape(-1, n)
    levels = 20 * np.log10(np.sqrt((frames.astype(np.float64) ** 2).mean(axis=1)) + 1e-9)
    loud = frames[levels > gate_db]
    return rms_db(loud) if len(loud) else float("-inf")


def parse_range(s: str):
    a, b = s.split(":")
    a, b = float(a), float(b)
    if b <= a:
        raise argparse.ArgumentTypeError(f"bad range {s}")
    return a, b


def level_of(x: np.ndarray, ranges) -> float:
    parts = [x[int(a * SR):int(b * SR)] for a, b in ranges]
    return speech_db(np.concatenate(parts))


def spread(x: np.ndarray, win: float = 3.0):
    n = int(win * SR)
    levels = [speech_db(x[i:i + n]) for i in range(0, len(x) - n, n)]
    levels = np.array([v for v in levels if np.isfinite(v)])
    if len(levels) < 4:
        return float("nan"), float("nan"), float("nan")
    lo, hi = np.percentile(levels, [10, 90])
    return float(lo), float(hi), float(hi - lo)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("--a", type=parse_range, action="append", default=[])
    ap.add_argument("--b", type=parse_range, action="append", default=[])
    ap.add_argument("--spread", action="store_true")
    ap.add_argument("--max-diff", type=float, default=3.0)
    args = ap.parse_args()
    x = load(args.audio)
    if args.spread or not (args.a and args.b):
        lo, hi, d = spread(x)
        print(f"speech level spread: p10 {lo:.1f} dB, p90 {hi:.1f} dB, spread {d:.1f} dB")
        return 0
    la, lb = level_of(x, args.a), level_of(x, args.b)
    diff = abs(la - lb)
    print(f"host A {la:.1f} dB, host B {lb:.1f} dB, difference {diff:.1f} dB")
    if diff > args.max_diff:
        print(f"imbalanced: run level_audio.sh (or raise the quiet host by ~{diff:.0f} dB)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
