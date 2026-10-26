"""Tests for make_props.py (short config -> Remotion props, with the house checks)."""
import copy
import json
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from make_props import ICONS, build_props, main  # noqa: E402

TEMPLATE = Path(__file__).resolve().parent.parent / "template"

CFG = {
    "meta": {"episode": 8},
    "hook": {"start": 0.0, "end": 3.0, "top_line": 'למה נדל"ן', "bottom_line": "מלחיץ פחות?"},
    "tags": [[0.0, 18.4, "אמיתי רסקין"], [18.4, 25.7, "נדב רסקין"]],
    "captions": [{"start": 0.0, "end": 0.6, "text": "אפשר לדוגמה", "highlight": [],
                  "words": [{"w": "אפשר", "start": 0.0, "end": 0.3}, {"w": "לדוגמה", "start": 0.3, "end": 0.6}]},
                 {"start": 0.6, "end": 1.0, "text": 'לקנות נדל"ן,', "highlight": ['נדל"ן']},
                 {"start": 9.6, "end": 10.4, "text": "נכנסים לפורטפוליו שלהם", "highlight": []}],
    "cards": [{"id": "c1", "mode": "inset", "start": 9.0, "end": 14.2, "steps": [
        {"at": 9.0, "visual": "house", "title": "לא קמים בבוקר", "subtitle": ""},
        {"at": 11.0, "visual": "drop", "value": 30, "title": "צניחה של 30%", "subtitle": "בבית שלהם"}]}],
    "cta_overlay": {"start": 22.75, "end": 25.75, "text": "הקישור לפרק המלא בתיאור"},
}


def props(cfg=None, dur=25.75):
    return build_props(copy.deepcopy(cfg or CFG), dur)


def test_icon_list_matches_the_template():
    src = (TEMPLATE / "src" / "components" / "icons.tsx").read_text(encoding="utf-8")
    block = re.search(r"export const ICONS[^{]*=\s*\{(.*?)\};", src, re.S).group(1)
    assert set(re.findall(r"(\w+):", block)) == set(ICONS)


def test_props_shape_and_values():
    p = props()
    assert p["base"] == "base.mp4" and p["baseDuration"] == 25.75 and p["episode"] == 8
    assert p["captions"][0]["words"][1] == {"w": "לדוגמה", "start": 0.3, "end": 0.6}
    assert "words" not in p["captions"][1]
    assert p["hook"] == {"start": 0.0, "end": 3.0, "top": 'למה נדל"ן', "bottom": "מלחיץ פחות?"}
    assert p["cards"][0]["steps"][1]["value"] == 30 and "value" not in p["cards"][0]["steps"][0]
    assert p["cta"]["text"] == "הקישור לפרק המלא בתיאור"


def test_props_keys_match_the_template_type():
    src = (TEMPLATE / "src" / "props.ts").read_text(encoding="utf-8")
    block = re.search(r"export type ShortProps = \{(.*?)\n\};", src, re.S).group(1)
    assert set(re.findall(r"^\s+(\w+):", block, re.M)) == set(props())


def test_older_shorts_config_still_converts():
    cfg = copy.deepcopy(CFG)
    card = cfg.pop("cards")[0]
    card["panel"] = card.pop("mode")
    card["steps"][1] = {"at": 11.0, "visual": "clock", "pct": 95, "title": "95% מהזמן", "subtitle": ""}
    cfg["hyperframes"] = [card]
    step = props(cfg)["cards"][0]["steps"][1]
    assert props(cfg)["cards"][0]["mode"] == "inset" and step["visual"] == "pie" and step["value"] == 95


def test_default_mode_is_inset():
    cfg = copy.deepcopy(CFG)
    del cfg["cards"][0]["mode"]
    assert props(cfg)["cards"][0]["mode"] == "inset"


