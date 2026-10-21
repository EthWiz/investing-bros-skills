#!/usr/bin/env python3
"""Shift chapter timestamps after sections were cut from the middle of an episode.

Usage:
    python3 shift_after_cut.py DESCRIPTION.txt --cut A-B [--cut A-B ...] > shifted.txt

A and B are seconds (1605.0) or [H:]MM:SS(.ms) on the SAME timeline as the
chapter times in the description (convert raw -> edited first if needed).
Chapter lines start with a timestamp; times after a cut move earlier by the
cut's length; a chapter that starts inside a cut moves to the cut point.
Other lines are kept unchanged. Prints the new description.
"""
import argparse
import re
import sys

_TS = re.compile(r"^(\u200e?)(\d{1,2}:\d{2}(?::\d{2})?)(\b.*)$")


def to_sec(s: str) -> float:
    total = 0.0
    for part in s.split(":"):
        total = total * 60 + float(part)
    return total


def fmt(sec: float, hours: bool) -> str:
    sec = int(round(sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if hours or h else f"{m:02d}:{s:02d}"


def parse_cut(s: str) -> tuple[float, float]:
    a, b = (to_sec(x) for x in s.split("-", 1))
    if b <= a:
        raise argparse.ArgumentTypeError(f"cut end must be after start: {s}")
    return a, b


def shift(t: float, cuts: list[tuple[float, float]]) -> float:
    removed = 0.0
    for a, b in sorted(cuts):
        if t >= b:
            removed += b - a
        elif t > a:
            removed += t - a
    return t - removed


def shift_description(text: str, cuts: list[tuple[float, float]]) -> str:
    out = []
    for line in text.splitlines():
        m = _TS.match(line)
        if m:
            ts = m.group(2)
            line = m.group(1) + fmt(shift(to_sec(ts), cuts), ts.count(":") == 2) + m.group(3)
        out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("description")
    ap.add_argument("--cut", action="append", type=parse_cut, required=True)
    args = ap.parse_args()
    text = open(args.description, encoding="utf-8").read()
    sys.stdout.write(shift_description(text, args.cut))
    return 0


if __name__ == "__main__":
    sys.exit(main())
