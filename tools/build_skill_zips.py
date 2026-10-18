#!/usr/bin/env python3
"""Build one ZIP per skill for the Claude app (Customize -> Skills).

Usage: python3 tools/build_skill_zips.py OUT_DIR [--version TEXT]

Each ZIP's root is the skill folder, as the Claude app expects. A VERSION file is
added inside every skill folder (plugin version, commit, date), so an agent can
tell whether its installed copy matches the latest release. OUT_DIR/NOTES.md lists
the skills and the version, for the release notes.
"""
import argparse
import json
import os
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"__pycache__", ".pytest_cache"}
SKIP_SUFFIXES = {".pyc"}


def default_version() -> str:
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, check=True,
                             capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        sha = "unknown"
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"{plugin['version']} ({sha}, {date})"


def build(skills_dir: Path, out: Path, version: str) -> list:
    out.mkdir(parents=True, exist_ok=True)
    built = []
    for skill in sorted(p for p in skills_dir.iterdir() if (p / "SKILL.md").is_file()):
        target = out / f"{skill.name}.zip"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
            for dirpath, dirnames, filenames in os.walk(skill):
                dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
                for name in sorted(filenames):
                    f = Path(dirpath) / name
                    if f.suffix in SKIP_SUFFIXES:
                        continue
                    z.write(f, f.relative_to(skills_dir).as_posix())
            z.writestr(f"{skill.name}/VERSION", version + "\n")
        built.append(skill.name)
    lines = [f"Skills version: {version}", "",
             "Upload each ZIP under Customize -> Skills (start with investing-bros-show).",
             "Each installed skill has a VERSION file; if it differs from the line above, re-upload.", ""]
    lines += [f"- {name}.zip" for name in built]
    (out / "NOTES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return built


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", type=Path)
    ap.add_argument("--version")
    ap.add_argument("--skills", type=Path, default=ROOT / "skills")
    a = ap.parse_args(argv)
    built = build(a.skills, a.out, a.version or default_version())
    print(f"{len(built)} skill ZIP(s) in {a.out}")
    return 0 if built else 1


if __name__ == "__main__":
    sys.exit(main())
