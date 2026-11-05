#!/usr/bin/env python3
"""Check a finished cover or thumbnail before it is filed in Drive.

    python3 check_cover.py FILE --kind episode-wide|episode-square|segment-wide|shorts-vertical
                           [--episode N] [--register extras/artwork-register.json]
                           [--title "headline line" ...] [--config short.json] [--font Heebo-Black.ttf]
                           [--allow-green "Amitai HH:MM: why"]

Checks the file itself: real image format, file name for its kind, episode number in
the name, aspect ratio and size, no transparency, and the YouTube 2 MB limit for
thumbnails. With --register it also checks that the artifact register has a row for
this file with the same format, the real width and height, and the episode-tab rule
(main episodes carry a `פרק N` tab; segments and nothing else may not). Prints where
the file goes.

Headline text (episode 10: a U+061F Arabic question mark and square-bracket tofu reached
a thumbnail): every --title line, the config's cover_title.top_line/bottom_line and the
register row's `headline` are checked for characters Heebo cannot show or that never
belong in a headline (Arabic punctuation, brackets, replacement/box characters, control
and private-use characters, niqqud). With --font, every character must also be in the
font's cmap.

Palette (episode 10: a green disc instead of mustard): the image must contain brand
mustard (#D8A52E) or screen gold (#F5B71F), and no large saturated green area. A green
area that is really meant to be there needs --allow-green with Amitai's words.

Exit code 1 on any failure; warnings do not fail.
"""
import argparse
import json
import re
import sys
from pathlib import Path

YOUTUBE_THUMB_MAX = 2 * 1024 * 1024
# Brand palette (references/brand-rules.md).
NAVY = (9, 36, 59)          # #09243B
CREAM = (245, 235, 213)     # #F5EBD5
MUSTARD = (216, 165, 46)    # #D8A52E
SCREEN_GOLD = (245, 183, 31)  # #F5B71F, the motion accent
BRAND_GOLDS = (MUSTARD, SCREEN_GOLD)
GOLD_TOLERANCE = 60         # RGB distance that still reads as brand mustard/gold
GOLD_MIN_SHARE = 0.002      # at least 0.2% of pixels
GREEN_MAX_SHARE = 0.03      # a saturated green area above 3% of the frame fails

# Headline characters: Hebrew letters and Hebrew punctuation, Latin, digits and the
# ordinary punctuation the show uses.
HEADLINE_PUNCT = set(" .,:;!?%$€₪'\"-–—()/&+’‘“”״׳־…")
BANNED_CHARS = {
    "\u061f": "U+061F ARABIC QUESTION MARK (use '?')",
    "\u060c": "U+060C ARABIC COMMA (use ',')",
    "\u061b": "U+061B ARABIC SEMICOLON (use ';')",
    "\ufffd": "U+FFFD replacement character (broken encoding)",
    "[": "'[' square bracket (markup or tofu leaking into the headline)",
    "]": "']' square bracket (markup or tofu leaking into the headline)",
    "{": "'{' brace", "}": "'}' brace", "<": "'<'", ">": "'>'",
    "\u25a1": "U+25A1 white square (tofu)", "\u25a0": "U+25A0 black square (tofu)",
    "\u25af": "U+25AF rectangle (tofu)", "\u2b1c": "U+2B1C square (tofu)",
}

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


def _headline_char_ok(ch: str) -> bool:
    if ch in HEADLINE_PUNCT or ch.isascii() and ch.isalnum():
        return True
    return "\u05d0" <= ch <= "\u05ea"


def check_headline(text: str, cmap=None) -> list:
    """Errors for characters that must not reach a cover headline.

    cmap: optional set of code points the headline font has (fontTools getBestCmap())."""
    import unicodedata
    errs = []
    if not text or not text.strip():
        return ["headline is empty"]
    for i, ch in enumerate(text):
        where = f"headline {text!r} char {i + 1}"
        if ch in BANNED_CHARS:
            errs.append(f"{where}: {BANNED_CHARS[ch]}")
        elif "\u0591" <= ch <= "\u05c7" and ch != "\u05be":
            errs.append(f"{where}: U+{ord(ch):04X} niqqud/cantillation mark (not used in headlines)")
        elif "\u0600" <= ch <= "\u06ff":
            errs.append(f"{where}: U+{ord(ch):04X} Arabic character {unicodedata.name(ch, '?')}")
        elif unicodedata.category(ch) in ("Cc", "Cf", "Co", "Cn", "Cs"):
            errs.append(f"{where}: U+{ord(ch):04X} invisible/control/unassigned character")
        elif not _headline_char_ok(ch):
            errs.append(f"{where}: U+{ord(ch):04X} {unicodedata.name(ch, '?')} is outside the headline "
                        "character set (Hebrew, Latin, digits, ordinary punctuation)")
        elif cmap is not None and ch != " " and ord(ch) not in cmap:
            errs.append(f"{where}: U+{ord(ch):04X} has no glyph in the headline font (would render as tofu)")
    return errs


