#!/usr/bin/env python3
"""Re-render only what changed in a lesson and splice it into the previous export (render_lesson.py --patch).

A full lesson render takes 10-13 minutes; a new chart or a caption fix changes a few seconds of it. Every full
render (and every patch) leaves a sidecar beside the video, `<out>.render.json`: the props it was rendered from
and the hashes of the template's src/, the base and the scenes' images. --patch compares the new props with it:
- the template, the base, an image, or anything lesson-wide (duration, beats, face, title, parts) changed:
  refused, render in full. A template change can still be patched with an explicit --range START-END (seconds),
  since only the caller knows which scenes the change touches;
- otherwise the changed stretches are worked out from the props: captions that differ, segments that differ
  (their whole span, plus the glide into the next one), anchors that moved (to the end of the scene using them)
  and the disclaimer strip, each padded for entrances and fades, then widened to the previous export's keyframes.
Only those frames are rendered (muted, the same codec settings), and the rest of the previous export is
stream-copied around them; the audio is the previous export's, untouched (it is the base's sound, already lined
up). The splice is refused if the new frames were encoded with different parameter sets, and checked
afterwards: the same frame count, and every join decodes without an error. Run check_lesson.py after, as always.
"""
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

FPS = 30
PAD_BEFORE, PAD_AFTER = 1.0, 1.5   # entrances start ~0.1 s early; fades, glides and springs settle within ~0.8 s
ANCHOR_HOLD = 5.0                  # strips and titles on an anchor stay up to ~4 s
MERGE_GAP = 2.0
LESSON_WIDE = ("duration", "beats", "face", "title", "lesson", "parts", "partStarts", "assets")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(q for q in root.rglob("*") if q.is_file()):
        h.update(str(p.relative_to(root)).encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def sidecar_path(out: Path) -> Path:
    return out.with_name(out.name + ".render.json")


def fingerprint(props: dict, template_src: Path, base: Path) -> dict:
    return {"template": tree_hash(template_src), "base": sha256_file(base),
            "assets": {k: sha256_file(Path(v)) for k, v in sorted(props.get("assetSources", {}).items())}}


def write_sidecar(out: Path, props: dict, fp: dict):
    sidecar_path(out).write_text(json.dumps({"fingerprint": fp, "props": props}, ensure_ascii=False), encoding="utf-8")


def why_full(old: dict, new: dict, old_fp: dict, new_fp: dict, explicit: bool) -> list:
    """Reasons a patch can't be trusted; empty means it can."""
    why = [f"props '{k}' changed" for k in LESSON_WIDE if old.get(k) != new.get(k)]
    if old_fp["base"] != new_fp["base"]:
        why.append("the base changed")
    if old_fp["assets"] != new_fp["assets"]:
        why.append("a scene image changed")
    if old_fp["template"] != new_fp["template"] and not explicit:
        why.append("the template changed (patch it with --range START-END if you know where the change shows)")
    return why


def _key(x) -> str:
    return json.dumps(x, sort_keys=True, ensure_ascii=False)


def _segment_end_at(segs: list, t: float) -> float:
    for s in segs:
        if s.get("scene") and s["start"] <= t < s["end"]:
            return s["end"]
    return t


def changed_ranges(old: dict, new: dict) -> list:
    """The stretches of the lesson (seconds) whose frames differ between two props, padded and merged."""
    out = []
    for a, b in ((old, new), (new, old)):
        keep = {_key(c) for c in b["captions"]}
        out += [(c["start"] - PAD_BEFORE / 2, c["end"] + PAD_BEFORE / 2) for c in a["captions"] if _key(c) not in keep]
        segs, others = a["segments"], b["segments"]
        keep = {_key(s) for s in others}
        out += [(s["start"] - PAD_BEFORE, s["end"] + PAD_AFTER) for s in segs if _key(s) not in keep]
        for k, t in a.get("at", {}).items():
            if b.get("at", {}).get(k) != t:
                out.append((t - PAD_BEFORE, max(t + ANCHOR_HOLD, _segment_end_at(segs, t) + PAD_AFTER)))
    if old.get("disclaimer") != new.get("disclaimer"):
        for d in (old.get("disclaimer"), new.get("disclaimer")):
            if d:
                out.append((d["start"] - PAD_BEFORE, d["end"] + PAD_AFTER))
    return merge(out, new["duration"])


def merge(ranges, duration: float, gap: float = MERGE_GAP) -> list:
    spans = sorted((max(0.0, a), min(duration, b)) for a, b in ranges if b > 0 and a < duration)
    merged = []
    for a, b in spans:
        if merged and a <= merged[-1][1] + gap:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    return merged


def snap(ranges, keyframes: list, total_frames: int) -> list:
    """Widen each (start, end) in seconds to whole GOPs of the previous export: [first frame, end frame) pairs."""
    kf = sorted(set(keyframes) | {0})
    spans = []
    for a, b in ranges:
        fa, fb = round(a * FPS), round(b * FPS)
        first = max(k for k in kf if k <= fa)
        later = [k for k in kf if k >= fb]
        spans.append((first, later[0] if later else total_frames))
    out = []
    for a, b in sorted(spans):
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def plan(spans: list, total_frames: int) -> list:
    """The parts of the new video in order: ("copy"|"render", first frame, end frame)."""
    parts, cur = [], 0
    for a, b in spans:
        if a > cur:
            parts.append(("copy", cur, a))
        parts.append(("render", a, b))
        cur = b
    if cur < total_frames:
        parts.append(("copy", cur, total_frames))
    return parts


def keyframes(video: Path) -> list:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-skip_frame", "nokey",
                        "-show_entries", "frame=pts_time", "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True, check=True)
    return [round(float(x.strip(",")) * FPS) for x in r.stdout.split() if x.strip(",")]


def frame_count(video: Path) -> int:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
                        "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True, check=True)
    return int(r.stdout.strip().strip(","))


def frame_times(video: Path) -> list:
    """Every frame's presentation time, as a frame number, in file order (from the packets; nothing is decoded)."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time",
                        "-of", "csv=p=0", str(video)], capture_output=True, text=True, check=True)
    return [round(float(x.strip(",")) * FPS) for x in r.stdout.split() if x.strip(",")]


def parameter_sets(video: Path) -> bytes:
    """The H.264 SPS and PPS of the first frame: parts made with other ones can't be stream-copied together."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-map", "0:v:0", "-c", "copy", "-frames:v", "1",
                          "-bsf:v", "h264_mp4toannexb", "-f", "h264", "-"], capture_output=True, check=True).stdout
    nals = [n for n in re.split(b"\x00\x00\x01", raw) if n]
    return b"|".join(n.rstrip(b"\x00") for n in nals if n[0] & 0x1F in (7, 8))


