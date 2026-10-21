import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_titles_match import check  # noqa: E402
from rtl_fix import rtl_fix_title  # noqa: E402

YT = "פרק 5 - אנרגיה גרעינית: מי יספק את החשמל ל-AI?"


def test_rtl_fixed_copy_matches():
    assert check(YT, rtl_fix_title(YT)) == []


def test_different_wording_fails():
    errs = check(YT, rtl_fix_title("פרק 5 - אנרגיה גרעינית"))
    assert errs and "titles differ" in errs[0]


def test_marks_in_youtube_title_flagged():
    assert any("RTL marks" in e for e in check(rtl_fix_title(YT), rtl_fix_title(YT)))


def test_files_are_read(tmp_path):
    from check_titles_match import _read
    f = tmp_path / "t.txt"
    f.write_text(YT + "\n", encoding="utf-8")
    assert check(_read(str(f)), rtl_fix_title(YT)) == []
