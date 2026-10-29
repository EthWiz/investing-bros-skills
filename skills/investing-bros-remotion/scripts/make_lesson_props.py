#!/usr/bin/env python3
"""Props for a crypto-course lesson video (the "Lesson" composition): captions, layout, graphic anchors.

Usage:
    python3 make_lesson_props.py lesson-N/lesson-N-video.json --words-dir WORDS -o props.json \\
        [--srt captions.srt] [--takes-dir DIR]

lesson-N-video.json (the lesson's config; it lives in the lesson's own folder, beside its assets/ and
  script/, or is the Drive manifest שיעור-N-מניפסט.json; see investing-bros-crypto-course's video reference):
  lesson, title (lines), parts, part_starts (the beat each part starts on, null if not in this cut),
  disclaimer_beat, disclaimer_from (optional anchor [beat, "phrase"] inside that beat where the strip starts;
  it ends with the beat), face (optional {x, y}: the face in the base, between the eyes and the mouth;
  default 840, 450), script {doc, revision, revision_kind, snapshot, snapshot_sha256, beats: {beat: {title,
  on_screen, text}}, departures: {beat: why}} (parse_script.py, from the Google Doc; the snapshot is checked
  against its hash), takes [{beat, file, from, to}] (same trims as make_lesson_base.py),
  proofread {beat: what Amitai said in the take}, anchors {key: spec}, assets {key: {file, source}},
  segments [{at: spec, mode, zoom?, scene?, content?}].
WORDS holds one whisper file per take, קטע-NN.json (NN = beat): the whisper CLI's --output_format json
  (segments with word timings) or transcribe_clip.py's [{"w", "s", "e"}], in seconds of the take. They are
  timing only: caption wording is the config's `proofread`. With --takes-dir, each words file's sidecar
  קטע-NN.take.json must name the selected take's sha256, so words from a replaced take are refused.

An anchor spec says when something starts, always from a spoken word:
  [beat, "phrase"]          when the phrase's first word is said (exact proofread words, punctuation ignored)
  [beat, "phrase", offset]  the same plus offset seconds
  [beat, null, offset]      the beat's start plus offset
  {"beat_end": n, "offset": x}
Every graphic is anchored this way, so re-timing one is a one-line change in the config.

Captions are the proofread words on whisper's timings (make_captions.py's alignment), two calm lines
for 16:9, and never split a sentence's last word from it. What each scene needs is in the template's
src/lesson/scenes.json. The script refuses, before anything renders: a phrase it can't find; a take
with no script beat (the Google Doc wasn't read); a scene the template doesn't have or in the wrong
mode; a scene's anchor, content `at` or asset that is missing or outside its segment; a scene variant
(double-spend's scenario) that isn't allowed, lacks its content or has its events out of order; segments out of
order or past the end; a side or bubble stretch in the first 30 s (face only there); a punch-in over
1.25x (takes may be 720p); and agenda anchors for parts that don't exist.
"""
import argparse
import hashlib
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


