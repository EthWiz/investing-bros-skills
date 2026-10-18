"""Tests for make_cover.py. Run: python3 -m pytest skills/investing-bros-shorts/scripts"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from make_cover import build_command_fullbleed, PILL_HALF_H, PILL_Y, SQUARE, build_ass, build_command, headline_box, headline_lines  # noqa: E402


def test_pill_stays_inside_the_square_crop():
    # the 1:1 profile-grid crop of a 9:16 cover keeps y 420..1500
    assert SQUARE[0] < PILL_Y - PILL_HALF_H and PILL_Y + PILL_HALF_H < SQUARE[1]


@pytest.mark.parametrize("n_lines", [1, 2, 3])
def test_headline_sits_above_the_pill_and_inside_the_square(n_lines):
    # episode 7: a 3-line headline centred at a fixed y ran into the pill
    size, top, bottom, centre = headline_box(n_lines)
    assert bottom <= PILL_Y - PILL_HALF_H - 40
    assert top >= SQUARE[0] + 300               # leaves the face area above it alone
    assert top < centre < bottom


def test_headline_rules():
    assert headline_lines("סוויפט היא בכלל|[לא מערכת תשלומים]") == ["סוויפט היא בכלל", "[לא מערכת תשלומים]"]
    with pytest.raises(ValueError):
        headline_lines("א|ב|ג|ד")                        # max three lines
    with pytest.raises(ValueError):
        headline_lines("שורה ארוכה מדי בשביל תמונה ממוזערת")  # too long to read when tiny


def test_ass_is_rtl_with_gold_and_episode_pill():
    ass = build_ass("סוויפט היא בכלל|[לא מערכת תשלומים]", 6)
    assert "\\c&H1FB7F5&" in ass and "פרק 6" in ass
    for line in ass.splitlines():
        if line.startswith("Style:"):
            assert line.endswith(",-1")
    assert "פרק" not in build_ass("כותרת", None)


def test_command_picks_host_half_and_one_frame():
    cmd = build_command("raw.mp4", 857.2, "R", "frame.png", "c.ass", "fonts", "g.png", "out.jpg")
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "crop=iw/2:ih:iw/2:0" in fc and "setpts=0" in fc
    assert cmd[cmd.index("-ss") + 1] == "857.200" and "-frames:v" in cmd


def test_fullbleed_cover_matches_the_house_style():
    cmd = build_command_fullbleed("raw.mp4", 2121.0, [1130, 0, 608, 1080], "logo.png", "c.ass", "fonts", "g.png", "o.jpg")
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "crop=608:1080:1130:0" in fc and "overlay=56:150" in fc and "-frames:v" in cmd
    assert "vflip" in fc                                   # dark fade behind the logo: white "אחים" vanished on a bright wall


def test_boxed_line_and_word_rule():
    from make_cover import headline_warnings, is_boxed, line_centres
    ass = build_ass("סוויפט היא בכלל|[[לא מערכת תשלומים]]", 6)
    box = [l for l in ass.splitlines() if ",Box," in l]
    assert len(box) == 1 and "[" not in box[0].split(",,", 1)[1]           # brackets stripped, navy on a gold box
    assert is_boxed("[[א]]") and not is_boxed("[א]")
    with pytest.raises(ValueError):
        headline_lines("[[א]]|[[ב]]")                                     # one focal line
    with pytest.raises(ValueError):
        headline_lines("לא מערכת — תשלומים")                          # no dashes on screen
    assert headline_warnings("אחת שתיים שלוש|ארבע חמש שש שבע") and not headline_warnings("סוויפט|[[לא תשלומים]]")
    ys = line_centres(["א", "[[ב]]", "ג"])
    assert ys == sorted(ys) and ys[-1] < PILL_Y - PILL_HALF_H              # top to bottom, above the pill


@pytest.mark.parametrize("n_boxed", [0, 1])
def test_headline_inside_every_grid_crop(n_boxed):
    from make_cover import GRID_34
    _, top, bottom, _ = headline_box(3, n_boxed)
    assert GRID_34[0] < SQUARE[0] < top and bottom < SQUARE[1] < GRID_34[1]


def test_host_picture_gets_the_thumbnail_grade():
    from make_cover import GRADE
    for cmd in (build_command("raw.mp4", 1.0, "L", "f.png", "c.ass", "fonts", "g.png", "o.jpg"),
                build_command_fullbleed("raw.mp4", 1.0, [0, 0, 608, 1080], "l.png", "c.ass", "fonts", "g.png", "o.jpg")):
        assert GRADE in cmd[cmd.index("-filter_complex") + 1]
