#!/usr/bin/env python3
"""Props for a crypto-course lesson video (the "Lesson" composition): captions, layout, graphic anchors.

Usage:
    python3 make_lesson_props.py lesson-N-video.json --words-dir WORDS -o props.json [--srt captions.srt]

lesson-N-video.json (the lesson's config, investing-bros-crypto-course -> references/lessons/):
  lesson, title (lines), parts, part_starts (the beat each part starts on, null if not recorded yet),
  disclaimer_beat, takes [{beat, file, from, to}] (same trims as make_lesson_base.py),
  proofread {beat: what Amitai said in the take}, anchors {key: spec}, segments [{at: spec, mode, zoom?, scene?}].
WORDS holds one whisper file per take, קטע-NN.json (NN = beat): the whisper CLI's --output_format json
  (segments with word timings) or transcribe_clip.py's [{"w", "s", "e"}], in seconds of the take.

An anchor spec says when something starts, always from a spoken word:
  [beat, "phrase"]          when the phrase's first word is said (exact proofread words, punctuation ignored)
  [beat, "phrase", offset]  the same plus offset seconds
  [beat, null, offset]      the beat's start plus offset
  {"beat_end": n, "offset": x}
Every graphic is anchored this way, so re-timing one is a one-line change in the config.

Captions are the proofread words on whisper's timings (make_captions.py's alignment), two calm lines
for 16:9, and never split a sentence's last word from it. The script refuses: a phrase it can't find,
a scene the template doesn't have, a side or bubble stretch in the first 30 s (face only there), a
punch-in over 1.25x (takes may be 720p), and anchors for agenda parts that don't exist.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_captions as mc  # noqa: E402

TEMPLATE = Path(__file__).resolve().parent.parent / "template"
LINES = dict(max_words=10, max_chars=50, comma_min=4, min_seconds=1.3)   # two lines across a 16:9 frame
FACE_ONLY = 30.0
MAX_ZOOM = 1.25
END = re.compile(r"[.?!:]$")


def known_scenes(template: Path = TEMPLATE):
    text = (template / "src" / "lesson" / "scenes.ts").read_text(encoding="utf-8")
    return set(re.findall(r"'([a-z0-9-]+)':", text))


def load_words(path: Path, offset: float):
    """whisper CLI json or transcribe_clip.py list -> [{"w","s","e"}] moved by offset."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = [{"w": w["word"], "s": w["start"], "e": w["end"]} for s in data["segments"] for w in s.get("words", [])]
    return [{"w": w["w"].strip(), "s": w["s"] + offset, "e": w["e"] + offset} for w in data]


def tidy(caps):
    """Keep sentences whole at caption edges: a sentence's last word never opens the next caption, a new
    sentence's first word or two never trail at the end of one, and a lone word joins its neighbour."""
    for _ in range(2):
        for a, b in zip(caps, caps[1:]):
            if len(b["words"]) > 1 and END.search(b["words"][0]["w"]) and len(a["words"]) < LINES["max_words"]:
                a["words"].append(b["words"].pop(0))
            ends = [i for i, w in enumerate(a["words"][:-1]) if END.search(w["w"])]
            if ends and len(a["words"]) - ends[-1] - 1 <= 2:
                k = ends[-1] + 1
                b["words"][:0], a["words"] = a["words"][k:], a["words"][:k]
            if len(a["words"]) == 1 and b["words"] and b["words"][0]["start"] - a["words"][-1]["end"] < 2:
                b["words"][:0], a["words"] = a["words"], []
        caps = [c for c in caps if c["words"]]
    for c, nxt in zip(caps, caps[1:] + [None]):
        c["start"] = c["words"][0]["start"]
        last = c["words"][-1]["end"]
        c["end"] = round(last + 0.4 if nxt is None else min(max(last + 0.4, c["start"] + LINES["min_seconds"]),
                                                              nxt["words"][0]["start"]), 3)
    return [{"start": c["start"], "end": c["end"], "words": c["words"]} for c in caps]


def timeline(cfg):
    """Beats on the lesson timeline, each take on its own stretch of a source timeline, and the timemap."""
    beats, timemap, out = [], [], 0.0
    for t in cfg["takes"]:
        off = 1000.0 * t["beat"]
        timemap.append([off + t["from"], off + t["to"], out])
        beats.append({"n": t["beat"], "start": round(out, 3), "end": round(out + t["to"] - t["from"], 3)})
        out += t["to"] - t["from"]
    return beats, timemap, round(out, 3)


def captions(cfg, words_dir: Path, timemap):
    heard, pieces = [], []
    for t in cfg["takes"]:
        off = 1000.0 * t["beat"]
        f = words_dir / f"קטע-{t['beat']:02d}.json"
        if not f.is_file():
            raise SystemExit(f"error: no whisper words for beat {t['beat']} ({f})")
        heard += [w for w in load_words(f, off) if off + t["from"] <= w["s"] <= off + t["to"]]
        pieces.append({"from": off + t["from"], "to": off + t["to"], "text": cfg["proofread"][str(t["beat"])]})
    saved = dict(mc.LAYOUTS[2])
    mc.LAYOUTS[2] = LINES
    try:
        caps = mc.build(pieces, heard, timemap, speed=1.0, lines=2, style="lines")
    finally:
        mc.LAYOUTS[2] = saved
    return tidy(caps)


