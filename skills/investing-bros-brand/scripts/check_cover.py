#!/usr/bin/env python3
"""Check a finished cover or thumbnail before it is filed in Drive.

    python3 check_cover.py FILE --kind episode-wide|episode-square|segment-wide|shorts-vertical
                           [--episode N] [--register extras/artwork-register.json]

Checks the file itself: real image format, file name for its kind, episode number in
the name, aspect ratio and size, no transparency, and the YouTube 2 MB limit for
thumbnails. With --register it also checks that the artifact register has a row for
this file with the same format, the real width and height, and the episode-tab rule
(main episodes carry a `פרק N` tab; segments and nothing else may not). Prints where
the file goes. Exit code 1 on any failure; warnings do not fail.
"""
import argparse
import json
import re
import sys
from pathlib import Path

YOUTUBE_THUMB_MAX = 2 * 1024 * 1024
KINDS = {
    "episode-wide": {
        "format": "JPEG", "name": r"^thumbnail-פרק-(\d+)\.jpg$", "ratio": (16, 9),
        "min": (1280, 720), "target": (1920, 1080), "max_bytes": YOUTUBE_THUMB_MAX,
        "tab": True, "folder": "the episode root (פרק N), next to the transcript"},
    "episode-square": {
        "format": "PNG", "name": r"^cover-פרק-(\d+)\.png$", "ratio": (1, 1),
        "min": (1400, 1400), "target": (3000, 3000), "max_bytes": None,
        "tab": True, "folder": "the episode root (פרק N), next to the transcript"},
    "segment-wide": {
        "format": "JPEG", "name": r"^סגמנט-\d{2}-[^/]+-thumb\.jpg$", "ratio": (16, 9),
        "min": (1280, 720), "target": (1280, 720), "max_bytes": YOUTUBE_THUMB_MAX,
        "tab": False, "folder": "the episode's segments/ folder"},
    "shorts-vertical": {
        "format": "JPEG", "name": r"^שורט-\d{2}-[^/]+-cover\.jpg$", "ratio": (9, 16),
        "min": (1080, 1920), "target": (1080, 1920), "exact": True, "max_bytes": YOUTUBE_THUMB_MAX,
        "tab": True, "folder": "the episode's Shorts/ folder, next to its Short"},
}


def check_file(path: Path, kind: str, episode=None):
    """Returns (errors, warnings, (width, height))."""
    from PIL import Image
    spec, errs, warns = KINDS[kind], [], []
    m = re.match(spec["name"], path.name)
    if not m:
        errs.append(f"name {path.name!r} does not match {kind} pattern {spec['name']}")
    elif episode is not None and m.groups() and int(m.group(1)) != episode:
        errs.append(f"name says episode {m.group(1)}, expected {episode}")
    try:
        im = Image.open(path)
        im.load()
    except Exception as e:  # not an image at all (an HTML error page, a truncated download)
        return errs + [f"not a readable image: {e}"], warns, None
    w, h = im.size
    if im.format != spec["format"]:
        errs.append(f"is {im.format}, {kind} must be {spec['format']}")
    if im.mode in ("RGBA", "LA", "PA") or "transparency" in im.info:
        errs.append("has transparency; covers must be flat RGB")
    rw, rh = spec["ratio"]
    if abs(w * rh - h * rw) > 0.01 * h * rw:
        errs.append(f"{w}x{h} is not {rw}:{rh}")
    if spec.get("exact") and (w, h) != spec["target"]:
        errs.append(f"{w}x{h}, {kind} must be exactly {spec['target'][0]}x{spec['target'][1]}")
    elif w < spec["min"][0] or h < spec["min"][1]:
        errs.append(f"{w}x{h} is below the {spec['min'][0]}x{spec['min'][1]} minimum")
    elif (w, h) != spec["target"]:
        warns.append(f"{w}x{h}; target is {spec['target'][0]}x{spec['target'][1]} (disclose the real size)")
    size = path.stat().st_size
    if spec["max_bytes"] and size > spec["max_bytes"]:
        errs.append(f"{size / 1048576:.1f} MB is over YouTube's 2 MB thumbnail limit; re-save at lower JPEG quality")
    return errs, warns, (w, h)


def check_register(path: Path, register: Path, kind: str, dims):
    try:
        data = json.loads(register.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return [f"register {register}: {e}"]
    rows = [a for a in data.get("artifacts", []) if str(a.get("output_path") or "").endswith(path.name)]
    if not rows:
        return [f"register has no artifact whose output_path ends with {path.name}"]
    row, errs = rows[-1], []
    if row.get("format") != kind:
        errs.append(f"register format is {row.get('format')!r}, file is {kind}")
    if dims and (row.get("width"), row.get("height")) != dims:
        errs.append(f"register says {row.get('width')}x{row.get('height')}, file is {dims[0]}x{dims[1]}")
    if row.get("episode_tab") is not KINDS[kind]["tab"]:
        want = "true: main-episode and Shorts covers carry the פרק N tab" if KINDS[kind]["tab"] \
            else "false: segment thumbnails have no episode tab"
        errs.append(f"register episode_tab is {row.get('episode_tab')!r}, must be {want}")
    return errs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path)
    ap.add_argument("--kind", required=True, choices=sorted(KINDS))
    ap.add_argument("--episode", type=int, help="episode number the file name must carry (episode kinds)")
    ap.add_argument("--register", type=Path)
    a = ap.parse_args(argv)
    if not a.file.is_file():
        print(f"FAIL {a.file}: no such file")
        return 1
    errs, warns, dims = check_file(a.file, a.kind, a.episode)
    if a.register:
        errs += check_register(a.file, a.register, a.kind, dims)
    for w in warns:
        print("WARN", w)
    for e in errs:
        print("FAIL", e)
    if not errs:
        print(f"OK {a.file.name}: {dims[0]}x{dims[1]} {a.kind}; file it in {KINDS[a.kind]['folder']}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
