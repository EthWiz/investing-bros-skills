#!/usr/bin/env python3
"""Find the time offset between a Riverside per-host track and the combined video.

Usage:
    python3 align_tracks.py COMBINED.mp4 HOST_TRACK.mp4 [--start 300 --length 120]

Prints OFFSET in seconds: combined_time = track_time + OFFSET.
(Episode 8: the composed/combined file ran 0.1666 s behind the raw tracks,
so OFFSET = +0.167.) To take a moment at combined time T from the host's own
track, cut the track at T - OFFSET. Uses audio cross-correlation of the
envelopes (16 kHz mono, 1 ms resolution) over a stretch where that host talks.
"""
import argparse
import subprocess
import sys

import numpy as np

RATE = 16000


def load(path: str, start: float, length: float) -> np.ndarray:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-nostdin", "-ss", str(start), "-t", str(length), "-i", path,
         "-map", "0:a:0", "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"],
        check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def envelope(x: np.ndarray, hop: int = RATE // 1000) -> np.ndarray:
    n = len(x) // hop
    e = np.abs(x[: n * hop]).reshape(n, hop).mean(axis=1)
    return e - e.mean()


def offset_seconds(combined: np.ndarray, track: np.ndarray, rate: int = 1000,
                   max_shift: float = 5.0) -> float:
    """Seconds the combined signal lags the track (positive = combined is later)."""
    n = len(combined) + len(track) - 1
    size = 1 << (n - 1).bit_length()
    corr = np.fft.irfft(np.fft.rfft(combined, size) * np.conj(np.fft.rfft(track, size)), size)
    m = int(max_shift * rate)
    lags = np.concatenate([np.arange(0, m + 1), np.arange(-m, 0)])
    vals = np.concatenate([corr[: m + 1], corr[-m:]])
    return float(lags[int(np.argmax(vals))]) / rate


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("combined")
    ap.add_argument("track")
    ap.add_argument("--start", type=float, default=300.0, help="stretch start (s), same on both files")
    ap.add_argument("--length", type=float, default=120.0)
    ap.add_argument("--max-shift", type=float, default=5.0)
    a = ap.parse_args()
    off = offset_seconds(envelope(load(a.combined, a.start, a.length)),
                         envelope(load(a.track, a.start, a.length)), max_shift=a.max_shift)
    print(f"OFFSET {off:+.3f}  (combined_time = track_time {off:+.3f} s; cut track at T {-off:+.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
