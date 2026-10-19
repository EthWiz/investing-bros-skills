"""Contract checks for the resumable shell assembler."""
from pathlib import Path


SCRIPT = (Path(__file__).parent / "assemble_episode.sh").read_text(encoding="utf-8")


def test_assembler_uses_native_fps_by_default():
    assert "stream=avg_frame_rate" in SCRIPT
    assert "--fps) fps=" in SCRIPT
    assert "fps=24" not in SCRIPT
    assert "f / 24" not in SCRIPT


def test_assembler_has_explicit_force_mode():
    assert "--force) force=1" in SCRIPT
    assert "pass --force to overwrite it" in SCRIPT
    assert '(( replace_existing )) && rm -rf "$work"' in SCRIPT
    assert '-nostdin -y -i "$work/video.mp4"' in SCRIPT


def test_assembler_uses_pcm_sidecars_and_checks_samples():
    assert "--before-audio" in SCRIPT
    assert "pcm_samples()" in SCRIPT
    assert "check_pcm_frames" in SCRIPT
    assert "PCM concat has" in SCRIPT
    assert "aresample=48000:async=1" in SCRIPT