def font_cmap(font_path: Path):
    from fontTools.ttLib import TTFont
    return set(TTFont(str(font_path)).getBestCmap())


def headlines_from_config(config: Path) -> list:
    data = json.loads(config.read_text(encoding="utf-8"))
    title = data.get("cover_title")
    if not isinstance(title, dict):
        raise ValueError(f"{config}: no cover_title object")
    lines = [title.get(k) for k in ("top_line", "bottom_line")]
    if not all(isinstance(x, str) and x.strip() for x in lines):
        raise ValueError(f"{config}: cover_title needs non-empty top_line and bottom_line strings")
    return lines


def check_palette(path: Path, allow_green: bool = False):
    """Returns (errors, warnings): brand mustard/gold present, no big saturated green area."""
    import numpy as np
    from PIL import Image
    im = Image.open(path).convert("RGB")
    im.thumbnail((480, 480))
    a = np.asarray(im, dtype=np.float32).reshape(-1, 3)
    errs, warns = [], []
    gold = np.zeros(len(a), bool)
    for colour in BRAND_GOLDS:
        gold |= np.linalg.norm(a - np.array(colour, np.float32), axis=1) < GOLD_TOLERANCE
    r, g, b = a[:, 0], a[:, 1], a[:, 2]
    mx, mn = a.max(axis=1), a.min(axis=1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    green = (g >= r + 30) & (g >= b + 20) & (sat > 0.35) & (mx > 60)
    green_share, gold_share = float(green.mean()), float(gold.mean())
    if green_share > GREEN_MAX_SHARE:
        msg = (f"{green_share:.1%} of the image is saturated green; the brand disc and strips are "
               f"mustard #D8A52E, never green (brand-rules.md)")
        (warns if allow_green else errs).append(msg + (" [allowed by --allow-green]" if allow_green else ""))
    if gold_share < GOLD_MIN_SHARE:
        errs.append(f"no brand mustard #D8A52E / gold #F5B71F found ({gold_share:.2%} of pixels); "
                    "check the palette against brand-rules.md")
    navy = np.linalg.norm(a - np.array(NAVY, np.float32), axis=1) < 45
    if float(navy.mean()) < 0.002:
        warns.append("almost no brand navy #09243B; check the palette against brand-rules.md")
    return errs, warns


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


def register_headlines(path: Path, register: Path) -> list:
    try:
        data = json.loads(register.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    rows = [a for a in data.get("artifacts", []) if str(a.get("output_path") or "").endswith(path.name)]
    if not rows:
        return []
    h = rows[-1].get("headline")
    if isinstance(h, str):
        return [h]
    if isinstance(h, list):
        return [x for x in h if isinstance(x, str)]
    return []


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path)
    ap.add_argument("--kind", required=True, choices=sorted(KINDS))
    ap.add_argument("--episode", type=int, help="episode number the file name must carry (episode kinds)")
    ap.add_argument("--register", type=Path)
    ap.add_argument("--title", action="append", default=[], help="a headline line on the cover (repeatable)")
    ap.add_argument("--config", type=Path, help="Short/cover config whose cover_title lines are checked")
    ap.add_argument("--font", type=Path, help="headline font; every headline character must have a glyph")
    ap.add_argument("--allow-green", metavar="AMITAI_WORDS",
                    help="a large green area is intended: quote Amitai (\"Amitai HH:MM: ...\")")
    a = ap.parse_args(argv)
    if not a.file.is_file():
        print(f"FAIL {a.file}: no such file")
        return 1
    if a.allow_green is not None and not a.allow_green.strip().lower().startswith("amitai"):
        print("FAIL --allow-green must quote Amitai: \"Amitai HH:MM: ...\"")
        return 2
    errs, warns, dims = check_file(a.file, a.kind, a.episode)
    if a.register:
        errs += check_register(a.file, a.register, a.kind, dims)
    titles = list(a.title)
    if a.config:
        try:
            titles += headlines_from_config(a.config)
        except (OSError, ValueError) as e:
            errs.append(str(e))
    if a.register:
        titles += register_headlines(a.file, a.register)
    cmap = font_cmap(a.font) if a.font else None
    for t in titles:
        errs += check_headline(t, cmap)
    if not titles and a.kind != "segment-wide":
        warns.append("no headline checked: pass --title/--config, or a register row `headline`")
    if dims:
        p_errs, p_warns = check_palette(a.file, allow_green=a.allow_green is not None)
        errs += p_errs
        warns += p_warns
    for w in warns:
        print("WARN", w)
    for e in errs:
        print("FAIL", e)
    if not errs:
        print(f"OK {a.file.name}: {dims[0]}x{dims[1]} {a.kind}; file it in {KINDS[a.kind]['folder']}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
