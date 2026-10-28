#!/usr/bin/env python3
"""Join a lesson's takes into the base video the lesson composition plays (16:9, 1080p, 30 fps).

Usage:
    python3 make_lesson_base.py suggest lesson-N.json --takes-dir DIR     # trims from where speech starts/ends
    python3 make_lesson_base.py build lesson-N.json --takes-dir DIR -o base.mp4 [--extras OUT_DIR]

lesson-N.json `takes`: [{"beat": 1, "file": "Beat 1 - take 1.mov", "from": 2.0, "to": 43.0}, ...] in
beat order; `from`/`to` are seconds of the take. `suggest` prints a from/to per take: 0.3 s before the
first speech and 0.45 s after the last (silencedetect at -38 dB); check them against the whisper
words, since a click or a breath can read as speech. `build` trims each take, scales it to 1920x1080
(lanczos; 720p takes are upscaled, so keep punch-ins small), joins them in beat order with a 40 ms
fade at each cut, and levels the audio to -14 LUFS (stereo AAC). No speed change: a lesson that runs
long is split, not sped up.

With a `background` block in the config, `build` puts Amitai on that image in every take: `vision` cuts him
out with Apple Vision (macOS; one matte per take, cached in --matte-dir, by default `mattes/` beside the
output), `chroma` keys out the green screen (lesson_background.py has the details). The takes themselves are
never changed, so the Drive package keeps the originals and a rebuild can key them again.

--extras DIR fills the lesson's Drive extras/ package: each take as קטע-NN.mp4 (stream copy, no
re-encode), the config's assets, the script snapshot, with --words-dir the Whisper words קטע-NN.json and
their sidecars, and שיעור-N-מניפסט.json, which is the config itself plus a `package` block (the skills
version, the config's hash, the base's length, the file names). The manifest works as the config:
`build שיעור-N-מניפסט.json --takes-dir extras/` rebuilds the same base from Drive alone, because a take
is found by its own name or by its Drive name קטע-NN.mp4, and make_lesson_props.py reads it the same way.

    python3 make_lesson_base.py stamp lesson-N.json --takes-dir DIR --words-dir WORDS
    python3 make_lesson_base.py status lesson-N.json --takes-dir DIR --words-dir WORDS [--record RECORDS]

`stamp`, right after Whisper: a sidecar קטע-NN.take.json per words file with the take's name and sha256,
so words from a replaced take are caught (make_lesson_props.py --takes-dir refuses them). `status`: per
beat, whether the take, its words and its stamp agree, and against the last export record
(check_lesson.py --record) what changed and so what to run again: a new take -> Whisper, proofread, base,
props, render; new trims -> base, props, render; proofread, anchors or layout -> props, render; a new
script snapshot -> review the changed beats. It runs nothing.
"""
import argparse
import datetime
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import lesson_background

W, H, FPS = 1920, 1080, 30
LEAD, TAIL, FADE = 0.3, 0.45, 0.04


