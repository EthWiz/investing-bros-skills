#!/usr/bin/env python3
"""Check the brand reference index; reference images live in Drive, not in this skill.

    python3 check_reference_index.py                      # index + skill tree only
    python3 check_reference_index.py --dir WORK a.png b.png   # also check downloads

Fails when an index row lacks a real Drive file ID, a file name or ID repeats, a
reference image was committed back into the skill, the skill text still points at
the old `assets/references/` paths, or (with --dir) a requested reference is not in
the index or was not downloaded as a real PNG/JPEG.
"""
import argparse
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
INDEX = SKILL / "references" / "asset-index.md"
# Images that legitimately stay in the skill (production inputs other skills copy).
KEPT_IMAGES = {"assets/logo-solid.png", "assets/lesson-background-navy-studio.jpg"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
DRIVE_ID = re.compile(r"^[A-Za-z0-9_-]{25,}$")
MAGIC = {b"\x89PNG\r\n\x1a\n": "png", b"\xff\xd8\xff": "jpeg"}


def parse_index(text: str) -> list:
    """Rows of the `| File | Drive folder | Drive file ID | Role | Status |` table."""
    rows, in_table = [], False
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.lstrip().startswith("| File |"):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.lstrip().startswith("|"):
            break
        if set("".join(cells)) <= set("- :"):
            continue
        if len(cells) >= 3:
            rows.append({"file": cells[0], "folder": cells[1], "id": cells[2]})
    return rows


def check_index(rows: list) -> list:
    errs = []
    if not rows:
        return ["asset-index.md: no reference table found"]
    seen_files, seen_ids = set(), set()
    for r in rows:
        if not DRIVE_ID.match(r["id"]):
            errs.append(f"{r['file']}: Drive file ID missing or invalid ({r['id']!r})")
        if not r["folder"].startswith("references"):
            errs.append(f"{r['file']}: Drive folder should be under references/ ({r['folder']!r})")
        if r["file"] in seen_files:
            errs.append(f"{r['file']}: listed twice")
        if DRIVE_ID.match(r["id"]) and r["id"] in seen_ids:
            errs.append(f"{r['file']}: Drive ID {r['id']} used twice")
        seen_files.add(r["file"])
        seen_ids.add(r["id"])
    return errs


def check_tree(skill: Path) -> list:
    errs = []
    for f in sorted(skill.rglob("*")):
        rel = f.relative_to(skill).as_posix()
        if f.is_file() and f.suffix.lower() in IMAGE_EXT and rel not in KEPT_IMAGES:
            errs.append(f"{rel}: reference images belong in Drive (Brand Resources/references), not the repo")
        if f.is_file() and f.suffix in {".md", ".json", ".yaml"} and "assets/references/" in f.read_text(encoding="utf-8"):
            errs.append(f"{rel}: still points at assets/references/; use the file name from the asset index")
    return errs


def check_downloads(rows: list, folder: Path, names: list) -> list:
    errs, known = [], {r["file"] for r in rows}
    for name in names:
        if name not in known:
            errs.append(f"{name}: not in the asset index")
            continue
        p = folder / name
        if not p.is_file() or p.stat().st_size == 0:
            errs.append(f"{name}: not downloaded to {folder}")
            continue
        head = p.read_bytes()[:8]
        if not any(head.startswith(m) for m in MAGIC):
            errs.append(f"{name}: not a PNG/JPEG (download returned something else)")
    return errs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", type=Path, help="working folder the references were downloaded to")
    ap.add_argument("names", nargs="*", help="reference file names to check in --dir")
    a = ap.parse_args(argv)
    rows = parse_index(INDEX.read_text(encoding="utf-8"))
    errs = check_index(rows) + check_tree(SKILL)
    if a.dir:
        errs += check_downloads(rows, a.dir, a.names or [r["file"] for r in rows])
    for e in errs:
        print("FAIL", e)
    if not errs:
        print(f"OK {len(rows)} references indexed" + (f", {len(a.names) or len(rows)} downloaded" if a.dir else ""))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
