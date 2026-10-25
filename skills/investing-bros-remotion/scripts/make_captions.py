#!/usr/bin/env python3
"""Word-timed captions for a short: proofread words + whisper timings -> output timeline.

Usage:
    python3 make_captions.py text.json words.json timemap.json -o captions.json \\
        [--wav window.wav --wav-offset T0] [--speed 1.25]

text.json   the proofread words of each kept piece, on the SOURCE timeline (same times as
            make_base.py's K list), keywords in [brackets]:
            [{"from": 1526.88, "to": 1549.87, "text": "אפשר לדוגמה לקנות [נדל\"ן], ..."}]
words.json  transcribe_clip.py output for the same stretch: [{"w", "s", "e"}] (source time)
timemap.json from make_base.py: [[source_start, source_end, output_start], ...]
--wav       optional mono 16 kHz WAV of the window (its start at --wav-offset on the source
            timeline): word starts that whisper put in silence move to where speech begins.

Whisper's words are matched to the proofread words by sequence alignment (Whisper's
spelling may differ); proofread words it missed get times shared out between their
matched neighbours. Words are grouped into captions of 1-4 words, one line (<= 18
characters), breaking at punctuation and pauses. Each caption keeps its words' times, so
the Remotion template shows each word as it is spoken. Output: the `captions` list for
the short's config (output seconds).
"""
import argparse
import json
import re
import sys
from difflib import SequenceMatcher

MAX_WORDS, MAX_CHARS, PAUSE = 4, 18, 0.35
PUNCT = re.compile(r"[.,?!:;״׳\"'()\-–—]")


def norm(w: str) -> str:
    return PUNCT.sub("", w.replace("[", "").replace("]", "")).strip()


def tokens(text: str):
    """Proofread text -> [(word, is_key)]; [key words] may span several words."""
    out, depth = [], 0
    for tok in text.split():
        key = depth > 0 or "[" in tok
        if "[" in tok:
            depth += 1
        if "]" in tok:
            depth = 0
        out.append((tok.replace("[", "").replace("]", ""), key))
    return out


def similarity(a: str, b: str) -> float:
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    if any(c.isdigit() for c in a) or any(c.isdigit() for c in b):
        return 0.6 if (any(c.isdigit() for c in a) != any(c.isdigit() for c in b)) else float(a == b)
    return SequenceMatcher(None, a, b).ratio()


def align(proof, heard, gap=-0.35, floor=0.45):
    """Needleman-Wunsch over words. Returns {proof index: heard index} for good matches."""
    n, m = len(proof), len(heard)
    score = [[0.0] * (m + 1) for _ in range(n + 1)]
    move = [[0] * (m + 1) for _ in range(n + 1)]       # 0 diag, 1 up (skip proof), 2 left (skip heard)
    for i in range(1, n + 1):
        score[i][0], move[i][0] = i * gap, 1
    for j in range(1, m + 1):
        score[0][j], move[0][j] = j * gap, 2
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = similarity(proof[i - 1], heard[j - 1])
            options = (score[i - 1][j - 1] + (s if s >= floor else s - 1), score[i - 1][j] + gap, score[i][j - 1] + gap)
            k = max(range(3), key=lambda x: options[x])
            score[i][j], move[i][j] = options[k], k
    pairs, i, j = {}, n, m
    while i > 0 and j > 0:
        k = move[i][j]
        if k == 0:
            if similarity(proof[i - 1], heard[j - 1]) >= floor:
                pairs[i - 1] = j - 1
            i, j = i - 1, j - 1
        elif k == 1:
            i -= 1
        else:
            j -= 1
    return pairs


def time_words(proof, heard, start, end):
    """Give every proofread word a start and end (source time) within [start, end]."""
    pairs = align([w for w, _ in proof], [h["w"] for h in heard])
    st = [None] * len(proof)
    for i, j in pairs.items():
        st[i] = min(max(heard[j]["s"], start), end)
    known = [i for i, s in enumerate(st) if s is not None]
    anchors = [(-1, start)] + [(i, st[i]) for i in known] + [(len(proof), end)]
    for (i0, t0), (i1, t1) in zip(anchors, anchors[1:]):
        gap_words = list(range(i0 + 1, i1))
        if not gap_words:
            continue
        lo = t0 if i0 < 0 else (heard[pairs[i0]]["e"] if i0 in pairs else t0)
        lo = min(max(lo, t0), t1)
        lens = [len(norm(proof[k][0])) + 1 for k in gap_words]
        acc = 0
        for k, ln in zip(gap_words, lens):
            st[k] = lo + (t1 - lo) * acc / sum(lens)
            acc += ln
    for k in range(1, len(st)):                         # keep order
        st[k] = max(st[k], st[k - 1] + 0.02)
    ends = [st[k + 1] if k + 1 < len(st) else end for k in range(len(st))]
    for i, j in pairs.items():                          # whisper's end when it is earlier (a pause follows)
        ends[i] = min(ends[i], max(heard[j]["e"], st[i] + 0.08))
    return [{"w": w, "key": key, "s": round(s, 3), "e": round(max(e, s + 0.05), 3)}
            for (w, key), s, e in zip(proof, st, ends)]


