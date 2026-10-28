"""Tests for draft_proofread.py: the script's spelling, his ad-libs and skips, every disagreement listed."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from draft_proofread import draft, heard, script_words  # noqa: E402


def kinds(spots):
    return [k for k, _, _ in spots]


def test_a_garbled_name_keeps_the_script_spelling_and_is_listed():
    words, spots = draft(script_words("הפתרון של **סאטושי:** במקום פנקס אחד"), "הפתרון של סטושי במקום פנקס אחד".split())
    assert " ".join(words) == "הפתרון של סאטושי: במקום פנקס אחד"
    assert spots == [("heard differently", ["סאטושי:"], ["סטושי"])]


def test_an_ad_lib_is_added_and_a_skipped_phrase_dropped():
    script = script_words("מחשבים שנקראים כורים מתחרים על פתרון. ומעל כולם יש בנק מרכזי מאוד חזק.")
    said = "מחשבים שנקראים כורים בטח שמעתם את הביטוי מתחרים על פתרון. ומעל כולם יש בנק מרכזי.".split()
    words, spots = draft(script, said)
    assert "בטח שמעתם את הביטוי" in " ".join(words) and "מאוד חזק" not in " ".join(words)
    assert kinds(spots) == ["ad-lib", "skipped"]


def test_a_short_restart_is_only_listed():
    script = script_words("גם אם פתרו בשבילו את החידה.")
    words, spots = draft(script, "גם אם פתרו בשבילו פתרו בשבילו את החידה".split())
    assert " ".join(words) == "גם אם פתרו בשבילו את החידה." and kinds(spots) == ["extra"]


def test_whisper_words_split_at_the_geresh_are_joined(tmp_path):
    data = {"segments": [{"words": [{"word": " או", "start": 0, "end": 1}, {"word": " בלוקצ", "start": 1, "end": 2},
                                    {"word": "'יין", "start": 2, "end": 3}]}]}
    (tmp_path / "w.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    assert heard(tmp_path / "w.json") == ["או", "בלוקצ'יין"]
