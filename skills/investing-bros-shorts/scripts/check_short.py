#!/usr/bin/env python3
"""Check a rendered short before handing it back: length, loudness, peak, the first second, and a frame strip.

Usage:
    python3 check_short.py short.mp4 --config short.json --youtube-notes youtube-שורט-01.md

Prints duration, integrated loudness (target about -14 LUFS) and true peak (below -1 dB),
and checks the opening and the ending: frame 1 is not black or fading in, speech starts
within 0.4 s on a clean, strong first word (never eh/אה or a repeated-word stutter;
a first caption after 1.0 s is a hard fail, 0.4–1.0 s is a warning), and the short doesn't
trail off in more than 1 s of silence. Length outside
15-45 s fails: 45 seconds is a hard cap, measured after the 1.15x speed-up.
If NAME_layout.json from build_fullbleed.py sits next to the video (or --layout is
given), the caption and hook positions must be inside brand.CAPTION_Y_BOUNDS and
brand.HOOK_Y_BOUNDS, and the hook block must keep brand.HOOK_GAP below the logo and above
the captions. Approved renders declare their intentional 3 s silent end card in
NAME_layout.json, so it is not mistaken for trailing dead air.
Then LOOK at the strip: captions right-to-left and inside the safe zone, the right host
on screen, nothing over the face, the hook readable on the first frame.
"""
import argparse
import json
import os
import re
import subprocess
import sys


def probe(path):
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                             capture_output=True, text=True, check=True).stdout)
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", log)[-1])
    peak = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", log)[-1])
    return d, lufs, peak


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brand import CAPTION_HALF, CAPTION_Y_BOUNDS, HOOK_GAP, HOOK_Y_BOUNDS, LOGO_BOX  # noqa: E402

LIMIT = (15, 45)
DARK_FRAME = 25            # mean luma (0-255) below this reads as a black frame
LEAD_SILENCE, TAIL_SILENCE = 0.4, 1.0
LATE_WORD_FAIL = 1.0
OPENING_WINDOW = 3.0
# Whole-word fillers only (episode 11: "eh"/"אה"). No prefix match: "אהבה" and "umbrella" are real words.
FILLER_WORDS = frozenset({
    "אה", "אהה", "אההה",
    "eh", "uh", "um", "umm", "uhh", "ah",
})
# Prefix-stutter warnings skip these common particles ("זה זהב", "כל כלכלה").
PREFIX_STUTTER_SKIP = frozenset({"זה", "מי", "על", "כל", "יש", "או"})


def _norm_word(tok):
    return re.sub(r"^[^\w\u0590-\u05FF]+|[^\w\u0590-\u05FF]+$", "", tok or "", flags=re.UNICODE).lower()


def _is_filler_token(tok):
    w = _norm_word(tok)
    return bool(w) and w in FILLER_WORDS


def _is_prefix_stutter(a, b):
    return bool(a and b and a != b and b.startswith(a) and len(a) <= 4 and a not in PREFIX_STUTTER_SKIP)


def _is_repeated_word(a, b):
    return bool(a and b and a == b)


