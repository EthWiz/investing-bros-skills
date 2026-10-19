#!/usr/bin/env python3
"""Check the episode title options and description against the house layout.

Usage:
  python3 check_copy.py --titles titles.txt [--episode N]
  python3 check_copy.py --description description.txt
  python3 check_copy.py --titles titles.txt --description description.txt --episode N --spotify
  python3 check_copy.py --description video-description.txt --youtube

Input is the plain text of the episode's title and description files (the .txt files
in the episode's Drive folder). --spotify adds the rules Spotify needs to show chapters
(the RedCircle description feeds Spotify): MM:SS timestamps, 30 s apart, short labels.
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
SPOTIFY_LINE_PREFIX = "🎧 להאזנה בספוטיפיי: "
SPOTIFY_EPISODE_RE = re.compile(
    r"^🎧 להאזנה בספוטיפיי: https://open\.spotify\.com/episode/[A-Za-z0-9]+$"
)
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

HEBREW_RE = re.compile(r"[\u05D0-\u05EA]")
LATIN_RE = re.compile(r"[A-Za-z]")
MIN_CHAPTER_GAP = 10  # seconds; YouTube ignores chapters shorter than this
SPOTIFY_MIN_GAP = 30  # seconds between chapter starts on Spotify
SPOTIFY_LABEL_MAX = 40
SPOTIFY_TIME_RE = re.compile(r"^(\d{2}:)?\d{2}:\d{2} ")  # MM:SS or HH:MM:SS, zero-padded
BIDI_FIX = ("start it with a Hebrew word; a line that starts with English or a number turns "
            "left-to-right in a Hebrew description, and its timestamp, numbers and words land out of order")


def _first_strong(s: str):
    """'R' if the first letter is Hebrew, 'L' if Latin, None if there's no letter."""
    for ch in s:
        if HEBREW_RE.match(ch):
            return "R"
        if LATIN_RE.match(ch):
            return "L"
    return None


EMOJI_RE = re.compile("[\U0001F000-\U0001FAFF☀-➿️]")


def _visible_len(s: str) -> int:
    return sum(1 for ch in s if unicodedata.category(ch) not in ("Cf", "Mn"))


def _common(text: str, where: str, out: list, allowed_emoji: str = ""):
    for ch, name in EM_DASHES.items():
        if ch in text:
            out.append(f"error: {where}: contains an {name} '{ch}' - use ':' or ',' or a plain hyphen '-'")
    for ch, name in DIRECTION_MARKS.items():
        if ch in text:
            out.append(f"error: {where}: contains an invisible {name} mark - the .txt stays plain; "
                       "marks are added only at upload (investing-bros-episode-upload)")
            break
    emoji_text = text
    for emoji in allowed_emoji:
        emoji_text = emoji_text.replace(emoji, "")
    if EMOJI_RE.search(emoji_text):
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

    # A single title: Amitai cut the file down to his pick, or a published title is being checked.
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


