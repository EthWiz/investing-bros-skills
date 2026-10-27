#!/usr/bin/env python3
"""Check a rendered lesson against its plan before Amitai sees it.

Usage:
    python3 check_lesson.py lesson.mp4 --props props.json [--base base.mp4] [--fonts FONTS] [--json report.json]
        [--record RECORDS --config lesson-N-video.json [--takes-dir DIR] [--manifest שיעור-N-מניפסט.json]]

--record: when everything passes, write שיעור-N-ייצוא-<UTC>.json into RECORDS (never over an older one): the
export's name, sha256, length, size and frame rate; this report; the hashes of the config, props, base and
manifest; the script's Doc revision and snapshot hash; each take with its trims and sha256; the skills
commit, and `draft: true` when the checkout had local changes. A failed check writes no record.
make_lesson_base.py status (investing-bros-crypto-course) compares the current config with it.
Passing this check is not Amitai's approval; that is recorded in the hand-back, not here.

Fails (exit 1) on:
  media     not 1920x1080 h264 at 30 fps with an audio track, or the base missing / not the planned length
  length    the video more than 0.1 s off the props' duration (the planned timeline)
  loudness  integrated loudness outside -16..-12 LUFS, or a true peak above -1 dBTP
  sync      the video's sound more than one frame away from the base's (checked around every take cut)
  dead air  a silence of 1.5 s or more across a take cut (a trim left a gap)
  captions  out of order, overlapping, past the end, starting after their first word or ending before
            their last, on screen under 0.7 s, or (with --fonts) more than two lines in their layout's width
Warns on captions read faster than 22 characters a second and silences over 2.5 s anywhere.
Stills can't show timing: this checks the sound and the captions' clock; `render_lesson.py --transitions`
gives a short clip of every cut to watch.
"""
import argparse
import datetime
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

FPS = 30
FRAME = 1 / FPS
LUFS = (-16.0, -12.0)
TRUE_PEAK = -1.0
GAP_AT_CUT = 1.5
LONG_SILENCE = 2.5
MIN_ON_SCREEN = 0.7
MAX_CPS = 22.0
# caption box per layout: width in px (Lesson.tsx CAP), 50 px Heebo ExtraBold
CAPTION_WIDTH = {"full": 1300, "side": 860, "bubble": 1300}
CAPTION_SIZE = 50


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate",
                          "-show_entries", "format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def check_media(info, label="video"):
    errs = []
    v = [s for s in info["streams"] if s["codec_type"] == "video"]
    a = [s for s in info["streams"] if s["codec_type"] == "audio"]
    if not v:
        return [f"{label}: no video stream"]
    v = v[0]
    if (v.get("width"), v.get("height")) != (1920, 1080):
        errs.append(f"{label}: {v.get('width')}x{v.get('height')}, not 1920x1080")
    if v.get("codec_name") != "h264":
        errs.append(f"{label}: codec {v.get('codec_name')}, not h264")
    num, den = (int(x) for x in v.get("r_frame_rate", "0/1").split("/"))
    if den and abs(num / den - FPS) > 0.01:
        errs.append(f"{label}: {num / den:.3f} fps, not {FPS}")
    if not a:
        errs.append(f"{label}: no audio track")
    return errs


def parse_ebur128(log: str):
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", log)
    p = re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", log)
    return (float(i[-1]) if i else None), (float(p[-1]) if p and p[-1] != "-inf" else None)


def loudness(path):
    log = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-map", "0:a:0", "-af", "ebur128=peak=true",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    return parse_ebur128(log)


def check_loudness(lufs, peak):
    errs = []
    if lufs is None or not LUFS[0] <= lufs <= LUFS[1]:
        errs.append(f"loudness: {lufs} LUFS, outside {LUFS[0]}..{LUFS[1]}")
    if peak is not None and peak > TRUE_PEAK:
        errs.append(f"loudness: true peak {peak} dBTP above {TRUE_PEAK}")
    return errs


def pcm(path, start, seconds, rate=8000):
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, start):.3f}", "-t", f"{seconds:.3f}", "-i", str(path),
                          "-map", "0:a:0", "-ac", "1", "-ar", str(rate), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32)


def lag_seconds(a, b, rate=8000, max_lag=0.5):
    """How far b's sound is behind a's (seconds), by cross-correlation."""
    import numpy as np
    n = min(len(a), len(b))
    if n < rate // 4:
        return None
    a, b = a[:n] - a[:n].mean(), b[:n] - b[:n].mean()
    size = 1 << (2 * n - 1).bit_length()
    corr = np.fft.irfft(np.fft.rfft(b, size) * np.conj(np.fft.rfft(a, size)), size)
    m = int(max_lag * rate)
    window = np.concatenate([corr[-m:], corr[:m + 1]])
    return (int(np.argmax(window)) - m) / rate


