#!/usr/bin/env python3
"""Rank short candidates: your scores for each moment plus what the transcript can measure.

Usage:
    python3 score_moments.py segments.json candidates.json [--top 5]

candidates.json (times on the RAW timeline, same as segments.json):
[
  {"start": 2106.0, "end": 2148.5, "title": "אסטרואיד שמכפיל את הזהב",
   "shape": "surprising fact", "part": "deep dive",
   "scores": {"hook": 5, "standalone": 4, "payoff": 4, "friction": 2}}
]
scores (1-5, see references/moment-scoring.md):
  hook        the first sentence alone makes you stay: a number, a claim against intuition, a question, stakes
  standalone  makes sense with no episode context
  payoff      one idea that resolves in a line you can end on
  friction    the brothers push back, disagree or surprise each other

The script adds, from the transcript:
  pace        words per second against the episode's median (a rough energy proxy), scored 1-5
  length      flags candidates outside the 20-45 s target
  opener      flags a first sentence that starts on filler ("אז", "כן", "אוקיי"...)
and prints a markdown table, best first, to paste for Amitai.
"""
import argparse
import json
import statistics
import sys

FILLERS = ("אז", "כן", "אוקיי", "אוקי", "טוב", "בקיצור", "רגע", "אה", "אממ", "יאללה", "נו")
RUBRIC = ("hook", "standalone", "payoff", "friction")
TARGET = (20, 45)


def words(text):
    return [w for w in text.replace("|", " ").split() if any(c.isalnum() for c in w)]


def rate(segments, start, end):
    """Words per second of the transcript inside [start, end] (segments counted by overlap)."""
    n = 0.0
    for s in segments:
        a, b = max(s["start"], start), min(s["end"], end)
        if b > a and s["end"] > s["start"]:
            n += len(words(s["text"])) * (b - a) / (s["end"] - s["start"])
    return n / (end - start) if end > start else 0.0


def episode_rate(segments):
    rates = [len(words(s["text"])) / (s["end"] - s["start"]) for s in segments if s["end"] - s["start"] >= 2]
    return statistics.median(rates) if rates else 0.0


def pace_score(ratio):
    for limit, score in ((0.85, 1), (0.95, 2), (1.05, 3), (1.15, 4)):
        if ratio < limit:
            return score
    return 5


def opening_line(segments, start):
    for s in segments:
        if s["end"] > start + 0.2:
            return s["text"].strip()
    return ""


def starts_on_filler(line):
    w = words(line)
    return bool(w) and w[0].strip(",.?!…") in FILLERS


def rank(segments, candidates):
    median = episode_rate(segments)
    rows = []
    for c in candidates:
        start, end = float(c["start"]), float(c["end"])
        sc = c.get("scores", {})
        missing = [k for k in RUBRIC if k not in sc]
        if missing:
            raise ValueError(f"{c.get('title', start)}: missing scores {missing}")
        ratio = rate(segments, start, end) / median if median else 1.0
        pace = pace_score(ratio)
        line = opening_line(segments, start)
        flags = []
        if not TARGET[0] <= end - start <= TARGET[1]:
            flags.append(f"{end - start:.0f} s")
        if starts_on_filler(line):
            flags.append("filler opener")
        total = sum(int(sc[k]) for k in RUBRIC) + pace
        rows.append({**c, "pace": pace, "pace_ratio": round(ratio, 2), "opening": line,
                     "flags": flags, "total": total})
    rows.sort(key=lambda r: (-r["total"], -r["scores"]["hook"]))
    return rows


def clock(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def table(rows):
    head = "| # | start–end | title | shape / part | hook | stand | payoff | friction | pace | total | opening line | flags |"
    out = [head, "|" + "---|" * 12]
    for i, r in enumerate(rows, 1):
        s = r["scores"]
        out.append(f"| {i} | {clock(r['start'])}–{clock(r['end'])} | {r.get('title', '')} | "
                   f"{r.get('shape', '')} / {r.get('part', '')} | {s['hook']} | {s['standalone']} | {s['payoff']} | "
                   f"{s['friction']} | {r['pace']} ({r['pace_ratio']}×) | **{r['total']}** | {r['opening'][:60]} | "
                   f"{', '.join(r['flags'])} |")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("segments"); ap.add_argument("candidates"); ap.add_argument("--top", type=int, default=0)
    a = ap.parse_args()
    segments = json.load(open(a.segments, encoding="utf-8"))
    rows = rank(segments, json.load(open(a.candidates, encoding="utf-8")))
    print(table(rows[:a.top] if a.top else rows))
    deep = sum(1 for r in rows[:a.top or 5] if "deep" in str(r.get("part", "")).lower())
    if deep < 2:
        print(f"\nnote: {deep} of the top picks come from the deep dive; aim for 2 (they sell the episode)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
