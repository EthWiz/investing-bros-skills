import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from validate_skills import check_skill  # noqa: E402

SKILL = "---\nname: investing-bros-x\ndescription: Does x. Use when x.\n---\n# X\n\n## Done when\n- x\n"


def test_installed_node_modules_are_not_scanned(tmp_path):
    skill = tmp_path / "investing-bros-x"
    pkg = skill / "template" / "node_modules" / "webpack"
    pkg.mkdir(parents=True)
    (skill / "SKILL.md").write_text(SKILL)
    (pkg / "README.md").write_text('token = "abcdefghijkl" and [a](src/missing.ts)')
    assert check_skill(skill) == []
    (skill / "template" / "notes.md").write_text("[a](missing.md)")
    assert any("broken link" in e for e in check_skill(skill))
