"""Tests for transcribe.py helpers. Run: python3 -m pytest skills/investing-bros-post-production/scripts"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from transcribe import fmt_clock, fmt_srt_time, merge_speech  # noqa: E402


def test_merge_speech_joins_close_spans_and_caps_length():
    spans = [(0.0, 2.0), (2.3, 5.0), (5.2, 11.5), (11.6, 13.0), (20.0, 21.0)]
    assert merge_speech(spans) == [[0.0, 11.5], [11.6, 13.0], [20.0, 21.0]]


def test_time_formats():
    assert fmt_srt_time(3723.5) == "01:02:03,500"
    assert fmt_clock(65) == "1:05" and fmt_clock(3725) == "1:02:05"
