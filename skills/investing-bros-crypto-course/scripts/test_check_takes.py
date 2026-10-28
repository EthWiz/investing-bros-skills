"""Tests for check_takes.py: what counts as a problem in a take, before cutting."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from check_takes import face_findings, parse_audio, take_findings  # noqa: E402

PIC = {"width": 1920, "height": 1080, "fps": 30.0, "duration": 126.8}
QUIET = {"floor": -62.0, "peak": -3.0, "at_peak": 1}


def levels(findings):
    return [level for level, _ in findings]


def test_astats_logs_give_the_noise_floor_and_the_peaks():
    log = "\n".join(f"lavfi.astats.Overall.RMS_level={x}" for x in [-20, -22, -44, -45, -46, -21, -19, -23, -25, -30, -60])
    log += "\n[Parsed_astats_2 @ 0x1] Overall\n[Parsed_astats_2 @ 0x1] Peak level dB: 0.000000\n[Parsed_astats_2 @ 0x1] Peak count: 2.000000\n"
    a = parse_audio(log)
    assert a == {"floor": -46.0, "peak": 0.0, "at_peak": 2}


def test_a_clean_1080p_take_has_nothing_to_fix():
    assert take_findings(1, PIC, QUIET, [(0.5, 1.0), (120.0, 125.0)]) == []


def test_the_record_click_is_not_clipping_but_a_clipping_voice_is():
    assert take_findings(1, PIC, {"floor": -62.0, "peak": 0.0, "at_peak": 2}) == []
    assert levels(take_findings(1, PIC, {"floor": -62.0, "peak": 0.0, "at_peak": 400})) == ["fix"]


def test_720p_must_be_fixed_and_a_noisy_room_or_a_long_wait_are_notes():
    assert levels(take_findings(1, {**PIC, "width": 1280, "height": 720}, QUIET)) == ["fix"]
    found = take_findings(5, PIC, {**QUIET, "floor": -46.0}, [(14.42, 14.6), (125.0, 125.44)])
    assert levels(found) == ["note", "note"] and "14.4 s before the first word" in found[1][1]


def test_framing_that_drifted_between_takes_is_flagged():
    same = {1: {"cx": 840, "top": 360, "w": 630}, 2: {"cx": 838, "top": 366, "w": 628}}
    assert "fix" not in levels(face_findings(same))
    drift = {1: {"cx": 950, "top": 173, "w": 617}, 2: {"cx": 784, "top": 291, "w": 667}, 3: {"cx": 942, "top": 295, "w": 714}}
    assert levels(face_findings(drift))[-1] == "fix"
    assert face_findings({1: same[1]}) == []