def opening_word_review(words, lead=LEAD_SILENCE, late_fail=LATE_WORD_FAIL, window=OPENING_WINDOW):
    """Return (hard_fails, warnings). `words` are on the cut timeline (0 = start)."""
    timed = sorted(
        (w for w in words if w.get("end", 0) > 0 and w.get("start", 0) < window),
        key=lambda w: w["start"],
    )
    if not timed:
        return [f"no words in the first {window:.0f} s; transcribe the opening and trim to the first clean word"], []
    first = timed[0]
    fails, warns = [], []
    if first["start"] > late_fail:
        fails.append(
            f"first word {first['w']!r} starts at {first['start']:.1f} s; "
            f"trim the opening to the first clean word (lead must be ≤ {late_fail:.1f} s)"
        )
    elif first["start"] > lead:
        warns.append(
            f"first word {first['w']!r} starts at {first['start']:.1f} s; "
            f"prefer trimming so the lead is ≤ {lead:.1f} s"
        )
    if _is_filler_token(first["w"]):
        fails.append(
            f"opens on filler {first['w']!r}; the first audio must be a clean, strong word, "
            "never eh/אה, a filler, a false start or a stutter"
        )
    if len(timed) >= 2:
        a, b = _norm_word(timed[0]["w"]), _norm_word(timed[1]["w"])
        if _is_repeated_word(a, b):
            fails.append(
                f"opens on a stutter {timed[0]['w']!r} {timed[1]['w']!r}; "
                "cut to the first clean full word"
            )
        elif _is_prefix_stutter(a, b):
            warns.append(
                f"opens on a possible stutter {timed[0]['w']!r} {timed[1]['w']!r}; "
                "listen and cut to the first clean full word if it is a false start"
            )
    return fails, warns


def opening_word_problems(words, lead=LEAD_SILENCE, late_fail=LATE_WORD_FAIL, window=OPENING_WINDOW):
    """Hard-fail opening problems (warnings are in opening_word_review)."""
    fails, _ = opening_word_review(words, lead=lead, late_fail=late_fail, window=window)
    return fails


def first_clean_start(words, proposed_start, lead=LEAD_SILENCE, window=OPENING_WINDOW):
    """Raw-timeline in-point: skip filler/repeated-word stutter in the first `window` s."""
    timed = sorted(
        (w for w in words if w["end"] > proposed_start and w["start"] < proposed_start + window),
        key=lambda w: w["start"],
    )
    i = 0
    while i < len(timed) and _is_filler_token(timed[i]["w"]):
        i += 1
    if i + 1 < len(timed):
        a, b = _norm_word(timed[i]["w"]), _norm_word(timed[i + 1]["w"])
        if _is_repeated_word(a, b):
            i += 1
        elif _is_prefix_stutter(a, b):
            i += 1
    if i >= len(timed):
        return proposed_start
    start = timed[i]["start"]
    return start if start - proposed_start > lead else proposed_start


def iter_words(payload):
    """Flatten captions.json, words.json, or a bare word list into {w, start, end}."""
    if not payload:
        return []
    if isinstance(payload, dict):
        payload = payload.get("words") or payload.get("captions") or payload.get("segments") or []
    out = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        if "words" in item and isinstance(item["words"], list):
            out.extend(iter_words(item["words"]))
            continue
        w = item.get("w") or item.get("word") or item.get("text")
        s = item.get("start", item.get("s"))
        e = item.get("end", item.get("e"))
        if w and s is not None and e is not None:
            out.append({"w": str(w), "start": float(s), "end": float(e)})
    return out


def words_from_srt(text):
    """One word record per cue (cue start + first token) plus remaining tokens spread across the cue."""
    cues = re.findall(
        r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*\n(.*?)(?=\n\n|\Z)",
        text.replace("\r\n", "\n"),
        flags=re.S,
    )

    def stamp(h, m, s, ms):
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0

    out = []
    for c in cues:
        t0, t1 = stamp(*c[:4]), stamp(*c[4:8])
        body = re.sub(r"<[^>]+>", "", c[8])
        toks = [t for t in body.replace("\n", " ").split() if _norm_word(t)]
        if not toks:
            continue
        step = (t1 - t0) / len(toks)
        for i, tok in enumerate(toks):
            out.append({"w": tok, "start": t0 + i * step, "end": t0 + (i + 1) * step})
    return out


def load_opening_words(path):
    raw = open(path, encoding="utf-8").read()
    if path.lower().endswith(".srt"):
        return words_from_srt(raw)
    return iter_words(json.loads(raw))


