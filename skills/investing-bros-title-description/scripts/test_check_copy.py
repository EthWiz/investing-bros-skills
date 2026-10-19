import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_copy import check_description, check_title, check_titles, main  # noqa: E402

EP4 = "פרק 4 - ניו קלאודס: מי ינצח במלחמת העננים?"

TITLES_OK = """1. פרק 7 - זהב: למה הבנקים המרכזיים קונים?
2. פרק 7 - זהב: מגן מאינפלציה או סתם מתכת?
3. פרק 7 - איך משקיעים בזהב ב־2026?
4. פרק 7 - זהב מול ביטקוין: מי באמת שומר ערך?
5. פרק 7 - זהב, בנקים מרכזיים ומה שביניהם

בחירה סופית:
"""

# Episode 2's Doc description (real), with chapters re-based to 0:00.
EP2_DESC = """למה חברות כמו ספייסאקס, פלנטיר ואנדוריל מתחרות בענקיות הביטחון של ארה״ב? בפרק 2 מדברים על מרוץ ה-AI ובעיקר על טרנד הניו-פריימס, עם רעיונות מהתיק האישי כולל זיסקיילר וסייבר.

אין כאן המלצת השקעה. רק שיחה.

0:00 ברוכים הבאים לפרק
1:05 מרוץ המודלים: OpenAI Astra מול אנתרופיק

3:47 גרוק, אג׳נטים ושימוש במחשב

8:14 מה זה ניו-פריימס: ספייסאקס, פלנטיר, אנדוריל וסרוניק
45:33 סייבר וזיסקיילר
"""

SPOTIFY_EP1 = "🎧 להאזנה בספוטיפיי: https://open.spotify.com/episode/7gV79L2FqVTfr6f8TPZWMA"
YOUTUBE_DESC = EP2_DESC.replace(
    "אין כאן המלצת השקעה. רק שיחה.\n",
    f"אין כאן המלצת השקעה. רק שיחה.\n\n{SPOTIFY_EP1}\n",
)


def errors(problems):
    return [p for p in problems if p.startswith("error:")]


def test_episode_4_title_passes():
    assert check_title(EP4, "t", 4) == []


def test_em_dash_fails_title():
    errs = errors(check_title("פרק 4 - ניו קלאודס — מי ינצח במלחמת העננים?", "t"))
    assert any("em dash" in e for e in errs)


def test_em_dash_after_number_fails():
    # the Drive folder uses an em dash; the title must not
    errs = errors(check_title("פרק 4 — ניו קלאודס", "t"))
    assert any("plain hyphen" in e for e in errs) and any("em dash" in e for e in errs)


def test_en_dash_fails_anywhere():
    # Amitai, 2026-10-15: an en dash reads as AI-written, same as an em dash
    errs = errors(check_title("פרק 4 \u2013 ניו קלאודס: מי ינצח במלחמת העננים?", "t"))
    assert any("en dash" in e for e in errs) and any("plain hyphen" in e for e in errs)
    assert any("en dash" in e for e in errors(check_description(EP2_DESC.replace("8:14 מה זה", "8:14 \u2013 מה זה"))))


def test_plain_hyphen_titles_pass():
    # episode 6 and 7 as published use the plain hyphen
    assert errors(check_title("פרק 6 - מהפכת הטוקניזציה", "t")) == []


def test_wrong_episode_number():
    assert errors(check_title(EP4, "t", 5))


def test_too_long_title_fails_and_long_warns():
    long_body = "א" * 61
    assert errors(check_title(f"פרק 4 - {long_body}", "t"))
    mid = check_title(f"פרק 4 - {'א' * 55}", "t")
    assert not errors(mid) and any(p.startswith("warn:") for p in mid)


def test_clickbait_and_hype_fail():
    for bad in ["פרק 4 - לא תאמינו מה קרה לענן?", "פרק 4 - הענן המטורף",
                "פרק 4 - ניו קלאודס!", "פרק 4 - ניו קלאודס 🚀"]:
        assert errors(check_title(bad, "t")), bad


