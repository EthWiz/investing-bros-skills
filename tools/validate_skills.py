#!/usr/bin/env python3
"""Check every skills/<name>/SKILL.md against the Agent Skills spec and repo rules.

Usage: python3 tools/validate_skills.py [skills_dir]
Exits non-zero on any error; warnings are printed and don't fail (yet).

Errors: frontmatter, name, description length, the required sections in order (When to use ->
Inputs -> Steps -> Done when -> Hand back -> Never), broken links (with #anchors), links that
leave the skill, hard-coded secrets, differing copies of a shared script, and retired phrases
(tools/retired_phrases.txt: wording a fix replaced, so an old copy can't come back).
Warnings: a rule copied into two skills' SKILL.md (a >= 10-word sentence, word Jaccard >= 0.6;
tools/copied_rules_allow.txt lists accepted boilerplate), a show fact (channel ID, Telegram chat
ID, Drive file ID, account email from investing-bros-show) repeated outside investing-bros-show
and scripts, and a trigger phrase (tools/triggers.txt) in another skill's description.
"""
import re
import sys
from itertools import combinations
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
NO_DONE_WHEN = {"investing-bros-show"}  # shared conventions, not a step
SECTIONS = ["When to use", "Inputs", "Steps", "Done when", "Hand back", "Never"]
SHOW = "investing-bros-show"
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
    if folder.name not in NO_DONE_WHEN:
        errs += [f"{folder.name}: {e}" for e in section_errors(text)]
    if len(text.splitlines()) > 500:
        errs.append(f"{folder.name}: SKILL.md over 500 lines; move detail to references/")
    for f in folder.rglob("*"):
        if "node_modules" in f.relative_to(folder).parts:   # installed npm packages, never committed
            continue
        if f.is_file() and f.suffix in {".md", ".py", ".sh", ".json"}:
            body = f.read_text(encoding="utf-8", errors="ignore")
            if SECRET_RE.search(body):
                errs.append(f"{f}: looks like a hard-coded secret")
            if f.suffix == ".md":
                errs += link_errors(f, body)
    return errs


def section_errors(text: str) -> list:
    """The required sections, each present, in order (other sections may sit between them)."""
    heads = re.findall(r"^## (.+?)\s*$", text, re.M)
    pos = []
    for s in SECTIONS:
        hit = next((i for i, h in enumerate(heads) if h == s or h.startswith(s + " ")), None)
        if hit is None:
            return [f"SKILL.md needs a '## {s}' section ({' -> '.join(SECTIONS)})"]
        pos.append(hit)
    if pos != sorted(pos):
        return [f"SKILL.md sections must be in the order {' -> '.join(SECTIONS)}"]
    return []


def slug(heading: str) -> str:
    """GitHub's heading anchor: lowercase, punctuation dropped, spaces to hyphens (Hebrew kept)."""
    h = re.sub(r"[`*_]", "", heading.strip().lower())
    return re.sub(r"[^\w\- ]", "", h).replace(" ", "-")


def anchors(md: Path) -> set:
    text = md.read_text(encoding="utf-8", errors="ignore")
    return {slug(h) for h in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.M)}


def link_errors(f: Path, body: str) -> list:
    errs = []
    for link in LINK_RE.findall(body):
        if link.startswith(("http://", "https://", "mailto:")):
            continue
        path, _, anchor = link.partition("#")
        if path and ".." in Path(path).parts:
            errs.append(f"{f}: link '{link}' leaves the skill folder; refer to other skills by name")
            continue
        target = f.parent / path if path else f
        if not target.exists():
            errs.append(f"{f}: broken link '{link}'")
        elif anchor and target.suffix == ".md" and anchor not in anchors(target):
            errs.append(f"{f}: broken anchor '#{anchor}' in '{link}'")
    return errs


# ---- drift checks -----------------------------------------------------------------------------------

def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def read_list(path: Path) -> list:
    if not path.is_file():
        return []
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.split(" #", 1)[0].strip() if not ln.lstrip().startswith("#") else ""
        if ln:
            out.append(ln)
    return out


def doc_files(folder: Path):
    for f in sorted(folder.rglob("*")):
        if "node_modules" in f.relative_to(folder).parts or "scripts" in f.relative_to(folder).parts:
            continue
        if f.is_file() and f.suffix in {".md", ".yaml", ".yml"}:
            yield f


