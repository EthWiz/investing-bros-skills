"""Tests for speaker_balance.py. Run: python3 -m pytest skills/investing-bros-post-production/scripts"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from speaker_balance import SR, level_of, speech_db, spread  # noqa: E402


def tone(seconds: float, amp: float) -> np.ndarray:
    t = np.arange(int(seconds * SR)) / SR
    return (amp * np.sin(2 * np.pi * 220 * t)).astype(np.float32)


def test_speech_db_ignores_silence():
    x = np.concatenate([tone(1, 0.1), np.zeros(SR, np.float32)])
    assert abs(speech_db(x) - speech_db(tone(1, 0.1))) < 0.1


def test_level_of_detects_16_db_gap():
    # Host A loud, host B ~16 dB quieter (the episode 6 situation).
    x = np.concatenate([tone(5, 0.2), tone(5, 0.2 / 6.3)])
    a, b = level_of(x, [(0, 5)]), level_of(x, [(5, 10)])
    assert 15 < a - b < 17


def test_spread_is_large_for_imbalanced_and_small_for_even():
    uneven = np.concatenate([tone(3, 0.2), tone(3, 0.03)] * 5)
    even = np.concatenate([tone(3, 0.2), tone(3, 0.18)] * 5)
    assert spread(uneven)[2] > 10
    assert spread(even)[2] < 2
