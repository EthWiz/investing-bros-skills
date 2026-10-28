"""Tests for phone_copy.py: the bitrate that fits a phone-sized file."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from phone_copy import video_kbps  # noqa: E402


def test_a_seven_minute_lesson_fits_in_thirty_megabytes():
    kbps = video_kbps(435.5, 30)
    assert 450 <= kbps <= 480
    assert (kbps + 64) * 435.5 / 8 / 1024 <= 30


def test_too_long_for_the_size_is_refused():
    with pytest.raises(SystemExit, match="doesn't fit"):
        video_kbps(1800, 30)
