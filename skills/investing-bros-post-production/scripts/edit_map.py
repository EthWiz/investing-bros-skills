#!/usr/bin/env python3
"""Map raw-recording time to edited-episode time, using edit.json from trim.sh.

edit.json: {"start": s, "end": e, "cuts": [[a, b], ...], ...}  (raw seconds; "cuts" optional)
The edited episode is raw [start, end] with every cut [a, b] removed.

Usage:
    python3 edit_map.py edit.json --keep            # kept raw ranges, one "a b" per line
    python3 edit_map.py edit.json --raw 754.2 1310  # edited time for each raw time (MM:SS and seconds)
    python3 edit_map.py --check START END --cut A-B [--cut A-B ...]   # validate, print kept ranges

Shared by investing-bros-post-production, -title-description, -video and -shorts
(identical copies; edit them together).
"""
import argparse
import json
import sys


def to_sec(v) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    s = 0.0
    for part in str(v).strip().split(":"):
        s = s * 60 + float(part)
    return s


def parse_cut(text: str):
    """'A-B' with A, B in seconds or [HH:]MM:SS(.ms)."""
    a, sep, b = text.partition("-")
    if not sep or not a or not b:
        raise ValueError(f"cut '{text}' must be START-END")
    return to_sec(a), to_sec(b)


def normalise(start: float, end: float, cuts) -> list:
    """Validate cuts against [start, end]; return them sorted. Raises ValueError."""
    if end <= start:
        raise ValueError("end must be after start")
    out = sorted((float(a), float(b)) for a, b in cuts or [])
    prev = start
    for a, b in out:
        if b <= a:
            raise ValueError(f"cut {a}-{b}: end must be after start")
        if a <= start or b >= end:
            raise ValueError(f"cut {a}-{b} must lie inside the episode ({start}-{end}); "
                             "move the start or end instead")
        if a < prev:
            raise ValueError(f"cut {a}-{b} overlaps the previous cut")
        prev = b
    return [[a, b] for a, b in out]


def keep_ranges(start: float, end: float, cuts) -> list:
    ranges, cur = [], start
    for a, b in normalise(start, end, cuts):
        ranges.append([cur, a])
        cur = b
    ranges.append([cur, end])
    return ranges


def raw_to_edited(t: float, start: float, end: float, cuts):
    """Edited time for raw time t, or None if t falls before start, after end or inside a cut."""
    if t < start or t > end:
        return None
    edited = t - start
    for a, b in normalise(start, end, cuts):
        if t >= b:
            edited -= b - a
        elif t > a:
            return None
    return edited


def mmss(t: float) -> str:
    t = int(t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("edit", nargs="?", help="edit.json")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--raw", nargs="+", help="raw times to map")
    ap.add_argument("--check", nargs=2, metavar=("START", "END"))
    ap.add_argument("--cut", action="append", default=[], help="START-END, repeatable (with --check)")
    a = ap.parse_args(argv)
    try:
        if a.check:
            start, end = to_sec(a.check[0]), to_sec(a.check[1])
            cuts = [parse_cut(c) for c in a.cut]
        else:
            if not a.edit:
                ap.error("give edit.json, or --check START END")
            e = json.load(open(a.edit, encoding="utf-8"))
            start, end, cuts = float(e["start"]), float(e["end"]), e.get("cuts", [])
        ranges = keep_ranges(start, end, cuts)
    except (ValueError, KeyError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    if a.raw:
        for r in a.raw:
            t = raw_to_edited(to_sec(r), start, end, cuts)
            print(f"{r}\t" + ("cut" if t is None else f"{mmss(t)}\t{t:.2f}"))
    elif a.check or a.keep:
        for x, y in ranges:
            print(f"{x:.3f} {y:.3f}")
    else:
        ap.error("give --keep, --raw or --check")
    return 0


if __name__ == "__main__":
    sys.exit(main())
