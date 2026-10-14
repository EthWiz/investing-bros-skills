"""Tests for build_short.py. Run: python3 -m pytest skills/investing-bros-shorts/scripts"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from build_short import Timeline, build_ass, build_command, build_srt, check_cards, close_gaps, snap  # noqa: E402

CFG = {
    "name": "t",
    "fps": 24,
    "pieces": [[100.0, 110.0], [120.0, 125.0, 6.0]],
    "shots": [[100.0, 110.0, "L"], [120.0, 125.0, "R"]],
    "headline": ["כותרת", "[ירוק]"],
    "endcard": ["הפרק המלא"],
    "tags": [[100.0, 103.0, "אמיתי רסקין"]],
    "cards": [[100.0, 104.0, "שורה אחת|שורה שתיים"], [104.2, 109.9, "ל־use cases"], [120.0, 125.0, "סוף"]],
}


def test_snap_to_frame_grid():
    assert snap(843.69, 24) == round(843.69 * 24) / 24


def test_timeline_maps_across_cut():
    tl = Timeline(CFG["pieces"], 24)
    assert tl.duration == pytest.approx(15.0)
    assert tl.map(100.0) == pytest.approx(0.0)
    assert tl.map(120.0) == pytest.approx(10.0)   # second piece starts right after the first
    assert tl.map(125.0) == pytest.approx(15.0)
    with pytest.raises(ValueError):
        tl.map(115.0)                               # inside the removed part


def test_close_gaps_fills_small_gaps_and_overlaps():
    cards = close_gaps([(0, 1.0, "a"), (1.2, 2.0, "b"), (1.9, 3.0, "c"), (4.0, 5.0, "d")])
    assert cards[0][1] == 1.2     # small gap filled
    assert cards[1][1] == 1.9     # overlap removed
    assert cards[2][1] == 3.0     # big gap kept


def test_ass_has_headline_endcard_tag_and_captions():
    tl = Timeline(CFG["pieces"], 24)
    ass, cards = build_ass(CFG, tl)
    assert ass.count("Dialogue: 0,") == 3
    assert ",Head," in ass and ",End," in ass and ",Tag," in ass
    assert "\\c&H1FB7F5&" in ass                      # emerald highlight
    assert "⁦use cases⁩" in ass             # English isolated inside Hebrew
    for line in ass.splitlines():
        if line.startswith("Style:"):
            assert line.endswith(",-1")              # auto base direction for RTL


def test_srt_strips_highlight_brackets():
    tl = Timeline(CFG["pieces"], 24)
    _, cards = build_ass(CFG, tl)
    srt = build_srt(cards)
    assert "[" not in srt and "00:00:00,000 --> " in srt


def test_command_switches_host_and_applies_gain():
    tl = Timeline(CFG["pieces"], 24)
    cmd = build_command(CFG, tl)
    assert "between(t,10.000,15.000)" in cmd        # R shot in output time
    assert "volume=6.0dB" in cmd
    assert "crop=iw/2:ih:iw/2:0" in cmd and "crop=iw/2:ih:0:0" in cmd
    assert "loudnorm=I=-14" in cmd


def test_check_cards_flags_three_lines_and_long_lines():
    warnings = check_cards([[0, 1, "א|ב|ג"], [1, 2, "א" * 30]])
    assert len(warnings) == 2