def resolver(beats, caps):
    by_n = {b["n"]: b for b in beats}
    words = [w for c in caps for w in c["words"]]

    def find(n, phrase):
        b = by_n.get(n)
        if b is None:
            raise SystemExit(f"error: beat {n} isn't in the takes")
        ws = [w for w in words if b["start"] - 1e-3 <= w["start"] < b["end"]]
        target = [mc.norm(x) for x in phrase.split()]
        for i in range(len(ws) - len(target) + 1):
            if all(mc.norm(ws[i + k]["w"]) == x for k, x in enumerate(target)):
                return ws[i]["start"]
        raise SystemExit(f"error: beat {n}: '{phrase}' isn't in the proofread words")

    def resolve(spec):
        if isinstance(spec, dict):
            return round(by_n[spec["beat_end"]]["end"] + spec.get("offset", 0.0), 3)
        n, phrase, *rest = spec
        offset = rest[0] if rest else 0.0
        t = by_n[n]["start"] if phrase is None else find(n, phrase)
        return round(t + offset, 3)

    return resolve


def layout(cfg, resolve, duration, scenes):
    segs = []
    for s in cfg["segments"]:
        start = resolve(s["at"])
        mode = s["mode"]
        if mode not in ("full", "side", "bubble"):
            raise SystemExit(f"error: segment at {s['at']}: unknown mode '{mode}'")
        if mode != "full":
            if start < FACE_ONLY:
                raise SystemExit(f"error: a {mode} segment at {start:.1f} s: the first {FACE_ONLY:.0f} s are face only")
            if s.get("scene") not in scenes:
                raise SystemExit(f"error: segment at {s['at']}: scene '{s.get('scene')}' isn't in template "
                                 f"src/lesson/scenes.ts ({', '.join(sorted(scenes))})")
        if s.get("zoom", 1.0) > MAX_ZOOM or s.get("zoom", 1.0) < 1.0:
            raise SystemExit(f"error: segment at {s['at']}: zoom {s['zoom']} outside 1-{MAX_ZOOM}")
        segs.append({"start": start, "mode": mode, **{k: s[k] for k in ("zoom", "scene") if k in s}})
    segs.sort(key=lambda x: x["start"])
    if not segs or segs[0]["start"] > 0.05:
        raise SystemExit("error: the first segment must start with the first beat")
    segs[0]["start"] = 0.0
    for a, b in zip(segs, segs[1:] + [None]):
        a["end"] = round(b["start"] if b else duration, 3)
    return [{"start": s["start"], "end": s["end"], "mode": s["mode"], **{k: s[k] for k in ("zoom", "scene") if k in s}}
            for s in segs]


def build(cfg, words_dir: Path, scenes=None):
    scenes = known_scenes() if scenes is None else scenes
    beats, timemap, duration = timeline(cfg)
    caps = captions(cfg, words_dir, timemap)
    resolve = resolver(beats, caps)
    at = {k: resolve(v) for k, v in cfg["anchors"].items()}
    extra = [k for k in at if re.fullmatch(r"ag\d+", k) and int(k[2:]) > len(cfg["parts"])]
    if extra:
        raise SystemExit(f"error: anchors {extra} have no part in 'parts'")
    by_n = {b["n"]: b for b in beats}
    part_starts = [by_n[n]["start"] if n in by_n else 1e9 for n in cfg["part_starts"] if n is not None]
    return {"base": "base.mp4", "duration": duration, "lesson": cfg["lesson"], "title": cfg["title"],
            "parts": cfg["parts"], "partStarts": part_starts, "disclaimerBeat": cfg["disclaimer_beat"],
            "beats": beats, "segments": layout(cfg, resolve, duration, scenes), "captions": caps, "at": at}


def srt(caps) -> str:
    def ts(t):
        ms = int(round(t * 1000))
        h, ms = divmod(ms, 3600000)
        m, ms = divmod(ms, 60000)
        s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    return "\n".join(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{' '.join(w['w'] for w in c['words'])}\n"
                     for i, c in enumerate(caps, 1))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--words-dir", required=True)
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--srt", help="also write the captions as SRT (lesson timeline), for Drive")
    a = ap.parse_args(argv)
    cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))
    props = build(cfg, Path(a.words_dir))
    Path(a.out).write_text(json.dumps(props, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.srt:
        Path(a.srt).write_text(srt(props["captions"]), encoding="utf-8")
    print(f"{a.out}: {len(props['captions'])} captions, {props['duration']:.1f} s, {len(props['segments'])} segments")
    for k, v in sorted(props["at"].items(), key=lambda kv: kv[1]):
        print(f"  {v:8.2f}  {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
