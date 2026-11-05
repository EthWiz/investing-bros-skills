import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import validate_skills as vs  # noqa: E402
from validate_skills import check_skill  # noqa: E402

BODY = "## When to use\nx\n## Inputs\nx\n## Steps\nx\n## Done when\n- x\n## Hand back\nx\n## Never\n- x\n"
SKILL = "---\nname: investing-bros-x\ndescription: Does x. Use when x.\n---\n# X\n\n" + BODY


def make(tmp_path, name="investing-bros-x", body=BODY, desc="Does x. Use when x."):
    skill = tmp_path / name
    skill.mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {desc}\n---\n# X\n\n{body}", encoding="utf-8")
    return skill


def test_installed_node_modules_are_not_scanned(tmp_path):
    skill = tmp_path / "investing-bros-x"
    pkg = skill / "template" / "node_modules" / "webpack"
    pkg.mkdir(parents=True)
    (skill / "SKILL.md").write_text(SKILL)
    (pkg / "README.md").write_text('token = "abcdefghijkl" and [a](src/missing.ts)')
    assert check_skill(skill) == []
    (skill / "template" / "notes.md").write_text("[a](missing.md)")
    assert any("broken link" in e for e in check_skill(skill))


def test_links_with_anchors_are_checked(tmp_path):
    skill = make(tmp_path)
    (skill / "references").mkdir()
    (skill / "references" / "studio.md").write_text("# Studio\n## Segment videos: cards, end screen\n", encoding="utf-8")
    (skill / "references" / "a.md").write_text(
        "[ok](studio.md#segment-videos-cards-end-screen) [self](#here)\n## Here\n", encoding="utf-8")
    assert check_skill(skill) == []
    (skill / "references" / "b.md").write_text("[bad](studio.md#segment-videos)", encoding="utf-8")
    (skill / "references" / "c.md").write_text("[up](../other/x.md#a)", encoding="utf-8")
    errs = check_skill(skill)
    assert any("broken anchor '#segment-videos'" in e for e in errs)
    assert any("leaves the skill folder" in e for e in errs)


def test_sections_required_in_order(tmp_path):
    assert check_skill(make(tmp_path, body=BODY.replace("## Never\n- x\n", ""))) and \
        "needs a '## Never'" in check_skill(make(tmp_path, body=BODY.replace("## Never\n- x\n", "")))[0]
    swapped = "## Inputs\nx\n## When to use\nx\n## Steps (all)\nx\n## Done when\n- x\n## Hand back\nx\n## Never\n- x\n"
    assert any("in the order" in e for e in check_skill(make(tmp_path, body=swapped)))
    extra = BODY.replace("## Steps\n", "## Types\nx\n## Steps (same for every type)\n")
    assert check_skill(make(tmp_path, body=extra)) == []


def test_retired_phrases_fail(tmp_path):
    skill = make(tmp_path, body=BODY + "Shorts: Do not upload the three\nShorts until the full episode is live.\n")
    errs = vs.retired_errors([skill], ["Do not upload the three Shorts until the full episode is live"])
    assert len(errs) == 1 and "retired wording" in errs[0]
    (skill / "scripts").mkdir()
    (skill / "scripts" / "notes.md").write_text("Unlisted URL", encoding="utf-8")
    assert len(vs.retired_errors([skill], ["Unlisted URL"])) == 0      # scripts are not docs


def test_copied_rules_warn_with_an_allowlist(tmp_path):
    rule = "Set the Related video to the full episode in Studio, then reopen the edit page and confirm it."
    a = make(tmp_path, "investing-bros-a", body=BODY + rule + "\n")
    b = make(tmp_path, "investing-bros-b", body=BODY + rule.replace("confirm it", "check it") + "\n")
    warns = vs.copied_rule_warnings([a, b], [])
    assert len(warns) == 1 and "investing-bros-a and investing-bros-b" in warns[0]
    assert vs.copied_rule_warnings([a, b], ["Set the Related video"]) == []


def test_show_facts_outside_the_show_warn(tmp_path):
    show = make(tmp_path, "investing-bros-show", body="Channel `UCWIlggXQNDFiyJghl6VB6Xw`, chat `-5592316645`, "
                "login `ami.ruskin@gmail.com`, file 1knRZzjQc7I5OT65_ZH46oklv4wwbij1U\n")
    other = make(tmp_path, "investing-bros-a", body=BODY + "Open UCWIlggXQNDFiyJghl6VB6Xw as ami.ruskin@gmail.com\n")
    (other / "scripts").mkdir()
    (other / "scripts" / "x.md").write_text("-5592316645", encoding="utf-8")
    facts = vs.show_facts(tmp_path)
    assert {"UCWIlggXQNDFiyJghl6VB6Xw", "-5592316645", "ami.ruskin@gmail.com"} <= facts
    warns = vs.fact_warnings([show, other], facts)
    assert len(warns) == 1 and "UCWIlggXQNDFiyJghl6VB6Xw" in warns[0] and "ami.ruskin@gmail.com" in warns[0]


def test_trigger_phrases_belong_to_one_skill(tmp_path):
    pub = make(tmp_path, "investing-bros-publish", desc='Publish it. Use when he says "publish episode N".')
    up = make(tmp_path, "investing-bros-episode-upload", desc='Upload it. Use for "upload episode N" or "publish".')
    seg = make(tmp_path, "investing-bros-segment-video", desc="Segments. Use when publishing episode N.")
    warns = vs.trigger_warnings([pub, up, seg], ["publish -> investing-bros-publish",
                                                 "upload episode N -> investing-bros-episode-upload",
                                                 "תחקיר -> investing-bros-publish"])
    assert any("investing-bros-episode-upload, investing-bros-segment-video" in w for w in warns)
    assert any("missing from investing-bros-publish" in w for w in warns)
    assert not any("upload episode N" in w for w in warns)


def test_the_repo_has_no_errors():
    folders = sorted(p for p in (Path(__file__).parent.parent / "skills").iterdir() if p.is_dir())
    errs = [e for f in folders for e in check_skill(f)] + vs.check_shared_scripts(folders)
    errs += vs.retired_errors(folders, vs.read_list(vs.TOOLS / "retired_phrases.txt"))
    assert errs == []
