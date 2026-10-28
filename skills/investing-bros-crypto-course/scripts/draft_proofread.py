#!/usr/bin/env python3
"""Draft each take's proofread text from the script and Whisper, and list every place they disagree.

Usage:
    python3 draft_proofread.py lesson-N/lesson-N-video.json --words-dir WORDS [--write] [--force]

The proofread text (the config's `proofread`) is what Amitai said inside the take's from/to, and captions show it. Whisper hears most of it
right but garbles Hebrew names and words ("סטטושי", "נכים להשקעות"); the script has the right spelling but not his
ad-libs, skipped words or restarts. This lines the two up word by word and drafts from the script:
- where they agree, or Whisper heard something else of about the same length: the script's words (a garble, most
  likely; listed, so it can be checked by ear);
- two or more script words Whisper didn't hear at all: dropped (he skipped them; listed);
- three or more words Whisper heard that the script doesn't have: added (an ad-lib; listed). Shorter extras, often
  a restart ("גם עם פתרון בשבילו, פתרו בשבילו"), are only listed.
Every listed spot goes to the config's `notes` once checked. --write fills `proofread` for takes that have none
(--force: all takes). Nothing here replaces listening to the take.
"""
import argparse
import difflib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_lesson_base import words_name  # noqa: E402

PUNCT = re.compile(r"[\"'״׳`.,:;!?()\[\]*\\…–—]")
ADLIB, SKIP = 3, 2


def norm(word: str) -> str:
    return PUNCT.sub("", word).replace("־", "-").strip("-").strip()


def script_words(text: str):
    """The script's words as written (markdown bold and escapes removed)."""
    return [w for w in text.replace("**", "").replace("\\&", "&").split() if norm(w)]


def heard(path: Path, start=0.0, end=float("inf")):
    """Whisper's words that start inside the take's trim (start..end, seconds of the take), so a sound check
    before it or chatter after it never reaches the captions; a piece Whisper split off at the geresh
    ("בלוקצ", "'יין") is joined back."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        raw = [(w["word"].strip(), w["start"]) for seg in data["segments"] for w in seg.get("words", [])]
    else:
        raw = [(w["w"].strip(), w["s"]) for w in data]
    out = []
    for w, t in raw:
        if not start - 0.05 <= t < end:
            continue
        if out and w[:1] in ("'", "׳"):
            out[-1] += w
        else:
            out.append(w)
    return out


def draft(script: list, whisper: list):
    """(draft words, [(kind, script span, whisper span)]) for one take."""
    sm = difflib.SequenceMatcher(a=[norm(w) for w in script], b=[norm(w) for w in whisper], autojunk=False)
    out, spots = [], []
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        said, wrote = whisper[b0:b1], script[a0:a1]
        if op == "equal":
            out += wrote
        elif op == "delete":
            if len(wrote) >= SKIP:
                spots.append(("skipped", wrote, []))
            else:
                out += wrote
                spots.append(("not heard", wrote, []))
        elif op == "insert":
            if len(said) >= ADLIB:
                out += said
                spots.append(("ad-lib", [], said))
            else:
                spots.append(("extra", [], said))
        else:
            out += wrote
            kind = "ad-lib? (not added)" if len(said) - len(wrote) >= ADLIB else "heard differently"
            spots.append((kind, wrote, said))
    return out, spots


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--words-dir", required=True)
    ap.add_argument("--write", action="store_true", help="fill `proofread` for takes that have none")
    ap.add_argument("--force", action="store_true", help="with --write: replace every take's proofread")
    a = ap.parse_args(argv)
    cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))
    beats = (cfg.get("script") or {}).get("beats") or {}
    proof = cfg.setdefault("proofread", {})
    for t in cfg["takes"]:
        b = str(t["beat"])
        if b not in beats:
            raise SystemExit(f"error: beat {b} has no script text; run parse_script.py first")
        said = heard(Path(a.words_dir) / words_name(t["beat"]), t["from"], t["to"])
        words, spots = draft(script_words(beats[b]["text"]), said)
        print(f"beat {b}: {len(spots)} to check")
        for kind, wrote, said in spots:
            print(f"  {kind}: script '{' '.join(wrote)}' / Whisper '{' '.join(said)}'")
        if a.write and (a.force or not proof.get(b)):
            proof[b] = " ".join(words)
    if a.write:
        Path(a.config).write_text(json.dumps(cfg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{a.config}: proofread drafted; check the listed spots by ear before captions go out")
    return 0


if __name__ == "__main__":
    sys.exit(main())