def snap_to_speech(words, env, rate, offset, quiet):
    """Move a start that sits in silence forward to where the sound begins."""
    for w in words:
        i0 = int((w["s"] - offset) * rate)
        i1 = int((w["e"] - offset) * rate)
        if i0 < 0 or i1 > len(env) or i1 - i0 < 2:
            continue
        if max(env[i0:i0 + max(1, int(0.08 * rate))]) < quiet:
            loud = [k for k in range(i0, i1) if env[k] >= quiet]
            if loud:
                w["s"] = round(min(offset + loud[0] / rate, w["e"] - 0.05), 3)
    return words


def wav_envelope(path, rate=100):
    import wave
    import numpy as np
    with wave.open(path) as f:
        sr = f.getframerate()
        x = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float32)
    hop = sr // rate
    n = len(x) // hop
    env = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1))
    return env.tolist(), float(np.percentile(env, 30) * 1.6)


def to_output(t, timemap, speed):
    for a, b, out in timemap:
        if a - 1e-6 <= t <= b + 1e-6:
            return round(out + (min(max(t, a), b) - a) / speed, 3)
    return None


def chunk(words):
    groups, cur = [], []
    for k, w in enumerate(words):
        if cur:
            text = " ".join(x["w"] for x in cur + [w])
            pause = w["s"] - cur[-1]["e"] > PAUSE
            if len(cur) >= MAX_WORDS or len(text) > MAX_CHARS or pause or re.search(r"[.,?!:;]$", cur[-1]["w"]):
                groups.append(cur)
                cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    return groups


def build(pieces, heard, timemap, speed=1.25, env=None, rate=100, offset=0.0, quiet=0.0):
    captions = []
    for p in pieces:
        hs = [h for h in heard if p["from"] - 0.25 <= h["s"] <= p["to"] + 0.1]
        words = time_words(tokens(p["text"]), hs, p["from"], p["to"])
        if env is not None:
            words = snap_to_speech(words, env, rate, offset, quiet)
        for w in words:
            w["s"], w["e"] = to_output(w["s"], timemap, speed), to_output(w["e"], timemap, speed)
        words = [w for w in words if w["s"] is not None and w["e"] is not None]
        for g in chunk(words):
            captions.append({"start": g[0]["s"], "end": g[-1]["e"], "text": " ".join(w["w"] for w in g),
                             "highlight": [norm(w["w"]) for w in g if w["key"]],
                             "words": [{"w": w["w"], "start": w["s"], "end": w["e"]} for w in g]})
    for c, nxt in zip(captions, captions[1:]):          # hold through short gaps, never overlap
        c["end"] = round(min(max(c["end"], c["words"][-1]["end"] + 0.4), nxt["start"]), 3)
    if captions:
        a, b, out = timemap[-1]
        video_end = out + (b - a) / speed
        captions[-1]["end"] = round(min(captions[-1]["words"][-1]["end"] + 0.4, video_end), 3)
    return captions


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text"); ap.add_argument("words"); ap.add_argument("timemap")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--speed", type=float, default=1.25)
    ap.add_argument("--wav"); ap.add_argument("--wav-offset", type=float, default=0.0)
    a = ap.parse_args(argv)
    load = lambda p: json.load(open(p, encoding="utf-8"))
    env, quiet = (None, 0.0)
    if a.wav:
        env, quiet = wav_envelope(a.wav)
    caps = build(load(a.text), load(a.words), load(a.timemap), a.speed, env, 100, a.wav_offset, quiet)
    json.dump(caps, open(a.output, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{a.output}: {len(caps)} captions, {sum(len(c['words']) for c in caps)} words")
    return 0


if __name__ == "__main__":
    sys.exit(main())