def find_opening_words(video, explicit=None):
    """Prefer an explicit file, then NAME.srt / captions.json next to the video (output timeline)."""
    if explicit:
        return explicit, load_opening_words(explicit)
    stem = re.sub(r"\.[^.]+$", "", video)
    directory = os.path.dirname(os.path.abspath(video)) or "."
    name = os.path.basename(stem)
    candidates = [
        stem + ".srt",
        os.path.join(directory, "captions.json"),
        os.path.join(directory, name + "_captions.json"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path, load_opening_words(path)
    return None, None



def luma(path, t):
    """Mean luma of the frame at time t."""
    log = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1",
                          "-vf", "signalstats,metadata=print", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.findall(r"YAVG=(-?[\d.]+)", log)
    return float(m[-1]) if m else 0.0


def silences(path, noise_db=-35, min_len=0.3):
    """[(start, end)] stretches of silence; an open one at the end runs to None."""
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", f"silencedetect=n={noise_db}dB:d={min_len}",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: (-?[\d.]+)", log)]
    return [(s, ends[i] if i < len(ends) else None) for i, s in enumerate(starts)]


def opening_problems(d, first_luma, later_luma, quiet, silent_endcard_seconds=0.0):
    """The first second has to hook: a visible frame and speech straight away; no dead air at the end."""
    out = []
    if first_luma < DARK_FRAME:
        out.append(f"frame 1 is nearly black (luma {first_luma:.0f}); open on the host, not a fade or a title card")
    elif later_luma and first_luma < 0.6 * later_luma:
        out.append(f"frame 1 is much darker than 0.5 s in ({first_luma:.0f} vs {later_luma:.0f}); remove the fade-in")
    for s, e in quiet:
        if s <= 0.05 and (e if e is not None else d) > LEAD_SILENCE:
            out.append(f"{(e if e is not None else d):.1f} s of silence before the first word; start on the word")
        speech_tail = max(0.0, d - s - silent_endcard_seconds)
        if (e is None or e >= d - 0.05) and speech_tail > TAIL_SILENCE:
            out.append(f"{d - s:.1f} s of silence at the end "
                       f"({silent_endcard_seconds:.1f} s is the intentional end card); cut right after the payoff")
    return out


def layout_problems(lay):
    """Caption and hook positions recorded by build_fullbleed.py, against the brand bounds."""
    out = []
    lo, hi = CAPTION_Y_BOUNDS
    if not lo <= lay.get("caption_y", lo) <= hi:
        out.append(f"caption_y {lay['caption_y']} is outside {lo}-{hi}; captions must clear the UI and the hook band")
    if lay.get("hook_style", "strips") == "strips":
        lo, hi = HOOK_Y_BOUNDS
        if not lo <= lay.get("hook_y", lo) <= hi:
            out.append(f"hook_y {lay['hook_y']} is outside the top band {lo}-{hi}")
        box = lay.get("hook_box")
        if box and box[0] < LOGO_BOX[3] + HOOK_GAP:
            out.append(f"hook starts at y={box[0]}: it needs {HOOK_GAP} px clear below the logo (bottom {LOGO_BOX[3]})")
        cap = lay.get("caption_y")
        if box and cap and box[1] > cap - CAPTION_HALF - HOOK_GAP:
            out.append(f"hook ends at y={box[1]}: it needs {HOOK_GAP} px clear above the captions (caption_y {cap})")
    for c in lay.get("callouts", []):
        (top, bottom), (t0, t1) = c["box"], c["window"]
        cap = lay.get("caption_y", CAPTION_Y_BOUNDS[1])
        if top < LOGO_BOX[3] + HOOK_GAP or bottom > cap - CAPTION_HALF - HOOK_GAP:
            out.append(f"callout y {top}-{bottom} needs {HOOK_GAP} px clear of the logo and the captions")
        end = lay.get("endcard_start", lay["duration"] - 2.8 if lay.get("duration") else None)
        if t0 < 2.7 or (end is not None and t1 > end + 0.31):     # 0.3 s crossfade into the card is fine
            out.append(f"callout {t0}-{t1} s overlaps the hook or the end card")
    if lay.get("endcard_box"):
        top, bottom = lay["endcard_box"]
        if top < LOGO_BOX[1] or bottom > CAPTION_Y_BOUNDS[1] + CAPTION_HALF:
            out.append(f"end card y {top}-{bottom} leaves the safe zone (y {LOGO_BOX[1]}-{CAPTION_Y_BOUNDS[1] + CAPTION_HALF})")
    return out


