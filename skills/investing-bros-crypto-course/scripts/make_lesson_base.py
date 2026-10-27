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

--extras DIR fills the lesson's Drive extras/ package: each take as קטע-NN.mp4 (stream copy, no
re-encode), the config's assets, and שיעור-N-מניפסט.json, which is the config itself plus a `package`
block (the skills version, the config's hash, the base's length, the file names). The manifest works
as the config: `build שיעור-N-מניפסט.json --takes-dir extras/` rebuilds the same base from Drive alone,
because a take is found by its own name or by its Drive name קטע-NN.mp4.
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


def filter_graph(takes) -> str:
    parts, labels = [], []
    for i, t in enumerate(takes):
        a, b = t["from"], t["to"]
        if b <= a:
            raise SystemExit(f"take for beat {t['beat']}: 'to' ({b}) must be after 'from' ({a})")
        d = b - a
        parts.append(f"[{i}:v]trim={a}:{b},setpts=PTS-STARTPTS,scale={W}:{H}:flags=lanczos,fps={FPS},setsar=1[v{i}]")
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


def build_cmd(takes, takes_dir: Path, out: Path, find=take_path):
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for t in takes:
        cmd += ["-i", str(find(t, takes_dir))]
    return cmd + ["-filter_complex", filter_graph(takes), "-map", "[v]", "-map", "[ao]", "-c:v", "libx264",
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("suggest", "build"))
    ap.add_argument("config")
    ap.add_argument("--takes-dir", required=True)
    ap.add_argument("-o", "--out")
    ap.add_argument("--extras", help="also write the takes as קטע-NN.mp4 here")
    a = ap.parse_args(argv)
    config_text = Path(a.config).read_text(encoding="utf-8")
    cfg = json.loads(config_text)
    takes = cfg["takes"]
    tdir = Path(a.takes_dir)
    if a.cmd == "suggest":
        for t in takes:
            p = take_path(t, tdir)
            fr, to = trims_from_silences(silences(p), duration(p))
            print(json.dumps({"beat": t["beat"], "file": t["file"], "from": fr, "to": to}, ensure_ascii=False))
        return 0
    if not a.out:
        ap.error("build needs -o")
    subprocess.run(build_cmd(takes, tdir, Path(a.out)), check=True)
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
        for key, asset in cfg.get("assets", {}).items():
            src = (Path(a.config).resolve().parent / asset["file"])
            if src.resolve() != (extras / src.name).resolve():
                shutil.copy2(src, extras / src.name)
        made = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        m = manifest(cfg, config_text, Path(a.out).name, duration(a.out), skills_version(), made)
        dst = extras / f"שיעור-{cfg['lesson']}-מניפסט.json"
        dst.write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
