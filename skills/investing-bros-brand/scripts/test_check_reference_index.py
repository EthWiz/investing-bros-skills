import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "check_reference_index", Path(__file__).with_name("check_reference_index.py"))
cri = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cri)

GOOD_ID = "1Cs12YBSBHtPPmw6EFp4pHgLZu10cYBVW"
TABLE = """intro
| File | Drive folder | Drive file ID | Role | Status |
| --- | --- | --- | --- | --- |
{rows}

after
"""


def rows(*lines):
    return cri.parse_index(TABLE.format(rows="\n".join(lines)))


def test_real_skill_passes():
    assert cri.main([]) == 0


def test_pending_id_fails():
    r = rows("| a.png | references/covers | DRIVE_ID_PENDING | x | y |")
    assert any("Drive file ID" in e for e in cri.check_index(r))


def test_duplicates_fail():
    r = rows(f"| a.png | references/covers | {GOOD_ID} | x | y |",
             f"| a.png | references/hosts | {GOOD_ID} | x | y |")
    errs = cri.check_index(r)
    assert any("listed twice" in e for e in errs)
    assert any("used twice" in e for e in errs)


def test_folder_outside_references_fails():
    r = rows(f"| a.png | Brand Resources | {GOOD_ID} | x | y |")
    assert any("under references/" in e for e in cri.check_index(r))


def test_committed_reference_image_fails(tmp_path):
    (tmp_path / "assets" / "references").mkdir(parents=True)
    (tmp_path / "assets" / "references" / "x.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (tmp_path / "assets" / "logo-solid.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (tmp_path / "SKILL.md").write_text("see assets/references/x.png", encoding="utf-8")
    errs = cri.check_tree(tmp_path)
    assert len(errs) == 2  # the stray image and the stale path; logo-solid.png is allowed


def test_downloads(tmp_path):
    r = rows(f"| a.png | references/covers | {GOOD_ID} | x | y |",
             "| b.jpg | references/teasers | 1uPE8XZBGa-KCWcOwuQ5usw8EIBrGE6m7 | x | y |")
    (tmp_path / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 10)
    (tmp_path / "b.jpg").write_text("<html>quota exceeded</html>")
    errs = cri.check_downloads(r, tmp_path, ["a.png", "b.jpg", "c.png"])
    assert errs == ["b.jpg: not a PNG/JPEG (download returned something else)",
                    "c.png: not in the asset index"]
    assert cri.check_downloads(r, tmp_path, ["a.png"]) == []
