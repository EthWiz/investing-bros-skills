"""Tests for clip_captions.py. Run: python3 -m pytest skills/investing-bros-shorts/scripts"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from clip_captions import ass_time, build_ass, chunk_segments, rtl  # noqa: E402

SEGMENTS = [
    {"start": 90.0, "end": 94.0, "text": "לפני הקטע"},
    {"start": 100.0, "end": 106.0, "text": "אחת שתיים שלוש ארבע חמש שש שבע שמונה תשע"},
    {"start": 106.0, "end": 110.0, "text": "סוף המשפט"},
    {"start": 120.0, "end": 125.0, "text": "אחרי הקטע"},
]


def test_range_is_clipped_and_shifted():
    chunks = list(chunk_segments(SEGMENTS, 100.0, 110.0, max_words=6))
    assert chunks[0][0] == 0.0
    assert all(0 <= a < b <= 10.0 for a, b, _ in chunks)
    texts = [t for _, _, t in chunks]
    assert "לפני הקטע" not in texts and "אחרי הקטע" not in texts


def test_long_segment_is_split_into_short_chunks():
    chunks = list(chunk_segments(SEGMENTS, 100.0, 106.0, max_words=6))
    assert [len(t.split()) for _, _, t in chunks] == [6, 3]
    assert chunks[0][1] == chunks[1][0]          # back to back, no gap


def test_partial_overlap_keeps_only_inside_part():
    chunks = list(chunk_segments(SEGMENTS, 108.0, 115.0, max_words=6))
    assert chunks == [(0.0, 2.0, "סוף המשפט")]


def test_ass_time_format():
    assert ass_time(0) == "0:00:00.00"
    assert ass_time(65.5) == "0:01:05.50"


def test_build_ass_uses_format_canvas():
    ass = build_ass([(0.0, 1.0, "שלום")], "square", "DejaVu Sans")
    assert "PlayResX: 1080" in ass and "PlayResY: 1080" in ass
    assert "Dialogue: 0,0:00:00.00,0:00:01.00,Default,,0,0,0,,‏שלום‏" in ass


def test_rtl_marks_question_marks_and_ends():
    assert rtl("קלאודס ו-NVIDIA?") == "‏קלאודס ו-NVIDIA?‏"
    assert rtl("מה זה? בדיוק") == "‏מה זה?‏ בדיוק‏"
    assert rtl(rtl("מה זה?")) == rtl("מה זה?")
