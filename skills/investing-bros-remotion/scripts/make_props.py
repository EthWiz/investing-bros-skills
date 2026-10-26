#!/usr/bin/env python3
"""Turn a short's config into props for the Remotion template, and check it first.

Usage:
    python3 make_props.py short.json --base WORK/clean.mp4 -o props.json [--captions captions.json]

short.json is the investing-bros-shorts config (all times on the OUTPUT timeline):
  meta {episode}, hook {start, end, top_line, bottom_line},
  tags [[start, end, name]], captions [{start, end, text, highlight}],
  cards (or the older key hyperframes) [{id, mode: inset|full|card (or panel), start, end,
         steps: [{at, visual, title, subtitle, value}]}], cta_overlay {start, end, text}.
The base video's length comes from ffprobe (or --base-duration). --captions takes the
word-timed captions from make_captions.py in place of the config's.

Refuses: an unknown icon, emoji on a card, a card over the hook (first 3 s) or the CTA,
overlapping cards, steps outside their card, a card subtitle that repeats the captions
under it, captions over 4 words, out of order or past the end of the video, word times
outside their caption, and a CTA that stops before the end (there is no end card).
Card words must be the hosts' own words: that part is on you.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Must match ICONS in template/src/components/icons.tsx (a test checks it).
ICONS = ("house", "house_lock", "drop", "rise", "bars_up", "bars_down", "pie", "chip")
VALUE_ICONS = ("drop", "rise", "pie")
LEGACY_VISUALS = {"clock": "pie"}           # build_amitai_short.py names that map to a Remotion icon
MODES = ("inset", "full", "card")
DEFAULT_MODE = "inset"
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿️‍]")


def probe_duration(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def card_problems(cards, hook, cta, duration):
    errs, last_end = [], -1.0
    for c in sorted(cards, key=lambda c: c["start"]):
        cid = c["id"]
        if c["mode"] not in MODES:
            errs.append(f"card {cid}: mode {c['mode']!r} is not one of {', '.join(MODES)}")
        if not 0 <= c["start"] < c["end"] <= duration:
            errs.append(f"card {cid}: {c['start']}-{c['end']} must sit inside the video (0-{duration:.2f})")
        if c["start"] < hook["end"]:
            errs.append(f"card {cid}: starts at {c['start']} inside the hook (until {hook['end']})")
        if c["end"] > cta["start"] and c["start"] < cta["end"]:
            errs.append(f"card {cid}: overlaps the CTA ({cta['start']}-{cta['end']})")
        if c["start"] < last_end:
            errs.append(f"card {cid}: overlaps the previous card")
        last_end = max(last_end, c["end"])
        if not c["steps"]:
            errs.append(f"card {cid}: no steps")
        prev = None
        for s in c["steps"]:
            if not c["start"] - 1e-6 <= s["at"] < c["end"]:
                errs.append(f"card {cid}: step at {s['at']} is outside the card")
            if prev is not None and s["at"] <= prev:
                errs.append(f"card {cid}: steps must be in time order")
            prev = s["at"]
            if s["visual"] not in ICONS:
                errs.append(f"card {cid}: unknown icon {s['visual']!r}; available: {', '.join(ICONS)}")
            if s["visual"] in VALUE_ICONS and not isinstance(s.get("value"), (int, float)):
                errs.append(f"card {cid}: icon {s['visual']!r} needs the number the host said as 'value'")
            for k in ("title", "subtitle"):
                if EMOJI.search(s.get(k) or ""):
                    errs.append(f"card {cid}: emoji in {k} {s[k]!r}")
            if not s.get("title"):
                errs.append(f"card {cid}: step at {s['at']} has no title")
    return errs


def caption_problems(captions, duration, max_words=4):
    errs, prev = [], -1.0
    for c in captions:
        if not 0 <= c["start"] < c["end"] <= duration + 1e-6:
            errs.append(f"caption {c['text']!r}: {c['start']}-{c['end']} outside the video")
        if c["start"] < prev - 1e-6:
            errs.append(f"caption {c['text']!r}: out of order or overlapping")
        prev = c["end"]
        if not 1 <= len(c["text"].split()) <= max_words:
            errs.append(f"caption {c['text']!r}: must be 1-{max_words} words")
        words = c.get("words")
        if words is not None:
            if [w["w"] for w in words] != c["text"].split():
                errs.append(f"caption {c['text']!r}: its words don't match its text")
            last = c["start"] - 1e-6
            for w in words:
                if not (last <= w["start"] < c["end"]):
                    errs.append(f"caption {c['text']!r}: word {w['w']!r} at {w['start']} is out of order or outside the caption")
                last = w["start"]
    return errs


def plain(text: str) -> list:
    return [re.sub(r"[.,?!:;\"'״׳()]", "", w) for w in text.split()]


def repeat_problems(cards, captions):
    """A card subtitle that repeats the words captioned during its step adds nothing."""
    errs = []
    for c in cards:
        for k, s in enumerate(c["steps"]):
            sub = plain(s.get("subtitle") or "")
            if not sub:
                continue
            until = c["steps"][k + 1]["at"] if k + 1 < len(c["steps"]) else c["end"]
            heard = [w for cap in captions if cap["end"] > s["at"] and cap["start"] < until for w in plain(cap["text"])]
            if any(heard[i:i + len(sub)] == sub for i in range(len(heard) - len(sub) + 1)):
                errs.append(f"card {c['id']}: subtitle {s['subtitle']!r} repeats the captions under it; "
                            "leave it empty or say something the picture needs")
    return errs


def build_props(cfg: dict, duration: float) -> dict:
    meta, hook, cta = cfg.get("meta", {}), cfg["hook"], cfg["cta_overlay"]
    cards = []
    for c in cfg.get("cards", cfg.get("hyperframes", [])):
        steps = [{"at": s["at"], "visual": LEGACY_VISUALS.get(s["visual"], s["visual"]), "title": s["title"],
                  "subtitle": s.get("subtitle", ""),
                  **({"value": s.get("value", s.get("pct"))} if s.get("value", s.get("pct")) is not None else {})}
                 for s in c["steps"]]
        cards.append({"id": c["id"], "mode": c.get("mode", c.get("panel", DEFAULT_MODE)),
                      "start": c["start"], "end": c["end"], "steps": steps})
    if not isinstance(meta.get("episode"), int):
        raise ValueError("meta.episode (the number Amitai stated) is required")
    max_words = {"build": 4, "punch": 6}.get(cfg.get("caption_style"), 8)
    errs = (card_problems(cards, hook, cta, duration) + caption_problems(cfg["captions"], duration, max_words)
            + repeat_problems(cards, cfg["captions"]))
    if cfg.get("caption_highlight", "spoken") not in ("keywords", "spoken"):
        errs.append("caption_highlight must be 'keywords' or 'spoken'")
    if cfg.get("caption_style", "line") not in ("build", "line", "punch"):
        errs.append("caption_style must be 'build', 'line' or 'punch'")
    if not 0 <= cta["start"] < cta["end"] <= duration + 1e-6:
        errs.append(f"CTA {cta['start']}-{cta['end']} outside the video")
    elif cta["end"] < duration - 0.35:
        errs.append(f"CTA ends at {cta['end']} but the video runs to {duration:.2f}; there is no end card, "
                    "so the CTA stays to the last frame")
    if errs:
        raise ValueError("\n".join(errs))
    return {
        "base": "base.mp4", "baseDuration": round(duration, 3), "episode": meta["episode"],
        "hook": {"start": hook["start"], "end": hook["end"], "top": hook["top_line"], "bottom": hook["bottom_line"]},
        "tags": cfg.get("tags") or [[0.0, duration, meta.get("speaker", "")]],
        "captions": [{"start": c["start"], "end": c["end"], "text": c["text"], "highlight": c.get("highlight", []),
                      **({"words": c["words"]} if c.get("words") else {})} for c in cfg["captions"]],
        "captionHighlight": cfg.get("caption_highlight", "spoken"),
        "captionStyle": cfg.get("caption_style", "line"),
        "cards": cards,
        "cta": {"start": cta["start"], "end": cta["end"], "text": cta["text"]},
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--base", help="clean base video from make_base.py (for its length)")
    ap.add_argument("--base-duration", type=float)
    ap.add_argument("--captions", help="word-timed captions from make_captions.py (replace the config's)")
    ap.add_argument("-o", "--output", required=True)
    a = ap.parse_args(argv)
    if a.base_duration is None and not a.base:
        ap.error("give --base or --base-duration")
    cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))
    if a.captions:
        cfg["captions"] = json.loads(Path(a.captions).read_text(encoding="utf-8"))
    duration = a.base_duration if a.base_duration is not None else probe_duration(a.base)
    try:
        props = build_props(cfg, duration)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    Path(a.output).write_text(json.dumps(props, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{a.output}: {len(props['cards'])} card(s), {len(props['captions'])} captions, "
          f"{props['baseDuration']:.2f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
