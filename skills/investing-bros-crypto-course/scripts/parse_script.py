#!/usr/bin/env python3
"""Read a lesson's script (the Google Doc תסריט-שיעור-N) into its video config, beat by beat.

Usage:
    python3 parse_script.py script.md --doc DOC_ID --revision MODIFIED_TIME [--update lesson-N-video.json]

script.md: the Doc's text as the Drive connector's read_file_content returns it (saved to a file).
--revision: the Doc's modifiedTime from get_file_metadata, so the config says which version it follows.
Prints {doc, revision, beats: {N: {title, seconds, on_screen, text}}}; with --update it writes that into
the config's `script`, keeping its `departures` (beat -> why the video deliberately differs from that
beat's על המסך line). The Doc decides what is on screen; the recording decides captions and timing.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HEADING = re.compile(r"^#{1,3}\s*\**\s*קטע\s+(\d+)\s*:\s*(.+?)\s*(?:\(כ-?\s*(\d+)\s*שניות\))?\s*\**\s*$")
ON_SCREEN = re.compile(r"^\*?\s*על המסך\s*:\s*(.+?)\s*\*?$")
LIST_ITEM = re.compile(r"^\s*(?:\d+\.|[-*])\s+")


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
        if line.startswith("#"):                   # another heading (sources, notes) ends the beats
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script")
    ap.add_argument("--doc", required=True)
    ap.add_argument("--revision", required=True)
    ap.add_argument("--update", help="the lesson's video config to write the script into")
    a = ap.parse_args(argv)
    beats = parse(Path(a.script).read_text(encoding="utf-8"))
    if not beats:
        raise SystemExit("error: no 'קטע N: …' headings found; is this the script Doc's text?")
    missing = [n for n, b in beats.items() if not b["on_screen"]]
    if missing:
        print(f"warning: beats {missing} have no 'על המסך' line", file=sys.stderr)
    script = {"doc": a.doc, "revision": a.revision, "beats": beats}
    if a.update:
        path = Path(a.update)
        cfg = json.loads(path.read_text(encoding="utf-8"))
        script["departures"] = (cfg.get("script") or {}).get("departures", {})
        cfg["script"] = script
        path.write_text(json.dumps(cfg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{path}: script from {a.doc} @ {a.revision}, {len(beats)} beats")
    else:
        print(json.dumps(script, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
