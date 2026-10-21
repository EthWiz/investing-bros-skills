import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from shift_after_cut import shift, shift_description  # noqa: E402

CUT = [(1605.0, 1645.2)]  # episode 8 courier call


def test_before_cut_unchanged():
    assert shift(600, CUT) == 600


def test_after_cut_moves_by_cut_length():
    assert round(shift(1800, CUT), 1) == 1759.8


def test_inside_cut_snaps_to_cut_point():
    assert shift(1620, CUT) == 1605.0


def test_description_lines():
    text = "תיאור\n\n00:00 פתיחה\n26:00 לפני\n30:00 אחרי\n1:05:00 סוף\n"
    out = shift_description(text, CUT)
    assert out == "תיאור\n\n00:00 פתיחה\n26:00 לפני\n29:20 אחרי\n1:04:20 סוף\n"


def test_two_cuts_add_up():
    assert shift(1000, [(100, 110), (200, 230)]) == 960
