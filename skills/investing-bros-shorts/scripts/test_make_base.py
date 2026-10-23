"""Tests for make_base.py speed handling."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from make_base import build_filter, time_map  # noqa: E402


def test_default_style_speed_filters_video_audio_and_timemap():
    kept = [(10.0, 20.0, 0), (30.0, 35.0, 0.1)]
    graph = build_filter(kept, 1.25)
    assert "setpts=PTS/1.25" in graph and "atempo=1.25" in graph
    mapped, duration = time_map(kept, 1.25)
    assert mapped[1][2] == pytest.approx(8.0)
    assert duration == pytest.approx(12.0)


def test_speed_one_uses_no_tempo_change():
    graph = build_filter([(0.0, 10.0, 0)], 1.0)
    assert "setpts=PTS/1" not in graph and "atempo=" not in graph


def test_approved_renderer_declares_its_intentional_silent_endcard():
    source = Path(__file__).with_name("build_amitai_short.py").read_text()
    assert '"silent_endcard_seconds": 3.0' in source
