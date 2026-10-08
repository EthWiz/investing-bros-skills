"""Tests for make_cover.py. Run: python3 -m pytest skills/investing-bros-shorts/scripts"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from make_cover import HEAD_CENTER_Y, PILL_Y, SQUARE, build_ass, build_command, headline_lines  # noqa: E402


def test_headline_and_pill_stay_inside_the_square_crop():
    # the 1:1 profile-grid crop of a 9:16 cover keeps y 420..1500
    assert SQUARE[0] < HEAD_CENTER_Y - 130 and HEAD_CENTER_Y + 130 < SQUARE[1]
    assert SQUARE[0] < PILL_Y < SQUARE[1] - 40


def test_headline_rules():
    assert headline_lines("סוויפט היא בכלל|[לא מערכת תשלומים]") == ["סוויפט היא בכלל", "[לא מערכת תשלומים]"]
    with pytest.raises(ValueError):
        headline_lines("א|ב|ג|ד")                        # max three lines
    with pytest.raises(ValueError):
        headline_lines("שורה ארוכה מדי בשביל תמונה ממוזערת")  # too long to read when tiny


def test_ass_is_rtl_with_emerald_and_episode_pill():
    ass = build_ass("סוויפט היא בכלל|[לא מערכת תשלומים]", 6)
    assert "\\c&H7ABF1F&" in ass and "פרק 6" in ass
    for line in ass.splitlines():
        if line.startswith("Style:"):
            assert line.endswith(",-1")
    assert "פרק" not in build_ass("כותרת", None)


def test_command_picks_host_half_and_one_frame():
    cmd = build_command("raw.mp4", 857.2, "R", "frame.png", "c.ass", "fonts", "g.png", "out.jpg")
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "crop=iw/2:ih:iw/2:0" in fc and "setpts=0" in fc
    assert cmd[cmd.index("-ss") + 1] == "857.200" and "-frames:v" in cmd
