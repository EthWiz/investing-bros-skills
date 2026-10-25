"""Tests for make_base.py: speed, per-host Riverside tracks, side-by-side guard, sync."""
import os
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from make_base import DEFAULT_CROP, build_filter, envelope_offset, seam_share, time_map  # noqa: E402


def test_default_style_speed_filters_video_audio_and_timemap():
    kept = [(10.0, 20.0, 0), (30.0, 35.0, 0.1)]
    graph, _ = build_filter(kept, 1.25)
    assert "setpts=PTS/1.25" in graph and "atempo=1.25" in graph
    mapped, duration = time_map(kept, 1.25)
    assert mapped[1][2] == pytest.approx(8.0)
    assert duration == pytest.approx(12.0)


def test_speed_one_uses_no_tempo_change():
    graph, _ = build_filter([(0.0, 10.0, 0)], 1.0)
    assert "setpts=PTS/1" not in graph and "atempo=" not in graph


def test_three_tuple_keeps_source_picture_and_default_crop():
    graph, keys = build_filter([(0.0, 5.0, 0)], 1.25)
    assert keys == [] and f"[0:v]trim" in graph and f"crop={DEFAULT_CROP}," in graph
    assert "[1:v]format=rgba[gr]" in graph and "[2:v]scale=210" in graph


def test_each_piece_takes_its_hosts_track_crop_and_offset_with_master_audio():
    kept = [(10.0, 15.0, 0, "1080:1920:420:0", "A"), (16.0, 20.0, 0, "1080:1920:380:0", "N"),
            (21.0, 23.0, 0, "1080:1920:420:0", "A")]
    graph, keys = build_filter(kept, 1.25, {"A": 0.5, "N": -0.25})
    assert keys == ["A", "N"]
    assert "[1:v]trim=start=10.500:end=15.500" in graph and "crop=1080:1920:420:0," in graph
    assert "[2:v]trim=start=15.750:end=19.750" in graph and "crop=1080:1920:380:0," in graph
    assert "[1:v]trim=start=21.500:end=23.500" in graph
    assert graph.count("[0:a]atrim") == 3 and "[0:v]" not in graph   # audio from SRC only
    assert "[3:v]format=rgba[gr]" in graph and "[4:v]scale=210" in graph
    assert time_map(kept, 1.0)[1] == pytest.approx(11.0)


def test_bad_crop_and_range_rejected():
    with pytest.raises(ValueError):
        build_filter([(0.0, 5.0, 0, "608:1080", "A")], 1.25)
    with pytest.raises(ValueError):
        build_filter([(5.0, 5.0, 0)], 1.25)


def _frame(left, right, w=640, h=360, seed=0):
    rng = np.random.default_rng(seed)
    g = np.empty((h, w), np.float32)
    g[:, : w // 2] = left
    g[:, w // 2:] = right
    return np.clip(g + rng.normal(0, 3, g.shape), 0, 255)


def test_seam_flags_side_by_side_but_not_one_host():
    assert seam_share(_frame(60, 180)) > 0.9                      # two hosts, two backgrounds
    smooth = np.tile(np.linspace(40, 200, 640, dtype=np.float32), (360, 1))
    assert seam_share(smooth) < 0.1                               # one continuous picture
    assert seam_share(_frame(60, 180, w=360, h=640)) == 0.0       # vertical frames are never checked


def test_envelope_offset_finds_track_shift():
    sr, rng = 8000, np.random.default_rng(1)
    bursts = np.repeat(rng.random(60) > 0.5, sr // 4) * rng.normal(0, 3000, 60 * (sr // 4))
    t0, search, shift = 5.0, 3.0, 0.42              # track time = master time + 0.42 s
    master = bursts[int(t0 * sr):int((t0 + 8) * sr)]
    start = int((t0 - search - shift) * sr)        # track at T shows master content of T - shift
    track = bursts[start:start + int((8 + 2 * search) * sr)]
    off, score = envelope_offset(master, track, sr, search)
    assert off == pytest.approx(shift, abs=0.011) and score > 0.9


def test_approved_renderer_declares_its_intentional_silent_endcard():
    source = Path(__file__).with_name("build_amitai_short.py").read_text()
    assert '"silent_endcard_seconds": 3.0' in source
