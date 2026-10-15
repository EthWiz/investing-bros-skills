"""The batch-playbook scripts stay portable and on the house accent. No ffmpeg, font or model needed."""
import py_compile
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POST = ROOT.parents[1] / "investing-bros-post-production" / "scripts"
GOLD = "(245, 183, 31"  # #F5B71F


def _sources():
    files = [p for p in ROOT.glob("*.py") if p.is_file() and not p.name.startswith("test_")]
    files += [p for p in ROOT.glob("*.sh") if p.is_file()]
    files += [p for p in (ROOT / "reel").glob("*") if p.is_file()]
    return files


def test_gold_accent_is_house_gold():
    for name in ("make_title.py", "reel/captions.py", "reel/mg.py"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "255, 184, 0" not in text
        assert "#FFB800" not in text
        assert GOLD in text


def test_no_machine_absolute_paths():
    for p in _sources():
        text = p.read_text(encoding="utf-8")
        assert "/workspace/" not in text, p.name
        assert "/Users/" not in text, p.name


def test_shorts_loudnorm_is_social_target():
    text = (ROOT / "reel" / "run.sh").read_text(encoding="utf-8")
    assert text.count("I=-14:TP=-1.5:LRA=11") == 2
    assert "TP=-1:" not in text


def test_shared_helpers_match_post_production():
    for name in ("lib.sh", "export.sh"):
        assert (ROOT / name).read_bytes() == (POST / name).read_bytes(), name


def test_guide_scripts_compile_and_parse():
    for p in _sources():
        if p.suffix == ".py":
            py_compile.compile(str(p), doraise=True)
        elif p.suffix == ".sh":
            subprocess.run(["bash", "-n", str(p)], check=True)