def test_buy_call_only_warns():
    p = check_title("פרק 4 - ניו קלאודס: לקנות או לחכות?", "t")
    assert not errors(p) and any("buy/sell" in x for x in p)


def test_five_options_ok():
    assert errors(check_titles(TITLES_OK, 7)) == []


def test_needs_five_options_and_final_line():
    four = "\n".join(TITLES_OK.splitlines()[:4]) + "\n\nבחירה סופית:\n"
    assert any("expected exactly 5" in e for e in errors(check_titles(four, 7)))
    no_final = "\n".join(TITLES_OK.splitlines()[:5])
    assert any("בחירה סופית" in e for e in errors(check_titles(no_final, 7)))


def test_needs_three_questions():
    flat = "\n".join(f"{i}. פרק 7 - זהב ומה שביניהם {i}" for i in range(1, 6)) + "\n\nבחירה סופית:\n"
    assert any("questions" in e for e in errors(check_titles(flat, 7)))


def test_single_chosen_title_ok():
    assert check_titles(EP4 + "\n", 4) == []


def test_single_published_title():
    # episode 7 went up on YouTube as "פרק 7 - למה כולם קונים זהב?"
    assert errors(check_titles("פרק 7 - למה כולם קונים זהב?\n", 7)) == []
    errs = errors(check_titles("פרק 7 \u2013 למה כולם קונים זהב?\n", 7))
    assert errs and all("dash" in e or "hyphen" in e for e in errs)


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


def test_chapter_label_starting_with_english_fails():
    # episode 2 went out with "1:05 OpenAI Astra מול אנתרופיק ומרוץ המודלים": the line flips LTR
    bad = EP2_DESC.replace("1:05 מרוץ המודלים: OpenAI Astra מול אנתרופיק", "1:05 OpenAI Astra מול אנתרופיק ומרוץ המודלים")
    errs = errors(check_description(bad))
    assert len(errs) == 1 and "chapter 2" in errs[0] and "Hebrew word" in errs[0]


def test_chapter_label_starting_with_number_or_symbol_fails():
    for label in ["2022: רוסיה והדולר", "- פתיחה", "SpaceX וטלקום"]:
        bad = EP2_DESC.replace("45:33 סייבר וזיסקיילר", f"45:33 {label}")
        assert any("Hebrew word" in e for e in errors(check_description(bad))), label


def test_english_inside_a_hebrew_label_is_fine():
    ok = EP2_DESC.replace("45:33 סייבר וזיסקיילר", "45:33 סייבר: Zscaler ו-CrowdStrike")
    assert errors(check_description(ok)) == []


def test_intro_must_start_with_hebrew():
    bad = EP2_DESC.replace("למה חברות כמו", "SpaceX, Palantir: למה חברות כמו")
    assert any("intro line" in e for e in errors(check_description(bad)))


def test_youtube_chapter_rules():
    close = EP2_DESC.replace("1:05 מרוץ", "0:05 מרוץ")
    assert any("at least 10 s" in e for e in errors(check_description(close)))
    two = "למה זהב? שיחה על זהב.\n\nאין כאן המלצת השקעה. רק שיחה.\n\n0:00 פתיחה\n1:00 זהב\n"
    assert any("at least 3" in e for e in errors(check_description(two)))


def test_youtube_description_requires_clean_episode_spotify_link():
    assert errors(check_description(YOUTUBE_DESC, youtube=True)) == []
    missing = check_description(EP2_DESC, youtube=True)
    assert any("per-episode Spotify line" in e for e in errors(missing))
    pending = check_description(EP2_DESC, youtube=True, allow_missing_spotify=True)
    assert not errors(pending)
    assert any(p.startswith("warn:") and "Spotify" in p for p in pending)


