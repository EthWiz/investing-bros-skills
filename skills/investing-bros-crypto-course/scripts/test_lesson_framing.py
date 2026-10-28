"""Tests for lesson_framing.py, framing in make_lesson_base.py (frame, build, status) and the trim fallback."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import lesson_background  # noqa: E402
import lesson_framing  # noqa: E402
from make_lesson_base import filter_graph, fingerprint, trims_from_words, word_times  # noqa: E402

# lesson 1's OBS takes, 2026-10-28 (face boxes in base pixels): beat 1's head is cut off at the top
LESSON1 = {1: (950.4, 172.9, 616.9), 2: (783.7, 290.7, 667.1), 3: (875.5, 260.6, 684.9),
           4: (969.2, 330.3, 654.4), 5: (941.6, 295.1, 713.9), 6: (791.6, 338.3, 690.2)}
FACES = {b: {"cx": cx, "top": top, "w": w, "h": w} for b, (cx, top, w) in LESSON1.items()}
VISION = {"method": "vision", "image": "assets/bg.jpg"}


def placed(face, fr):
    """Where the face box lands after the take is scaled by fr['scale'] and put at fr['x'], fr['y']."""
    s = fr["scale"]
    return {"cx": fr["x"] + s * face["cx"], "top": fr["y"] + s * face["top"], "w": s * face["w"],
            "bottom": fr["y"] + s * 1080}


def test_every_take_gets_the_same_face_width_at_the_same_x():
    r = lesson_framing.plan(FACES)
    for b, face in FACES.items():
        p = placed(face, r["takes"][b])
        assert p["w"] == pytest.approx(r["width"], abs=1) and p["cx"] == pytest.approx(840, abs=1)


def test_the_body_stays_on_the_bottom_edge_and_takes_only_move_down():
    r = lesson_framing.plan(FACES)
    for b, face in FACES.items():
        fr = r["takes"][b]
        assert placed(face, fr)["bottom"] >= 1080 - 0.5          # never a gap under the shoulders
        assert fr["y"] >= 1080 - fr["scale"] * 1080 - 0.5         # moved down from the bottom-anchored place, never up
    tops = [placed(FACES[b], r["takes"][b])["top"] for b in (2, 3, 4)]
    assert max(tops) - min(tops) < 2                              # the higher takes come down to one line


def test_a_take_with_the_head_cut_off_is_never_shrunk():
    r = lesson_framing.plan(FACES)
    assert r["takes"][1]["scale"] >= 1.0 and r["takes"][1]["y"] == 0.0
    assert r["width"] == pytest.approx(616.9)                     # the smallest face, so nothing else is enlarged
    r = lesson_framing.plan(FACES, width=580)
    assert r["takes"][1]["scale"] == 1.0 and r["takes"][2]["scale"] < 1.0


def test_the_face_point_for_the_template_follows_the_framed_takes():
    r = lesson_framing.plan(FACES)
    assert r["face"]["x"] == 840 and 650 < r["face"]["y"] < 780


def test_a_take_too_far_off_is_refused():
    with pytest.raises(SystemExit, match="re-record"):
        lesson_framing.plan({1: {"cx": 960, "top": 300, "w": 900, "h": 900}, 2: {"cx": 960, "top": 300, "w": 500, "h": 500}})


def test_a_face_measured_in_a_720p_take_is_moved_to_base_pixels():
    f = lesson_framing.to_base({"cx": 640, "top": 100, "w": 300, "h": 300, "width": 1280})
    assert f == {"cx": 960.0, "top": 150.0, "w": 450.0, "h": 450.0}


def test_a_framed_take_is_scaled_feathered_and_placed():
    takes = [{"beat": 1, "file": "a.mov", "from": 0.0, "to": 5.0, "frame": {"scale": 0.92, "x": 115.3, "y": 104.4}},
             {"beat": 2, "file": "b.mov", "from": 0.0, "to": 5.0}]
    g = filter_graph(takes, lesson_background.check(VISION))
    assert "scale=w=trunc(iw*0.92/2)*2:h=trunc(ih*0.92/2)*2" in g
    assert "[bg0][fs0]overlay=x=115.3:y=104.4:shortest=1" in g and "alphaextract" in g
    assert "[bg1][fg1]overlay=shortest=1,format=yuv420p[v1]" in g      # an unframed take is as before
    with pytest.raises(SystemExit, match="needs a background"):
        filter_graph(takes)


def test_framing_and_the_face_point_count_as_changes_but_leave_older_configs_alone():
    cfg = {"takes": [{"beat": 1, "file": "a.mov", "from": 0.0, "to": 5.0}], "anchors": {}}
    before = fingerprint(cfg)
    assert before["trims"]["1"] == ["a.mov", 0.0, 5.0]                     # same as an older export record
    framed = json.loads(json.dumps(cfg))
    framed["takes"][0]["frame"] = {"scale": 0.9, "x": 1, "y": 2}
    assert fingerprint(framed)["trims"] != before["trims"]
    framed["face"] = {"x": 840, "y": 713}
    assert fingerprint(framed)["layout"] != before["layout"]


def test_check_lesson_fingerprints_framing_the_same_way():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "investing-bros-remotion", "scripts"))
    import check_lesson
    cfg = {"takes": [{"beat": 1, "file": "a.mov", "from": 0.0, "to": 5.0, "frame": {"scale": 0.9, "x": 1, "y": 2}}],
           "anchors": {}, "face": {"x": 840, "y": 713}, "background": VISION}
    assert check_lesson.fingerprint(cfg) == fingerprint(cfg)


def test_trims_come_from_the_words_when_silence_detection_finds_none(tmp_path):
    words = {"segments": [{"words": [{"word": " אז", "start": 14.42, "end": 14.6}, {"word": " להתבהר", "start": 125.0,
                                                                                    "end": 125.44}]}]}
    (tmp_path / "w.json").write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
    assert trims_from_words(word_times(tmp_path / "w.json"), 126.77) == (14.12, 125.89)
    assert trims_from_words([(0.1, 0.4), (3.0, 3.5)], 3.6) == (0.0, 3.6)
