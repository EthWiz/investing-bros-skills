"""Tests for build_teaser.py. Run: python3 -m pytest skills/investing-bros-video/scripts"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from build_teaser import X264, Timeline, build_ass, build_command  # noqa: E402

CFG = {
    "name": "teaser_nadav", "out": "teaser.mp4", "fps": 24, "host": "right",
    "audio_source": "ep_audio.wav", "label": "פרק 6 · טוקניזציה", "speaker": "נדב רסקין",
    "pieces": [[2217.05, 2233.0], [1452.88, 1460.0]],     # out of source order on purpose
    "cards": [[2217.05, 2220.0, "בחיים שלי|לא הייתי מאמין"], [1452.88, 1460.0, "יש לי [מניה בכיס]?"]],
}


def test_out_of_order_pieces_map_in_teaser_order():
    tl = Timeline(CFG["pieces"], 24)
    first = tl.pieces[0][1] - tl.pieces[0][0]
    assert tl.map(1452.88) == pytest.approx(first, abs=0.05)
    assert round(tl.duration * 24, 6) == round(tl.duration * 24)   # whole frames


def test_panel_side_follows_host():
    tl = Timeline(CFG["pieces"], 24)
    assert "\\pos(480," in build_ass(CFG, tl)                        # host right -> panel left
    left = dict(CFG, host="left")
    assert "\\pos(1440," in build_ass(left, tl)


def test_command_uses_episode_encoder_and_leveled_audio():
    tl = Timeline(CFG["pieces"], 24)
    cmd = build_command(CFG, tl)
    assert X264 in cmd                                               # joinable with the episode body
    assert '-i "ep_audio.wav"' in cmd and "loudnorm" not in cmd      # leveled audio is reused as is
    assert "crop=iw/2:ih:iw/2:0" in cmd and "overlay=960:0" in cmd
    assert f"atrim=duration={tl.duration:.4f}" in cmd


def test_without_audio_source_levels_each_piece():
    tl = Timeline([[10.0, 20.0, 16.5]], 24)
    cfg = dict(CFG, pieces=[[10.0, 20.0, 16.5]], cards=[[10.0, 20.0, "א"]])
    cfg.pop("audio_source")
    cmd = build_command(cfg, tl)
    assert "volume=16.5dB" in cmd and "loudnorm=I=-16" in cmd
