import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_copy import check_description, check_title, check_titles, main  # noqa: E402

EP4 = "פרק 4 – ניו קלאודס: מי ינצח במלחמת העננים?"

TITLES_OK = """1. פרק 7 – זהב: למה הבנקים המרכזיים קונים?
2. פרק 7 – זהב: מגן מאינפלציה או סתם מתכת?
3. פרק 7 – איך משקיעים בזהב ב־2026?
4. פרק 7 – זהב מול ביטקוין: מי באמת שומר ערך?
5. פרק 7 – זהב, בנקים מרכזיים ומה שביניהם

בחירה סופית:
"""

# Episode 2's Doc description (real), with chapters re-based to 0:00.
EP2_DESC = """למה חברות כמו ספייסאקס, פלנטיר ואנדוריל מתחרות בענקיות הביטחון של ארה״ב? בפרק 2 מדברים על מרוץ ה-AI ובעיקר על טרנד הניו-פריימס, עם רעיונות מהתיק האישי כולל זיסקיילר וסייבר.

אין כאן המלצת השקעה. רק שיחה.

0:00 ברוכים הבאים לפרק
1:05 OpenAI Astra מול אנתרופיק ומרוץ המודלים

3:47 גרוק, אג׳נטים ושימוש במחשב

8:14 מה זה ניו-פריימס: ספייסאקס, פלנטיר, אנדוריל וסרוניק
45:33 סייבר וזיסקיילר
"""


def errors(problems):
    return [p for p in problems if p.startswith("error:")]


def test_episode_4_title_passes():
    assert check_title(EP4, "t", 4) == []


def test_em_dash_fails_title():
    errs = errors(check_title("פרק 4 – ניו קלאודס — מי ינצח במלחמת העננים?", "t"))
    assert any("em dash" in e for e in errs)


def test_em_dash_after_number_fails():
    # the Drive folder uses an em dash; the title must not
    errs = errors(check_title("פרק 4 — ניו קלאודס", "t"))
    assert any("en dash" in e for e in errs) and any("em dash" in e for e in errs)


def test_hyphen_after_number_fails():
    # episode 6 went out as "פרק 6 - מהפכת הטוקניזציה"
    assert errors(check_title("פרק 6 - מהפכת הטוקניזציה", "t"))


def test_wrong_episode_number():
    assert errors(check_title(EP4, "t", 5))


def test_too_long_title_fails_and_long_warns():
    long_body = "א" * 61
    assert errors(check_title(f"פרק 4 – {long_body}", "t"))
    mid = check_title(f"פרק 4 – {'א' * 55}", "t")
    assert not errors(mid) and any(p.startswith("warn:") for p in mid)


def test_clickbait_and_hype_fail():
    for bad in ["פרק 4 – לא תאמינו מה קרה לענן?", "פרק 4 – הענן המטורף",
                "פרק 4 – ניו קלאודס!", "פרק 4 – ניו קלאודס 🚀"]:
        assert errors(check_title(bad, "t")), bad


def test_buy_call_only_warns():
    p = check_title("פרק 4 – ניו קלאודס: לקנות או לחכות?", "t")
    assert not errors(p) and any("buy/sell" in x for x in p)


def test_five_options_ok():
    assert errors(check_titles(TITLES_OK, 7)) == []


def test_needs_five_options_and_final_line():
    four = "\n".join(TITLES_OK.splitlines()[:4]) + "\n\nבחירה סופית:\n"
    assert any("expected exactly 5" in e for e in errors(check_titles(four, 7)))
    no_final = "\n".join(TITLES_OK.splitlines()[:5])
    assert any("בחירה סופית" in e for e in errors(check_titles(no_final, 7)))


def test_needs_three_questions():
    flat = "\n".join(f"{i}. פרק 7 – זהב ומה שביניהם {i}" for i in range(1, 6)) + "\n\nבחירה סופית:\n"
    assert any("questions" in e for e in errors(check_titles(flat, 7)))


def test_single_chosen_title_ok():
    assert check_titles(EP4 + "\n", 4) == []


def test_final_pick_is_checked():
    bad = TITLES_OK.replace("בחירה סופית:", "בחירה סופית: פרק 7 — זהב")
    assert errors(check_titles(bad, 7))


def test_episode_2_description_passes():
    assert errors(check_description(EP2_DESC)) == []


def test_episode_2_draft_em_dash_fails():
    # the real episode 2 .txt draft: "אחים להשקעות פרק 2 — שני אחים מדברים..."
    desc = EP2_DESC.replace("בפרק 2 מדברים", "פרק 2 — שני אחים מדברים")
    assert any("em dash" in e for e in errors(check_description(desc)))


def test_missing_disclaimer_fails():
    # episode 4's description Doc had no disclaimer
    assert any("disclaimer" in e for e in errors(check_description(EP2_DESC.replace("אין כאן המלצת השקעה. רק שיחה.\n", ""))))


def test_chapters_must_start_at_zero_and_increase():
    late = EP2_DESC.replace("0:00 ברוכים הבאים לפרק\n", "")
    assert any("0:00" in e for e in errors(check_description(late)))
    swapped = EP2_DESC.replace("3:47", "0:30")
    assert any("go up" in e for e in errors(check_description(swapped)))


def test_chapter_must_be_time_first():
    bad = EP2_DESC.replace("45:33 סייבר וזיסקיילר", "סייבר וזיסקיילר 45:33")
    assert any("time first" in e for e in errors(check_description(bad)))


def test_direction_marks_fail():
    assert any("mark" in e for e in errors(check_description(EP2_DESC.replace("?", "?‏", 1))))


def test_intro_question_is_only_a_warning():
    desc = EP2_DESC.replace("למה חברות כמו ספייסאקס, פלנטיר ואנדוריל מתחרות בענקיות הביטחון של ארה״ב? ", "")
    p = check_description(desc)
    assert not errors(p) and any("question" in x for x in p)


def test_cli_exit_codes(tmp_path):
    good = tmp_path / "t.txt"
    good.write_text(TITLES_OK, encoding="utf-8")
    assert main(["--titles", str(good), "--episode", "7"]) == 0
    bad = tmp_path / "d.txt"
    bad.write_text("משהו — אחר\n", encoding="utf-8")
    assert main(["--description", str(bad)]) == 1
