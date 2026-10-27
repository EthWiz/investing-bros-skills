"""Tests for make_lesson_props.py (anchors, scene needs, layout rules, sentence-safe captions, script intake)."""
import copy
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from make_lesson_props import build, known_scenes, load_words, scene_manifest, srt, tidy  # noqa: E402

LESSON_1 = (Path(__file__).resolve().parents[2] / "investing-bros-crypto-course" / "references" / "lessons"
            / "lesson-1-video.json")
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


def test_lesson_1_config_matches_the_template_manifest():
    """No words needed: every scene segment in lesson 1 names a known scene in the right mode, and carries
    the content keys and assets that scene declares; every anchor it needs is in the config."""
    manifest, cfg = scene_manifest(), json.loads(LESSON_1.read_text(encoding="utf-8"))
    assert {"terms", "lesson1-money-flow", "lesson1-satoshi"} <= known_scenes()
    for seg in cfg["segments"]:
        if seg["mode"] == "full":
            continue
        spec = manifest[seg["scene"]]
        assert spec["mode"] == seg["mode"], seg["scene"]
        assert set(spec["content"]) <= set(seg.get("content", {})), seg["scene"]
        assert set(spec["anchors"]) <= set(cfg["anchors"]), seg["scene"]
        assert set(spec.get("assets", [])) <= set(cfg.get("assets", {})), seg["scene"]
    for a in cfg.get("assets", {}).values():
        assert (LESSON_1.parent / a["file"]).is_file() and a["source"]
    broken = copy.deepcopy(cfg)
    del broken["anchors"]["s_paper"]
    assert "s_paper" in manifest["lesson1-satoshi"]["anchors"]   # so dropping it is refused at build time
