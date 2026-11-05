"""rule_sites.py: every place a topic appears, grouped by skill, with the owner."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import rule_sites as rs  # noqa: E402


def repo(tmp_path):
    for rel, text in {
        "skills/investing-bros-shorts/SKILL.md": "Set the Related video to the full episode.\nCaptions.\n",
        "skills/investing-bros-publish/SKILL.md": "Related video is a hard rule.\nNo related links here.\n",
        "skills/investing-bros-publish/references/studio-checks.md": "Reopen: Related video shows it.\n",
        "skills/investing-bros-publish/scripts/notes.md": "Related video (a script folder: skipped)\n",
        "skills/investing-bros-show/SKILL.md": "Telegram chat ID -1. Publishing waits for the owner.\n",
        "tools/retired_phrases.txt": "old related video wording\n",
        "AGENTS.md": "x\n",
    }.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return tmp_path


def test_sites_need_all_words_and_skip_scripts(tmp_path):
    root = repo(tmp_path)
    hits = rs.sites(root, "related video")
    files = {h["file"] for h in hits}
    assert files == {"skills/investing-bros-shorts/SKILL.md", "skills/investing-bros-publish/SKILL.md",
                     "skills/investing-bros-publish/references/studio-checks.md", "tools/retired_phrases.txt"}
    assert len(rs.sites(root, "related video", any_word=True)) == 5      # "No related links here." too


def test_word_prefix_and_owner(tmp_path, capsys):
    root = repo(tmp_path)
    assert [h["skill"] for h in rs.sites(root, "publish")] == ["investing-bros-show"]   # "Publishing"
    assert rs.owner("telegram chat id", []) == "investing-bros-show"
    assert rs.owner("related video", rs.sites(root, "related video")) in ("investing-bros-publish", "investing-bros-shorts")
    assert rs.main(["related video", "--root", str(root)]) == 0
    out = capsys.readouterr().out
    assert "<- owner" in out and "retired_phrases.txt" in out
    assert rs.main(["nothing here at all", "--root", str(root)]) == 1


def test_the_real_repo(capsys):
    assert rs.main(["Related video", "--root", str(Path(__file__).resolve().parents[3])]) == 0
