#!/usr/bin/env python3
"""Give each word of the proofread captions a time, using whisper's word timings.

Usage:
    python3 align_words.py short.json words.json -o aligned.json

short.json "cards": [[start, end, "text|line2 with [key words]"], ...] (source time).
words.json: from transcribe_clip.py. Per card: if whisper found the same number of
words, its start times are used; otherwise the card's span is shared out by word
length. Output: list of chunks (2-3 words, <=16 characters, never across cards),
each a list of {"w","s","e","key"} — the input for build_fullbleed.py's word-by-word
captions. Punctuation-only tokens ("—") stick to the previous word.
"""
import argparse
import json
import math
import re


def align(cards, words):
    out = []
    for s, e, t in cards:
        toks = []
        for x in [x for x in re.split(r"[ |]+", t) if x]:
            if not re.search(r"\w", x) and toks:
                toks[-1] += "" if x == "—" else " " + x
            else:
                toks.append(x)
        ws = [w for w in words if s - 0.15 <= w["s"] <= e + 0.1]
        if len(ws) == len(toks):
            st = [max(w["s"], s) for w in ws]
            st[0] = s
        else:
            b = min(e, ws[-1]["e"]) if ws else e
            L = [len(x.strip("[],.?—")) + 1 for x in toks]
            tot, acc, st = sum(L), 0, []
            for n in L:
                st.append(s + (b - s) * acc / tot)
                acc += n
        depth, card = 0, []
        for i, tok in enumerate(toks):
            key = depth > 0 or "[" in tok
            if "[" in tok:
                depth += 1
            if "]" in tok:
                depth = 0
            card.append({"w": tok.replace("[", "").replace("]", ""), "s": round(st[i], 3),
                         "e": round(st[i + 1] if i + 1 < len(toks) else e, 3), "key": key})
        k = max(1, math.ceil(sum(len(w["w"]) + 1 for w in card) / 16))
        n, i = len(card), 0
        for sz in [n // k + (1 if j < n % k else 0) for j in range(k)]:
            if sz:
                out.append(card[i:i + sz])
            i += sz
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("short"); ap.add_argument("words"); ap.add_argument("-o", "--out", default="aligned.json")
    a = ap.parse_args()
    chunks = align(json.load(open(a.short, encoding="utf-8"))["cards"], json.load(open(a.words, encoding="utf-8")))
    json.dump(chunks, open(a.out, "w"), ensure_ascii=False)
    print(f"{a.out}: {len(chunks)} chunks")


if __name__ == "__main__":
    main()