def duration(path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def silences(path, noise="-38dB", min_len=0.6):
    """[(start, end)] of silences, from ffmpeg's silencedetect log."""
    log = subprocess.run(["ffmpeg", "-v", "info", "-i", str(path), "-af", f"silencedetect=noise={noise}:d={min_len}",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    return parse_silences(log, duration(path))


def parse_silences(log: str, total: float):
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    ends += [total] * (len(starts) - len(ends))          # silence running to the end of the file
    return list(zip(starts, ends))


def trims_from_silences(sil, total: float, lead=LEAD, tail=TAIL, blip=0.25, edge=0.6):
    """Speech window of a take: after the opening silence, before the closing one. A sound shorter than
    `blip` between two silences, or shorter than `edge` at either end of the file (the click of the
    camera starting or stopping), counts as silence."""
    merged = []
    for a, b in sorted(sil):
        if merged and a - merged[-1][1] < blip:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    start = merged[0][1] if merged and merged[0][0] <= edge else 0.0
    end = merged[-1][0] if merged and merged[-1][1] >= total - edge else total
    return round(max(0.0, start - lead), 2), round(min(total, end + tail), 2)


def filter_graph(takes, background=None) -> str:
    """Inputs: the takes, then with a background its image once per take, then with `vision` a matte per take."""
    parts, labels, n = [], [], len(takes)
    for i, t in enumerate(takes):
        a, b = t["from"], t["to"]
        if b <= a:
            raise SystemExit(f"take for beat {t['beat']}: 'to' ({b}) must be after 'from' ({a})")
        d = b - a
        cut = f"[{i}:v]trim={a}:{b},setpts=PTS-STARTPTS,scale={W}:{H}:flags=lanczos,fps={FPS},setsar=1"
        if background:
            vision = background["method"] == "vision"
            parts += lesson_background.take_chain(i, a, b, cut, background, n + i, 2 * n + i if vision else None)
        else:
            parts.append(f"{cut}[v{i}]")
        parts.append(f"[{i}:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d={FADE},"
                     f"afade=t=out:st={round(d - 0.06, 3)}:d=0.06[a{i}]")
        labels.append(f"[v{i}][a{i}]")
    parts.append(f"{''.join(labels)}concat=n={len(takes)}:v=1:a=1[v][a]")
    parts.append("[a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,pan=stereo|c0=c0|c1=c0[ao]")
    return ";".join(parts)


def take_path(t, takes_dir: Path) -> Path:
    """The take under its own name, else under its Drive name (a package downloaded from Drive)."""
    for name in (t["file"], extras_name(t["beat"])):
        if (takes_dir / name).is_file():
            return takes_dir / name
    raise SystemExit(f"error: beat {t['beat']}: neither {t['file']} nor {extras_name(t['beat'])} is in {takes_dir}")


def build_cmd(takes, takes_dir: Path, out: Path, find=take_path, background=None, image=None, mattes=()):
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for t in takes:
        cmd += ["-i", str(find(t, takes_dir))]
    if background:
        for _ in takes:
            cmd += ["-loop", "1", "-framerate", str(FPS), "-i", str(image)]
        for m in mattes:
            cmd += ["-i", str(m)]
    return cmd + ["-filter_complex", filter_graph(takes, background), "-map", "[v]", "-map", "[ao]", "-c:v", "libx264",
                  "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                  "-movflags", "+faststart", str(out)]


def extras_name(beat: int) -> str:
    return f"קטע-{beat:02d}.mp4"


def skills_version(here: Path = Path(__file__).resolve().parent) -> str:
    """The skills repo commit, or the VERSION file a release ZIP carries."""
    try:
        rev = subprocess.run(["git", "-C", str(here), "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
        if rev.returncode == 0 and rev.stdout.strip():
            dirty = subprocess.run(["git", "-C", str(here), "status", "--porcelain", "--", str(here.parent)],
                                   capture_output=True, text=True).stdout.strip()
            return rev.stdout.strip() + ("+local-changes" if dirty else "")
    except OSError:
        pass
    for v in (here.parent / "VERSION", here.parent.parent / "VERSION"):
        if v.is_file():
            return v.read_text(encoding="utf-8").strip()
    return "unknown"


def manifest(cfg: dict, config_text: str, base_name: str, base_seconds: float, version: str, made: str) -> dict:
    """The config, rewritten to the package's own file names, plus where and how it was made."""
    out = json.loads(json.dumps(cfg))
    n = cfg["lesson"]
    for key, a in out.get("assets", {}).items():
        a["file"] = Path(a["file"]).name
    if (out.get("script") or {}).get("snapshot"):
        out["script"]["snapshot"] = Path(out["script"]["snapshot"]).name
    if out.get("background"):
        out["background"]["image"] = Path(out["background"]["image"]).name
    out["package"] = {
        "made": made,
        "skills_version": version,
        "config_sha256": hashlib.sha256(config_text.encode("utf-8")).hexdigest(),
        "base": base_name,
        "base_seconds": round(base_seconds, 3),
        "takes": {str(t["beat"]): {"drive": extras_name(t["beat"]), "recorded_as": t["file"]} for t in cfg["takes"]},
        "words": [f"קטע-{t['beat']:02d}.json" for t in cfg["takes"]],
        "captions": f"שיעור-{n}-כתוביות.srt",
        "rebuild": f"python3 make_lesson_base.py build שיעור-{n}-מניפסט.json --takes-dir . -o {base_name}",
    }
    return out


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def words_name(beat: int) -> str:
    return f"קטע-{beat:02d}.json"


def sidecar_name(beat: int) -> str:
    return f"קטע-{beat:02d}.take.json"


def digest(value) -> str:
    """sha256 of a JSON value, keys sorted. check_lesson.py (investing-bros-remotion) uses the same recipe for
    the export record, and both tests pin the same digest, so the record and `status` compare like with like."""
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


LAYOUT_KEYS = ("title", "parts", "part_starts", "disclaimer_beat", "disclaimer_from", "anchors", "segments", "assets")


def fingerprint(cfg: dict) -> dict:
    """What `status` compares against an export record: trims per beat, proofread per beat, the layout, the script,
    and the background when there is one (check_lesson.py in investing-bros-remotion keeps the same function)."""
    out = {"trims": {str(t["beat"]): [t["file"], t["from"], t["to"]] for t in cfg["takes"]},
           "proofread": {k: digest(v) for k, v in cfg.get("proofread", {}).items()},
           "layout": digest({k: cfg.get(k) for k in LAYOUT_KEYS}),
           "script": (cfg.get("script") or {}).get("snapshot_sha256") or (cfg.get("script") or {}).get("revision")}
    if cfg.get("background"):
        out["background"] = digest(cfg["background"])
    return out


def stamp(cfg: dict, takes_dir: Path, words_dir: Path, force=False, hasher=sha256_file):
    """Write קטע-NN.take.json beside each words file: which take (file name, sha256) the words were made from.
    Run it right after Whisper. An existing sidecar is checked, never overwritten unless `force`."""
    out = []
    for t in cfg["takes"]:
        words, side = words_dir / words_name(t["beat"]), words_dir / sidecar_name(t["beat"])
        if not words.is_file():
            out.append((t["beat"], "no words"))
            continue
        take = take_path(t, takes_dir)
        sha = hasher(take)
        if side.is_file() and not force:
            rec = json.loads(side.read_text(encoding="utf-8"))
            out.append((t["beat"], "ok" if sha in (rec.get("sha256"), rec.get("package_sha256")) else "STALE: the take changed"))
            continue
        side.write_text(json.dumps({"beat": t["beat"], "take": take.name, "sha256": sha, "words_sha256": hasher(words)},
                                   ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        out.append((t["beat"], "stamped"))
    return out


def copy_words(takes, words_dir: Path, extras: Path, hasher=sha256_file):
    """The words and their sidecars into the package; each sidecar also gets the Drive copy's sha256
    (קטע-NN.mp4 is a remux, so its bytes differ from the recorded file's)."""
    for t in takes:
        b = t["beat"]
        src = words_dir / words_name(b)
        if not src.is_file():
            raise SystemExit(f"error: beat {b}: no words {src} to put in the package")
        if src.resolve() != (extras / src.name).resolve():
            shutil.copy2(src, extras / src.name)
        side = words_dir / sidecar_name(b)
        if side.is_file():
            rec = json.loads(side.read_text(encoding="utf-8"))
            rec["package_sha256"] = hasher(extras / extras_name(b))
            (extras / side.name).write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def latest_record(path: Path):
    """An export record (check_lesson.py --record), or the newest one in a folder; None when there is none."""
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    found = sorted(path.glob("שיעור-*-ייצוא-*.json")) if path.is_dir() else []
    return json.loads(found[-1].read_text(encoding="utf-8")) if found else None


def status(cfg: dict, takes_dir: Path, words_dir: Path, record=None, hasher=sha256_file):
    """Per beat, and against the last export, what is missing or changed and so what to run again. Runs nothing."""
    lines, todo = [], set()
    for t in cfg["takes"]:
        b = t["beat"]
        try:
            take = take_path(t, takes_dir)
        except SystemExit:
            lines.append(f"beat {b}: take missing ({t['file']})")
            todo.add("find the take")
            continue
        side = words_dir / sidecar_name(b)
        if not (words_dir / words_name(b)).is_file():
            lines.append(f"beat {b}: no words")
            todo |= {"whisper", "props", "render"}
        elif not side.is_file():
            lines.append(f"beat {b}: words not stamped (make_lesson_base.py stamp)")
        else:
            rec = json.loads(side.read_text(encoding="utf-8"))
            if hasher(take) not in (rec.get("sha256"), rec.get("package_sha256")):
                lines.append(f"beat {b}: the take changed since its words were made")
                todo |= {"whisper", "proofread", "base", "props", "render"}
    if record is None:
        lines.append("no export record yet: everything after the words runs")
        return lines, sorted(todo | {"base", "props", "render"})
    now, then = fingerprint(cfg), record.get("fingerprint", {})
    took = {str(x["beat"]): x for x in record.get("takes", [])}
    for beat, trim in now["trims"].items():
        old = then.get("trims", {}).get(beat)
        if old is None:
            lines.append(f"beat {beat}: new since the last export")
            todo |= {"base", "props", "render"}
        elif old != trim:
            lines.append(f"beat {beat}: take or trims changed")
            todo |= {"base", "props", "render"}
        elif beat in took:
            t = next(x for x in cfg["takes"] if str(x["beat"]) == beat)
            try:
                if hasher(take_path(t, takes_dir)) not in (took[beat].get("sha256"), took[beat].get("package_sha256")):
                    lines.append(f"beat {beat}: the take's file changed")
                    todo |= {"whisper", "proofread", "base", "props", "render"}
            except SystemExit:
                pass
    for beat in set(then.get("trims", {})) - set(now["trims"]):
        lines.append(f"beat {beat}: dropped since the last export")
        todo |= {"base", "props", "render"}
    changed = [b for b, h in now["proofread"].items() if then.get("proofread", {}).get(b) not in (None, h)]
    if changed:
        lines.append(f"proofread changed: beats {', '.join(sorted(changed, key=int))}")
        todo |= {"props", "render"}
    if now.get("background") != then.get("background"):
        lines.append("the background changed")
        todo |= {"base", "props", "render"}
    if now["layout"] != then.get("layout"):
        lines.append("layout, anchors or scene content changed")
        todo |= {"props", "render"}
    if now["script"] != then.get("script"):
        lines.append("the script snapshot changed: review the beats parse_script.py listed")
        todo.add("review the script")
    if not lines:
        lines.append(f"nothing changed since the export of {record.get('made')}")
    return lines, sorted(todo)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("suggest", "build", "stamp", "status"))
    ap.add_argument("config")
    ap.add_argument("--takes-dir", required=True)
    ap.add_argument("-o", "--out")
    ap.add_argument("--extras", help="also write the takes as קטע-NN.mp4 here")
    ap.add_argument("--words-dir", help="stamp/status: the Whisper words; build --extras: copied into the package")
    ap.add_argument("--record", help="status: an export record from check_lesson.py --record, or its folder")
    ap.add_argument("--force", action="store_true", help="stamp: rewrite existing sidecars")
    ap.add_argument("--matte-dir", help="build with a vision background: where the mattes are kept (default: "
                                        "mattes/ beside the output)")
    a = ap.parse_args(argv)
    config_text = Path(a.config).read_text(encoding="utf-8")
    cfg = json.loads(config_text)
    takes = cfg["takes"]
    tdir = Path(a.takes_dir)
    if a.cmd in ("stamp", "status") and not a.words_dir:
        ap.error(f"{a.cmd} needs --words-dir")
    if a.cmd == "stamp":
        for beat, what in stamp(cfg, tdir, Path(a.words_dir), a.force):
            print(f"beat {beat}: {what}")
        return 0
    if a.cmd == "status":
        lines, todo = status(cfg, tdir, Path(a.words_dir), latest_record(Path(a.record)) if a.record else None)
        print("\n".join(lines))
        print(f"run again: {', '.join(todo) if todo else 'nothing'}")
        return 0
    if a.cmd == "suggest":
        for t in takes:
            p = take_path(t, tdir)
            fr, to = trims_from_silences(silences(p), duration(p))
            print(json.dumps({"beat": t["beat"], "file": t["file"], "from": fr, "to": to}, ensure_ascii=False))
        return 0
    if not a.out:
        ap.error("build needs -o")
    here = Path(a.config).resolve().parent
    background, image, mattes = None, None, []
    if cfg.get("background"):
        background = lesson_background.check(cfg["background"])
        image = here / background["image"]
        if not image.is_file():
            raise SystemExit(f"error: no background image {image}")
        if background["method"] == "vision":
            tool = lesson_background.matte_tool()
            folder = Path(a.matte_dir) if a.matte_dir else Path(a.out).resolve().parent / "mattes"
            for t in takes:
                take = take_path(t, tdir)
                mattes.append(lesson_background.matte(take, sha256_file(take), folder, tool))
                print(f"beat {t['beat']}: matte {mattes[-1]}")
    subprocess.run(build_cmd(takes, tdir, Path(a.out), background=background, image=image, mattes=mattes), check=True)
    total = sum(t["to"] - t["from"] for t in takes)
    print(f"{a.out}: {duration(a.out):.2f} s (takes add up to {total:.2f} s)")
    if a.extras:
        extras = Path(a.extras)
        extras.mkdir(parents=True, exist_ok=True)
        for t in takes:
            src, dst = take_path(t, tdir), extras / extras_name(t["beat"])
            if src.resolve() != dst.resolve():
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-map", "0:v:0", "-map", "0:a:0",
                                "-c", "copy", "-movflags", "+faststart", str(dst)], check=True)
            print(dst)
        files = [here / asset["file"] for asset in cfg.get("assets", {}).values()]
        if image:
            files.append(image)
        if (cfg.get("script") or {}).get("snapshot"):
            files.append(here / cfg["script"]["snapshot"])
        for src in files:
            if src.resolve() != (extras / src.name).resolve():
                shutil.copy2(src, extras / src.name)
        if a.words_dir:
            copy_words(takes, Path(a.words_dir), extras)
        made = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        m = manifest(cfg, config_text, Path(a.out).name, duration(a.out), skills_version(), made)
        dst = extras / f"שיעור-{cfg['lesson']}-מניפסט.json"
        dst.write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
