#!/usr/bin/env python3
"""List long silences in the episode, with the transcript around each, to build
the cut list Nadav approves before the trim (investing-bros-post-production).

Suggestions only: a pause can be a thinking beat that belongs in the episode.

Usage:
    python3 find_gaps.py AUDIO [--segments segments.json] [--min-gap 2.5]
                               [--threshold -45] [--start S --end E] [--json gaps.json]

AUDIO is the leveled episode (episode-leveled.wav) or the raw master; times are on
the RAW timeline, the same as segments.json and trim.sh. --start/--end limit the
report to the part that will be kept (the cut points from find_bounds.py).
"""
import argparse
import json
import subprocess
import sys

import numpy as np

SR = 16000
FRAME = 0.05  # seconds


def frame_db(samples: np.ndarray, sr: int = SR, frame: float = FRAME) -> np.ndarray:
    n = int(sr * frame)
    usable = len(samples) // n * n
    if usable == 0:
        return np.array([])
    x = samples[:usable].astype(np.float64).reshape(-1, n)
    rms = np.sqrt(np.mean(x * x, axis=1))
    return 20 * np.log10(np.maximum(rms, 1e-10))


def find_gaps(db: np.ndarray, threshold: float, min_gap: float, frame: float = FRAME) -> list:
    """Runs of frames below threshold lasting at least min_gap seconds -> [(start, end)]."""
    gaps, start = [], None
    quiet = list(db < threshold) + [False]
    for i, q in enumerate(quiet):
        if q and start is None:
            start = i
        elif not q and start is not None:
            if (i - start) * frame >= min_gap:
                gaps.append((round(start * frame, 2), round(i * frame, 2)))
            start = None
    return gaps


def context(segments: list, t0: float, t1: float):
    before = next((s for s in reversed(segments) if s["end"] <= t0 + 0.5), None)
    after = next((s for s in segments if s["start"] >= t1 - 0.5), None)
    return (before or {}).get("text", ""), (after or {}).get("text", "")


def _decode(path: str) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", path, "-ac", "1", "-ar", str(SR),
                          "-f", "f32le", "-"], check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def _fmt(t: float) -> str:
    m, s = divmod(t, 60)
    return f"{int(m)}:{s:05.2f}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("--segments")
    ap.add_argument("--min-gap", type=float, default=2.5, help="seconds of silence to report (default 2.5)")
    ap.add_argument("--threshold", type=float, default=-45.0, help="dBFS counted as silence (default -45)")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--json", help="also write the gaps as JSON")
    a = ap.parse_args(argv)

    db = frame_db(_decode(a.audio))
    segs = json.load(open(a.segments, encoding="utf-8")) if a.segments else []
    gaps = [(s, e) for s, e in find_gaps(db, a.threshold, a.min_gap)
            if e > a.start and (a.end is None or s < a.end)]
    rows = []
    for s, e in gaps:
        b, f = context(segs, s, e)
        rows.append({"start": s, "end": e, "length": round(e - s, 2), "before": b, "after": f})
        print(f"{_fmt(s)}-{_fmt(e)}  {e - s:4.1f} s   ...{b[-40:]}  ||  {f[:40]}...")
    total = sum(r["length"] for r in rows)
    print(f"{len(rows)} gap(s) of {a.min_gap}+ s, {total:.1f} s in all (raw timeline). "
          "Put the ones worth cutting on the cut list for Nadav; don't cut without his OK.")
    if a.json:
        json.dump(rows, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