def copy_cmd(src: Path, dst: Path, first: int, frames: int):
    # `first` is a keyframe: seek to exactly its time. A stream copy shifts the part's timestamps by the seek, not by
    # the keyframe, so 4 ms past it left the part 4 ms short and the joined frames out of order; 1 ms early took the
    # GOP before. Rounded to the microsecond it lands (checked at 24.1333 s-style times, test_lesson_patch.py).
    seek = ["-ss", f"{first / FPS:.6f}"] if first else []
    return ["ffmpeg", "-v", "error", "-y", *seek, "-i", str(src), "-map", "0:v:0", "-an", "-c", "copy",
            "-frames:v", str(frames), str(dst)]


def join_cmd(listing: Path, audio_from: Path, dst: Path):
    return ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-i", str(audio_from),
            "-map", "0:v:0", "-map", "1:a:0", "-c", "copy", "-movflags", "+faststart", str(dst)]


def decode_errors(video: Path, at: float, seconds: float = 2.0) -> str:
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, at - seconds / 2):.3f}", "-i", str(video),
                        "-t", f"{seconds:.3f}", "-map", "0:v:0", "-f", "null", "-"], capture_output=True, text=True)
    return r.stderr.strip()


def splice(prev: Path, out: Path, parts: list, render, work: Path) -> list:
    """Build `out` from `prev` and freshly rendered parts. `render(first, last, dst)` renders frames
    first..last (inclusive) to dst, muted. Returns the join times (seconds) it checked."""
    work.mkdir(parents=True, exist_ok=True)
    total = frame_count(prev)
    sets = parameter_sets(prev)
    files = []
    for i, (kind, a, b) in enumerate(parts):
        dst = work / f"part_{i:02d}_{kind}.mp4"
        if kind == "copy":
            subprocess.run(copy_cmd(prev, dst, a, b - a), check=True)
        else:
            render(a, b - 1, dst)
            if parameter_sets(dst) != sets:
                raise SystemExit("error: the new frames were encoded with other H.264 parameters than the previous "
                                 "export; render in full")
        n = frame_count(dst)
        if n != b - a:
            raise SystemExit(f"error: part {i} ({kind} {a}-{b}) has {n} frames, not {b - a}; render in full")
        files.append(dst)
    listing = work / "parts.txt"
    listing.write_text("".join(f"file '{f}'\n" for f in files), encoding="utf-8")
    subprocess.run(join_cmd(listing, prev, out), check=True)
    if frame_count(out) != total:
        raise SystemExit(f"error: the spliced video has {frame_count(out)} frames, the previous export {total}")
    if sorted(frame_times(out)) != list(range(total)):
        raise SystemExit("error: the spliced video's frames aren't each shown once, in order; render in full")
    joins = [a / FPS for _, a, _ in parts[1:]]
    for t in joins:
        err = decode_errors(out, t)
        if err:
            raise SystemExit(f"error: the join at {t:.2f} s doesn't decode cleanly: {err.splitlines()[0]}")
    shutil.rmtree(work, ignore_errors=True)
    return joins


def parse_range(text: str) -> tuple:
    a, b = (float(x) for x in text.split("-", 1))
    if b <= a:
        raise ValueError(f"empty range {text}")
    return a, b
