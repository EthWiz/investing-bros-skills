#!/usr/bin/env python3
"""Check every skills/<name>/SKILL.md against the Agent Skills spec and repo rules.

Usage: python3 tools/validate_skills.py [skills_dir]
Exits non-zero on any error.
"""
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\]\(([^)#]+)\)")
NO_DONE_WHEN = {"investing-bros-show"}  # shared conventions, not a step
SECRET_RE = re.compile(r"(?i)(password|token|api[_-]?key|secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{8,}")


def parse_frontmatter(text: str):
    if not text.startswith("---\n"):
        return None, "missing YAML frontmatter"
    end = text.find("\n---", 4)
    if end < 0:
        return None, "unterminated frontmatter"
    try:
        import yaml
        data = yaml.safe_load(text[4:end])
    except ImportError:  # minimal fallback: name + folded description
        data, key = {}, None
        for line in text[4:end].splitlines():
            m = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
            if m:
                key, val = m.group(1), m.group(2)
                data[key] = "" if val in (">-", ">", "|", "|-") else val.strip()
            elif key and line.startswith(" "):
                data[key] = (data[key] + " " + line.strip()).strip()
    return (data if isinstance(data, dict) else None), None


def check_skill(folder: Path) -> list:
    errs = []
    md = folder / "SKILL.md"
    if not md.is_file():
        return [f"{folder.name}: no SKILL.md"]
    text = md.read_text(encoding="utf-8")
    fm, err = parse_frontmatter(text)
    if err or fm is None:
        return [f"{folder.name}: {err or 'frontmatter is not a mapping'}"]
    name, desc = str(fm.get("name", "")), str(fm.get("description", ""))
    if not NAME_RE.match(name) or len(name) > 64:
        errs.append(f"{folder.name}: name '{name}' must be lowercase letters/digits/hyphens, max 64")
    if name != folder.name:
        errs.append(f"{folder.name}: name '{name}' must match the folder name")
    if not desc or len(desc) > 1024:
        errs.append(f"{folder.name}: description must be 1-1024 characters (is {len(desc)})")
    if folder.name not in NO_DONE_WHEN and not re.search(r"^## Done when\s*$", text, re.M):
        errs.append(f"{folder.name}: SKILL.md needs a '## Done when' section listing the files it leaves")
    if len(text.splitlines()) > 500:
        errs.append(f"{folder.name}: SKILL.md over 500 lines; move detail to references/")
    for f in folder.rglob("*"):
        if f.is_file() and f.suffix in {".md", ".py", ".sh", ".json"}:
            body = f.read_text(encoding="utf-8", errors="ignore")
            if SECRET_RE.search(body):
                errs.append(f"{f}: looks like a hard-coded secret")
            if f.suffix == ".md":
                for link in LINK_RE.findall(body):
                    if link.startswith(("http://", "https://", "mailto:")):
                        continue
                    if ".." in Path(link).parts:
                        errs.append(f"{f}: link '{link}' leaves the skill folder; refer to other skills by name")
                    elif not (f.parent / link).exists():
                        errs.append(f"{f}: broken link '{link}'")
    return errs


def check_shared_scripts(folders) -> list:
    """Scripts copied into several skills (same file name) must stay identical."""
    by_name = {}
    for folder in folders:
        for f in sorted((folder / "scripts").glob("*")):
            if f.is_file() and not f.name.startswith("test_"):
                by_name.setdefault(f.name, []).append(f)
    errs = []
    for name, copies in by_name.items():
        first = copies[0].read_bytes()
        for other in copies[1:]:
            if other.read_bytes() != first:
                errs.append(f"{other} differs from {copies[0]}; shared scripts must be identical copies")
    return errs


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "skills")
    folders = sorted(p for p in root.iterdir() if p.is_dir())
    errs = [e for f in folders for e in check_skill(f)]
    errs += check_shared_scripts(folders)
    for e in errs:
        print(f"error: {e}")
    print(f"{len(folders)} skills checked, {len(errs)} error(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
