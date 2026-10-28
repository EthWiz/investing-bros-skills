"""Tests for check_takes.py: what counts as a problem in a take, before cutting."""
import os
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from check_takes import check_take, face_findings, parse_audio, take_findings  # noqa: E402

PIC = {"width": 1920, "height": 1080, "fps": 30.0, "duration": 126.8, "audio": True}
# lesson 1 beat 4 (2026-10-28): 570 of 8.2 million samples within 1 dB of full scale, room noise at -46 dB
SPEECH = {"samples": 8183616, "mean": -23.0, "max": 0.0, "near_full": 570, "floor": -62.0}
needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")


def levels(findings):
    return [level for level, _ in findings]


def test_the_logs_give_level_peaks_and_noise_floor():
    log = "\n".join(f"lavfi.astats.Overall.RMS_level={x}" for x in [-20, -22, -44, -45, -46, -21, -19, -23, -25, -30, -60])
    log += ("\n[Parsed_volumedetect_0 @ 0x1] n_samples: 0\n[Parsed_volumedetect_1 @ 0x2] n_samples: 2643840"
            "\n[Parsed_volumedetect_1 @ 0x2] mean_volume: -23.1 dB\n[Parsed_volumedetect_1 @ 0x2] max_volume: 0.0 dB"
            "\n[Parsed_volumedetect_1 @ 0x2] histogram_0db: 32\n[Parsed_volumedetect_1 @ 0x2] histogram_1db: 96\n")
    assert parse_audio(log) == {"samples": 2643840, "mean": -23.1, "max": 0.0, "near_full": 32, "floor": -46.0}
    assert parse_audio("") == {"samples": 0, "mean": None, "max": None, "near_full": 0, "floor": None}


def test_a_clean_1080p_take_has_nothing_to_fix():
    assert take_findings(1, PIC, SPEECH, [(0.5, 1.0), (120.0, 125.0)]) == []


def test_missing_unmeasured_or_silent_sound_must_be_fixed():
    assert levels(take_findings(1, PIC, None)) == ["fix"]
    assert levels(take_findings(1, PIC, parse_audio(""))) == ["fix"]
    found = take_findings(1, PIC, {**SPEECH, "mean": -91.0, "max": -91.0, "near_full": 0})
    assert levels(found) == ["fix"] and "no audible sound" in found[0][1]


def test_a_clipping_voice_is_fixed_and_a_touch_of_full_scale_noted():
    assert levels(take_findings(1, PIC, {**SPEECH, "near_full": 95163, "samples": 192000})) == ["fix"]
    assert levels(take_findings(1, PIC, {**SPEECH, "near_full": 2000})) == ["note"]


def test_720p_must_be_fixed_and_a_noisy_room_or_a_long_wait_are_notes():
    assert levels(take_findings(1, {**PIC, "width": 1280, "height": 720}, SPEECH)) == ["fix"]
    found = take_findings(5, PIC, {**SPEECH, "floor": -46.0}, [(14.42, 14.6), (125.0, 125.44)])
    assert levels(found) == ["note", "note"] and "14.4 s before the first word" in found[1][1]


def test_framing_that_drifted_between_takes_is_flagged():
    same = {1: {"cx": 840, "top": 360, "w": 630}, 2: {"cx": 838, "top": 366, "w": 628}}
    assert "fix" not in levels(face_findings(same))
    drift = {1: {"cx": 950, "top": 173, "w": 617}, 2: {"cx": 784, "top": 291, "w": 667}, 3: {"cx": 942, "top": 295, "w": 714}}
    assert levels(face_findings(drift))[-1] == "fix"
    assert face_findings({1: same[1]}) == []


def take(tmp_path, name, audio):
    """A 3 s 1080p30 take with the given lavfi audio (None: no audio track), AAC like OBS records it."""
    out = tmp_path / name
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=gray:s=1920x1080:r=30:d=3"]
    if audio:
        cmd += ["-f", "lavfi", "-i", audio, "-c:a", "aac", "-b:a", "192k", "-shortest"]
    subprocess.run(cmd + ["-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(out)], check=True)
    return out


VOICE = "0.4*sin(2*PI*220*t)*(0.6+0.4*sin(2*PI*3*t))"


@needs_ffmpeg
def test_real_files_clipped_after_aac_silent_or_without_sound_are_caught(tmp_path):
    clean = take(tmp_path, "clean.mp4", f"aevalsrc='{VOICE}':s=48000:d=3")
    assert "fix" not in levels(check_take(1, clean))      # a steady tone has no quiet stretch: a noise note only
    clipped = take(tmp_path, "clipped.mp4", f"aevalsrc='clip(7.5*{VOICE},-1,1)':s=48000:d=3")
    assert ["clips" in text for level, text in check_take(1, clipped) if level == "fix"] == [True]
    silent = take(tmp_path, "silent.mp4", "anullsrc=r=48000:cl=stereo:d=3")
    assert ["no audible sound" in text for _, text in check_take(1, silent)] == [True]
    mute = take(tmp_path, "mute.mp4", None)
    assert ["no audio track" in text for _, text in check_take(1, mute)] == [True]