def check_sync(video, base, props):
    errs = []
    points = [2.0] + [b["start"] + 1.0 for b in props["beats"][1:]]
    for t in points:
        if t + 3 > props["duration"]:
            continue
        lag = lag_seconds(pcm(base, t, 3.0), pcm(video, t, 3.0))
        if lag is not None and abs(lag) > FRAME:
            errs.append(f"sync: at {t:.1f} s the video's sound is {lag * 1000:+.0f} ms off the base")
    return errs


def silences(path, noise="-40dB", min_len=1.0):
    log = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-map", "0:a:0", "-af",
                          f"silencedetect=noise={noise}:d={min_len}", "-f", "null", "-"], capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    return list(zip(starts, ends + [float("inf")] * (len(starts) - len(ends))))


def check_silences(sil, props):
    errs, warns = [], []
    cuts = [b["start"] for b in props["beats"][1:]]
    for a, b in sil:
        length = min(b, props["duration"]) - a
        if any(a - 0.05 <= c <= b + 0.05 for c in cuts) and length >= GAP_AT_CUT:
            errs.append(f"dead air: {length:.1f} s of silence across the cut at {a:.1f}-{b:.1f} s")
        elif length >= LONG_SILENCE:
            warns.append(f"silence: {length:.1f} s at {a:.1f} s")
    return errs, warns


def mode_at(props, t):
    for s in props["segments"]:
        if s["start"] <= t < s["end"]:
            return s["mode"]
    return "full"


def wrap_lines(text, width, measure):
    lines, cur = [], ""
    for w in text.split():
        trial = f"{cur} {w}".strip()
        if cur and measure(trial) > width:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    return lines + ([cur] if cur else [])


def check_captions(props, measure=None):
    errs, warns = [], []
    caps, end = props["captions"], props["duration"]
    for i, c in enumerate(caps):
        text = " ".join(w["w"] for w in c["words"])
        where = f"caption {i + 1} ({c['start']:.2f} s, '{text[:30]}')"
        if c["end"] <= c["start"]:
            errs.append(f"{where}: ends before it starts")
        if c["end"] - c["start"] < MIN_ON_SCREEN - 1e-6:
            errs.append(f"{where}: on screen {c['end'] - c['start']:.2f} s, under {MIN_ON_SCREEN}")
        if c["end"] > end + 0.05:
            errs.append(f"{where}: runs past the end ({end:.2f} s)")
        if i and c["start"] < caps[i - 1]["end"] - 1e-3:
            errs.append(f"{where}: overlaps the caption before it")
        if i and c["start"] < caps[i - 1]["start"]:
            errs.append(f"{where}: out of order")
        if c["words"] and (c["start"] > c["words"][0]["start"] + 0.05 or c["end"] < c["words"][-1]["end"] - 0.05):
            errs.append(f"{where}: shows after its first word or leaves before its last")
        if len(text) / max(c["end"] - c["start"], 1e-3) > MAX_CPS:
            warns.append(f"{where}: {len(text) / (c['end'] - c['start']):.0f} characters a second")
        if measure:
            mode = mode_at(props, c["start"])
            lines = wrap_lines(text, CAPTION_WIDTH[mode], measure)
            if len(lines) > 2:
                errs.append(f"{where}: {len(lines)} lines in the {mode} layout ({CAPTION_WIDTH[mode]} px); two at most")
    return errs, warns


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def digest(value) -> str:
    """sha256 of a JSON value, keys sorted: the same recipe as make_lesson_base.py (investing-bros-crypto-course),
    pinned by the same digest in both skills' tests, so its `status` can compare against this record."""
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


LAYOUT_KEYS = ("title", "parts", "part_starts", "disclaimer_beat", "disclaimer_from", "anchors", "segments", "assets")


def fingerprint(cfg: dict) -> dict:
    return {"trims": {str(t["beat"]): [t["file"], t["from"], t["to"]] for t in cfg["takes"]},
            "proofread": {k: digest(v) for k, v in cfg.get("proofread", {}).items()},
            "layout": digest({k: cfg.get(k) for k in LAYOUT_KEYS}),
            "script": (cfg.get("script") or {}).get("snapshot_sha256") or (cfg.get("script") or {}).get("revision")}


