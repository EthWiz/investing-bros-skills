"""Tests for find_bounds.py."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from find_bounds import find_bounds  # noqa: E402


def seg(a, b, text):
    return {"start": a, "end": b, "text": text}


def test_mid_episode_phone_call_bye_is_not_the_end():
    segs = [seg(0, 5, "שלום"), seg(10, 15, "ברוכים הבאים לאחים להשקעות")]
    segs += [seg(1600 + i, 1601 + i, "כן, ביי" if i == 40 else "שיחה") for i in range(0, 45, 5)]
    segs += [seg(1700 + 10 * i, 1705 + 10 * i, "דיבור") for i in range(140)]
    segs += [seg(3100, 3105, "תודה רבה, נתראה בפרק הבא"), seg(3106, 3108, "עוד משהו")]
    si, ei = find_bounds(segs)
    assert si == 1
    assert segs[ei]["start"] == 3100


def test_lone_bye_needs_a_pause_after_it():
    segs = [seg(0, 5, "פרק 9")] + [seg(10 * i, 10 * i + 5, "דיבור") for i in range(1, 60)]
    segs += [seg(600, 601, "ביי"), seg(601.5, 603, "רגע, עוד דבר"), seg(603, 604, "ביי")]
    _, ei = find_bounds(segs)
    assert ei == len(segs) - 1
