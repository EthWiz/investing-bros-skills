"""Tests for make_lesson_props.py (anchors, layout rules, sentence-safe captions, words formats)."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from make_lesson_props import build, known_scenes, load_words, srt, tidy  # noqa: E402


def words(text, start=0.5, step=0.4):
    return [{"w": w, "s": round(start + i * step, 3), "e": round(start + i * step + 0.3, 3)} for i, w in enumerate(text.split())]


def config(**over):
    long = " ".join(["מילה"] * 80) + "."
    cfg = {
        "lesson": 9, "title": ["כותרת"], "parts": ["אחד", "שתיים"], "part_starts": [2, None], "disclaimer_beat": 1,
        "takes": [{"beat": 1, "file": "a.mov", "from": 0.0, "to": 34.0}, {"beat": 2, "file": "b.mov", "from": 0.0, "to": 6.0}],
        "proofread": {"1": f"שלום לכולם. {long} והיום נלמד משהו.", "2": "זה הבנק שלכם, וזה הבנק שלו."},
        "anchors": {"title": [1, "והיום נלמד"], "ag1": [1, "שלום"], "bank": [2, "הבנק שלו"], "late": [2, None, 0.5],
                    "dock": {"beat_end": 1, "offset": -0.5}},
        "segments": [{"at": [1, None], "mode": "full", "zoom": 1.1}, {"at": [1, "והיום", -0.15], "mode": "full"},
                     {"at": [2, None], "mode": "bubble", "scene": "s1"}],
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


def test_anchors_come_from_spoken_words(words_dir):
    p = build(config(), words_dir, scenes={"s1"})
    b1, b2 = p["beats"]
    assert (b1["start"], b1["end"], b2["start"], b2["end"]) == (0.0, 34.0, 34.0, 40.0)
    assert p["at"]["ag1"] == pytest.approx(0.5, abs=0.05)
    assert b2["start"] < p["at"]["bank"] < b2["end"]          # whisper CLI format, take 2 moved onto the lesson
    assert p["at"]["late"] == 34.5 and p["at"]["dock"] == 33.5
    assert p["partStarts"] == [34.0] and p["disclaimerBeat"] == 1 and p["duration"] == 40.0


def test_segments_cover_the_lesson_back_to_back(words_dir):
    segs = build(config(), words_dir, scenes={"s1"})["segments"]
    assert segs[0]["start"] == 0.0 and segs[-1]["end"] == 40.0
    assert all(a["end"] == b["start"] for a, b in zip(segs, segs[1:]))
    assert segs[-1] == {"start": 34.0, "end": 40.0, "mode": "bubble", "scene": "s1"}


@pytest.mark.parametrize("over, message", [
    ({"segments": [{"at": [1, None], "mode": "full"}, {"at": [1, "שלום"], "mode": "side", "scene": "s1"}]}, "face only"),
    ({"segments": [{"at": [1, None], "mode": "full"}, {"at": [2, None], "mode": "bubble", "scene": "nope"}]}, "isn't in template"),
    ({"segments": [{"at": [1, None], "mode": "full", "zoom": 1.5}]}, "zoom"),
    ({"anchors": {"x": [2, "מילים שלא נאמרו"]}}, "isn't in the proofread words"),
    ({"anchors": {"ag3": [1, "שלום"]}}, "no part"),
])
def test_refuses_what_breaks_the_house_rules(words_dir, capsys, over, message):
    with pytest.raises(SystemExit) as e:
        build(config(**over), words_dir, scenes={"s1"})
    assert message in str(e.value)


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


def test_the_template_lists_lesson_1_scenes():
    assert {"lesson1-money-flow", "lesson1-satoshi", "lesson1-glossary"} <= known_scenes()
