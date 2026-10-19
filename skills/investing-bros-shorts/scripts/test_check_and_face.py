"""Tests for check_short.py limits and face_crop.py's centring. Run: python3 -m pytest skills/investing-bros-shorts/scripts"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from check_short import opening_problems, problems  # noqa: E402
from face_crop import skin_centre_x  # noqa: E402


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


def test_skin_centre_finds_the_face():
    half = np.zeros((540, 480, 3), np.float32) + 40
    half[100:300, 300:400] = (220, 160, 130)            # a skin-coloured patch right of centre
    assert 330 < skin_centre_x(half) < 370
