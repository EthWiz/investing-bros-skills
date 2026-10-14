"""Tests for align_words.py and find_cuts.py. Run: python3 -m pytest skills/investing-bros-shorts/scripts"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from align_words import align  # noqa: E402
from find_cuts import snap  # noqa: E402


def test_align_uses_whisper_times_and_marks_keys():
    words = [{"w": "a", "s": 10.1, "e": 10.4}, {"w": "b", "s": 10.5, "e": 10.9}, {"w": "c", "s": 11.0, "e": 11.5}]
    chunks = align([[10.0, 11.6, "יצליחו [להנחית אסטרואיד]."]], words)
    flat = [w for c in chunks for w in c]
    assert [w["w"] for w in flat] == ["יצליחו", "להנחית", "אסטרואיד]."[:-2] + "."]
    assert flat[0]["s"] == 10.0 and flat[1]["s"] == 10.5 and [w["key"] for w in flat] == [False, True, True]


def test_align_falls_back_to_word_length_and_never_crosses_cards():
    chunks = align([[0, 2, "אחת שתיים"], [3, 4, "שלוש"]], [])
    assert len(chunks) == 2 and chunks[1][0]["s"] == 3


def test_snap_finds_the_pause():
    sr = 16000
    x = np.concatenate([np.random.randn(sr) * 3000, np.zeros(sr // 5), np.random.randn(sr) * 3000]).astype(np.float32)
    r = snap(x, sr, 100.0, 101.05)
    assert 101.0 <= r["cut"] <= 101.2 and r["rms"] < 200
