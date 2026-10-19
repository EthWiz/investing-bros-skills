"""Tests for transcribe.py helpers. Run: python3 -m pytest skills/investing-bros-post-production/scripts"""
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(__file__))
import transcribe  # noqa: E402
from transcribe import PTS_FILTER, fmt_clock, fmt_srt_time, merge_speech  # noqa: E402


def test_merge_speech_joins_close_spans_and_caps_length():
    spans = [(0.0, 2.0), (2.3, 5.0), (5.2, 11.5), (11.6, 13.0), (20.0, 21.0)]
    assert merge_speech(spans) == [[0.0, 11.5], [11.6, 13.0], [20.0, 21.0]]


def test_time_formats():
    assert fmt_srt_time(3723.5) == "01:02:03,500"
    assert fmt_clock(65) == "1:05" and fmt_clock(3725) == "1:02:05"


def test_faster_whisper_honours_threads_and_pts(monkeypatch, tmp_path):
    calls = {}

    class FakeModel:
        def __init__(self, *args, **kwargs):
            calls["model"] = kwargs

        def transcribe(self, *_args, **_kwargs):
            return iter(()), SimpleNamespace(duration=0)

    def fake_run(command, **_kwargs):
        calls["ffmpeg"] = command
        return SimpleNamespace()

    monkeypatch.setitem(sys.modules, "faster_whisper", SimpleNamespace(WhisperModel=FakeModel))
    monkeypatch.setattr(transcribe.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["transcribe.py", "source.mp4", str(tmp_path / "transcript"), "--threads", "7", "--no-level"],
    )
    assert transcribe.main() == 0
    assert calls["model"]["cpu_threads"] == 7
    assert PTS_FILTER in calls["ffmpeg"]
