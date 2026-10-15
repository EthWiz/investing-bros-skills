"""Episode video recipes: no machine paths, and the cold-open mix matches investing-bros-teaser."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def test_cold_open_follows_teaser_music_bed():
    text = (ROOT / "cold_open.sh").read_text(encoding="utf-8")
    assert "sidechaincompress=threshold=0.03:ratio=4:attack=15:release=400" in text
    assert "afade=t=in:d=0.8" in text
    assert "afade=t=in:d=1,areverse" in text
    assert "afftdn=nr=10:nf=-30" in text
    assert "highpass=f=8000" in text
    assert "256000" in text
    assert 'loudnorm2 "$T/mix.wav" "$T/ln.wav" -14 -1' in text
    assert "ARNNDN_MODEL" in text
    assert "/workspace/" not in text
    assert "/Users/" not in text


def test_intro_is_an_argument():
    lib = (ROOT / "lib.sh").read_text(encoding="utf-8")
    assert "INTRO=${INTRO:-}" in lib
    assert "/workspace/" not in lib
    intro = (ROOT / "conform_intro.sh").read_text(encoding="utf-8")
    assert "INTRO:?" in intro or "${INTRO:?set INTRO=" in intro
    for name in ("cut_episode.sh", "join.sh", "export.sh", "conform_intro.sh"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "/workspace/" not in text, name
        assert "/Users/" not in text, name


def test_recipe_shell_parses():
    for name in ("cold_open.sh", "cut_episode.sh", "join.sh", "conform_intro.sh", "export.sh", "lib.sh"):
        subprocess.run(["bash", "-n", str(ROOT / name)], check=True)
