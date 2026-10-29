"""Tests for export_metadata.py's editable final-timeline lesson bundle."""
import hashlib
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from export_metadata import export, verify_bundle, words_from_props  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    snapshot = tmp_path / "תסריט-שיעור-2-2026-10-29.md"
    snapshot.write_text("## קטע 1: פתיחה\nשלום.\n\n## קטע 2: הסבר\nעולם חדש.\n", encoding="utf-8")
    manifest = {
        "lesson": 2,
        "takes": [
            {"beat": 1, "file": "Beat 1.mov", "from": 1.0, "to": 5.0},
            {"beat": 2, "file": "Beat 2.mov", "from": 2.0, "to": 7.0},
        ],
        "script": {
            "snapshot": snapshot.name,
            "snapshot_sha256": sha(snapshot),
            "beats": {"1": {"title": "פתיחה"}, "2": {"title": "הסבר"}},
            "departures": {"2": "The card stays beside Amitai instead of covering him."},
        },
        "notes": {"audio": "A restart remains in beat 2."},
        "package": {
            "config_sha256": "a" * 64,
            "takes": {
                "1": {"drive": "קטע-01.mp4", "recorded_as": "Beat 1.mov"},
                "2": {"drive": "קטע-02.mp4", "recorded_as": "Beat 2.mov"},
            }
        },
    }
    manifest_path = tmp_path / "שיעור-2-מניפסט.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    props = {
        "lesson": 2,
        "duration": 9.0,
        "title": ["עולם חדש"],
        "parts": ["פתיחה", "הסבר"],
        "partStarts": [0.0, 4.0],
        "at": {"title": 0.5, "name": 1.0},
        "disclaimer": {"start": 3.0, "end": 4.0},
        "face": {"x": 840, "y": 450},
        "assets": {"page": "assets/page.png"},
        "assetSources": {"page": "https://example.com/page"},
        "beats": [{"n": 1, "start": 0.0, "end": 4.0}, {"n": 2, "start": 4.0, "end": 9.0}],
        "segments": [
            {"start": 0.0, "end": 4.0, "mode": "full", "zoom": 1.1},
            {"start": 4.0, "end": 7.0, "mode": "side", "scene": "terms", "content": {"title": "חדש"}},
            {"start": 7.0, "end": 9.0, "mode": "bubble", "scene": "flow"},
        ],
        "captions": [
            {"start": 0.5, "end": 1.5, "words": [
                {"w": "שלום.", "start": 0.5, "end": 0.9},
            ]},
            {"start": 4.2, "end": 5.8, "words": [
                {"w": "עולם", "start": 4.2, "end": 4.6},
                {"w": "חדש.", "start": 4.7, "end": 5.1},
            ]},
        ],
    }
    props_path = tmp_path / "props.json"
    props_path.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    srt = tmp_path / "שיעור-2-כתוביות.srt"
    srt.write_text(
        "1\n00:00:00,500 --> 00:00:01,500\nשלום.\n\n"
        "2\n00:00:04,200 --> 00:00:05,800\nעולם חדש.\n",
        encoding="utf-8",
    )
    record = {
        "lesson": 2,
        "export": {"file": "שיעור-2-וידאו.mp4", "sha256": "b" * 64, "seconds": 9.0},
        "check": {"errors": [], "warnings": ["caption 2 is fast"]},
        "inputs": {
            "config_sha256": "a" * 64,
            "props_sha256": sha(props_path),
            "manifest_sha256": sha(manifest_path),
        },
        "script": {"snapshot_sha256": sha(snapshot)},
    }
    record_path = tmp_path / "שיעור-2-ייצוא-20261029T080000Z.json"
    record_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    args = SimpleNamespace(
        manifest=str(manifest_path),
        props=str(props_path),
        srt=str(srt),
        record=str(record_path),
        out=str(tmp_path / "transcript-and-metadata"),
        video_url="https://drive.google.com/file/d/VIDEO/view",
        raw_takes_url="https://drive.google.com/drive/folders/EXTRAS",
    )
    return args, record_path


