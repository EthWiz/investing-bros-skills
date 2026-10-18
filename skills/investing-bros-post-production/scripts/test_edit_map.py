import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from edit_map import keep_ranges, main, mmss, parse_cut, raw_to_edited  # noqa: E402


def test_no_cuts_is_start_offset():
    assert keep_ranges(42, 2700, []) == [[42, 2700]]
    assert raw_to_edited(100, 42, 2700, []) == 58


def test_cuts_shift_later_times():
    cuts = [[600, 610], [1200, 1230.5]]
    assert keep_ranges(42, 2700, cuts) == [[42, 600], [610, 1200], [1230.5, 2700]]
    assert raw_to_edited(500, 42, 2700, cuts) == 458
    assert raw_to_edited(700, 42, 2700, cuts) == 700 - 42 - 10
    assert raw_to_edited(1300, 42, 2700, cuts) == 1300 - 42 - 10 - 30.5
    assert raw_to_edited(605, 42, 2700, cuts) is None        # inside a cut
    assert raw_to_edited(10, 42, 2700, cuts) is None         # before the start


def test_cuts_are_sorted_and_validated():
    assert keep_ranges(0, 100, [[50, 60], [10, 20]]) == [[0, 10], [20, 50], [60, 100]]
    with pytest.raises(ValueError, match="overlaps"):
        keep_ranges(0, 100, [[10, 30], [20, 40]])
    with pytest.raises(ValueError, match="inside the episode"):
        keep_ranges(42, 100, [[30, 50]])
    with pytest.raises(ValueError, match="end must be after start"):
        keep_ranges(0, 100, [[50, 50]])


def test_parse_cut_accepts_clock_times():
    assert parse_cut("10:05-10:12.5") == (605.0, 612.5)
    assert parse_cut("605-612.5") == (605.0, 612.5)
    with pytest.raises(ValueError):
        parse_cut("605")


def test_mmss():
    assert mmss(65) == "01:05" and mmss(3725) == "01:02:05"


def test_cli(tmp_path, capsys):
    e = tmp_path / "edit.json"
    e.write_text(json.dumps({"start": 42, "end": 2700, "cuts": [[600, 610]]}))
    assert main([str(e), "--raw", "700", "605"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0].split("\t")[1] == "10:48" and out[1].endswith("cut")
    assert main(["--check", "42", "2700", "--cut", "600-610"]) == 0
    assert capsys.readouterr().out.split() == ["42.000", "600.000", "610.000", "2700.000"]
    assert main(["--check", "42", "2700", "--cut", "30-50"]) == 1