@pytest.mark.parametrize("change, message", [
    (lambda c: c["cards"][0].update(start=2.0, end=6.0) or c["cards"][0]["steps"][0].update(at=2.0)
     or c["cards"][0]["steps"][1].update(at=4.0), "inside the hook"),
    (lambda c: c["cards"][0].update(end=23.0), "overlaps the CTA"),
    (lambda c: c["cards"][0]["steps"][0].update(visual="rocket"), "unknown icon"),
    (lambda c: c["cards"][0]["steps"][1].pop("value"), "needs the number"),
    (lambda c: c["cards"][0]["steps"][0].update(title="לא קמים 🏠"), "emoji"),
    (lambda c: c["cards"][0]["steps"][1].update(at=15.0), "outside the card"),
    (lambda c: c["cards"].append(dict(copy.deepcopy(c["cards"][0]), id="c2", start=13.0, end=16.0,
                                      steps=[{"at": 13.0, "visual": "pie", "value": 5, "title": "x"}])), "overlaps the previous"),
    (lambda c: c["captions"].insert(2, {"start": 1.0, "end": 2.0, "text": "אחת שתיים שלוש ארבע חמש שש שבע"}),
     "1-6 words"),
    (lambda c: c.update(caption_style="build") or c["captions"].insert(2, {"start": 1.0, "end": 2.0,
                                                                      "text": "אחת שתיים שלוש ארבע חמש"}), "1-4 words"),
    (lambda c: c["captions"].append({"start": 0.5, "end": 2.0, "text": "שוב"}), "out of order"),
    (lambda c: c["cards"][0]["steps"].reverse(), "time order"),
    (lambda c: c["cards"][0]["steps"][0].update(subtitle="נכנסים לפורטפוליו"), "repeats the captions"),
    (lambda c: c["cta_overlay"].update(end=24.0), "no end card"),
    (lambda c: c["captions"][0]["words"].reverse(), "out of order"),
    (lambda c: c["captions"][0]["words"].pop(), "don't match its text"),
])
def test_house_rules_are_enforced(change, message):
    cfg = copy.deepcopy(CFG)
    change(cfg)
    with pytest.raises(ValueError, match=message):
        build_props(cfg, 25.75)


def test_house_caption_format_is_kinetic_with_the_spoken_word_highlighted():
    cfg = copy.deepcopy(CFG)
    cfg["captions"].insert(2, {"start": 1.0, "end": 3.0, "text": "אחת שתיים שלוש ארבע חמש שש", "highlight": []})
    p = build_props(cfg, 25.75)
    assert p["captionStyle"] == "punch" and p["captionHighlight"] == "spoken"
    cfg["caption_style"] = "line"
    assert build_props(cfg, 25.75)["captionStyle"] == "line"                   # older looks stay available
    cfg.update(caption_style="build", caption_highlight="keywords")
    with pytest.raises(ValueError, match="1-4 words"):
        build_props(cfg, 25.75)
    cfg["caption_style"] = "bounce"
    with pytest.raises(ValueError, match="caption_style"):
        build_props(cfg, 25.75)


def test_punch_style_keeps_phrases_to_six_words():
    cfg = copy.deepcopy(CFG)
    cfg["caption_style"] = "punch"
    assert build_props(cfg, 25.75)["captionStyle"] == "punch"
    cfg["captions"].insert(2, {"start": 1.0, "end": 2.0, "text": "אחת שתיים שלוש ארבע חמש שש שבע", "highlight": []})
    with pytest.raises(ValueError, match="1-6 words"):
        build_props(cfg, 25.75)


def test_a_subtitle_that_adds_something_is_fine():
    cfg = copy.deepcopy(CFG)
    cfg["cards"][0]["steps"][0]["subtitle"] = "בבית"
    assert props(cfg)["cards"][0]["steps"][0]["subtitle"] == "בבית"


def test_cli_takes_word_timed_captions(tmp_path):
    caps = [{"start": 0.0, "end": 1.0, "text": "אחת שתיים", "highlight": [],
             "words": [{"w": "אחת", "start": 0.0, "end": 0.5}, {"w": "שתיים", "start": 0.5, "end": 1.0}]}]
    (tmp_path / "c.json").write_text(json.dumps(caps, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "s.json").write_text(json.dumps(CFG, ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "p.json"
    assert main([str(tmp_path / "s.json"), "--base-duration", "25.75", "--captions", str(tmp_path / "c.json"),
                 "-o", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["captions"] == caps


def test_cli_writes_props(tmp_path):
    cfg = tmp_path / "short.json"
    cfg.write_text(json.dumps(CFG, ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "props.json"
    assert main([str(cfg), "--base-duration", "25.75", "-o", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["episode"] == 8
    bad = copy.deepcopy(CFG)
    bad["cards"][0]["steps"][0]["visual"] = "rocket"
    cfg.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    assert main([str(cfg), "--base-duration", "25.75", "-o", str(out)]) == 1


def test_template_sample_props_pass_the_checks():
    sample = json.loads((TEMPLATE / "src" / "sample-props.json").read_text(encoding="utf-8"))
    cfg = {"meta": {"episode": sample["episode"]},
           "hook": {"start": sample["hook"]["start"], "end": sample["hook"]["end"],
                    "top_line": sample["hook"]["top"], "bottom_line": sample["hook"]["bottom"]},
           "tags": sample["tags"], "captions": sample["captions"], "cards": sample["cards"], "cta_overlay": sample["cta"]}
    assert build_props(cfg, sample["baseDuration"])["cards"] == sample["cards"]