def retired_errors(folders, phrases) -> list:
    errs = []
    for folder in folders:
        for f in doc_files(folder):
            text = norm(f.read_text(encoding="utf-8", errors="ignore"))
            for ph in phrases:
                if norm(ph) in text:
                    errs.append(f"{f}: retired wording \"{ph}\" (tools/retired_phrases.txt); use the current rule")
    return errs


def sentences(text: str) -> list:
    body = text.split("\n---", 1)[-1] if text.startswith("---") else text
    body = re.sub(r"```.*?```", " ", body, flags=re.S)
    parts = re.split(r"(?<=[.!?])\s+|\n\s*[-*\d.]+\s+|\n{2,}|\n#+ ", body)
    out = []
    for s in parts:
        words = re.findall(r"\w+", s.lower())
        if len(words) >= 10:
            out.append((" ".join(s.split()), frozenset(words)))
    return out


def copied_rule_warnings(folders, allow) -> list:
    allow = [norm(a) for a in allow]
    per = {}
    for folder in folders:
        md = folder / "SKILL.md"
        if md.is_file():
            per[folder.name] = [s for s in sentences(md.read_text(encoding="utf-8"))
                                if not any(a in norm(s[0]) for a in allow)]
    warns = []
    for (a, sa), (b, sb) in combinations(sorted(per.items()), 2):
        for ta, wa in sa:
            for tb, wb in sb:
                small, big = sorted((len(wa), len(wb)))
                if small < 0.6 * big:
                    continue
                if len(wa & wb) / len(wa | wb) >= 0.6:
                    warns.append(f"copied rule in {a} and {b}: \"{ta[:90]}...\" (keep it in the owning skill, "
                                 "point to it from the other)")
                    break
    return warns


FACT_RES = [re.compile(r"\bUC[A-Za-z0-9_-]{22}\b"), re.compile(r"(?<![\w-])-\d{9,}\b"),
            re.compile(r"\b1[A-Za-z0-9_-]{32}\b"), re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")]


def show_facts(root: Path) -> set:
    md = root / SHOW / "SKILL.md"
    text = md.read_text(encoding="utf-8") if md.is_file() else ""
    return {m for rx in FACT_RES for m in rx.findall(text)}


def fact_warnings(folders, facts) -> list:
    warns = []
    for folder in folders:
        if folder.name == SHOW:
            continue
        for f in doc_files(folder):
            text = f.read_text(encoding="utf-8", errors="ignore")
            hits = sorted(x for x in facts if x in text)
            if hits:
                warns.append(f"{f}: show fact(s) {', '.join(hits)} belong in {SHOW}; refer to it by name")
    return warns


def description_of(folder: Path) -> str:
    md = folder / "SKILL.md"
    if not md.is_file():
        return ""
    fm, _ = parse_frontmatter(md.read_text(encoding="utf-8"))
    return str((fm or {}).get("description", ""))


def trigger_warnings(folders, triggers) -> list:
    """Each `phrase -> skill` line: the phrase (as a word prefix) only in that skill's description."""
    desc = {f.name: description_of(f) for f in folders}
    warns = []
    for line in triggers:
        phrase, sep, owner = line.partition("->")
        phrase, owner = phrase.strip().strip('"'), owner.strip()
        if not sep or not phrase:
            continue
        rx = re.compile(r"(?<!\w)" + re.escape(phrase), re.I)
        others = sorted(n for n, d in desc.items() if n != owner and rx.search(d))
        if others:
            warns.append(f"trigger \"{phrase}\" belongs to {owner} but is also in the description of "
                         + ", ".join(others))
        if owner in desc and not rx.search(desc[owner]):
            warns.append(f"trigger \"{phrase}\" is missing from {owner}'s description")
    return warns


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
    errs += retired_errors(folders, read_list(TOOLS / "retired_phrases.txt"))
    warns = copied_rule_warnings(folders, read_list(TOOLS / "copied_rules_allow.txt"))
    warns += fact_warnings(folders, show_facts(root))
    warns += trigger_warnings(folders, read_list(TOOLS / "triggers.txt"))
    for w in warns:
        print(f"warning: {w}")
    for e in errs:
        print(f"error: {e}")
    print(f"{len(folders)} skills checked, {len(errs)} error(s), {len(warns)} warning(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
