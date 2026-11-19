#!/usr/bin/env python3
"""Find references to past episodes in a transcript and propose YouTube info cards.

Usage:
  find_past_episode_refs.py SEGMENTS_JSON --episode N --index EPISODE_INDEX_JSON
      [--edit EDIT_JSON] [--offset SECONDS] [--out CARDS_JSON]

Detection:
  * by number: "פרק 8", "בפרק שמונה", "episode 8" (digits or Hebrew number words)
  * by topic: a back-reference cue ("דיברנו", "בפרק", "talked about", ...) in the same
    segment as a topic keyword from the index, for an episode < N.
Pick: one card per referenced episode at its first strong mention; rank by
(number references first, then mention count); max 4. Transcript times are in
raw-master time. Pass --edit extras/edit.json so start and cuts are mapped with
edit_map.py, then --offset for the teaser + intro on the delivered video.
Without --edit, only --offset is added, which is wrong when the edit has cuts
(episode 12 first computed 16:40 instead of 13:28). Check times by ear before
Studio. Candidates are a proposal: a human/agent reads every quote before
adding cards.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import edit_map as em

MAX_CARDS = 4
HEB_NUM = {"אחד": 1, "אחת": 1, "שתיים": 2, "שניים": 2, "שני": 2, "שלוש": 3, "שלושה": 3, "ארבע": 4,
           "ארבעה": 4, "חמש": 5, "חמישה": 5, "שש": 6, "שישה": 6, "שבע": 7, "שבעה": 7, "שמונה": 8,
           "תשע": 9, "תשעה": 9, "עשר": 10, "עשרה": 10, "אחת עשרה": 11, "שתים עשרה": 12}
NUM_RE = re.compile(r"(?:ב|ה|של |מ)?(?:פרק|episode)\s+(\d{1,3}|" + "|".join(sorted(HEB_NUM, key=len, reverse=True)) + r")\b", re.I)
CUE_RE = re.compile(r"דיברנו|דברנו|סיפרנו|בפרק|בפרקים|הפרק על|הפרק של|נגעתי|נגענו|talked about|we covered|episode", re.I)


def _num(tok):
    return int(tok) if tok.isdigit() else HEB_NUM.get(tok)


def load_edit(path):
    """Return (start, end, cuts) from an edit.json (raw seconds)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    start = em.to_sec(data["start"])
    end = em.to_sec(data["end"])
    cuts = [[em.to_sec(a), em.to_sec(b)] for a, b in (data.get("cuts") or [])]
    return start, end, cuts


def video_time(raw_start, offset=0.0, edit=None):
    """Map a raw transcript time to delivered-video seconds, or None if cut/outside."""
    if edit is None:
        return raw_start + offset
    start, end, cuts = edit
    edited = em.raw_to_edited(raw_start, start, end, cuts)
    if edited is None:
        return None
    return edited + offset


def find(segments, episode, index):
    eps = {e["episode"]: e for e in index["episodes"]}
    hits = {}
    for s in segments:
        text = s["text"]
        found = []
        for m in NUM_RE.finditer(text):
            n = _num(m.group(1))
            if n and n < episode and n in eps:
                found.append((n, "number"))
        if not found and CUE_RE.search(text):
            for n, e in eps.items():
                if n < episode and any(k.lower() in text.lower() for k in e.get("topics", [])):
                    found.append((n, "topic"))
        for n, how in found:
            h = hits.setdefault(n, {"episode": n, "how": how, "count": 0, "first": s, "mentions": []})
            h["count"] += 1
            h["mentions"].append(s)
            if how == "number" and h["how"] == "topic":
                h.update(how="number", first=s)
    return hits


def pick(hits, index, offset=0.0, edit=None):
    eps = {e["episode"]: e for e in index["episodes"]}
    ranked = sorted(hits.values(), key=lambda h: (h["how"] != "number", -h["count"], h["first"]["start"]))
    cards = []
    for h in ranked[:MAX_CARDS]:
        e = eps[h["episode"]]
        vid = e.get("youtube_id")
        t = None
        quote_seg = h["first"]
        for s in h.get("mentions") or [h["first"]]:
            t = video_time(s["start"], offset, edit)
            if t is not None:
                quote_seg = s
                break
        if t is None:
            continue
        cards.append({"v5_timestamp": round(t, 2), "quote": quote_seg["text"],
                      "referenced_episode": h["episode"], "youtube_video_id": vid,
                      "url": f"https://youtu.be/{vid}" if vid else None,
                      "card_teaser_text": e["title"], "detection": f"{h['how']} x{h['count']}"})
    return sorted(cards, key=lambda c: c["v5_timestamp"])


def validate(cards, index):
    """Return a list of problems with a cards file (empty = OK)."""
    ids = {e["youtube_id"] for e in index["episodes"] if e.get("youtube_id")}
    errs = []
    if not isinstance(cards, list):
        return ["cards file must be a JSON list"]
    if len(cards) > MAX_CARDS:
        errs.append(f"{len(cards)} cards > max {MAX_CARDS}")
    seen = set()
    for c in cards:
        ep = c.get("referenced_episode")
        if ep in seen:
            errs.append(f"episode {ep} carded twice")
        seen.add(ep)
        if c.get("youtube_video_id") not in ids:
            errs.append(f"episode {ep}: video id {c.get('youtube_video_id')} not in episode index")
        if not c.get("quote") or c.get("v5_timestamp") is None:
            errs.append(f"episode {ep}: missing quote or timestamp")
    return errs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("segments")
    ap.add_argument("--episode", type=int, required=True)
    ap.add_argument("--index", required=True)
    ap.add_argument("--edit", help="edit.json (start, end, cuts) so raw times map through cuts")
    ap.add_argument("--offset", type=float, default=0.0)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    segs = json.load(open(a.segments, encoding="utf-8"))
    segs = segs.get("segments", segs) if isinstance(segs, dict) else segs
    index = json.load(open(a.index, encoding="utf-8"))
    edit = load_edit(a.edit) if a.edit else None
    cards = pick(find(segs, a.episode, index), index, a.offset, edit)
    txt = json.dumps(cards, ensure_ascii=False, indent=1)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(txt)
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