def test_export_builds_and_verifies_the_editable_bundle(tmp_path):
    args, _ = fixture(tmp_path)
    assert export(args) == 0
    out = Path(args.out)
    assert verify_bundle(out) == 0

    words = json.loads((out / "שיעור-2-מילים.json").read_text(encoding="utf-8"))
    assert words == [
        {"beat": 1, "start": 0.5, "end": 0.9, "word": "שלום."},
        {"beat": 2, "start": 4.2, "end": 4.6, "word": "עולם"},
        {"beat": 2, "start": 4.7, "end": 5.1, "word": "חדש."},
    ]
    transcript = (out / "שיעור-2-תמליל.txt").read_text(encoding="utf-8")
    assert "[00:00:00.000 - 00:00:04.000] קטע 1: פתיחה" in transcript
    assert "[00:00:04.000 - 00:00:09.000] קטע 2: הסבר" in transcript
    assert "עולם חדש." in transcript

    timeline = json.loads((out / "שיעור-2-ציר-זמן.json").read_text(encoding="utf-8"))
    assert timeline["beats"][1] == {
        "beat": 2,
        "raw_take": {"recorded_as": "Beat 2.mov", "drive_file": "קטע-02.mp4", "start": 2.0, "end": 7.0},
        "final": {"start": 4.0, "end": 9.0},
    }
    assert [s["layout"] for s in timeline["segments"]] == [
        "host-full", "host-with-side-panel", "scene-full-with-host-pip"
    ]
    assert timeline["segments"][-1]["host_pip"] is True
    assert timeline["animation"]["at"] == {"title": 0.5, "name": 1.0}
    assert timeline["animation"]["disclaimer"] == {"start": 3.0, "end": 4.0}
    assert timeline["animation"]["asset_sources"] == {"page": "https://example.com/page"}

    issues = (out / "שיעור-2-בעיות-ידועות.md").read_text(encoding="utf-8")
    assert "A restart remains in beat 2." in issues
    assert "caption 2 is fast" in issues
    assert "SRT cue boundaries are display times" in issues
    readme = (out / "README.md").read_text(encoding="utf-8")
    assert args.video_url in readme and args.raw_takes_url in readme
    assert "final_time = raw_take_time - raw_take.start + final.start" in readme
    assert (out / "תסריט-שיעור-2-2026-10-29.md").read_text(encoding="utf-8").startswith("## קטע 1")


def test_export_refuses_a_failed_or_mismatched_check_record(tmp_path):
    args, record_path = fixture(tmp_path)
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["check"]["errors"] = ["length mismatch"]
    record_path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(SystemExit, match="did not pass"):
        export(args)

    record["check"]["errors"] = []
    record["inputs"]["props_sha256"] = "wrong"
    record_path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(SystemExit, match="props do not match"):
        export(args)

    record["inputs"]["props_sha256"] = sha(Path(args.props))
    record_path.write_text(json.dumps(record), encoding="utf-8")
    args.video_url = "wrong-version"
    with pytest.raises(SystemExit, match="drive.google.com"):
        export(args)


def test_export_refuses_an_srt_from_another_render(tmp_path):
    args, _ = fixture(tmp_path)
    Path(args.srt).write_text("1\n00:00:00,000 --> 00:00:01,000\nטקסט אחר\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="SRT does not match"):
        export(args)


def test_word_on_a_cut_belongs_to_the_beat_that_starts_there():
    props = {
        "beats": [{"n": 1, "start": 0.0, "end": 4.0}, {"n": 2, "start": 4.0, "end": 8.0}],
        "captions": [{"words": [{"w": "התחלה", "start": 4.0, "end": 4.4}]}],
    }
    assert words_from_props(props) == [{"beat": 2, "start": 4.0, "end": 4.4, "word": "התחלה"}]


def test_verify_refuses_an_incomplete_or_binary_bundle(tmp_path):
    args, _ = fixture(tmp_path)
    export(args)
    out = Path(args.out)
    (out / "שיעור-2-תמליל.txt").unlink()
    with pytest.raises(SystemExit, match="incomplete"):
        verify_bundle(out)

    args, _ = fixture(tmp_path / "again")
    export(args)
    out = Path(args.out)
    (out / "not-editable.bin").write_bytes(b"\xff\xfe")
    with pytest.raises(SystemExit, match="not editable UTF-8"):
        verify_bundle(out)

    args, _ = fixture(tmp_path / "stale")
    export(args)
    out = Path(args.out)
    (out / "old-script.md").write_text("old", encoding="utf-8")
    with pytest.raises(SystemExit, match="README does not document old-script.md"):
        verify_bundle(out)

    args, _ = fixture(tmp_path / "nested")
    export(args)
    out = Path(args.out)
    (out / "stale").mkdir()
    (out / "stale" / "words.json").write_text("[]", encoding="utf-8")
    with pytest.raises(SystemExit, match="not subfolders"):
        verify_bundle(out)
