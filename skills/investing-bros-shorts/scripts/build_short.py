#!/usr/bin/env python3
"""Build one branded vertical short from an edit decision list (JSON).

Usage:
    python3 build_short.py short.json [--out-dir DIR] [--speed 1.25]

Writes NAME.ass (captions + headline + name tag + end card), NAME.srt (same
captions, for the platform's own subtitle field) and NAME.sh (the ffmpeg
command). Run NAME.sh from a folder that holds the source, the frame PNG and
the fonts folder.

short.json (times are seconds on the SOURCE timeline):
{
  "name": "short1_swift",
  "title": "metadata title",
  "source": "raw.mp4",            # side-by-side recording (Riverside layout)
  "source_layout": "split",       # "split": left/right halves are the two hosts; "full": whole frame
  "fps": 24,                      # the source frame rate (cuts snap to its frame grid)
  "frame": "frame_vertical.png",  # from brand.py frame vertical
  "fonts": "fonts",               # folder with static Heebo weights (brand.py fonts)
  "pieces": [[843.69, 864.40], [866.48, 871.45, 0.0]],   # kept ranges in PLAY order, optional gain dB per piece;
                                                         # may open on a later line (moved, never repeated)
  "shots": [[843.69, 871.45, "L"]],                      # which host fills the frame (L/R), by source time
  "headline": ["סוויפט היא בכלל", "[לא מערכת תשלומים]"],  # fixed hook text under the logo; [..] = gold accent
  "endcard": ["בפרק המלא: למה טוקניזציה", "[אחים להשקעות]"],  # last seconds; name what the episode adds
  "tags": [[843.69, 847.2, "אמיתי רסקין"]],              # name tag on the video
  "cards": [[843.69, 845.35, "אתה רוצה להעביר כסף|מישראל לארצות הברית —"]],  # | = line break
  "audio": "highpass=f=80,acompressor=threshold=0.06:ratio=2.5:attack=15:release=250:makeup=1.5"
}

Captions: max two lines per card, short lines (~24 characters), proofread
against the audio. Cut pieces at pauses, never mid-word.
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brand import ACCENT, FONT_BLACK, FONT_EXTRABOLD, FONT_SEMIBOLD, VERTICAL, WHITE, ass_colour  # noqa: E402
from clip_captions import rtl  # noqa: E402

EM, WH = "{\\c&H" + ass_colour(ACCENT)[4:] + "&}", "{\\c&H" + ass_colour(WHITE)[4:] + "&}"
VIDEO_H = {"split": 1215, "full": 608}   # 960x1080 half -> 1080x1215; 1920x1080 -> 1080x608
MAX_LINE = 26
DEFAULT_SPEED = 1.15  # house speed (Amitai, 2026-10-26; was 1.25)


def playback_speed(value) -> float:
    """Validate a pitch-preserving playback-speed multiplier."""
    speed = float(value)
    if not math.isfinite(speed) or not 0.5 <= speed <= 2.0:
        raise ValueError("speed must be a finite number between 0.5 and 2.0")
    return speed


def speed_arg(value: str) -> float:
    try:
        return playback_speed(value)
    except (TypeError, ValueError) as e:
        raise argparse.ArgumentTypeError(str(e)) from e


def snap(t: float, fps: float) -> float:
    return round(t * fps) / fps


def highlight(s: str) -> str:
    return s.replace("[", EM).replace("]", WH)


def ass_time(t: float) -> str:
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


class Timeline:
    """Maps source time to output time across the kept pieces."""

    def __init__(self, pieces, fps, speed=1.0):
        self.speed = playback_speed(speed)
        self.pieces = [(snap(p[0], fps), snap(p[1], fps)) for p in pieces]
        self.gains = [float(p[2]) if len(p) > 2 else 0.0 for p in pieces]
        for (a, b) in self.pieces:
            if b <= a:
                raise ValueError(f"piece {a}-{b} is empty")
        # Pieces may be reordered (open on the strongest line), but never repeated:
        # a source time inside two pieces would map to the wrong one.
        spans = sorted(self.pieces)
        for (a1, b1), (a2, b2) in zip(spans, spans[1:]):
            if a2 < b1:
                raise ValueError(f"pieces {a1}-{b1} and {a2}-{b2} overlap; move a line, don't repeat it")
        self.duration = sum(b - a for a, b in self.pieces) / self.speed

    def map(self, t: float) -> float:
        out = 0.0
        for a, b in self.pieces:
            if a - 0.05 <= t <= b + 0.05:
                return min(max(out + (t - a) / self.speed, out), out + (b - a) / self.speed)
            out += (b - a) / self.speed
        raise ValueError(f"time {t} is not inside any piece")


def close_gaps(cards, max_gap=0.35):
    """Back-to-back cards: fill tiny gaps (no flicker) and remove overlaps."""
    cards = [list(c) for c in cards]
    for i in range(len(cards) - 1):
        gap = cards[i + 1][0] - cards[i][1]
        if 0 < gap < max_gap or gap < 0:
            cards[i][1] = cards[i + 1][0]
    return cards


LENGTH_TARGET = (20, 45)   # seconds; shorter shorts finish more often
LENGTH_LIMIT = (15, 60)
GENERIC_ENDCARDS = {"לפרק המלא", "השיחה ממשיכה בפרק המלא", "הפרק המלא", "לצפייה בפרק המלא"}


def check_packaging(cfg, duration, hook_key):
    """Warnings for the length, the opening hook and the end card of one short."""
    out = []
    lo, hi = LENGTH_TARGET
    if not LENGTH_LIMIT[0] <= duration <= LENGTH_LIMIT[1]:
        out.append(f"{duration:.1f} s is outside {LENGTH_LIMIT[0]}–{LENGTH_LIMIT[1]} s")
    elif not lo <= duration <= hi:
        out.append(f"{duration:.1f} s is outside the {lo}–{hi} s target; say why in the hand-back")
    if not cfg.get(hook_key):
        out.append(f"no '{hook_key}': the first frame needs the hook on screen")
    end = cfg.get("endcard") or []
    first = end[0].strip("[]").strip() if end else ""
    if not end:
        out.append("no 'endcard': point viewers to the full episode")
    elif first in GENERIC_ENDCARDS:
        out.append(f"end card '{first}' is generic; name what the episode adds, e.g. 'בפרק המלא: למה סין קונה זהב'")
    return out


def check_cards(cards):
    warnings = []
    for _, _, text in cards:
        lines = text.split("|")
        if len(lines) > 2:
            warnings.append(f"more than two lines: {text}")
        for line in lines:
            if len(line.replace("[", "").replace("]", "")) > MAX_LINE:
                warnings.append(f"line longer than {MAX_LINE} characters: {line}")
    return warnings


def build_ass(cfg, tl: Timeline) -> tuple:
    L = VERTICAL
    font = cfg.get("font_bold", FONT_EXTRABOLD)
    head_font = cfg.get("font_black", FONT_BLACK)
    tag_font = cfg.get("font_semibold", FONT_SEMIBOLD)
    deep = ass_colour((14, 61, 96))  # dark blue box behind the name tag
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{font},70,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,5,3,2,{L['caption_margin_l']},{L['caption_margin_r']},{L['caption_margin_v']},-1
Style: Head,{head_font},76,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,8,60,60,{L['headline_margin_v']},-1
Style: Tag,{tag_font},38,&H00FFFFFF,&H00FFFFFF,{deep},{deep},0,0,0,0,100,100,0,0,3,10,0,9,40,40,{L['video_y'] + 30},-1
Style: End,{font},64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,8,60,60,{L['headline_margin_v'] + 8},-1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def lines(items):
        return "\\N".join(highlight(rtl(x)) for x in items)

    dur = tl.duration
    end_t = max(0.0, dur - float(cfg.get("end_card_seconds", 2.8)))
    ev = [f"Dialogue: 1,{ass_time(0)},{ass_time(end_t)},Head,,0,0,0,,{{\\fad(150,200)}}{lines(cfg['headline'])}"]
    if cfg.get("endcard"):
        ev.append(f"Dialogue: 1,{ass_time(end_t)},{ass_time(dur)},End,,0,0,0,,{{\\fad(200,0)}}{lines(cfg['endcard'])}")
    for a, b, name in cfg.get("tags", []):
        ev.append(f"Dialogue: 2,{ass_time(tl.map(a))},{ass_time(tl.map(b))},Tag,,0,0,0,,{{\\fad(150,150)}}{rtl(name)}")
    cards = close_gaps([(tl.map(a), tl.map(b), t) for a, b, t in cfg["cards"]])
    for s, e, text in cards:
        ev.append(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},Sub,,0,0,0,,{lines(text.split('|'))}")
    return head + "\n".join(ev) + "\n", cards


def build_srt(cards) -> str:
    out = []
    for i, (s, e, text) in enumerate(cards, 1):
        body = "\n".join(rtl(x.replace("[", "").replace("]", "")) for x in text.split("|"))
        out.append(f"{i}\n{srt_time(s)} --> {srt_time(e)}\n{body}\n")
    return "\n".join(out)


def build_command(cfg, tl: Timeline) -> str:
    name, src, fps = cfg["name"], cfg.get("source", "raw.mp4"), cfg.get("fps", 24)
    layout = cfg.get("source_layout", "split")
    P, n = tl.pieces, len(tl.pieces)
    S = P[0][0] - 1.0 if P[0][0] >= 1.0 else 0.0
    T = max(b for _, b in P) - S + 1.0
    if min(a for a, _ in P) < S:
        raise ValueError("pieces must be in source order for one input seek; split into two shorts otherwise")
    vs = f"[0:v]split={n}" + "".join(f"[v{i}]" for i in range(n)) + ";" if n > 1 else "[0:v]null[v0];"
    pts_audio = "aresample=async=1:min_hard_comp=0.01:first_pts=0"
    as_ = (
        f"[0:a]{pts_audio},asplit={n}" + "".join(f"[a{i}]" for i in range(n)) + ";"
        if n > 1 else f"[0:a]{pts_audio}[a0];"
    )
    vt = "".join(f"[v{i}]trim=start={a - S:.4f}:end={b - S:.4f},setpts=PTS-STARTPTS[t{i}];" for i, (a, b) in enumerate(P))
    at = "".join(
        f"[a{i}]atrim=start={a - S:.4f}:end={b - S:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,"
        f"afade=t=out:st={b - a - 0.015:.4f}:d=0.015,volume={tl.gains[i]}dB[u{i}];" for i, (a, b) in enumerate(P))
    cv = "".join(f"[t{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[vc0];"
    ca = "".join(f"[u{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[ac0];"
    speed = f"{tl.speed:g}"
    if tl.speed == 1.0:
        tempo = "[vc0]null[vc];[ac0]anull[ac];"
    else:
        tempo = f"[vc0]setpts=PTS/{speed}[vc];[ac0]atempo={speed}[ac];"
    vh, vy = VIDEO_H[layout], VERTICAL["video_y"]
    if layout == "split":
        crops = {"L": "crop=iw/2:ih:0:0", "R": "crop=iw/2:ih:iw/2:0"}
        base = cfg.get("base", "L")
        other = "R" if base == "L" else "L"
        en = "+".join(f"between(t,{tl.map(a):.3f},{tl.map(b):.3f})" for a, b, side in cfg["shots"] if side == other) or "0"
        vf = (f"[vc]split[x1][x2];[x1]{crops[base]},scale=1080:{vh}:flags=lanczos[B];"
              f"[x2]{crops[other]},scale=1080:{vh}:flags=lanczos[O];"
              f"[1:v]loop=-1:1:0,fps={fps},trim=duration={tl.duration:.4f},setpts=PTS-STARTPTS,format=yuv420p[bg];"
              f"[bg][B]overlay=0:{vy}:shortest=1[y1];[y1][O]overlay=0:{vy}:enable='{en}'[y2];")
    else:
        vf = (f"[vc]scale=1080:{vh}:flags=lanczos[B];"
              f"[1:v]loop=-1:1:0,fps={fps},trim=duration={tl.duration:.4f},setpts=PTS-STARTPTS,format=yuv420p[bg];"
              f"[bg][B]overlay=0:{vy + (1215 - vh) // 2}:shortest=1[y2];")
    vf += f"[y2]ass={name}.ass:fontsdir={cfg.get('fonts', 'fonts')},format=yuv420p[vout];"
    audio = cfg.get("audio", "highpass=f=80,acompressor=threshold=0.06:ratio=2.5:attack=15:release=250:makeup=1.5")
    af = (f"[ac]{audio},loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000,"
          "aformat=sample_fmts=fltp:channel_layouts=stereo[aout]")
    title = cfg.get("title", name).replace('"', "'")
    return (f'ffmpeg -v error -y -ss {S:.3f} -t {T:.3f} -i "{src}" -i "{cfg.get("frame", "frame_vertical.png")}" '
            f'-filter_complex "{vs}{as_}{vt}{at}{cv}{ca}{tempo}{vf}{af}" -map "[vout]" -map "[aout]" '
            f"-c:v libx264 -preset medium -crf 18 -profile:v high -pix_fmt yuv420p -r {fps} "
            f'-c:a aac -b:a 192k -movflags +faststart -metadata title="{title}" "{name}.mp4"\n')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--speed", type=speed_arg, default=DEFAULT_SPEED,
                    help=f"video/audio playback speed (default: {DEFAULT_SPEED}; 1.0 disables)")
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8"))
    tl = Timeline(cfg["pieces"], cfg.get("fps", 24), a.speed)
    ass, cards = build_ass(cfg, tl)
    base = os.path.join(a.out_dir, cfg["name"])
    open(base + ".ass", "w", encoding="utf-8").write(ass)
    open(base + ".srt", "w", encoding="utf-8").write(build_srt(cards))
    open(base + ".sh", "w", encoding="utf-8").write(build_command(cfg, tl))
    print(f"{cfg['name']}: {tl.duration:.2f} s at {tl.speed:g}x, "
          f"{len(tl.pieces)} piece(s), {len(cards)} caption card(s)")
    for w in check_packaging(cfg, tl.duration, "headline"):
        print("warning:", w)
    for w in check_cards(cfg["cards"]):
        print("warning:", w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