def problems(d, lufs, peak):
    out = []
    if not LIMIT[0] <= d <= LIMIT[1]:
        out.append(f"duration {d:.1f} s is outside {LIMIT[0]}–{LIMIT[1]} s")
    if abs(lufs + 14) > 1.5:
        out.append(f"loudness {lufs} LUFS is not about -14")
    if peak > -1.0:
        out.append(f"true peak {peak} dB is above -1 dB")
    return out


def metadata_problems(config_path, notes_path):
    """The cover/banner title must also be the YouTube title and description line 1."""
    cfg = json.load(open(config_path, encoding="utf-8"))
    title = cfg.get("cover_title") or {}
    expected = " ".join(filter(None, (title.get("top_line"), title.get("bottom_line"))))
    if not expected:
        return ["config has no shared cover_title"]
    notes = open(notes_path, encoding="utf-8").read()

    def section(name):
        match = re.search(rf"(?ms)^## {re.escape(name)}\s*\n(.*?)(?=^## |\Z)", notes)
        if not match:
            return None
        return next((line.strip() for line in match.group(1).splitlines() if line.strip()), None)

    out = []
    if section("Title") != expected:
        out.append(f"YouTube title must equal cover title exactly: {expected!r}")
    if section("Description") != expected:
        out.append(f"YouTube description first line must equal cover title exactly: {expected!r}")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video"); ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--layout", help="NAME_layout.json from build_fullbleed.py (default: next to the video)")
    ap.add_argument("--config", help="Short config containing the shared cover_title")
    ap.add_argument("--youtube-notes", help="youtube-שורט-NN.md; checked against --config")
    ap.add_argument("--words", help="captions.json, words.json or .srt on the cut timeline (default: NAME.srt or captions.json next to the video)")
    a = ap.parse_args()
    if bool(a.config) != bool(a.youtube_notes):
        ap.error("--config and --youtube-notes must be given together")
    d, lufs, peak = probe(a.video)
    strip = re.sub(r"\.[^.]+$", "", a.video) + "_strip.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-vf", f"fps={a.frames}/{d:.3f},scale=270:480,tile={a.frames}x1",
                    "-frames:v", "1", strip], check=True)
    print(f"{a.video}: {d:.2f} s, {lufs} LUFS, peak {peak} dB -> {strip}")
    lay_path = a.layout or re.sub(r"\.[^.]+$", "", a.video) + "_layout.json"
    lay = json.load(open(lay_path)) if os.path.exists(lay_path) else None
    silent_endcard = float(lay.get("silent_endcard_seconds", 0.0)) if lay else 0.0
    bad = problems(d, lufs, peak) + opening_problems(
        d, luma(a.video, 0), luma(a.video, min(0.5, d / 2)), silences(a.video), silent_endcard)
    if lay is not None:
        print(f"layout: caption_y {lay.get('caption_y')}, hook_y {lay.get('hook_y')} ({lay.get('hook_style')})")
        bad += layout_problems(lay)
    elif a.layout:
        bad.append(f"layout file {a.layout} not found")
    if a.config:
        bad += metadata_problems(a.config, a.youtube_notes)
    src, opening = find_opening_words(a.video, a.words)
    if opening is None:
        bad.append("no captions/words/srt for the opening; pass --words or keep NAME.srt next to the video")
    else:
        print(f"opening words: {src}")
        fails, warns = opening_word_review(opening)
        bad += fails
        for p in warns:
            print("warning:", p)
    for p in bad:
        print("warning:", p)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
