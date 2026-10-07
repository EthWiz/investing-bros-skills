#!/usr/bin/env python3
"""Add the direction marks RedCircle needs for Hebrew titles/descriptions.

Usage:
    python3 rtl_fix.py --title FILE         > title-rtl.txt
    python3 rtl_fix.py --description FILE   > description-rtl.txt
    (FILE may be '-' for stdin)

Rules (see references/redcircle-rtl.md):
  title        RLM right after the final '?'
  description  RLM after every '?'; LRM at the start of chapter lines (timestamp first);
               RLM at the end of every other Hebrew line; blank lines kept.
Idempotent: running it on already-marked text changes nothing.
"""
import argparse
import re
import sys

RLM, LRM = "‏", "‎"
_TIMESTAMP = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?\b")
_HEBREW = re.compile(r"[֐-׿]")


def _rlm_after_questions(s: str) -> str:
    return s.replace("?" + RLM, "?").replace("?", "?" + RLM)


def rtl_fix_title(title: str) -> str:
    t = title.strip()
    return t if t.endswith(RLM) else t + RLM


def rtl_fix_description(text: str) -> str:
    out = []
    for line in text.splitlines():
        s = line.rstrip()
        bare = s.lstrip(LRM)
        if _TIMESTAMP.match(bare):
            out.append(LRM + _rlm_after_questions(bare))
            continue
        s = _rlm_after_questions(s)
        if _HEBREW.search(s) and not s.endswith(RLM):
            s += RLM
        out.append(s)
    return "\n".join(out).rstrip("\n") + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--title", metavar="FILE")
    g.add_argument("--description", metavar="FILE")
    a = ap.parse_args()
    path = a.title or a.description
    text = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    sys.stdout.write(rtl_fix_title(text) if a.title else rtl_fix_description(text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
