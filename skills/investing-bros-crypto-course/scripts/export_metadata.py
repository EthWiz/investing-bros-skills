#!/usr/bin/env python3
"""Build and verify a lesson's editable transcript-and-metadata Drive bundle.

Usage:
    python3 export_metadata.py שיעור-N-מניפסט.json --props props.json --srt שיעור-N-כתוביות.srt \
        --record שיעור-N-ייצוא-....json --out transcript-and-metadata \
        --video-url DRIVE_VIDEO_URL --raw-takes-url DRIVE_EXTRAS_URL
    python3 export_metadata.py --verify transcript-and-metadata

Run this after check_lesson.py has passed and written an export record. The props supply proofread
words, beat boundaries and resolved scene timings on the final-video timeline. The manifest supplies
the selected raw takes and trims, script snapshot, departures and notes. All output is UTF-8 text,
JSON, Markdown or SRT; the command verifies the completed bundle before returning success.
"""
import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse


LAYOUTS = {
    "full": "host-full",
    "side": "host-with-side-panel",
    "bubble": "scene-full-with-host-pip",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise SystemExit(f"error: cannot read JSON {path}: {e}") from e


def stamp(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def srt_stamp(seconds: float) -> str:
    return stamp(seconds).replace(".", ",")


def srt_from_props(props: dict) -> str:
    return "\n".join(
        f"{i}\n{srt_stamp(cue['start'])} --> {srt_stamp(cue['end'])}\n"
        f"{' '.join(word['w'] for word in cue['words'])}\n"
        for i, cue in enumerate(props.get("captions") or [], 1)
    )


def srt_seconds(value: str) -> float:
    match = re.fullmatch(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})", value)
    if not match:
        raise SystemExit(f"error: invalid SRT timestamp {value!r}")
    hours, minutes, seconds, millis = (int(part) for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def parse_srt(text: str) -> list:
    """SRT -> display cues, strict enough to catch a stale or unrelated caption file."""
    blocks = re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip())
    cues = []
    for expected, block in enumerate(blocks, 1):
        lines = block.splitlines()
        if len(lines) < 3 or lines[0] != str(expected) or " --> " not in lines[1]:
            raise SystemExit(f"error: malformed SRT cue {expected}")
        start, end = lines[1].split(" --> ", 1)
        cues.append({"start": srt_seconds(start), "end": srt_seconds(end), "text": " ".join(lines[2:]).strip()})
    if not cues:
        raise SystemExit("error: SRT has no cues")
    return cues


def words_from_props(props: dict) -> list:
    """Flatten aligned, proofread caption words and add their beat number."""
    beats = props.get("beats") or []
    if not beats:
        raise SystemExit("error: props has no beats")
    flat = []
    for caption in props.get("captions") or []:
        for item in caption.get("words") or []:
            start, end = item.get("start"), item.get("end")
            word = str(item.get("w", "")).strip()
            if not word or not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
                raise SystemExit("error: every props caption word needs w, start and end")
            candidates = [b for b in beats if b["start"] <= start + 1e-6]
            beat = max(candidates, key=lambda b: b["start"]) if candidates else None
            if beat is None or start > beat["end"] + 0.001:
                raise SystemExit(f"error: word {word!r} at {start:.3f} s is outside every beat")
            flat.append({"beat": beat["n"], "start": round(start, 3), "end": round(end, 3), "word": word})
    if not flat:
        raise SystemExit("error: props has no word-timed captions")
    return flat


def transcript(manifest: dict, props: dict, words: list) -> str:
    """Plain Hebrew transcript, grouped under beat headings with final-video times."""
    script_beats = (manifest.get("script") or {}).get("beats") or {}
    lines = []
    for beat in props["beats"]:
        number = beat["n"]
        title = (script_beats.get(str(number)) or {}).get("title", "")
        heading = f"קטע {number}" + (f": {title}" if title else "")
        lines.append(f"[{stamp(beat['start'])} - {stamp(beat['end'])}] {heading}")
        spoken = " ".join(w["word"] for w in words if w["beat"] == number)
        lines.extend((spoken, ""))
    return "\n".join(lines).rstrip() + "\n"


def timeline(manifest: dict, props: dict) -> dict:
    """Raw-take trims mapped to final time, plus resolved layout and animation segments."""
    takes = {t["beat"]: t for t in manifest.get("takes") or []}
    package_takes = (manifest.get("package") or {}).get("takes") or {}
    beats = []
    for beat in props.get("beats") or []:
        number = beat["n"]
        if number not in takes:
            raise SystemExit(f"error: props beat {number} has no take in the manifest")
        take = takes[number]
        final_duration = round(beat["end"] - beat["start"], 3)
        raw_duration = round(take["to"] - take["from"], 3)
        if abs(final_duration - raw_duration) > 0.002:
            raise SystemExit(
                f"error: beat {number}: final duration {final_duration} does not match raw trim {raw_duration}"
            )
        package_take = package_takes.get(str(number), {})
        beats.append({
            "beat": number,
            "raw_take": {
                "recorded_as": take["file"],
                **({"drive_file": package_take["drive"]} if package_take.get("drive") else {}),
                "start": round(take["from"], 3),
                "end": round(take["to"], 3),
            },
            "final": {"start": round(beat["start"], 3), "end": round(beat["end"], 3)},
        })
    segments = []
    for segment in props.get("segments") or []:
        mode = segment.get("mode")
        if mode not in LAYOUTS:
            raise SystemExit(f"error: unknown props segment mode {mode!r}")
        entry = {
            "start": round(segment["start"], 3),
            "end": round(segment["end"], 3),
            "mode": mode,
            "layout": LAYOUTS[mode],
            "host_pip": mode == "bubble",
            "scene": segment.get("scene"),
        }
        for key in ("zoom", "content"):
            if key in segment:
                entry[key] = segment[key]
        segments.append(entry)
    return {
        "schema_version": 1,
        "time_unit": "seconds",
        "duration": round(props["duration"], 3),
        "beats": beats,
        "segments": segments,
        "animation": {
            "title": props.get("title") or [],
            "parts": props.get("parts") or [],
            "part_starts": props.get("partStarts") or [],
            "at": props.get("at") or {},
            "disclaimer": props.get("disclaimer"),
            "face": props.get("face"),
            "assets": props.get("assets") or {},
            "asset_sources": props.get("assetSources") or {},
            "background": manifest.get("background"),
        },
    }


def markdown_departures(manifest: dict) -> str:
    departures = (manifest.get("script") or {}).get("departures") or {}
    lines = ["# Script departures", "", "Differences deliberately made from the saved script snapshot.", ""]
    if departures:
        lines.extend(f"- Beat {beat}: {why}" for beat, why in sorted(departures.items(), key=lambda x: int(x[0])))
    else:
        lines.append("- None recorded.")
    return "\n".join(lines) + "\n"


def note_lines(notes) -> list:
    if not notes:
        return []
    if isinstance(notes, dict):
        return [f"- {key}: {value}" for key, value in notes.items()]
    if isinstance(notes, list):
        return [f"- {value}" for value in notes]
    return [f"- {notes}"]


def markdown_issues(manifest: dict, record: dict) -> str:
    lines = ["# Known issues", ""]
    issues = note_lines(manifest.get("notes"))
    issues += [f"- Check warning: {warning}" for warning in (record.get("check") or {}).get("warnings", [])]
    lines.extend(issues or ["- None recorded."])
    lines += [
        "",
        "## Caption-timing caveat",
        "",
        "The words are proofread text aligned to Whisper's estimated word boundaries. They are suitable for "
        "search, captions and later editing, but are not frame-accurate manual speech annotations. SRT cue "
        "ends may be extended for reading time, so SRT cue boundaries are display times rather than exact "
        "speech boundaries. All exported word and SRT times use the final-video timeline.",
    ]
    return "\n".join(lines) + "\n"


def readme(lesson: int, names: dict, video_url: str, raw_takes_url: str, checked_export: dict) -> str:
    return f"""# Lesson {lesson} transcript and metadata

This editable bundle describes the checked lesson export.

## Media links

- [Final lesson video]({video_url})
- [Raw takes and rebuild package]({raw_takes_url})
- Checked export file: `{checked_export['file']}`
- Checked export SHA-256: `{checked_export['sha256']}`

## Files

- `{names['transcript']}`: Hebrew transcript of what was said, grouped by beat with final-video timestamps.
- `{names['words']}`: one JSON array entry per proofread spoken word on the final-video timeline.
- `{names['srt']}`: subtitles used by the checked export, on the final-video display timeline.
- `{names['manifest']}`: lesson config/manifest snapshot used for this bundle.
- `{names['timeline']}`: raw-take trims mapped to final time, plus every resolved layout and animation segment.
- `{names['script']}`: unedited snapshot of the Google Doc script named by the manifest.
- `{names['departures']}`: deliberate departures from that script, copied from `script.departures`.
- `{names['issues']}`: manifest notes, check warnings, and the required caption-timing caveat.
- `README.md`: this inventory, schema and time-base reference.

All files are UTF-8 text, JSON, Markdown or SRT and remain directly editable.

## Time bases

- **Final-video time:** seconds from the first frame of the checked final video. The transcript, word JSON,
  SRT, timeline `final` ranges and timeline segments use this time base.
- **Raw-take time:** seconds from the start of each original take. Only timeline `raw_take.start` and
  `raw_take.end`, and the manifest take trims, use this time base.
- For each beat: `final_time = raw_take_time - raw_take.start + final.start`.
- Times are decimal seconds rounded to milliseconds. Transcript stamps are `HH:MM:SS.mmm`; SRT uses
  `HH:MM:SS,mmm`.
- SRT cue ends can include reading-time holds. See `{names['issues']}` before treating cue boundaries as speech.

## JSON schemas

### `{names['words']}`

The root is an array, ordered by final time. Every object has exactly:

- `beat` (integer): manifest beat number.
- `start` (number): word start in final-video seconds.
- `end` (number): word end in final-video seconds.
- `word` (string): proofread spoken word, including its display punctuation.

### `{names['timeline']}`

- `schema_version` (integer): this timeline schema version.
- `time_unit` (`"seconds"`).
- `duration` (number): final-video duration.
- `beats` (array): each item has `beat`; `raw_take` with `recorded_as`, optional `drive_file`, `start`, `end`;
  and `final` with `start`, `end`.
- `segments` (array): consecutive final-time ranges with `start`, `end`, manifest `mode`, explicit `layout`,
  `host_pip`, optional `scene`, optional `zoom`, and resolved animation `content`.
- `animation` (object): resolved overlay anchors in `at`, title, lesson parts and `part_starts`, disclaimer
  range, face point, assets and their sources, and the manifest background. Its times are final-video seconds.
- Layout values are `host-full` (`mode: full`), `host-with-side-panel` (`mode: side`), and
  `scene-full-with-host-pip` (`mode: bubble`).

### `{names['manifest']}`

This is the production config/manifest, not a separate normalized schema. Its main fields are `lesson`,
`takes` (raw files and trims), `proofread`, `script` (Doc revision, beat notes, snapshot and departures),
`anchors`, `segments` (unresolved production anchors and scene content), `assets`, `notes`, and `package`
(rebuild filenames and provenance). Production segment anchors are resolved into final seconds in
`{names['timeline']}`.
"""


def expected_names(lesson: int, script_name: str) -> dict:
    prefix = f"שיעור-{lesson}"
    return {
        "transcript": f"{prefix}-תמליל.txt",
        "words": f"{prefix}-מילים.json",
        "srt": f"{prefix}-כתוביות.srt",
        "manifest": f"{prefix}-מניפסט.json",
        "timeline": f"{prefix}-ציר-זמן.json",
        "script": script_name,
        "departures": f"{prefix}-סטיות-מהתסריט.md",
        "issues": f"{prefix}-בעיות-ידועות.md",
    }


def script_path(manifest_path: Path, manifest: dict) -> Path:
    name = (manifest.get("script") or {}).get("snapshot")
    if not name:
        raise SystemExit("error: manifest script.snapshot is missing")
    path = manifest_path.parent / name
    if not path.is_file():
        raise SystemExit(f"error: script snapshot {path} is missing")
    expected = (manifest.get("script") or {}).get("snapshot_sha256")
    if expected and sha256_file(path) != expected:
        raise SystemExit("error: script snapshot hash does not match script.snapshot_sha256")
    return path


def check_drive_url(value: str, kind: str):
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.netloc != "drive.google.com":
        raise SystemExit(f"error: {kind} must be an https://drive.google.com link")
    if kind == "video URL" and not re.search(r"/file/d/[^/]+", parsed.path):
        raise SystemExit("error: video URL must be a Drive file link (/file/d/...)")
    if kind == "raw-takes URL" and not re.search(r"/folders/[^/]+", parsed.path):
        raise SystemExit("error: raw-takes URL must be a Drive folder link (/folders/...)")


def check_record(record: dict, lesson: int, props_path: Path, manifest_path: Path):
    if record.get("lesson") != lesson:
        raise SystemExit(f"error: export record is for lesson {record.get('lesson')}, not lesson {lesson}")
    errors = (record.get("check") or {}).get("errors")
    if errors is None:
        raise SystemExit("error: export record has no check.errors result")
    if errors:
        raise SystemExit(f"error: export record did not pass check_lesson.py: {errors}")
    checked_export = record.get("export") or {}
    if not checked_export.get("file") or not re.fullmatch(r"[0-9a-f]{64}", checked_export.get("sha256", "")):
        raise SystemExit("error: export record does not identify the checked video file and SHA-256")
    inputs = record.get("inputs") or {}
    props_hash = inputs.get("props_sha256")
    if not props_hash:
        raise SystemExit("error: export record does not pin props_sha256")
    if props_hash != sha256_file(props_path):
        raise SystemExit("error: props do not match the checked export record")
    manifest_hash = inputs.get("manifest_sha256")
    if not manifest_hash:
        raise SystemExit("error: export record does not pin manifest_sha256; rerun check_lesson.py with --manifest")
    if manifest_hash != sha256_file(manifest_path):
        raise SystemExit("error: manifest does not match the checked export record")
    manifest = read_json(manifest_path)
    config_hash = (manifest.get("package") or {}).get("config_sha256")
    if not config_hash or config_hash != inputs.get("config_sha256"):
        raise SystemExit("error: manifest package does not match the checked lesson config")
    snapshot_hash = (manifest.get("script") or {}).get("snapshot_sha256")
    record_snapshot_hash = (record.get("script") or {}).get("snapshot_sha256")
    if not snapshot_hash or snapshot_hash != record_snapshot_hash:
        raise SystemExit("error: manifest script snapshot does not match the checked export record")


def verify_bundle(folder: Path) -> int:
    if not folder.is_dir():
        raise SystemExit(f"error: bundle folder {folder} is missing")
    nested = sorted(path.relative_to(folder).as_posix() for path in folder.rglob("*") if path.is_dir())
    if nested:
        raise SystemExit(f"error: bundle must contain editable files only, not subfolders: {', '.join(nested)}")
    manifests = list(folder.glob("שיעור-*-מניפסט.json"))
    if len(manifests) != 1:
        raise SystemExit(f"error: bundle needs exactly one שיעור-N-מניפסט.json, found {len(manifests)}")
    manifest = read_json(manifests[0])
    lesson = manifest.get("lesson")
    snapshot = Path((manifest.get("script") or {}).get("snapshot", "")).name
    if not isinstance(lesson, int) or not snapshot:
        raise SystemExit("error: bundle manifest needs integer lesson and script.snapshot")
    names = expected_names(lesson, snapshot)
    required = set(names.values()) | {"README.md"}
    missing = sorted(name for name in required if not (folder / name).is_file())
    if missing:
        raise SystemExit(f"error: incomplete transcript-and-metadata bundle; missing {', '.join(missing)}")
    for path in folder.iterdir():
        if path.is_file():
            try:
                path.read_text(encoding="utf-8")
            except UnicodeDecodeError as e:
                raise SystemExit(f"error: bundle file {path.name} is not editable UTF-8 text") from e
    words = read_json(folder / names["words"])
    if not isinstance(words, list) or not words:
        raise SystemExit("error: word JSON must be a non-empty array")
    for i, word in enumerate(words):
        if set(word) != {"beat", "start", "end", "word"}:
            raise SystemExit(f"error: word JSON entry {i} does not have exactly beat, start, end, word")
        if not isinstance(word["beat"], int) or not isinstance(word["word"], str):
            raise SystemExit(f"error: word JSON entry {i} has the wrong field types")
        if not 0 <= word["start"] <= word["end"]:
            raise SystemExit(f"error: word JSON entry {i} has invalid times")
        if i and word["start"] < words[i - 1]["start"]:
            raise SystemExit("error: word JSON is not ordered by final time")
    tl = read_json(folder / names["timeline"])
    if tl.get("schema_version") != 1 or tl.get("time_unit") != "seconds":
        raise SystemExit("error: unsupported timeline schema")
    if not tl.get("beats") or not tl.get("segments") or not isinstance(tl.get("animation"), dict):
        raise SystemExit("error: timeline needs beats, segments and animation metadata")
    for beat in tl["beats"]:
        raw, final = beat["raw_take"], beat["final"]
        if abs((raw["end"] - raw["start"]) - (final["end"] - final["start"])) > 0.002:
            raise SystemExit(f"error: beat {beat['beat']} raw/final mapping durations differ")
    if tl["segments"][0]["start"] != 0 or abs(tl["segments"][-1]["end"] - tl["duration"]) > 0.002:
        raise SystemExit("error: timeline segments do not cover the final video")
    for left, right in zip(tl["segments"], tl["segments"][1:]):
        if abs(left["end"] - right["start"]) > 0.002:
            raise SystemExit("error: timeline segments are not consecutive")
    cues = parse_srt((folder / names["srt"]).read_text(encoding="utf-8"))
    cursor = 0
    for i, cue in enumerate(cues):
        cue_words = cue["text"].split()
        aligned = words[cursor:cursor + len(cue_words)]
        if [word["word"] for word in aligned] != cue_words:
            raise SystemExit(f"error: SRT cue {i + 1} does not match the word JSON")
        if cue["start"] > aligned[0]["start"] + 0.051 or cue["end"] < aligned[-1]["end"] - 0.051:
            raise SystemExit(f"error: SRT cue {i + 1} does not cover its spoken words")
        if cue["end"] > tl["duration"] + 0.051 or cue["end"] <= cue["start"]:
            raise SystemExit(f"error: SRT cue {i + 1} is outside the final timeline")
        if i and cue["start"] < cues[i - 1]["end"] - 0.001:
            raise SystemExit(f"error: SRT cue {i + 1} overlaps the cue before it")
        cursor += len(cue_words)
    if cursor != len(words):
        raise SystemExit("error: SRT does not contain every word in the word JSON")
    readme_text = (folder / "README.md").read_text(encoding="utf-8")
    actual = {path.name for path in folder.iterdir() if path.is_file()}
    undocumented = sorted(name for name in actual if name != "README.md" and f"`{name}`" not in readme_text)
    if undocumented:
        raise SystemExit(f"error: README does not document {', '.join(undocumented)}")
    snap_hash = (manifest.get("script") or {}).get("snapshot_sha256")
    if snap_hash and sha256_file(folder / snapshot) != snap_hash:
        raise SystemExit("error: bundled script snapshot hash does not match the manifest")
    print(f"{folder}: OK ({len(required)} editable files, {len(words)} words)")
    return 0


def export(args) -> int:
    manifest_path = Path(args.manifest)
    props_path = Path(args.props)
    srt_path = Path(args.srt)
    record_path = Path(args.record)
    for label, path in (("manifest", manifest_path), ("props", props_path), ("SRT", srt_path),
                        ("export record", record_path)):
        if not path.is_file():
            raise SystemExit(f"error: {label} {path} is missing")
    manifest, props, record = read_json(manifest_path), read_json(props_path), read_json(record_path)
    lesson = manifest.get("lesson")
    if not isinstance(lesson, int) or props.get("lesson") != lesson:
        raise SystemExit("error: manifest and props need the same integer lesson number")
    if abs(float(props.get("duration", -1)) - float((record.get("export") or {}).get("seconds", -2))) > 0.1:
        raise SystemExit("error: props duration does not match the checked export record")
    check_drive_url(args.video_url, "video URL")
    check_drive_url(args.raw_takes_url, "raw-takes URL")
    check_record(record, lesson, props_path, manifest_path)
    supplied_srt = srt_path.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
    expected_srt = srt_from_props(props).strip()
    if supplied_srt != expected_srt:
        raise SystemExit("error: SRT does not match the checked props")
    snapshot = script_path(manifest_path, manifest)
    names = expected_names(lesson, snapshot.name)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    words = words_from_props(props)
    generated = {
        names["transcript"]: transcript(manifest, props, words),
        names["words"]: json.dumps(words, ensure_ascii=False, indent=1) + "\n",
        names["timeline"]: json.dumps(timeline(manifest, props), ensure_ascii=False, indent=1) + "\n",
        names["departures"]: markdown_departures(manifest),
        names["issues"]: markdown_issues(manifest, record),
        "README.md": readme(lesson, names, args.video_url, args.raw_takes_url, record["export"]),
    }
    for name, text in generated.items():
        (out / name).write_text(text, encoding="utf-8")
    for src, dst_name in ((manifest_path, names["manifest"]), (srt_path, names["srt"]),
                          (snapshot, names["script"])):
        if src.resolve() != (out / dst_name).resolve():
            shutil.copyfile(src, out / dst_name)
    verify_bundle(out)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest", nargs="?", help="lesson config/manifest from make_lesson_base.py --extras")
    ap.add_argument("--props", help="checked render's props.json")
    ap.add_argument("--srt", help="checked render's SRT")
    ap.add_argument("--record", help="passing check_lesson.py export record")
    ap.add_argument("--out", help="output transcript-and-metadata folder")
    ap.add_argument("--video-url", help="Drive link to this checked video version")
    ap.add_argument("--raw-takes-url", help="Drive link to the extras folder containing the raw takes")
    ap.add_argument("--verify", metavar="FOLDER", help="only verify an existing bundle")
    args = ap.parse_args(argv)
    if args.verify:
        if args.manifest or any((args.props, args.srt, args.record, args.out, args.video_url, args.raw_takes_url)):
            ap.error("--verify cannot be combined with export arguments")
        return verify_bundle(Path(args.verify))
    missing = [name for name in ("manifest", "props", "srt", "record", "out", "video_url", "raw_takes_url")
               if not getattr(args, name)]
    if missing:
        ap.error("export needs " + ", ".join("--" + name.replace("_", "-") for name in missing))
    return export(args)


if __name__ == "__main__":
    sys.exit(main())
