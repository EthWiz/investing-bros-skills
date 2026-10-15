"""Edit plan: refined words (corrected text), silence cuts, time map, caption chunks."""
import json, wave, numpy as np
SRC = "src.mov"   # set by patch_reel.py
CONTENT_END = 34.84      # fade-to-black + logo end card start here; kept untouched
SRC_END = 38.416
GAP_MIN, PAD, XF = 0.25, 0.08, 0.015

def speech_segments(thr=-42, use_words=False):
    w = wave.open("src48k.wav"); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    hop = 480; n = len(x) // hop
    db = 20 * np.log10(np.sqrt((x[:n*hop].reshape(n, hop) ** 2).mean(1) + 1e-12))
    sp = db > thr; segs = []; i = 0
    while i < n:
        if sp[i]:
            j = i
            while j < n and sp[j]: j += 1
            segs.append([i * .01, j * .01]); i = j
        else: i += 1
    m = []
    for s in segs:
        if m and s[0] - m[-1][1] < 0.06: m[-1][1] = s[1]
        else: m.append(s)
    m = [s for s in m if s[1] - s[0] > 0.08 and s[0] < CONTENT_END]
    if not use_words: return m
    asr = [w for s in json.load(open("asr_ivrit_turbo.json")) for w in s["words"]]
    # keep only energy segments that overlap a recognised word (drops breaths / non-word filler sounds)
    return [s for s in m if any(w["end"] > s[0] + 0.05 and w["start"] < s[1] - 0.05 for w in asr)]

import os as _o
FIX = json.load(open('fix.json')) if _o.path.exists('fix.json') else {}   # {"heard": "correct"}
def words():
    asr = json.load(open("asr_ivrit_turbo.json"))
    ws = [dict(w) for s in asr for w in s["words"]]
    out = []
    i = 0
    while i < len(ws):
        w = ws[i]; t = w["word"]
        t = FIX.get(t, t)
        out.append({"start": w["start"], "end": w["end"], "word": t}); i += 1
    # snap word edges to detected speech (ASR word spans often swallow pauses)
    segs = speech_segments()
    for w in out:
        ov = [s for s in segs if s[1] > w["start"] and s[0] < w["end"]]
        if ov:
            w["start"] = max(w["start"], ov[0][0] - 0.03)
            w["end"] = min(w["end"], ov[-1][1] + 0.03)
    return out

def cuts():
    segs = speech_segments(); cs = []
    prev = 0.0
    for s in segs + [[CONTENT_END, CONTENT_END]]:
        gap = s[0] - prev
        if gap > GAP_MIN and prev > 0:
            cs.append((round(prev + PAD, 3), round(s[0] - PAD, 3)))
        prev = max(prev, s[1])
    return [c for c in cs if c[1] < CONTENT_END - 0.05]

def keeps():
    ks = []; t = 0.0
    for a, b in cuts():
        ks.append((t, a)); t = b
    ks.append((t, CONTENT_END))
    return ks

def timemap():
    """list of (src_start, src_end, out_start) — audio overlaps XF at each cut."""
    out = []; o = 0.0
    for k, (a, b) in enumerate(keeps()):
        out.append((a, b, o)); o += (b - a) - XF
    o += XF
    return out, o   # o = content duration in output

def src2out(t):
    tm, _ = timemap()
    for a, b, o in tm:
        if t <= b: return o + max(0.0, t - a)
    return tm[-1][2] + tm[-1][1] - tm[-1][0]

def idx_next_is_break(ws, w):
    i = ws.index(w)
    return i + 1 < len(ws) and ws[i+1]["word"] in ("בוא", "אם", "זה") and i > 0

def chunks():
    ws = words(); ch = []; cur = []
    for w in ws:
        cur.append(w)
        long_ = sum(len(x["word"]) for x in cur) > 13
        punct = w["word"].endswith((".", ","))
        if idx_next_is_break(ws, w): punct = True
        nxt_gap = False
        idx = ws.index(w)
        if idx + 1 < len(ws): nxt_gap = ws[idx+1]["start"] - w["end"] > 0.3
        if len(cur) >= 3 or long_ or punct or nxt_gap:
            ch.append(cur); cur = []
    if cur: ch.append(cur)
    res = []
    for c in ch:
        res.append({"words": [{"word": w["word"].rstrip(".,"), "s": round(src2out(w["start"]), 3), "e": round(src2out(w["end"]), 3),
                               "src_s": round(w["start"], 3), "src_e": round(w["end"], 3)} for w in c]})
    for i, c in enumerate(res):
        c["s"] = c["words"][0]["s"]
        nxt = res[i+1]["words"][0]["s"] if i + 1 < len(res) else c["words"][-1]["e"] + 0.4
        c["e"] = min(nxt, c["words"][-1]["e"] + 0.35)
    return res

if __name__ == "__main__":
    print("cuts:", cuts()); tm, d = timemap()
    print("removed", round(sum(b - a for a, b in cuts()), 2), "content out dur", round(d, 2), "n cuts", len(cuts()))
    for c in chunks(): print(round(c["s"], 2), round(c["e"], 2), " ".join(w["word"] for w in c["words"]))
