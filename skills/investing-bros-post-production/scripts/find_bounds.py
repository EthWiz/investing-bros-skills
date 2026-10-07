#!/usr/bin/env python3
"""Suggest start/end cut points from segments.json. Suggestions only — read the
transcript around them and ask Amitai if anything is ambiguous.

Usage:
    python3 find_bounds.py segments.json [--context 3]

Start: first segment containing an opening phrase (ברוכים הבאים / אחים להשקעות / פרק).
End:   end of the last segment containing a closing phrase (תודה / להתראות / ביי / נתראה / בפרק הבא).
"""
import argparse
import json
import sys

OPEN = ("ברוכים הבאים", "אחים להשקעות", "פרק")
CLOSE = ("להתראות", "ביי", "נתראה", "בפרק הבא", "תודה שהאזנתם", "תודה רבה")


def find_bounds(segments):
    start = next((i for i, s in enumerate(segments) if any(p in s["text"] for p in OPEN)), None)
    end = next((i for i in range(len(segments) - 1, -1, -1)
                if any(p in segments[i]["text"] for p in CLOSE)), None)
    return start, end


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("segments")
    ap.add_argument("--context", type=int, default=3)
    a = ap.parse_args()
    segs = json.load(open(a.segments, encoding="utf-8"))
    si, ei = find_bounds(segs)

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
