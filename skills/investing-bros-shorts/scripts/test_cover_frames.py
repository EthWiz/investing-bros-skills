"""Tests for cover_frames.py. Run: python3 -m pytest skills/investing-bros-shorts/scripts"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from cover_frames import build_command, crop_filter, times  # noqa: E402


def test_times_spread_inside_the_window():
    ts = times(100.0, 112.0, 12)
    assert len(ts) == 12 and ts[0] == 100.5 and ts[-1] == 111.5
    with pytest.raises(ValueError):
        times(10, 5, 4)


def test_crops_match_the_cover():
    assert crop_filter("R") == "crop=iw/2:ih:iw/2:0"
    assert crop_filter(crop=[656, 0, 1215, 2160]) == "crop=1215:2160:656:0"


def test_one_seek_per_frame_and_padded_grid():
    cmd = build_command("raw.mp4", [1.0, 2.0, 3.0, 4.0, 5.0], "null", "o.jpg")
    assert cmd.count("-ss") == 5
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "xstack=inputs=8" in fc and "text='5.00'" in fc               # 5 frames padded to 2 rows of 4
