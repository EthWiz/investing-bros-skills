#!/usr/bin/env python3
"""Check the two episode Docs (titles and description) against the house layout.

Usage:
  python3 check_copy.py --titles titles.txt [--episode N]
  python3 check_copy.py --description description.txt
  python3 check_copy.py --titles titles.txt --description description.txt --episode N

Input is the plain text of the Doc (`אפשרויות כותרת` / `תיאור הפרק`).
Prints one line per problem: "error: ..." must be fixed, "warn: ..." needs a judgement call.
Exit code 1 if there is any error, else 0.
"""
import argparse
import re
import sys
import unicodedata

EM_DASHES = {"—": "em dash", "―": "horizontal bar", "–": "en dash"}  # all read as AI-written; plain hyphen only
DIRECTION_MARKS = {"‎": "LRM", "‏": "RLM", "‪": "LRE", "‫": "RLE",
                   "‬": "PDF", "⁦": "LRI", "⁧": "RLI", "⁩": "PDI"}
DISCLAIMER = "אין כאן המלצת השקעה. רק שיחה."
FINAL_LABEL = "בחירה סופית:"
TITLE_RE = re.compile(r"^פרק (\d+) - (\S.*)$")          # plain hyphen, spaces both sides
NUMBERED_RE = re.compile(r"^\s*(\d+)[.)]\s*(.+)$")
CHAPTER_RE = re.compile(r"^(?:(\d{1,2}):)?(\d{1,2}):(\d{2}) (\S.*)$")

TITLE_MAX = 60        # characters after "פרק N - "
TITLE_AIM = 50
INTRO_MAX = 450
CHAPTER_LABEL_MAX = 60
MIN_QUESTION_TITLES = 3

# Hype and clickbait. Errors: never in a title or description.
CLICKBAIT = [
    "לא תאמינו", "לא תאמין", "מטורף", "מטורפת", "מטורפים", "בלעדי", "חובה לשמוע", "חובה",
    "הסוד", "סודות", "מזעזע", "בהלם", "הלם", "תתעשרו", "להתעשר", "התעשרות", "עשירים",
    "מובטח", "בטוח שתרוויחו", "רווח מובטח", "כולם טועים", "אף אחד לא מספר", "פצצה",
    "הזדמנות של פעם בחיים", "100%", "x10", "פי 10",
]
# Warnings: fine in a chapter, but a title that sounds like a buy/sell call needs a second look.
CALL_WORDS = ["לקנות", "למכור", "תקנו", "תמכרו", "קונים עכשיו", "מוכרים עכשיו"]

EMOJI_RE = re.compile("[\U0001F000-\U0001FAFF☀-➿️]")


def _visible_len(s: str) -> int:
    return sum(1 for ch in s if unicodedata.category(ch) not in ("Cf", "Mn"))


def _common(text: str, where: str, out: list):
    for ch, name in EM_DASHES.items():
        if ch in text:
            out.append(f"error: {where}: contains an {name} '{ch}' - use ':' or ',' or a plain hyphen '-'")
    for ch, name in DIRECTION_MARKS.items():
        if ch in text:
            out.append(f"error: {where}: contains an invisible {name} mark - the Doc stays plain; "
                       "marks are added only at upload (investing-bros-episode-upload)")
            break
    if EMOJI_RE.search(text):
        out.append(f"error: {where}: emoji - not in episode titles or descriptions")
    if "!" in text:
        out.append(f"error: {where}: '!' - keep the tone calm")
    for w in CLICKBAIT:
        if w in text:
            out.append(f"error: {where}: clickbait/hype wording '{w}'")


def check_title(line: str, where: str, episode=None) -> list:
    out = []
    _common(line, where, out)
    m = TITLE_RE.match(line.strip())
    if not m:
        out.append(f"error: {where}: must be 'פרק N - <כותרת>' with a plain hyphen '-' and a space each side")
        return out
    num, body = int(m.group(1)), m.group(2)
    if episode is not None and num != episode:
        out.append(f"error: {where}: episode number {num}, expected {episode}")
    n = _visible_len(body)
    if n > TITLE_MAX:
        out.append(f"error: {where}: title is {n} characters after the prefix (max {TITLE_MAX})")
    elif n > TITLE_AIM:
        out.append(f"warn: {where}: title is {n} characters after the prefix (aim for {TITLE_AIM} or less)")
    if body.count("?") > 1:
        out.append(f"error: {where}: one question per title")
    if "?" in body and not body.rstrip().endswith("?"):
        out.append(f"warn: {where}: the question isn't at the end - house layout is '<נושא>: <שאלה>?'")
    if " - " in body:
        out.append(f"warn: {where}: spaced hyphen used as a dash - prefer ':'")
    for w in CALL_WORDS:
        if w in body:
            out.append(f"warn: {where}: '{w}' can read as a buy/sell call - make sure it's framed as the debate")
    return out


