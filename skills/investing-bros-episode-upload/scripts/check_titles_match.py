#!/usr/bin/env python3
"""Check the RedCircle title is the YouTube title plus only the RTL marks.

Usage:
    python3 check_titles_match.py YOUTUBE_TITLE REDCIRCLE_TITLE
    (each argument is a file holding one line, or the title text itself)

The RedCircle copy must be exactly rtl_fix.py --title applied to the YouTube
title; stripping the direction marks from both must give the same text.
Exit 0 when they match, 1 with a diff-style message when they don't.
"""
import sys
from pathlib import Path

MARKS = "\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"


def _read(arg: str) -> str:
    p = Path(arg)
    try:
        if p.is_file():
            return p.read_text(encoding="utf-8")
    except OSError:
        pass
    return arg


def normalize(title: str) -> str:
    return " ".join(title.translate({ord(c): None for c in MARKS}).split())


def check(youtube: str, redcircle: str) -> list[str]:
    errors = []
    yt, rc = normalize(youtube), normalize(redcircle)
    if any(c in youtube for c in MARKS):
        errors.append("YouTube title contains RTL marks; paste it plain")
    if yt != rc:
        errors.append(f"titles differ:\n  YouTube:   {yt}\n  RedCircle: {rc}")
    return errors


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    errors = check(_read(sys.argv[1]), _read(sys.argv[2]))
    for e in errors:
        print("error:", e)
    if not errors:
        print("ok: RedCircle and YouTube titles match")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
