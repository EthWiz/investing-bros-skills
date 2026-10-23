"""Tests for check_short.py limits and face_crop.py's centring. Run: python3 -m pytest skills/investing-bros-shorts/scripts"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from check_short import layout_problems, opening_problems, problems  # noqa: E402
from face_crop import place, skin_centre_x  # noqa: E402


def test_house_limits():
    assert problems(48.5, -14.4, -4.5) == []
    assert len(problems(65, -18.0, -0.5)) == 3


def test_length_limits():
    assert problems(52, -14, -4) == []                 # over the 20-45 s target is a note, not a failure
    assert len(problems(12, -14, -4)) == 1


def test_first_second_and_ending():
    assert opening_problems(30, 90, 95, [(10.0, 10.5)]) == []
    assert any("black" in p for p in opening_problems(30, 5, 95, []))
    assert any("fade" in p for p in opening_problems(30, 40, 95, []))
    assert any("before the first word" in p for p in opening_problems(30, 90, 95, [(0.0, 0.9)]))
    assert any("at the end" in p for p in opening_problems(30, 90, 95, [(28.4, None)]))
    assert opening_problems(30, 90, 95, [(0.0, 0.2), (29.5, None)]) == []
    assert opening_problems(33, 90, 95, [(30.0, None)], silent_endcard_seconds=3.0) == []


def test_skin_centre_finds_the_face():
    half = np.zeros((540, 480, 3), np.float32) + 40
    half[100:300, 300:400] = (220, 160, 130)            # a skin-coloured patch right of centre
    assert 330 < skin_centre_x(half) < 370


def test_layout_bounds_fail_outside():
    assert layout_problems({"caption_y": 1470, "hook_y": 960, "hook_style": "strips", "hook_box": [816, 1105]}) == []
    assert any("caption_y" in p for p in layout_problems({"caption_y": 1600, "hook_y": 440}))
    assert any("hook_y" in p for p in layout_problems({"caption_y": 1290, "hook_y": 1100, "hook_style": "strips"}))
    assert any("logo" in p for p in layout_problems({"caption_y": 1290, "hook_y": 300, "hook_box": [290, 590]}))
    assert any("captions" in p for p in layout_problems({"caption_y": 1100, "hook_y": 960, "hook_box": [816, 1105]}))
    assert layout_problems({"caption_y": 1290, "hook_y": 700, "hook_style": "legacy"}) == []   # old exports


def test_place_clears_a_small_face_and_flags_a_close_up():
    small = place([(300, 500, 780, 1100)] * 3)                  # face well inside the frame
    assert small["caption_y"] == 1173 and small["hook_y"] == 918 and not small["warnings"]   # moved up off the captions
    big = place([(96, 352, 1088, 1429)])                        # webcam close-up (episode 1)
    assert big["caption_y"] == 1470 and big["hook_y"] == 960 and any("chin" in w for w in big["warnings"])   # centre


def test_callout_must_clear_captions_hook_and_end_card():
    ok = {"caption_y": 1470, "duration": 32.68, "callouts": [{"window": [13.0, 15.2], "box": [1157, 1357]}]}
    assert layout_problems(ok) == []
    low = dict(ok, callouts=[{"window": [13.0, 15.2], "box": [1250, 1450]}])
    assert any("captions" in p for p in layout_problems(low))
    late = dict(ok, callouts=[{"window": [29.0, 31.2], "box": [1157, 1357]}])
    assert any("end card" in p for p in layout_problems(late))
