#!/usr/bin/env python3
"""Read a lesson's script (the Google Doc תסריט-שיעור-N) into its video config, beat by beat.

Usage:
    python3 parse_script.py lesson-N/script/תסריט-שיעור-N-<when>.md --doc DOC_ID \\
        --revision REV [--revision-kind revision_id|modified_time] [--update lesson-N/lesson-N-video.json]

The script file is the snapshot: the Doc's text as the Drive connector's read_file_content returns it,
saved in the lesson's script/ folder and never edited afterwards, so an old export can always be
traced to the words it followed. --revision is the Docs API revisionId (read_doc's `revisionId`,
--revision-kind revision_id) or, when only Drive metadata is at hand, the file's modifiedTime
(get_file_metadata, --revision-kind modified_time, the default). Prints {doc, revision, revision_kind,
snapshot, snapshot_sha256, beats: {N: {title, seconds, on_screen, text}}}; with --update it writes that
into the config's `script` (the snapshot path relative to the config), keeps its `departures` (beat ->
why the video deliberately differs from that beat's על המסך line), and lists the beats whose title,
on-screen line or text changed since the config's previous script: review those, not the whole lesson.
The Doc decides what is on screen; the recording decides captions and timing.
"""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

HEADING = re.compile(r"^(?:#{1,3}\s*)?\**\s*קטע\s+(\d+)\s*:\s*(.+?)\s*(?:\(כ-?\s*(\d+)\s*שניות\))?\s*\**\s*$")
ON_SCREEN = re.compile(r"^\*?\s*על המסך\s*:\s*(.+?)\s*\*?$")
LIST_ITEM = re.compile(r"^\s*(?:\d+\.|[-*])\s+")
KINDS = ("revision_id", "modified_time")


def parse(text: str) -> dict:
    beats, cur = {}, None
    for raw in text.splitlines():
        line = raw.strip()
        m = HEADING.match(line)
        if m:
            cur = {"title": m.group(2).strip("* "), "seconds": int(m.group(3)) if m.group(3) else None,
                   "on_screen": "", "text": []}
            beats[m.group(1)] = cur
            continue
        if line.startswith("#") or line.strip("* \ufeff") in ("מקורות", "הערות"):
            # Native Docs text exports omit Markdown heading markers.
            cur = None
            continue
        if cur is None or not line:
            continue
        m = ON_SCREEN.match(line)
        if m and not cur["on_screen"]:
            cur["on_screen"] = m.group(1).strip("* ")
            continue
        cur["text"].append(LIST_ITEM.sub("", line))
    for b in beats.values():
        b["text"] = " ".join(b["text"])
    return beats


def changed_beats(old: dict, new: dict) -> list:
    """Beats added, removed, or with a different title, on-screen line or text (not a new length estimate)."""
    keys = ("title", "on_screen", "text")
    out = [n for n in set(old) | set(new)
           if n not in old or n not in new or any(old[n].get(k) != new[n].get(k) for k in keys)]
    return sorted(out, key=int)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", help="the saved snapshot of the Doc's text")
    ap.add_argument("--doc", required=True)
    ap.add_argument("--revision", required=True)
    ap.add_argument("--revision-kind", choices=KINDS, default="modified_time")
    ap.add_argument("--update", help="the lesson's video config to write the script into")
    a = ap.parse_args(argv)
    path = Path(a.script)
    raw = path.read_bytes()
    beats = parse(raw.decode("utf-8"))
    if not beats:
        raise SystemExit("error: no 'קטע N: …' headings found; is this the script Doc's text?")
    missing = [n for n, b in beats.items() if not b["on_screen"]]
    if missing:
        print(f"warning: beats {missing} have no 'על המסך' line", file=sys.stderr)
    script = {"doc": a.doc, "revision": a.revision, "revision_kind": a.revision_kind, "snapshot": path.name,
              "snapshot_sha256": hashlib.sha256(raw).hexdigest(), "beats": beats}
    if not a.update:
        print(json.dumps(script, ensure_ascii=False, indent=1))
        return 0
    cfg_path = Path(a.update)
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    old = cfg.get("script") or {}
    script["snapshot"] = Path(os.path.relpath(path.resolve(), cfg_path.resolve().parent)).as_posix()
    script["departures"] = old.get("departures", {})
    cfg["script"] = script
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{cfg_path}: script from {a.doc} @ {a.revision} ({a.revision_kind}), {len(beats)} beats")
    if old.get("beats"):
        changed = changed_beats(old["beats"], beats)
        print(f"  changed since {old.get('revision')}: {', '.join(changed) if changed else 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
