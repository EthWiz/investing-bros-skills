#!/usr/bin/env python3
"""Write burned-in Hebrew captions (.ass) for one clip from the episode transcript.

Usage:
    python3 clip_captions.py SEGMENTS.json START END OUT.ass
        [--format vertical|square] [--font-family NAME] [--max-words N]

START / END are seconds on the RAW timeline (the same timeline as segments.json).
Captions are cut to that range, shifted to start at 0, and split into short
chunks (a few words each) timed proportionally to their length.
Style Encoding is -1 (libass then picks the base direction per line; any other
value forces left-to-right and puts Hebrew punctuation on the wrong side). Each
caption gets RLM marks, and English words inside a Hebrew line are wrapped in
LRI/PDI isolates, so "ל־use cases", "So what?" or "NFTs" keep their place.
Proofread the Dialogue lines afterwards — whisper mishears names and numbers.
"""
import argparse
import json
import re
import subprocess
import sys

FORMATS = {
    #           canvas        font  margin_v (px from bottom)  max words per chunk
    "vertical": ((1080, 1920), 72, 400, 6),
    "square":   ((1080, 1080), 60, 70, 7),
}
PREFERRED_FONTS = ("Heebo", "Rubik", "Assistant", "Noto Sans Hebrew", "Arimo",
                   "Liberation Sans", "DejaVu Sans", "FreeSans")


def detect_hebrew_family() -> str:
    try:
        out = subprocess.run(["fc-list", ":lang=he", "family"], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        out = ""
    families = {f.strip() for line in out.splitlines() for f in line.split(",") if f.strip()}
    for name in PREFERRED_FONTS:
        if name in families:
            return name
    if families:
        return sorted(families)[0]
    sys.exit("error: no font with Hebrew found; install Heebo or Rubik, or pass --font-family")


def chunk_segments(segments, start, end, max_words):
    """Yield (t0, t1, text) chunks inside [start, end], shifted so start == 0."""
    for seg in segments:
        s0, s1 = float(seg["start"]), float(seg["end"])
        if s1 <= start or s0 >= end:
            continue
        words = seg["text"].split()
        if not words:
            continue
        groups = [words[i:i + max_words] for i in range(0, len(words), max_words)]
        total = sum(len(" ".join(g)) for g in groups)
        t = s0
        for g in groups:
            text = " ".join(g)
            dt = (s1 - s0) * len(text) / total
            c0, c1 = max(t, start), min(t + dt, end)
            t += dt
            if c1 - c0 >= 0.25:  # drop slivers at the clip edges
                yield round(c0 - start, 2), round(c1 - start, 2), text


RLM = "‏"
LRI, PDI = "⁦", "⁩"
# A run of Latin words (with digits, & ' . - inside), e.g. "use cases", "So what", "S&P 500".
LATIN_RUN = re.compile(r"[A-Za-z][A-Za-z0-9&'’.\-]*(?:\s+[A-Za-z0-9][A-Za-z0-9&'’.\-]*)*")


def rtl(text: str) -> str:
    """Pin a caption to right-to-left. Without this, a line with English and a
    trailing '?' (e.g. 'ו-NVIDIA?') renders with the '?' on the wrong side —
    the same problem as RedCircle. RLM at both ends and after every '?', and
    each Latin run isolated (LRI...PDI) so it can't drag Hebrew around it."""
    t = text.replace(RLM, "").replace(LRI, "").replace(PDI, "")
    if re.search(r"[\u0590-\u05FF]", t):
        t = LATIN_RUN.sub(lambda m: LRI + m.group(0) + PDI, t)
    t = t.replace("?", "?" + RLM)
    return RLM + t + ("" if t.endswith(RLM) else RLM)


def ass_time(t: float) -> str:
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def build_ass(chunks, fmt: str, family: str) -> str:
    (w, h), size, margin_v, _ = FORMATS[fmt]
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{family},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,0,2,90,90,{margin_v},-1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Default,,0,0,0,,{rtl(t.replace('{', '(').replace('}', ')'))}"
             for a, b, t in chunks]
    return head + "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("segments")
    ap.add_argument("start", type=float)
    ap.add_argument("end", type=float)
    ap.add_argument("out")
    ap.add_argument("--format", choices=FORMATS, default="vertical")
    ap.add_argument("--font-family")
    ap.add_argument("--max-words", type=int)
    a = ap.parse_args()
    if a.end <= a.start:
        sys.exit("error: END must be after START")

    segments = json.load(open(a.segments, encoding="utf-8"))
    max_words = a.max_words or FORMATS[a.format][3]
    chunks = list(chunk_segments(segments, a.start, a.end, max_words))
    if not chunks:
        sys.exit("error: no transcript text in that range")
    family = a.font_family or detect_hebrew_family()
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(build_ass(chunks, a.format, family))
    print(f"{len(chunks)} caption chunks, font '{family}' -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
