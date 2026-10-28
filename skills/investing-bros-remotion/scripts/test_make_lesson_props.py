"""Tests for make_lesson_props.py (anchors, scene needs, layout rules, sentence-safe captions, script intake)."""
import copy
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from make_lesson_props import (build, check_words_match_takes, known_scenes, load_words, scene_manifest,  # noqa: E402
                               sha256_file, srt, tidy)

EXAMPLE = (Path(__file__).resolve().parents[2] / "investing-bros-crypto-course" / "references"
           / "example-lesson-video.json")
MANIFEST = {
    "panel": {"mode": "side", "anchors": ["p1"], "content": ["heading"], "assets": []},
    "flow": {"mode": "bubble", "anchors": [], "content": [], "assets": ["page"]},
}


def words(text, start=0.5, step=0.4):
    return [{"w": w, "s": round(start + i * step, 3), "e": round(start + i * step + 0.3, 3)} for i, w in enumerate(text.split())]


def config(**over):
    long = " ".join(["מילה"] * 80) + "."
    cfg = {
        "lesson": 9, "title": ["כותרת"], "parts": ["אחד", "שתיים", "שלוש"], "part_starts": [None, 2, None],
        "disclaimer_beat": 1,
        "script": {"doc": "DOC", "revision": "2026-10-26T20:12:34Z",
                   "beats": {"1": {"on_screen": "רק אתה."}, "2": {"on_screen": "כרטיס ליד הפנים."}}},
        "takes": [{"beat": 1, "file": "a.mov", "from": 0.0, "to": 34.0}, {"beat": 2, "file": "b.mov", "from": 0.0, "to": 6.0}],
        "proofread": {"1": f"שלום לכולם. {long} והיום נלמד משהו.", "2": "זה הבנק שלכם, וזה הבנק שלו."},
        "anchors": {"title": [1, "והיום נלמד"], "ag1": [1, "שלום"], "p1": [2, "הבנק שלו"], "late": [2, None, 0.5],
                    "dock": {"beat_end": 1, "offset": -0.5}},
        "segments": [{"at": [1, None], "mode": "full", "zoom": 1.1}, {"at": [1, "והיום", -0.15], "mode": "full"},
                     {"at": [2, None], "mode": "side", "scene": "panel",
                      "content": {"heading": {"text": "הבנק", "at": [2, "הבנק שלכם"]}}}],
    }
    cfg.update(over)
    return cfg


@pytest.fixture
def words_dir(tmp_path):
    cfg = config()
    w1 = words(cfg["proofread"]["1"], step=0.38)
    (tmp_path / "קטע-01.json").write_text(json.dumps(w1, ensure_ascii=False), encoding="utf-8")
    whisper_cli = {"segments": [{"words": [{"word": " " + w["w"], "start": w["s"], "end": w["e"]}
                                           for w in words(cfg["proofread"]["2"])]}]}
    (tmp_path / "קטע-02.json").write_text(json.dumps(whisper_cli, ensure_ascii=False), encoding="utf-8")
    return tmp_path


def run(cfg, words_dir):
    return build(cfg, words_dir, manifest=MANIFEST, config_dir=words_dir)


def test_anchors_and_content_times_come_from_spoken_words(words_dir):
    p = run(config(), words_dir)
    b1, b2 = p["beats"]
    assert (b1["start"], b1["end"], b2["start"], b2["end"]) == (0.0, 34.0, 34.0, 40.0)
    assert p["at"]["ag1"] == pytest.approx(0.5, abs=0.05)
    assert b2["start"] < p["at"]["p1"] < b2["end"]          # whisper CLI format, take 2 moved onto the lesson
    assert p["at"]["late"] == 34.5 and p["at"]["dock"] == 33.5
    assert 34.0 <= p["segments"][-1]["content"]["heading"]["at"] < p["at"]["p1"]
    assert p["script"] == {"doc": "DOC", "revision": "2026-10-26T20:12:34Z"} and p["duration"] == 40.0


def test_progress_keeps_a_position_for_every_part(words_dir):
    # parts 1 and 3 aren't in this cut: part 2 must stay the second mark, not slide into the first
    assert run(config(), words_dir)["partStarts"] == [None, 34.0, None]
    assert run(config(part_starts=[1, None, 2]), words_dir)["partStarts"] == [0.0, None, 34.0]
    with pytest.raises(SystemExit, match="one entry per part"):
        run(config(part_starts=[1, 2]), words_dir)


