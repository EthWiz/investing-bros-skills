"""Tests for the approved full-frame teaser renderer."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from build_fullframe_teaser import Timeline, build_ass, build_filter, caption_text, resolve_path, validate_audio_clock  # noqa: E402


PIECES = [
    {
        "host": "amitai",
        "start": 10.0,
        "end": 25.01,
        "cards": [[10.0, 10.5, "[דבר] חשוב מאוד"]],
    },
    {
        "host": "nadav",
        "start": 40.0,
        "end": 55.01,
        "cards": [[40.0, 40.5, "דבר [אחר] עכשיו"]],
    },
]


def test_timeline_rounds_each_piece_to_native_frames():
    timeline = Timeline(PIECES, 25)
    assert timeline.duration == pytest.approx(30.0)
    assert timeline.segments[1]["output_start"] == pytest.approx(15.0)


def test_ass_matches_approved_title_and_caption_style():
    ass = build_ass({"kicker": "פרק 9", "title": "שם הפרק"}, Timeline(PIECES, 25))
    assert "Style: Cap,Heebo ExtraBold,72" in ass
    assert "Style: Kick,Heebo Black,112" in ass
    assert "Style: Title,Heebo Black,72" in ass
    assert r"\pos(1862,22)" in ass
    assert r"\pos(960,990)" in ass
    assert "speaker" not in ass.lower()
    assert "&H001FB7F5" in ass  # #F5B71F in ASS BGR order


def test_caption_highlights_only_the_bracketed_word():
    text = caption_text("זה [דבר] חשוב")
    assert text.startswith("\u200f") and text.endswith("\u200f")
    assert r"{\c&H001FB7F5}דבר{\c&H00FFFFFF}" in text


def test_relative_paths_are_based_on_config_not_working_directory(tmp_path):
    config = tmp_path / "extras" / "teaser.json"
    assert resolve_path(config, "../promo/out.mp4") == (tmp_path / "promo" / "out.mp4").resolve()


def test_audio_clock_rejects_gap_collapsed_wav(monkeypatch, tmp_path):
    durations = iter((16.25, 16.0))
    monkeypatch.setattr("build_fullframe_teaser.probe_duration", lambda *_: next(durations))
    with pytest.raises(ValueError, match="make_pts_audio.sh"):
        validate_audio_clock(tmp_path / "source.mp4", tmp_path / "audio.wav", 25)


def test_filter_keeps_fractional_native_frame_rate_exact():
    config = {
        "crops": {"amitai": [0, 0, 100, 100], "nadav": [0, 0, 100, 100]},
        "fonts": "/tmp/fonts",
    }
    graph = build_filter(config, Timeline(PIECES, 24000 / 1001), "24000/1001", "/tmp/teaser.ass")
    assert "fps=24000/1001" in graph


def test_piece_without_crop_is_full_frame_not_zoomed():
    graph = build_filter({"fonts": "/tmp/fonts"}, Timeline(PIECES, 25), "25", "/tmp/t.ass")
    assert "crop=" not in graph and "force_original_aspect_ratio=decrease" in graph


def test_piece_can_carry_its_own_source_and_crop():
    pieces = [dict(PIECES[0], source="amitai-cam.mp4", crop=[0, 0, 1920, 1080]), PIECES[1]]
    timeline = Timeline(pieces, 25)
    assert timeline.segments[0]["source"] == "amitai-cam.mp4"
    graph = build_filter({"fonts": "/tmp/fonts"}, timeline, "25", "/tmp/t.ass")
    assert "crop=1920:1080:0:0" in graph


def test_caption_order_rejects_backwards_highlight():
    from build_fullframe_teaser import check_caption_order
    bad = {"cards": [[1.0, 1.4, "עלה [15%] השנה"], [1.4, 1.8, "[עלה] 15% השנה"]]}
    good = {"cards": [[1.0, 1.4, "[עלה] 15% השנה"], [1.4, 1.8, "עלה [15%] השנה"]]}
    assert check_caption_order(bad) and not check_caption_order(good)
    with pytest.raises(ValueError):
        Timeline([dict(PIECES[0], cards=[[10.0, 10.4, "a [b] c"], [10.4, 10.8, "[a] b c"]])], 25)


LONG = "אם הייתם משקיעים אלף דולר בברקשייר כמה זה שווה היום"


def test_caption_safe_area_is_about_twelve_percent_each_side():
    from build_fullframe_teaser import safe_area
    x0, x1 = safe_area()
    assert 0.10 * 1920 <= x0 <= 0.12 * 1920 + 1
    assert 1920 - x1 == pytest.approx(x0)


def test_long_caption_wraps_inside_the_safe_area():
    from build_fullframe_teaser import check_caption_safe_area
    text = caption_text(LONG)
    assert r"\N" in text
    assert check_caption_safe_area([{"host": "amitai", "start": 0, "end": 5, "cards": [[0, 1, LONG]]}]) == []


def test_caption_that_cannot_fit_is_rejected():
    from build_fullframe_teaser import check_caption_safe_area
    word = "א" * 60  # one unbreakable word wider than the safe area
    problems = check_caption_safe_area([{"host": "nadav", "start": 0, "end": 5, "cards": [[0, 1, word]]}])
    assert problems and "safe area" in problems[0]


def test_caption_too_long_for_two_lines_is_rejected():
    from build_fullframe_teaser import check_caption_safe_area
    problems = check_caption_safe_area([{"host": "nadav", "start": 0, "end": 5, "cards": [[0, 1, LONG * 3]]}])
    assert any("lines" in p for p in problems)


def test_safe_area_check_uses_the_real_font_when_present(monkeypatch):
    import build_fullframe_teaser as teaser
    from PIL import ImageFont
    calls = []

    def fake_loader(fonts_dir, size):
        calls.append(size)
        return ImageFont.load_default(size)

    monkeypatch.setattr(teaser, "load_caption_font", fake_loader)
    assert teaser.check_caption_safe_area([{"host": "a", "start": 0, "end": 5, "cards": [[0, 1, LONG]]}]) == []
    assert calls == [72]


def test_bracketed_highlight_is_never_split_across_lines():
    from build_fullframe_teaser import wrap_caption
    lines = wrap_caption("מילה " * 12 + "[שתי מילים]", 600, None, 72)
    assert any("[שתי מילים]" in line for line in lines)


def test_short_moment_is_flagged_as_possibly_cut_before_payoff():
    from build_fullframe_teaser import moment_warnings
    warnings = moment_warnings([{"host": "nadav", "start": 10, "end": 12.5, "cards": []},
                                {"host": "amitai", "start": 20, "end": 30, "cards": []}])
    assert len(warnings) == 1 and "payoff" in warnings[0]


def test_check_mode_needs_no_media(tmp_path, monkeypatch, capsys):
    import json
    import build_fullframe_teaser as teaser
    config = {"layout": "fullframe", "fonts": "fonts", "pieces": [
        {"host": "amitai", "start": 0, "end": 8, "cards": [[0, 1, "[קוקה] קולה היא חפיר טוב"]]}]}
    path = tmp_path / "teaser.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["build_fullframe_teaser.py", str(path), "--check"])
    assert teaser.main() == 0
    assert "CAPTIONS OK" in capsys.readouterr().out


def test_missing_host_is_flagged():
    from build_fullframe_teaser import moment_warnings
    warnings = moment_warnings([
        {"host": "amitai", "start": 0, "end": 6, "cards": []},
        {"host": "amitai", "start": 10, "end": 16, "cards": []},
    ])
    assert any("missing nadav" in w for w in warnings)


def test_long_moment_is_flagged_as_not_punchy():
    from build_fullframe_teaser import moment_warnings
    warnings = moment_warnings([
        {"host": "amitai", "start": 0, "end": 8, "cards": []},
        {"host": "nadav", "start": 20, "end": 44, "cards": []},  # 24 s explainer
    ])
    assert any("punchy" in w or "hole punches" in w for w in warnings)

