#!/usr/bin/env python3
"""Every place a topic appears across the skills, so a rule change updates all of them (or replaces the
copies with a pointer to the one owner).

  rule_sites.py "related video" [--any] [--root REPO] [--json]

Searches every SKILL.md, references/*, agents/*.yaml, AGENTS.md, README.md and tools/*.txt in the repo
for lines holding all the topic words (`--any`: one of them), case-insensitive, Hebrew included. A word
matches as a word prefix ("publish" finds "publishing"). Prints the hits grouped by skill, SKILL.md
first, and the skill that should own the rule: facts and contact rules -> investing-bros-show, design
-> investing-bros-brand, otherwise the skill whose SKILL.md has the most hits.
Exit 0 with hits, 1 with none.
"""
import argparse
import json
import re
import sys
from pathlib import Path

DOC_SUFFIXES = {".md", ".yaml", ".yml", ".txt"}
FACT_WORDS = ("account", "channel id", "chat id", "spelling", "drive id", "file id", "email", "destination",
              "whatsapp", "telegram", "owner")
DESIGN_WORDS = ("cover", "thumbnail", "palette", "font", "heebo", "logo", "typography", "artwork")


def find_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "skills").is_dir() and (p / "tools").is_dir():
            return p
    here = Path(__file__).resolve()
    for p in here.parents:
        if (p / "skills").is_dir() and (p / "tools").is_dir():
            return p
    raise SystemExit("no repo with skills/ and tools/ found; run it in a clone of investing-bros-skills or pass --root")


def doc_files(root: Path):
    for f in sorted((root / "skills").rglob("*")):
        rel = f.relative_to(root / "skills").parts
        if f.is_file() and f.suffix in DOC_SUFFIXES and "node_modules" not in rel and "scripts" not in rel[1:2]:
            yield f
    for name in ("AGENTS.md", "README.md"):
        if (root / name).is_file():
            yield root / name
    yield from sorted((root / "tools").glob("*.txt"))


def matcher(words, any_word=False):
    rxs = [re.compile(r"(?<!\w)" + re.escape(w), re.I) for w in words]
    return (lambda line: any(r.search(line) for r in rxs)) if any_word else (lambda line: all(r.search(line) for r in rxs))


def sites(root: Path, topic: str, any_word=False) -> list:
    words = [w for w in topic.split() if w]
    if not words:
        raise ValueError("give the topic words")
    match = matcher(words, any_word)
    hits = []
    for f in doc_files(root):
        for n, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if match(line):
                rel = f.relative_to(root)
                skill = rel.parts[1] if rel.parts[0] == "skills" else "(repo)"
                hits.append({"skill": skill, "file": str(rel), "line": n, "text": line.strip()[:200]})
    return hits


def owner(topic: str, hits: list) -> str:
    t = topic.lower()
    if any(w in t for w in FACT_WORDS):
        return "investing-bros-show"
    if any(w in t for w in DESIGN_WORDS):
        return "investing-bros-brand"
    counts = {}
    for h in hits:
        if h["file"].endswith("SKILL.md"):
            counts[h["skill"]] = counts.get(h["skill"], 0) + 1
    return max(counts, key=counts.get) if counts else "(none yet: the skill that owns the step)"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("topic")
    ap.add_argument("--any", action="store_true", help="a line with any one of the words")
    ap.add_argument("--root", type=Path)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    root = a.root or find_root(Path.cwd())
    hits = sites(root, a.topic, a.any)
    own = owner(a.topic, hits)
    if a.json:
        print(json.dumps({"owner": own, "sites": hits}, ensure_ascii=False, indent=1))
        return 0 if hits else 1
    if not hits:
        print(f"no sites for {a.topic!r}")
        return 1
    order = sorted({h["skill"] for h in hits}, key=lambda s: (s != own, s))
    for s in order:
        mine = sorted((h for h in hits if h["skill"] == s), key=lambda h: (not h["file"].endswith("SKILL.md"), h["file"], h["line"]))
        print(f"{s}{'  <- owner' if s == own else ''}")
        for h in mine:
            print(f"  {h['file']}:{h['line']}  {h['text']}")
    print(f"\n{len(hits)} site(s) in {len(order)} place(s). Update every one, or keep the rule in {own} and point to it "
          "by skill name from the others; add the replaced wording to tools/retired_phrases.txt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