def test_youtube_description_rejects_show_url_query_and_wrong_order():
    show = YOUTUBE_DESC.replace(
        "https://open.spotify.com/episode/7gV79L2FqVTfr6f8TPZWMA",
        "https://open.spotify.com/show/4fREAemgQDMWIUK58N5Jjk",
    )
    assert any("per-episode URL" in e for e in errors(check_description(show, youtube=True)))
    query = YOUTUBE_DESC.replace("7gV79L2FqVTfr6f8TPZWMA", "7gV79L2FqVTfr6f8TPZWMA?si=abc")
    assert any("no ?si=" in e for e in errors(check_description(query, youtube=True)))
    wrong_order = YOUTUBE_DESC.replace(
        f"{SPOTIFY_EP1}\n\n0:00 ברוכים הבאים לפרק",
        f"0:00 ברוכים הבאים לפרק\n\n{SPOTIFY_EP1}",
    )
    assert any("before the chapters" in e for e in errors(check_description(wrong_order, youtube=True)))
    no_blank_before = YOUTUBE_DESC.replace(f"שיחה.\n\n{SPOTIFY_EP1}", f"שיחה.\n{SPOTIFY_EP1}")
    assert any("between the disclaimer" in e for e in errors(check_description(no_blank_before, youtube=True)))
    no_blank_after = YOUTUBE_DESC.replace(f"{SPOTIFY_EP1}\n\n0:00", f"{SPOTIFY_EP1}\n0:00")
    assert any("after the Spotify line" in e for e in errors(check_description(no_blank_after, youtube=True)))


def test_youtube_description_allows_only_headphone_emoji():
    assert not any("emoji" in e for e in errors(check_description(YOUTUBE_DESC, youtube=True)))
    assert any("emoji" in e for e in errors(check_description(YOUTUBE_DESC + "\n🚀", youtube=True)))
    extra_headphones = YOUTUBE_DESC.replace("למה חברות", "🎧 למה חברות")
    assert any("only on the Spotify" in e for e in errors(check_description(extra_headphones, youtube=True)))


def _pad(desc):
    for a, b in [("0:00 ", "00:00 "), ("1:05 ", "01:05 "), ("3:47 ", "03:47 "), ("8:14 ", "08:14 ")]:
        desc = desc.replace("\n" + a, "\n" + b)
    return desc


def test_spotify_needs_zero_padded_times():
    errs = errors(check_description(EP2_DESC, spotify=True))
    assert any("'01:05' not '1:05'" in e for e in errs)
    assert errors(check_description(_pad(EP2_DESC), spotify=True)) == []
    assert errors(check_description(_pad(EP2_DESC))) == []   # padded times are fine on YouTube too


def test_spotify_needs_30_seconds_between_chapters():
    close = _pad(EP2_DESC).replace("01:05 מרוץ", "00:20 מרוץ")
    assert errors(check_description(close)) == []
    assert any("Spotify needs at least 30 s" in e for e in errors(check_description(close, spotify=True)))


def test_spotify_warns_on_long_labels():
    probs = check_description(_pad(EP2_DESC), spotify=True)
    assert any("Spotify suggests under 40" in p for p in probs)   # the 08:14 label is 50 characters


def test_cli_spotify_flag(tmp_path, capsys):
    d = tmp_path / "description.txt"
    d.write_text(EP2_DESC, encoding="utf-8")
    assert main(["--description", str(d)]) == 0
    assert main(["--description", str(d), "--spotify"]) == 1


def test_cli_youtube_spotify_link_flags(tmp_path):
    description = tmp_path / "youtube.txt"
    description.write_text(YOUTUBE_DESC, encoding="utf-8")
    assert main(["--description", str(description), "--youtube"]) == 0
    description.write_text(EP2_DESC, encoding="utf-8")
    assert main(["--description", str(description), "--youtube"]) == 1
    assert main(["--description", str(description), "--youtube", "--allow-missing-spotify"]) == 0