def _padded(t: int) -> str:
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def check_description(
    text: str,
    spotify: bool = False,
    youtube: bool = False,
    allow_missing_spotify: bool = False,
) -> list:
    out = []
    _common(text, "description", out, allowed_emoji="🎧" if youtube else "")
    lines = [l.strip() for l in text.splitlines()]
    nonblank = [l for l in lines if l]
    if not nonblank:
        return ["error: description: empty"]
    if DISCLAIMER not in nonblank:
        out.append(f"error: description: missing the disclaimer line, exactly '{DISCLAIMER}'")
        return out

    d = nonblank.index(DISCLAIMER)
    intro, tail = nonblank[:d], nonblank[d + 1:]
    spotify_lines = [line for line in tail if line.startswith(SPOTIFY_LINE_PREFIX)]
    chapters = [line for line in tail if not line.startswith(SPOTIFY_LINE_PREFIX)]

    if youtube:
        if any("🎧" in line and not line.startswith(SPOTIFY_LINE_PREFIX) for line in nonblank):
            out.append("error: description: use the 🎧 emoji only on the Spotify episode line")
        if not spotify_lines:
            message = (
                "description: missing the per-episode Spotify line "
                f"'{SPOTIFY_LINE_PREFIX}https://open.spotify.com/episode/<id>'"
            )
            out.append(("warn: " if allow_missing_spotify else "error: ") + message)
        elif len(spotify_lines) > 1:
            out.append("error: description: more than one Spotify episode line")
        else:
            spotify_line = spotify_lines[0]
            if not SPOTIFY_EPISODE_RE.fullmatch(spotify_line):
                out.append(
                    "error: description: Spotify line must use the clean per-episode URL "
                    "'https://open.spotify.com/episode/<id>' with no ?si= query"
                )
            disclaimer_line = lines.index(DISCLAIMER)
            spotify_line_index = lines.index(spotify_line)
            chapter_line_indices = [i for i, line in enumerate(lines) if CHAPTER_RE.match(line)]
            if chapter_line_indices and spotify_line_index > chapter_line_indices[0]:
                out.append("error: description: Spotify line must be before the chapters")
            if spotify_line_index != disclaimer_line + 2 or lines[disclaimer_line + 1] != "":
                out.append("error: description: put one blank line between the disclaimer and Spotify line")
            if (
                spotify_line_index + 1 >= len(lines)
                or lines[spotify_line_index + 1] != ""
                or (spotify_line_index + 2 < len(lines) and not CHAPTER_RE.match(lines[spotify_line_index + 2]))
            ):
                out.append("error: description: put one blank line after the Spotify line, then start chapters")

    if not intro:
        out.append("error: description: no intro paragraph before the disclaimer")
    else:
        if len(intro) > 1:
            out.append("warn: description: intro is more than one paragraph - make it one cohesive paragraph")
        for l in intro:
            if CHAPTER_RE.match(l):
                out.append(f"error: description: a chapter line sits above the disclaimer: '{l}'")
            elif _first_strong(l) != "R" or not HEBREW_RE.match(l[0]):
                out.append(f"error: description: intro line '{l[:30]}...': {BIDI_FIX}")
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
        elif prev >= 0 and t - prev < MIN_CHAPTER_GAP:
            out.append(f"error: chapter {i}: only {t - prev} s after the previous chapter "
                       f"(YouTube needs at least {MIN_CHAPTER_GAP} s, or it drops the chapters)")
        elif spotify and prev >= 0 and t - prev < SPOTIFY_MIN_GAP:
            out.append(f"error: chapter {i}: only {t - prev} s after the previous chapter "
                       f"(Spotify needs at least {SPOTIFY_MIN_GAP} s)")
        if spotify and not SPOTIFY_TIME_RE.match(l):
            out.append(f"error: chapter {i}: Spotify reads zero-padded times, write "
                       f"'{_padded(t)}' not '{l.split()[0]}'")
        prev = t
        label = m.group(4)
        if not HEBREW_RE.match(label[0]):
            out.append(f"error: chapter {i}: label '{label}' - {BIDI_FIX} "
                       f"(e.g. '1:05 מרוץ המודלים: OpenAI מול אנתרופיק')")
        if spotify and _visible_len(label) > SPOTIFY_LABEL_MAX:
            out.append(f"warn: chapter {i}: label is {_visible_len(label)} characters "
                       f"(Spotify suggests under {SPOTIFY_LABEL_MAX})")
        elif _visible_len(label) > CHAPTER_LABEL_MAX:
            out.append(f"warn: chapter {i}: label is {_visible_len(label)} characters (aim for {CHAPTER_LABEL_MAX} or less)")
    if len(chapters) < 3:
        out.append(f"error: description: only {len(chapters)} chapters (YouTube needs at least 3 to show chapters)")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--titles", help="the five title options + 'בחירה סופית:' (.txt)")
    ap.add_argument("--description", help="the episode description (.txt)")
    ap.add_argument("--episode", type=int, help="episode number as Amitai stated it")
    ap.add_argument("--spotify", action="store_true",
                    help="also apply Spotify's chapter rules (use for the RedCircle copy)")
    ap.add_argument("--youtube", action="store_true",
                    help="require the clean per-episode Spotify link and YouTube block order")
    ap.add_argument("--allow-missing-spotify", action="store_true",
                    help="with --youtube, warn instead of fail while a new episode is still distributing")
    a = ap.parse_args(argv)
    if not a.titles and not a.description:
        ap.error("give --titles and/or --description")
    if a.allow_missing_spotify and not a.youtube:
        ap.error("--allow-missing-spotify requires --youtube")
    problems = []
    if a.titles:
        with open(a.titles, encoding="utf-8") as f:
            problems += check_titles(f.read(), a.episode)
    if a.description:
        with open(a.description, encoding="utf-8") as f:
            problems += check_description(
                f.read(),
                spotify=a.spotify,
                youtube=a.youtube,
                allow_missing_spotify=a.allow_missing_spotify,
            )
    for p in problems:
        print(p)
    errors = sum(p.startswith("error:") for p in problems)
    warns = len(problems) - errors
    print(f"{errors} error(s), {warns} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