def check_titles(text: str, episode=None) -> list:
    out = []
    lines = [l.rstrip() for l in text.splitlines()]
    nonblank = [l for l in lines if l.strip()]
    if not nonblank:
        return ["error: titles: empty"]

    # A single title: Amitai cut the Doc down to his pick, or a published title is being checked.
    if len(nonblank) == 1 and not NUMBERED_RE.match(nonblank[0]):
        return check_title(nonblank[0], "title", episode)

    finals = [i for i, l in enumerate(nonblank) if l.strip().startswith(FINAL_LABEL)]
    if len(finals) != 1:
        out.append(f"error: titles: needs exactly one '{FINAL_LABEL}' line at the end")
    options = nonblank[: finals[0]] if finals else nonblank
    if len(options) != 5:
        out.append(f"error: titles: {len(options)} options, expected exactly 5")

    numbers, questions = [], 0
    for i, line in enumerate(options, 1):
        m = NUMBERED_RE.match(line)
        if not m:
            out.append(f"error: option {i}: must start with '{i}. '")
            continue
        if int(m.group(1)) != i:
            out.append(f"error: option {i}: numbered {m.group(1)}")
        title = m.group(2).strip()
        out += check_title(title, f"option {i}", episode)
        tm = TITLE_RE.match(title)
        if tm:
            numbers.append(int(tm.group(1)))
        if "?" in title:
            questions += 1
    if len(set(numbers)) > 1:
        out.append(f"error: titles: options disagree on the episode number {sorted(set(numbers))}")
    if options and questions < MIN_QUESTION_TITLES:
        out.append(f"error: titles: {questions} of {len(options)} options are questions "
                   f"(at least {MIN_QUESTION_TITLES})")

    if finals:
        chosen = nonblank[finals[0]].strip()[len(FINAL_LABEL):].strip()
        if chosen:
            out += check_title(chosen, "final pick", episode)
        if finals[0] != len(nonblank) - 1:
            out.append(f"error: titles: nothing may follow the '{FINAL_LABEL}' line")
    return out


def _seconds(m) -> int:
    h = int(m.group(1) or 0)
    return h * 3600 + int(m.group(2)) * 60 + int(m.group(3))


def check_description(text: str) -> list:
    out = []
    _common(text, "description", out)
    lines = [l.strip() for l in text.splitlines()]
    nonblank = [l for l in lines if l]
    if not nonblank:
        return ["error: description: empty"]
    if DISCLAIMER not in nonblank:
        out.append(f"error: description: missing the disclaimer line, exactly '{DISCLAIMER}'")
        return out

    d = nonblank.index(DISCLAIMER)
    intro, chapters = nonblank[:d], nonblank[d + 1:]

    if not intro:
        out.append("error: description: no intro paragraph before the disclaimer")
    else:
        if len(intro) > 1:
            out.append("warn: description: intro is more than one paragraph - make it one cohesive paragraph")
        for l in intro:
            if CHAPTER_RE.match(l):
                out.append(f"error: description: a chapter line sits above the disclaimer: '{l}'")
        intro_text = " ".join(intro)
        if _visible_len(intro_text) > INTRO_MAX:
            out.append(f"warn: description: intro is {_visible_len(intro_text)} characters (aim for {INTRO_MAX} or less)")
        first_sentence = re.split(r"(?<=[.?])\s", intro_text, maxsplit=1)[0]
        if not first_sentence.endswith("?"):
            out.append("warn: description: intro doesn't open with a question (preferred, not required)")

    if not chapters:
        out.append("error: description: no chapters after the disclaimer")
        return out
    prev = -1
    for i, l in enumerate(chapters, 1):
        m = CHAPTER_RE.match(l)
        if not m:
            out.append(f"error: chapter {i}: must be time first, 'M:SS נושא': '{l}'")
            continue
        t = _seconds(m)
        if int(m.group(3)) > 59 or (m.group(1) and int(m.group(2)) > 59):
            out.append(f"error: chapter {i}: invalid time '{l.split()[0]}'")
        if i == 1 and t != 0:
            out.append(f"error: chapter 1: chapters start at 0:00 (edited timeline), got '{l.split()[0]}'")
        if t <= prev:
            out.append(f"error: chapter {i}: times must go up ('{l.split()[0]}')")
        prev = t
        label = m.group(4)
        if _visible_len(label) > CHAPTER_LABEL_MAX:
            out.append(f"warn: chapter {i}: label is {_visible_len(label)} characters (aim for {CHAPTER_LABEL_MAX} or less)")
    if len(chapters) < 3:
        out.append(f"warn: description: only {len(chapters)} chapters")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--titles", help="plain text of the 'אפשרויות כותרת' Doc")
    ap.add_argument("--description", help="plain text of the 'תיאור הפרק' Doc")
    ap.add_argument("--episode", type=int, help="episode number as Amitai stated it")
    a = ap.parse_args(argv)
    if not a.titles and not a.description:
        ap.error("give --titles and/or --description")
    problems = []
    if a.titles:
        with open(a.titles, encoding="utf-8") as f:
            problems += check_titles(f.read(), a.episode)
    if a.description:
        with open(a.description, encoding="utf-8") as f:
            problems += check_description(f.read())
    for p in problems:
        print(p)
    errors = sum(p.startswith("error:") for p in problems)
    warns = len(problems) - errors
    print(f"{errors} error(s), {warns} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