def test_disclaimer_strip_covers_its_beat_or_starts_on_a_phrase(words_dir):
    assert run(config(), words_dir)["disclaimer"] == {"start": 0.0, "end": 34.0}
    # lesson 1's six-beat script: the disclaimer is the last sentences of a longer beat, not a beat of its own
    p = run(config(disclaimer_beat=2, disclaimer_from=[2, "וזה הבנק שלו"]), words_dir)
    assert p["disclaimer"]["end"] == 40.0
    assert p["disclaimer"]["start"] == pytest.approx(p["at"]["p1"] - 0.4, abs=0.01)
    assert run(config(disclaimer_beat=3), words_dir)["disclaimer"] is None     # beat not in this cut
    with pytest.raises(SystemExit, match="disclaimer_from"):
        run(config(disclaimer_from=[2, "הבנק שלו"]), words_dir)


def test_segments_cover_the_lesson_back_to_back(words_dir):
    segs = run(config(), words_dir)["segments"]
    assert segs[0]["start"] == 0.0 and segs[-1]["end"] == 40.0
    assert all(a["end"] == b["start"] and a["start"] < a["end"] for a, b in zip(segs, segs[1:]))


def with_segments(*extra):
    base = [{"at": [1, None], "mode": "full"}]
    return {"segments": base + list(extra)}


PANEL = {"mode": "side", "scene": "panel", "content": {"heading": {"text": "x", "at": [2, None, 0.2]}}}


@pytest.mark.parametrize("over, message", [
    ({"anchors": {"x": [2, "מילים שלא נאמרו"]}}, "isn't in the proofread words"),
    ({"anchors": {"ag1": [1, "שלום"], "ag4": [1, "שלום"], "p1": [2, "הבנק שלו"]}}, "no part"),
    ({"anchors": {"far": [2, None, 600.0], "p1": [2, "הבנק שלו"]}}, "outside the lesson"),
    (with_segments({"at": [1, "שלום"], **PANEL}), "face only"),
    (with_segments({"at": [2, None], **PANEL, "scene": "nope"}), "isn't in template"),
    (with_segments({"at": [2, None], **PANEL, "mode": "bubble"}), "is a side scene, not bubble"),
    (with_segments({"at": [1, None, 0.2], "mode": "full", "zoom": 1.5}), "zoom"),
    (with_segments({"at": [2, None, 600.0], "mode": "full"}), "outside the lesson"),
    (with_segments({"at": [2, None], **PANEL}, {"at": [1, "והיום"], "mode": "full"}), "not after the segment before it"),
])
def test_refuses_what_breaks_the_house_rules(words_dir, over, message):
    with pytest.raises(SystemExit, match=message):
        run(config(**over), words_dir)


def test_the_face_position_is_optional_and_checked(words_dir):
    assert "face" not in run(config(), words_dir)
    assert run(config(face={"x": 840, "y": 690}), words_dir)["face"] == {"x": 840.0, "y": 690.0}
    for bad in ({"x": 840}, {"x": 2400, "y": 500}, [840, 450]):
        with pytest.raises(SystemExit, match="face must be"):
            run(config(face=bad), words_dir)


def test_a_scene_can_leave_out_what_the_take_doesnt_say(words_dir):
    manifest = {**MANIFEST, "panel": {**MANIFEST["panel"], "anchors": ["p1", "p2"], "content": ["heading", "extra"],
                                       "optional": {"anchors": ["p2"], "content": ["extra"]}}}
    build(config(), words_dir, manifest=manifest, config_dir=words_dir)       # p2 and extra left out: fine
    cfg = config()
    cfg["anchors"]["p2"] = [1, "שלום"]                           # given, so it must fall inside the scene
    with pytest.raises(SystemExit, match="fall outside it"):
        build(cfg, words_dir, manifest=manifest, config_dir=words_dir)


def test_a_phrase_said_twice_in_a_beat_is_warned_about(words_dir, capsys):
    cfg = config()
    cfg["proofread"]["2"] = "זה הבנק שלכם, וזה הבנק שלו."
    cfg["anchors"]["p1"] = [2, "הבנק"]
    run(cfg, words_dir)
    assert "'הבנק' is said 2 times; the first" in capsys.readouterr().err


