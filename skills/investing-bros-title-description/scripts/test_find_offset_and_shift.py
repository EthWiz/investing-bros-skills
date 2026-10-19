"""Tests for chapter offsetting."""
import os
import sys

import pytest
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import find_offset_and_shift as chapter_tool  # noqa: E402
from find_offset_and_shift import PTS_FILTER, format_timestamp, normalized_correlation, shift_description  # noqa: E402


def test_shift_description_adds_opening_and_preserves_other_copy():
    source = (
        "פתיח בעברית.\n\n"
        "אין כאן המלצת השקעה. רק שיחה.\n\n"
        "00:00 פתיחת הפרק\n"
        "01:05 חדשות השוק\n"
    )
    assert shift_description(source, 19.04) == (
        "פתיח בעברית.\n\n"
        "אין כאן המלצת השקעה. רק שיחה.\n\n"
        "00:00 טעימה מהפרק\n"
        "00:19 פתיחת הפרק\n"
        "01:24 חדשות השוק\n"
    )


def test_hour_chapters_and_negative_times():
    assert format_timestamp(3661) == "01:01:01"
    with pytest.raises(ValueError, match="before zero"):
        format_timestamp(-0.6)


def test_decoder_filter_preserves_pts_gaps():
    assert "async=1" in PTS_FILTER
    assert "first_pts=0" in PTS_FILTER


def test_normalized_correlation_has_meaningful_unit_score():
    reference = np.array([1, -1, 2, -2, 1, -1], dtype=np.float32)
    candidate = np.concatenate((np.zeros(4), 3 * reference + 7, np.zeros(3))).astype(np.float32)
    scores = normalized_correlation(candidate, reference)
    assert int(np.argmax(scores)) == 4
    assert scores[4] == pytest.approx(1.0, abs=1e-6)


def test_find_offset_returns_normalized_score(monkeypatch, tmp_path):
    reference = np.array([1, -1, 2, -2, 1, -1], dtype=np.float32)
    candidate = np.concatenate((np.zeros(4), 3 * reference + 7, np.zeros(3))).astype(np.float32)
    envelopes = iter((reference, candidate))
    monkeypatch.setattr(chapter_tool, "decode_pcm", lambda *_args, **_kwargs: np.zeros(1))
    monkeypatch.setattr(chapter_tool, "energy_envelope", lambda *_args, **_kwargs: next(envelopes))
    _, score = chapter_tool.find_offset(tmp_path / "video.mp4", tmp_path / "audio.wav")
    assert score == pytest.approx(1.0, abs=1e-6)
