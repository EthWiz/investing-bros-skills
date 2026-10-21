import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_skill_zips import build  # noqa: E402


def test_one_zip_per_skill_with_version(tmp_path):
    skills = tmp_path / "skills"
    (skills / "investing-bros-show" / "references").mkdir(parents=True)
    (skills / "investing-bros-show" / "SKILL.md").write_text("---\nname: investing-bros-show\n---\n")
    (skills / "investing-bros-show" / "references" / "env.md").write_text("x")
    (skills / "investing-bros-video" / "scripts" / "__pycache__").mkdir(parents=True)
    (skills / "investing-bros-video" / "SKILL.md").write_text("---\nname: investing-bros-video\n---\n")
    (skills / "investing-bros-video" / "scripts" / "a.py").write_text("print(1)")
    (skills / "investing-bros-video" / "scripts" / "__pycache__" / "a.cpython-312.pyc").write_bytes(b"x")
    (skills / "not-a-skill").mkdir()

    out = tmp_path / "dist"
    assert build(skills, out, "3.0.0 (abc123, 2026-10-18)") == ["investing-bros-show", "investing-bros-video"]
    with zipfile.ZipFile(out / "investing-bros-video.zip") as z:
        names = set(z.namelist())
        assert names == {"investing-bros-video/SKILL.md", "investing-bros-video/scripts/a.py",
                         "investing-bros-video/VERSION"}
        assert z.read("investing-bros-video/VERSION").decode().strip() == "3.0.0 (abc123, 2026-10-18)"
    assert "3.0.0 (abc123" in (out / "NOTES.md").read_text()