def test_a_scene_gets_every_anchor_content_and_asset_it_needs(words_dir):
    cfg = config()
    del cfg["anchors"]["p1"]                                     # the review's case: a scene's anchor deleted
    with pytest.raises(SystemExit, match=r"needs anchors \['p1'\]"):
        run(cfg, words_dir)
    cfg = config()
    cfg["anchors"]["p1"] = [1, "והיום"]                         # said, but before the scene's segment
    with pytest.raises(SystemExit, match="fall outside it"):
        run(cfg, words_dir)
    cfg = config()
    cfg["segments"][-1]["content"] = {}
    with pytest.raises(SystemExit, match=r"needs content \['heading'\]"):
        run(cfg, words_dir)
    cfg = config()
    cfg["segments"][-1]["content"]["heading"]["at"] = [1, "שלום"]
    with pytest.raises(SystemExit, match="content times"):
        run(cfg, words_dir)
    cfg = config(segments=[{"at": [1, None], "mode": "full"}, {"at": [2, None], "mode": "bubble", "scene": "flow"}],
                 anchors={})
    with pytest.raises(SystemExit, match=r"needs assets \['page'\]"):
        run(cfg, words_dir)
    (words_dir / "page.png").write_bytes(b"png")
    with pytest.raises(SystemExit, match="record where it comes from"):
        run({**cfg, "assets": {"page": {"file": "page.png"}}}, words_dir)
    p = run({**cfg, "assets": {"page": {"file": "page.png", "source": "https://example.org/p1"}}}, words_dir)
    assert p["assets"] == {"page": "assets/page.png"} and p["assetSources"]["page"] == str(words_dir / "page.png")


def test_the_script_doc_must_have_been_read(words_dir):
    cfg = config()
    cfg["script"] = {}
    with pytest.raises(SystemExit, match="Google Doc"):
        run(cfg, words_dir)
    cfg = config()
    del cfg["script"]["beats"]["2"]
    with pytest.raises(SystemExit, match=r"beats \[2\] have no 'על המסך'"):
        run(cfg, words_dir)


def test_a_sentence_never_leaves_its_last_word_behind():
    w = lambda t, s: {"w": t, "start": s, "end": s + 0.3}
    caps = [{"words": [w("ממשלות", 0), w("הזרימו", 0.4), w("כדי", 0.8), w("להציל", 1.2)]},
            {"words": [w("אותם.", 1.6), w("בעיצומו", 2.0), w("של", 2.4), w("המשבר,", 2.8)]},
            {"words": [w("אחד,", 6.0)]}, {"words": [w("מה", 6.4), w("הבעיה?", 6.8)]}]
    out = [" ".join(x["w"] for x in c["words"]) for c in tidy(caps)]
    assert out == ["ממשלות הזרימו כדי להציל אותם.", "בעיצומו של המשבר,", "אחד, מה הבעיה?"]


def test_words_formats_and_srt(tmp_path):
    f = tmp_path / "w.json"
    f.write_text(json.dumps([{"w": " שלום", "s": 1.0, "e": 1.4}]), encoding="utf-8")
    assert load_words(f, 1000.0) == [{"w": "שלום", "s": 1001.0, "e": 1001.4}]
    text = srt([{"start": 61.5, "end": 3725.25, "words": [{"w": "שלום"}, {"w": "לכולם."}]}])
    assert text == "1\n00:01:01,500 --> 01:02:05,250\nשלום לכולם.\n"


def example_words(cfg, folder: Path):
    """Whisper-shaped words for the example's proofread text, one word every 0.4 s from 0.5 s."""
    for t in cfg["takes"]:
        (folder / f"קטע-{t['beat']:02d}.json").write_text(
            json.dumps(words(cfg["proofread"][str(t["beat"])]), ensure_ascii=False), encoding="utf-8")


def test_the_example_config_builds_with_the_real_scene_manifest(tmp_path):
    """The made-up lesson in investing-bros-crypto-course runs end to end against the template's scenes.json:
    both double-spend scenarios, from content alone."""
    cfg = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    assert {"terms", "double-spend", "lesson1-money-flow", "lesson1-satoshi"} <= known_scenes()
    example_words(cfg, tmp_path)
    p = build(cfg, tmp_path, config_dir=EXAMPLE.parent)
    scenes = [s for s in p["segments"] if s.get("scene") == "double-spend"]
    assert [s["content"]["scenario"] for s in scenes] == ["copy", "ledger"]
    copy_, ledger = scenes[0]["content"], scenes[1]["content"]
    assert copy_["coin"]["at"] < copy_["payments"][0]["at"] < copy_["copy"]["at"] < copy_["payments"][1]["at"]
    assert ledger["split"]["at"] < ledger["payments"][1]["at"] < ledger["verdict"]["at"]
    assert p["departures"] == cfg["script"]["departures"]