def skills_commit(here: Path = Path(__file__).resolve().parent):
    """(commit, dirty) of the skills checkout, dirty meaning any change under skills/; a release ZIP's VERSION
    file otherwise (never dirty: it can't be told)."""
    try:
        top = subprocess.run(["git", "-C", str(here), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        rev = subprocess.run(["git", "-C", str(here), "rev-parse", "HEAD"], capture_output=True, text=True)
        if top.returncode == 0 and rev.returncode == 0:
            dirty = subprocess.run(["git", "-C", top.stdout.strip(), "status", "--porcelain", "--", "skills"],
                                   capture_output=True, text=True).stdout.strip()
            return rev.stdout.strip(), bool(dirty)
    except OSError:
        pass
    for v in (here.parent / "VERSION", here.parent.parent / "VERSION"):
        if v.is_file():
            return v.read_text(encoding="utf-8").strip(), False
    return "unknown", True


def take_file(t, takes_dir: Path):
    for name in (t["file"], f"קטע-{t['beat']:02d}.mp4"):
        if (takes_dir / name).is_file():
            return takes_dir / name
    return None


def export_record(video: Path, info: dict, report: dict, props_path: Path, base: Path, cfg_path: Path,
                  takes_dir=None, manifest=None, made="", commit=("unknown", True), hasher=sha256_file) -> dict:
    """What produced this export and what was checked. Only written for a render that passed."""
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    num, den = (int(x) for x in v["r_frame_rate"].split("/"))
    takes = []
    for t in cfg["takes"]:
        entry = {"beat": t["beat"], "file": t["file"], "from": t["from"], "to": t["to"]}
        f = take_file(t, Path(takes_dir)) if takes_dir else None
        if f is not None:
            entry["sha256" if f.name == t["file"] else "package_sha256"] = hasher(f)
        takes.append(entry)
    script = cfg.get("script") or {}
    return {
        "lesson": cfg["lesson"], "made": made,
        "export": {"file": video.name, "sha256": hasher(video), "seconds": round(float(info["format"]["duration"]), 3),
                   "width": v["width"], "height": v["height"], "fps": round(num / den, 3)},
        "check": report,
        "draft": commit[1],
        "skills": {"commit": commit[0], "dirty": commit[1]},
        "inputs": {"config_sha256": hasher(cfg_path), "props_sha256": hasher(props_path), "base_sha256": hasher(base),
                   **({"manifest_sha256": hasher(Path(manifest))} if manifest else {})},
        "script": {k: script[k] for k in ("doc", "revision", "revision_kind", "snapshot", "snapshot_sha256") if k in script},
        "takes": takes,
        "fingerprint": fingerprint(cfg),
    }


def write_record(rec: dict, folder: Path) -> Path:
    """שיעור-N-ייצוא-<UTC stamp>.json in `folder`; an existing record is never overwritten."""
    folder.mkdir(parents=True, exist_ok=True)
    stamp = re.sub(r"[^0-9TZ]", "", rec["made"].replace("+00:00", "Z"))
    out = folder / f"שיעור-{rec['lesson']}-ייצוא-{stamp}.json"
    if out.exists():
        raise SystemExit(f"error: {out} already exists; export records are never overwritten")
    out.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out


def font_measure(fonts: Path):
    from PIL import ImageFont
    font = ImageFont.truetype(str(fonts / "Heebo-ExtraBold.ttf"), CAPTION_SIZE)
    return lambda text: font.getlength(text)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--props", required=True)
    ap.add_argument("--base")
    ap.add_argument("--fonts", help="the static Heebo TTFs, to measure caption lines")
    ap.add_argument("--json", help="write the report here")
    ap.add_argument("--record", help="when the check passes, write the export record into this folder")
    ap.add_argument("--config", help="--record: the lesson config the props were made from")
    ap.add_argument("--takes-dir", help="--record: the takes, to record their hashes")
    ap.add_argument("--manifest", help="--record: the Drive package manifest, to record its hash")
    a = ap.parse_args(argv)
    if a.record and not (a.config and a.base):
        ap.error("--record needs --config and --base")
    props = json.loads(Path(a.props).read_text(encoding="utf-8"))
    errs, warns = [], []
    info = None
    if not Path(a.video).is_file():
        errs.append(f"media: {a.video} is missing")
    else:
        info = probe(a.video)
        errs += check_media(info)
        length = float(info["format"]["duration"])
        if abs(length - props["duration"]) > 0.1:
            errs.append(f"length: {length:.2f} s, planned {props['duration']:.2f} s")
        errs += check_loudness(*loudness(a.video))
        e, w = check_silences(silences(a.video), props)
        errs += e
        warns += w
        if a.base:
            if not Path(a.base).is_file():
                errs.append(f"media: base {a.base} is missing")
            else:
                b = probe(a.base)
                errs += check_media(b, "base")
                if abs(float(b["format"]["duration"]) - props["duration"]) > 0.1:
                    errs.append(f"media: base is {float(b['format']['duration']):.2f} s, planned {props['duration']:.2f} s")
                errs += check_sync(a.video, a.base, props)
    e, w = check_captions(props, font_measure(Path(a.fonts)) if a.fonts else None)
    errs += e
    warns += w
    for line in errs:
        print(f"FAIL  {line}")
    for line in warns:
        print(f"warn  {line}")
    print("OK" if not errs else f"{len(errs)} problem(s)")
    report = {"errors": errs, "warnings": warns}
    if a.json:
        Path(a.json).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.record and not errs:
        made = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        commit = skills_commit()
        rec = export_record(Path(a.video), info, report, Path(a.props), Path(a.base), Path(a.config), a.takes_dir,
                            a.manifest, made, commit)
        print(f"record: {write_record(rec, Path(a.record))}" + ("  (draft: the skills checkout has local changes)" if commit[1] else ""))
    elif a.record:
        print("no record: the check failed")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
