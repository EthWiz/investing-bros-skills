"""Tests for check_short.py limits and face_crop.py's centring. Run: python3 -m pytest skills/investing-bros-shorts/scripts"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from check_short import problems  # noqa: E402
from face_crop import skin_centre_x  # noqa: E402


def test_house_limits():
    assert problems(48.5, -14.4, -4.5) == []
    assert len(problems(65, -18.0, -0.5)) == 3


def test_skin_centre_finds_the_face():
    half = np.zeros((540, 480, 3), np.float32) + 40
    half[100:300, 300:400] = (220, 160, 130)            # a skin-coloured patch right of centre
    assert 330 < skin_centre_x(half) < 370


def test_pauses_ignore_edges_and_short_gaps():
    from check_short import pauses
    log = ("silence_start: 0.0\nsilence_end: 0.2\n"        # before the first word: fine
           "silence_start: 10.0\nsilence_end: 10.4\n"      # breath: fine
           "silence_start: 20.0\nsilence_end: 21.1\n"      # dead air
           "silence_start: 39.8\n")                          # tail, no end line
    assert pauses(log, 40.0) == [(20.0, 21.1)]