def scene_manifest(template: Path = TEMPLATE) -> dict:
    data = json.loads((template / "src" / "lesson" / "scenes.json").read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def known_scenes(template: Path = TEMPLATE):
    return set(scene_manifest(template))


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

    warned = set()

    def find(n, phrase):
        b = by_n.get(n)
        if b is None:
            raise SystemExit(f"error: beat {n} isn't in the takes")
        ws = [w for w in words if b["start"] - 1e-3 <= w["start"] < b["end"]]
        target = [mc.norm(x) for x in phrase.split()]
        hits = [ws[i]["start"] for i in range(len(ws) - len(target) + 1)
                if all(mc.norm(ws[i + k]["w"]) == x for k, x in enumerate(target))]
        if not hits:
            raise SystemExit(f"error: beat {n}: '{phrase}' isn't in the proofread words")
        if len(hits) > 1 and (n, phrase) not in warned:
            warned.add((n, phrase))
            print(f"warning: beat {n}: '{phrase}' is said {len(hits)} times; the first ({hits[0]:.2f} s) is used. "
                  "Add a word to pick another.", file=sys.stderr)
        return hits[0]

    def resolve(spec):
        if isinstance(spec, dict):
            return round(by_n[spec["beat_end"]]["end"] + spec.get("offset", 0.0), 3)
        n, phrase, *rest = spec
        offset = rest[0] if rest else 0.0
        t = by_n[n]["start"] if phrase is None else find(n, phrase)
        return round(t + offset, 3)

    return resolve


def resolve_content(value, resolve):
    """Any {"at": spec} inside a scene's content becomes {"at": seconds}."""
    if isinstance(value, dict):
        return {k: (resolve(v) if k == "at" else resolve_content(v, resolve)) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_content(v, resolve) for v in value]
    return value


def content_times(value):
    if isinstance(value, dict):
        return [t for k, v in value.items() for t in ([v] if k == "at" else content_times(v))]
    if isinstance(value, list):
        return [t for v in value for t in content_times(v)]
    return []


def layout(cfg, resolve, duration, manifest):
    segs, last = [], -1.0
    for s in cfg["segments"]:
        start = resolve(s["at"])
        mode = s["mode"]
        where = f"segment at {s['at']}"
        if mode not in ("full", "side", "bubble"):
            raise SystemExit(f"error: {where}: unknown mode '{mode}'")
        if not 0.0 <= start < duration:
            raise SystemExit(f"error: {where} starts at {start:.2f} s, outside the lesson (0-{duration:.2f} s)")
        if start <= last:
            raise SystemExit(f"error: {where} starts at {start:.2f} s, not after the segment before it ({last:.2f} s)")
        last = start
        if mode != "full" and start < FACE_ONLY:
            raise SystemExit(f"error: a {mode} segment at {start:.1f} s: the first {FACE_ONLY:.0f} s are face only")
        if mode != "full" or "scene" in s:  # a 'full' scene: cards on the wall beside him, allowed from the start
            spec = manifest.get(s.get("scene"))
            if spec is None:
                raise SystemExit(f"error: {where}: scene '{s.get('scene')}' isn't in template "
                                 f"src/lesson/scenes.json ({', '.join(sorted(manifest))})")
            if spec["mode"] != mode:
                raise SystemExit(f"error: {where}: scene '{s['scene']}' is a {spec['mode']} scene, not {mode}")
        if s.get("zoom", 1.0) > MAX_ZOOM or s.get("zoom", 1.0) < 1.0:
            raise SystemExit(f"error: {where}: zoom {s['zoom']} outside 1-{MAX_ZOOM}")
        seg = {"start": start, "mode": mode, **{k: s[k] for k in ("zoom", "scene") if k in s}}
        if "content" in s:
            seg["content"] = resolve_content(s["content"], resolve)
        segs.append(seg)
    if not segs or segs[0]["start"] > 0.05:
        raise SystemExit("error: the first segment must start with the first beat")
    segs[0]["start"] = 0.0
    for a, b in zip(segs, segs[1:] + [None]):
        a["end"] = round(b["start"] if b else duration, 3)
    return [{"start": s["start"], "end": s["end"], "mode": s["mode"],
             **{k: s[k] for k in ("zoom", "scene", "content") if k in s}} for s in segs]


def check_scenes(segments, at, assets, manifest):
    """Every scene gets what it needs, inside its own stretch of the lesson."""
    for seg in segments:
        if "scene" not in seg:
            continue
        spec, name = manifest[seg["scene"]], seg["scene"]
        lo, hi = seg["start"], seg["end"]
        content = seg.get("content", {})
        optional = spec.get("optional", {})
        missing = [k for k in spec["anchors"] if k not in at and k not in optional.get("anchors", [])]
        if missing:
            raise SystemExit(f"error: scene '{name}' needs anchors {missing}")
        outside = [k for k in spec["anchors"] if k in at and not lo <= at[k] <= hi]
        if outside:
            raise SystemExit(f"error: scene '{name}' ({lo:.2f}-{hi:.2f} s): anchors {outside} fall outside it")
        missing = [k for k in spec["content"] if k not in content and k not in optional.get("content", [])]
        if missing:
            raise SystemExit(f"error: scene '{name}' needs content {missing}")
        late = [round(t, 2) for t in content_times(content) if not lo <= t <= hi]
        if late:
            raise SystemExit(f"error: scene '{name}' ({lo:.2f}-{hi:.2f} s): content times {late} fall outside it")
        missing = [k for k in spec.get("assets", []) if k not in assets]
        if missing:
            raise SystemExit(f"error: scene '{name}' needs assets {missing} (config 'assets')")
        if "variants" in spec:
            check_variant(name, spec["variants"], content)


def content_at(content, dotted: str):
    """content['payments'][1]['at'] for 'payments.1.at'; None when any step is missing."""
    cur = content
    for step in dotted.split("."):
        if isinstance(cur, list) and step.isdigit() and int(step) < len(cur):
            cur = cur[int(step)]
        elif isinstance(cur, dict) and step in cur:
            cur = cur[step]
        else:
            return None
    return cur


def check_variant(name, variants, content):
    """A scene with variants (double-spend's scenario): an allowed value, its extra content, its events in order."""
    key, options = variants["key"], variants["options"]
    value = content.get(key)
    if value not in options:
        raise SystemExit(f"error: scene '{name}': {key} '{value}' isn't one of {sorted(options)}")
    opt = options[value]
    missing = [k for k in opt.get("content", []) if k not in content]
    if missing:
        raise SystemExit(f"error: scene '{name}' ({value}) needs content {missing}")
    times = [(p, content_at(content, p)) for p in opt.get("order", [])]
    absent = [p for p, t in times if not isinstance(t, (int, float))]
    if absent:
        raise SystemExit(f"error: scene '{name}' ({value}) needs times {absent}")
    for (pa, ta), (pb, tb) in zip(times, times[1:]):
        if tb < ta - 1e-6:
            raise SystemExit(f"error: scene '{name}' ({value}): {pb} ({tb:.2f} s) comes before {pa} ({ta:.2f} s)")


def check_script(cfg, config_dir: Path = Path(".")):
    """The Google Doc was read: its revision is recorded, every recorded beat has its on-screen line, and the
    saved snapshot (when the config names one, as parse_script.py writes it) is the text that was parsed."""
    script = cfg.get("script") or {}
    if not script.get("doc") or not script.get("revision"):
        raise SystemExit("error: config 'script' needs the Google Doc's id and revision (read תסריט-שיעור-N first)")
    beats = script.get("beats", {})
    missing = [t["beat"] for t in cfg["takes"] if not beats.get(str(t["beat"]), {}).get("on_screen")]
    if missing:
        raise SystemExit(f"error: beats {missing} have no 'על המסך' line from the script (parse_script.py)")
    if script.get("snapshot"):
        snap = config_dir / script["snapshot"]
        if not snap.is_file():
            raise SystemExit(f"error: the script snapshot {snap} is missing")
        if script.get("snapshot_sha256") and sha256_file(snap) != script["snapshot_sha256"]:
            raise SystemExit(f"error: the script snapshot {snap} changed after parse_script.py read it; "
                             "save the new Doc text as a new snapshot and parse that")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def take_file(t, takes_dir: Path):
    """The take under its own name, else its Drive name (make_lesson_base.py finds takes the same way)."""
    for name in (t["file"], f"קטע-{t['beat']:02d}.mp4"):
        if (takes_dir / name).is_file():
            return takes_dir / name
    return None


def check_words_match_takes(cfg, words_dir: Path, takes_dir: Path):
    """Each words file was made from the take the config selects: its sidecar קטע-NN.take.json
    (make_lesson_base.py stamp) holds that take's sha256 (the recorded file's, or its Drive copy's).
    Returns the beats with no sidecar, to report; a sidecar naming another take is refused."""
    unstamped = []
    for t in cfg["takes"]:
        side = words_dir / f"קטע-{t['beat']:02d}.take.json"
        if not side.is_file():
            unstamped.append(t["beat"])
            continue
        rec = json.loads(side.read_text(encoding="utf-8"))
        take = take_file(t, takes_dir)
        if take is None:
            raise SystemExit(f"error: beat {t['beat']}: neither {t['file']} nor its Drive name is in {takes_dir}")
        if sha256_file(take) not in {rec.get("sha256"), rec.get("package_sha256")}:
            raise SystemExit(f"error: beat {t['beat']}: the words were made from {rec.get('take')}, not from {take.name} "
                             f"as it is now; transcribe the selected take again")
    return unstamped


def stage_assets_spec(cfg, config_dir: Path):
    assets, sources = {}, {}
    for key, a in cfg.get("assets", {}).items():
        src = (config_dir / a["file"]).resolve()
        if not src.is_file():
            raise SystemExit(f"error: asset '{key}': {src} doesn't exist")
        if not a.get("source"):
            raise SystemExit(f"error: asset '{key}': record where it comes from ('source')")
        assets[key] = f"assets/{key}{src.suffix}"
        sources[key] = str(src)
    return assets, sources


def disclaimer(cfg, by_n, resolve):
    """The disclaimer strip's stretch: from `disclaimer_from` (or the beat's start) to the end of its beat."""
    n = cfg["disclaimer_beat"]
    if n not in by_n:
        return None
    spec = cfg.get("disclaimer_from", [n, None])
    if isinstance(spec, dict) or spec[0] != n:
        raise SystemExit(f"error: disclaimer_from must be [beat, phrase] in the disclaimer beat ({n})")
    return {"start": resolve(spec), "end": by_n[n]["end"]}


def face(cfg) -> dict:
    """Where the face is in the 1920x1080 base (between the eyes and the mouth); zooms and the bubble centre on it."""
    f = cfg["face"]
    if not (isinstance(f, dict) and set(f) == {"x", "y"} and 0 <= f["x"] <= 1920 and 0 <= f["y"] <= 1080):
        raise SystemExit("error: face must be {\"x\": 0-1920, \"y\": 0-1080}, pixels in the base")
    return {"x": float(f["x"]), "y": float(f["y"])}


def build(cfg, words_dir: Path, manifest=None, config_dir: Path = Path(".")):
    manifest = scene_manifest() if manifest is None else manifest
    check_script(cfg, config_dir)
    beats, timemap, duration = timeline(cfg)
    caps = captions(cfg, words_dir, timemap)
    resolve = resolver(beats, caps)
    at = {k: resolve(v) for k, v in cfg["anchors"].items()}
    outside = [k for k, v in at.items() if not 0.0 <= v <= duration]
    if outside:
        raise SystemExit(f"error: anchors {outside} fall outside the lesson (0-{duration:.2f} s)")
    extra = [k for k in at if re.fullmatch(r"ag\d+", k) and int(k[2:]) > len(cfg["parts"])]
    if extra:
        raise SystemExit(f"error: anchors {extra} have no part in 'parts'")
    if len(cfg["part_starts"]) != len(cfg["parts"]):
        raise SystemExit("error: part_starts needs one entry per part (null for a part not in this cut)")
    by_n = {b["n"]: b for b in beats}
    # one position per part, so the marker's labels never shift when a part is missing
    part_starts = [by_n[n]["start"] if n in by_n else None for n in cfg["part_starts"]]
    assets, sources = stage_assets_spec(cfg, config_dir)
    segments = layout(cfg, resolve, duration, manifest)
    check_scenes(segments, at, assets, manifest)
    extra = {"face": face(cfg)} if "face" in cfg else {}
    return {**extra, "base": "base.mp4", "duration": duration, "lesson": cfg["lesson"], "title": cfg["title"],
            "parts": cfg["parts"], "partStarts": part_starts, "disclaimer": disclaimer(cfg, by_n, resolve),
            "beats": beats, "segments": segments, "captions": caps, "at": at, "assets": assets,
            "assetSources": sources,
            "script": {k: cfg["script"][k] for k in ("doc", "revision", "revision_kind", "snapshot_sha256")
                       if k in cfg["script"]},
            "departures": cfg["script"].get("departures", {})}


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
    ap.add_argument("--takes-dir", help="check each words file was made from the selected take (its .take.json sidecar)")
    a = ap.parse_args(argv)
    cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))
    if a.takes_dir:
        unstamped = check_words_match_takes(cfg, Path(a.words_dir), Path(a.takes_dir))
        if unstamped:
            print(f"note: beats {unstamped} have no .take.json sidecar, so their words weren't checked against the takes "
                  "(make_lesson_base.py stamp)", file=sys.stderr)
    props = build(cfg, Path(a.words_dir), config_dir=Path(a.config).resolve().parent)
    Path(a.out).write_text(json.dumps(props, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.srt:
        Path(a.srt).write_text(srt(props["captions"]), encoding="utf-8")
    print(f"{a.out}: {len(props['captions'])} captions, {props['duration']:.1f} s, {len(props['segments'])} segments")
    for k, v in sorted(props["at"].items(), key=lambda kv: kv[1]):
        print(f"  {v:8.2f}  {k}")
    for beat, why in props["departures"].items():
        print(f"  departs from the script, beat {beat}: {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
