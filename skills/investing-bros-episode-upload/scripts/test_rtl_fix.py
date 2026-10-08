"""Tests for rtl_fix.py. Run: python3 -m pytest skills/investing-bros-episode-upload/scripts"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from rtl_fix import LRM, RLM, rtl_fix_description, rtl_fix_title  # noqa: E402

TITLE = "פרק 4 – ניו קלאודס: מי ינצח במלחמת העננים?"

DESCRIPTION = """\
מה זה NeoCloud? הכירו את החברות שמשכירות GPU לענקיות ה-AI.

אין כאן המלצת השקעה. רק שיחה.

0:00 פתיחה
1:05 מי ינצח במלחמת העננים?
"""


def test_title_gets_rlm_after_final_question_mark():
    assert rtl_fix_title(TITLE) == TITLE + RLM


def test_title_is_idempotent():
    once = rtl_fix_title(TITLE)
    assert rtl_fix_title(once) == once


def test_description_rules():
    lines = rtl_fix_description(DESCRIPTION).split("\n")
    # intro: RLM after mid-line '?' and at end of the Hebrew line
    assert lines[0] == "מה זה NeoCloud?" + RLM + " הכירו את החברות שמשכירות GPU לענקיות ה-AI." + RLM
    assert lines[1] == ""                                   # blank lines kept
    assert lines[2] == "אין כאן המלצת השקעה. רק שיחה." + RLM  # disclaimer
    assert lines[4] == LRM + "0:00 פתיחה"                    # chapter pinned with LRM
    assert lines[5] == LRM + "1:05 מי ינצח במלחמת העננים?" + RLM
    assert not lines[4].endswith(RLM)                        # chapters don't get a trailing RLM


def test_description_is_idempotent():
    once = rtl_fix_description(DESCRIPTION)
    assert rtl_fix_description(once) == once


def test_hour_long_timestamps_are_chapters():
    assert rtl_fix_description("1:02:30 סיכום\n") == LRM + "1:02:30 סיכום\n"
