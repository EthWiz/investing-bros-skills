#!/usr/bin/env python3
"""Suggest start/end cut points from segments.json. Suggestions only — read the
transcript around them and ask Amitai if anything is ambiguous.

Usage:
    python3 find_bounds.py segments.json [--context 3]

Start: first segment containing an opening phrase (ברוכים הבאים / אחים להשקעות / פרק).
End:   end of the last segment containing a closing phrase (תודה / להתראות / ביי / נתראה / בפרק הבא)
       that is near the end of the recording (last --end-window seconds, default 20%
       of the length, at least 120 s). A weak word on its own (ביי) also needs a
       pause after it of --min-silence seconds or to be the last speech: episode 8's
       courier phone call had a "ביי" mid-episode that used to win.
"""
import argparse
import json
import sys

OPEN = ("ברוכים הבאים", "אחים להשקעות", "פרק")
STRONG_CLOSE = ("להתראות", "נתראה", "בפרק הבא", "תודה שהאזנתם", "תודה רבה")
WEAK_CLOSE = ("ביי",)
CLOSE = STRONG_CLOSE + WEAK_CLOSE


def find_bounds(segments, end_window=None, min_silence=2.0):
    start = next((i for i, s in enumerate(segments) if any(p in s["text"] for p in OPEN)), None)
    if not segments:
        return start, None
    total = segments[-1]["end"]
    window = end_window if end_window is not None else max(120.0, 0.2 * total)
    cutoff = total - window
    end = None
    for i in range(len(segments) - 1, -1, -1):
        seg = segments[i]
        if seg["end"] < cutoff:
            break
        text = seg["text"]
        if any(p in text for p in STRONG_CLOSE):
            end = i
            break
        if any(p in text for p in WEAK_CLOSE):
            gap = segments[i + 1]["start"] - seg["end"] if i + 1 < len(segments) else float("inf")
            if gap >= min_silence:
                end = i
                break
    return start, end


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("segments")
    ap.add_argument("--context", type=int, default=3)
    ap.add_argument("--end-window", type=float, help="seconds from the end to look for the outro")
    ap.add_argument("--min-silence", type=float, default=2.0, help="pause needed after a lone ביי")
    a = ap.parse_args()
    segs = json.load(open(a.segments, encoding="utf-8"))
    si, ei = find_bounds(segs, a.end_window, a.min_silence)

    def show(idx, label):
        if idx is None:
            print(f"{label}: no match — pick manually")
            return
        lo, hi = max(0, idx - a.context), min(len(segs), idx + a.context + 1)
        for j in range(lo, hi):
            mark = ">>" if j == idx else "  "
            print(f"{mark} {segs[j]['start']:8.2f}-{segs[j]['end']:8.2f}  {segs[j]['text']}")
        print()

    show(si, "start")
    show(ei, "end")
    print(f"suggested START={segs[si]['start'] if si is not None else '?'}  "
          f"END={segs[ei]['end'] if ei is not None else '?'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