@pytest.mark.parametrize("change, message", [
    (lambda c: c.__setitem__("scenario", "mirror"), "scenario 'mirror' isn't one of"),
    (lambda c: c.pop("copy"), r"\(copy\) needs content \['copy'\]"),
    (lambda c: c["payments"].pop(), r"needs times \['payments.1.at'\]"),
    (lambda c: c.__setitem__("copy", {"at": [2, "יש"]}), r"copy.at .* comes before payments.0.at"),
])
def test_double_spend_refuses_a_wrong_scenario_or_events_out_of_order(tmp_path, change, message):
    cfg = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    example_words(cfg, tmp_path)
    change(cfg["segments"][2]["content"])
    with pytest.raises(SystemExit, match=message):
        build(cfg, tmp_path, config_dir=EXAMPLE.parent)


def test_the_script_snapshot_must_be_the_text_that_was_parsed(words_dir):
    (words_dir / "script").mkdir()
    snap = words_dir / "script" / "תסריט-שיעור-9-v1.md"
    snap.write_text("## קטע 1: פתיחה\n", encoding="utf-8")
    cfg = config()
    cfg["script"].update(snapshot="script/תסריט-שיעור-9-v1.md", snapshot_sha256=sha256_file(snap))
    assert run(cfg, words_dir)["script"]["snapshot_sha256"] == cfg["script"]["snapshot_sha256"]
    snap.write_text("## קטע 1: פתיחה אחרת\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="changed after parse_script.py read it"):
        run(cfg, words_dir)
    snap.unlink()
    with pytest.raises(SystemExit, match="snapshot .* is missing"):
        run(cfg, words_dir)


def test_words_from_a_replaced_take_are_refused(tmp_path):
    cfg = config()
    takes = tmp_path / "takes"
    takes.mkdir()
    (takes / "a.mov").write_text("take a")
    (takes / "קטע-02.mp4").write_text("drive copy of b")              # beat 2 only under its Drive name
    (tmp_path / "קטע-01.take.json").write_text(json.dumps({"take": "a.mov", "sha256": sha256_file(takes / "a.mov")}))
    (tmp_path / "קטע-02.take.json").write_text(json.dumps({"take": "b.mov", "sha256": "original",
                                                          "package_sha256": sha256_file(takes / "קטע-02.mp4")}))
    assert check_words_match_takes(cfg, tmp_path, takes) == []
    (takes / "a.mov").write_text("a re-recorded take a")
    with pytest.raises(SystemExit, match="the words were made from a.mov"):
        check_words_match_takes(cfg, tmp_path, takes)
    (tmp_path / "קטע-01.take.json").unlink()
    assert check_words_match_takes(cfg, tmp_path, takes) == [1]          # no sidecar: reported, not refused


def test_a_drive_package_builds_from_its_own_folder(tmp_path):
    """The manifest is a config: copied with its images, snapshot and words into a fresh folder, it builds
    the same props with no path back to where the lesson was made."""
    cfg = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    pkg = tmp_path / "extras"
    pkg.mkdir()
    (pkg / "page.png").write_bytes(b"png")
    (pkg / "תסריט-שיעור-9-v1.md").write_text("## קטע 1: פתיחה\n", encoding="utf-8")
    cfg["assets"] = {"page": {"file": "page.png", "source": "example"}}
    cfg["script"].update(snapshot="תסריט-שיעור-9-v1.md", snapshot_sha256=sha256_file(pkg / "תסריט-שיעור-9-v1.md"))
    cfg["package"] = {"base": "שיעור-9-בסיס.mp4"}
    example_words(cfg, pkg)
    p = build(cfg, pkg, config_dir=pkg)
    assert p["assetSources"] == {"page": str((pkg / "page.png").resolve())}
    assert str(EXAMPLE.parent) not in json.dumps(p, ensure_ascii=False)
