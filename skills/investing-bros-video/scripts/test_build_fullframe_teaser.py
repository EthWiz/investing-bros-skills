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
    assert "Style: Cap,Heebo ExtraBold,84" in ass
    assert "Style: Kick,Heebo Black,112" in ass
    assert "Style: Title,Heebo Black,72" in ass
    assert r"\pos(1862,22)" in ass
    assert r"\pos(960,1000)" in ass
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
