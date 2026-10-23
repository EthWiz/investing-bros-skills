#!/usr/bin/env python3
"""House style (episode 7 "option D" base): full-screen host, word-by-word gold captions.

Usage:
    python3 build_fullbleed.py short.json [--out-dir DIR] [--speed 1.25]
                                                               # writes NAME_fb.ass, NAME_grad.png, NAME_fb.sh
    bash NAME_fb.sh                                         # run where source, logo.png and fonts/ are

The output (1080x1920, keyframe every second) is a finished short, and also the
input video for a HyperFrames overlay with 1-2 animated explainer panels
(the HyperFrames render, references/hyperframes.md). Times are on the SOURCE timeline.

short.json:
{
  "name": "short3_asteroid", "source": "raw.mp4", "fps": 24,
  "pieces": [[2106.02, 2154.45, 0.0]],          # kept ranges in PLAY order (may open on a later line; never repeat one), optional gain dB
  "base": "R", "shots": [[2140.0, 2141.5, "L"]], # who fills the screen; shots = cuts to the other host (reactions)
  "crop_x": {"L": 176, "R": 170},               # x of the 608-px 9:16 crop inside each 960-px half (face_crop.py suggests it)
  "sources": {"L": "amitai.mp4", "R": "nadav.mp4"},   # optional: each host's own high-res Riverside track
  "crop": {"L": [656, 0, 1215, 2160]},          # optional: crop box per side in that source's pixels (x, y, w, h)
  "audio_source": "raw.mp4",                    # optional: audio file on the same timeline (default: source)
  "tags": [[2106.05, 2109.5, "נדב רסקין"]],      # name tag (top right)
  "words": "aligned.json",                      # from align_words.py (proofread caption text + whisper timing)
  "hook": ["למה לסייברקאב", "אין הגה?"],       # first ~2.7 s: ONE idea, as short as possible (<= ~6 words)
  "hook_style": "strips",                       # default: cream/mustard torn-paper strips, navy type (brand);
                                                # "legacy" = the old white/gold ASS hook (rebuilding old exports only)
  "hook_y": 960, "caption_y": 1290,             # centre y; bounds brand.HOOK_Y_BOUNDS / CAPTION_Y_BOUNDS.
                                                # brief hook -> centre of frame, padded below the logo and above
                                                # the captions; captions under the chin (face_crop.py suggests)
  "zooms": [[2114.5, 1.13], [2119.0, 1.0]],     # punch-ins: from this source time, this zoom (1.0 = none)
  "endcard": ["בפרק המלא: למה דווקא זהב?", "[אחים להשקעות · פרק 7]", "הקישור לפרק כאן למעלה"],
  "endcard_style": "cover",                     # optional: end card in the cover-art look (navy paper, logo, פרק N pill,
                                                # endcard = [title with |, "פרק N", link line], bobbing arrow); default "text"
  "endcard_at": 2150.3,                         # optional: source time the end card starts (default: last 2.8 s)
  "endcard_captions": true,                     # cover style: keep burning the captions over the card (payoff stays readable)
  "endcard_arrow": true,                        # optional: mustard down arrow under the end card (link in the description)
  "callouts": [{"at": 2131.9, "text": "הקישור לפרק המלא בתיאור", "dur": 2.2, "bottom": 1350, "bob": 7}],
                                                # optional: a paper-strip "look down" callout with a mustard arrow,
                                                # fades in, bobs ~2x/s, fades out; "at" = source time, or
                                                # "before_endcard": 4.0 = from 4 s before the end card, crossfading into it
  "logo": "logo.png", "fonts": "fonts"
}
[..] = gold in captions. Captions: 2-3 words at a time, the spoken word gold, centre at
caption_y (default 1290, allowed 1100-1470: above the Reels/Shorts UI). The hook is drawn
by brand.hook_strips into NAME_hook.png and overlaid for the first 2.7 s, so it never looks
like a caption. Logo top-left (56,150), 210 px wide. Also writes NAME.srt from "cards" for
the platform's subtitle field, and NAME_layout.json (caption_y, hook_y, hook box) that
check_short.py checks against the bounds. Check the export with check_short.py.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brand import (ACCENT, ARROW_ASS, arrow_png, endcard_cover, CALLOUT, JOURNAL_MUSTARD, JOURNAL_NAVY, callout_strip, CAPTION_HALF, CAPTION_Y_BOUNDS, CAPTION_Y_DEFAULT, FONT_BLACK,  # noqa: E402
                   FONT_EXTRABOLD, HOOK_GAP, HOOK_Y_BOUNDS, HOOK_Y_DEFAULT, LOGO_BOX, ass_colour,
                   hook_strips)
from build_short import DEFAULT_SPEED, Timeline, ass_time, build_srt, check_packaging, close_gaps, speed_arg  # noqa: E402
from clip_captions import rtl  # noqa: E402

GOLD = ACCENT
G = "{\\c" + ass_colour(GOLD) + "}"
W = "{\\c&H00FFFFFF}"
LEGACY_HOOK_Y, END_S, HOOK_S, XFADE = 700, 2.8, 2.7, 0.3


def endcard_start(cfg, tl):
    """Output time the end card starts: endcard_at (source time) or the last END_S seconds."""
    if cfg.get("endcard_at") is not None:
        return tl.map(cfg["endcard_at"])
    return max(0.0, tl.duration - END_S)
AUDIO = ("highpass=f=80,acompressor=threshold=0.06:ratio=2.5:attack=15:release=250:makeup=1.5,"
         "loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo")


def gold(s):
    return rtl(s).replace("[", G).replace("]", W)


def layout(cfg):
    """Caption and hook positions for this short, checked against the brand bounds."""
    style = cfg.get("hook_style", "strips")
    if style not in ("strips", "legacy"):
        raise ValueError(f"hook_style must be 'strips' or 'legacy', not {style!r}")
    cap_y = cfg.get("caption_y", CAPTION_Y_DEFAULT)
    hook_y = cfg.get("hook_y", HOOK_Y_DEFAULT if style == "strips" else LEGACY_HOOK_Y)
    lo, hi = CAPTION_Y_BOUNDS
    if not lo <= cap_y <= hi:
        raise ValueError(f"caption_y {cap_y} is outside {lo}-{hi} (platform UI below, hook band above)")
    lo, hi = HOOK_Y_BOUNDS
    if style == "strips" and not lo <= hook_y <= hi:
        raise ValueError(f"hook_y {hook_y} is outside the top band {lo}-{hi}")
    return {"hook_style": style, "caption_y": cap_y, "hook_y": hook_y}


def hook_box_problems(box, caption_y):
    """The drawn hook block must keep HOOK_GAP clear below the logo and above the captions."""
    out = []
    if box[0] < LOGO_BOX[3] + HOOK_GAP:
        out.append(f"hook starts at y={box[0]}: keep {HOOK_GAP} px below the logo (bottom {LOGO_BOX[3]})")
    if box[1] > caption_y - CAPTION_HALF - HOOK_GAP:
        out.append(f"hook ends at y={box[1]}: keep {HOOK_GAP} px above the captions (caption_y {caption_y})")
    return out


def callout_windows(cfg, tl):
    """[(start, end)] output time of each callout."""
    out, end = [], endcard_start(cfg, tl)
    for c in cfg.get("callouts", []):
        if "before_endcard" in c:
            out.append((end - c["before_endcard"], end + XFADE))      # hands over to the end card
        else:
            out.append((tl.map(c["at"]), tl.map(c["at"]) + c.get("dur", 2.2)))
    return out


def callout_problems(box, window, caption_y, end_start):
    """A callout must sit between the logo and the captions (with HOOK_GAP) and never over the hook or end card."""
    out = []
    if box[0] < LOGO_BOX[3] + HOOK_GAP or box[1] > caption_y - CAPTION_HALF - HOOK_GAP:
        out.append(f"callout y {box[0]}-{box[1]} needs {HOOK_GAP} px clear of the logo and the captions (caption_y {caption_y})")
    if window[0] < HOOK_S or window[1] > end_start + XFADE + 0.01:
        out.append(f"callout {window[0]:.2f}-{window[1]:.2f} s overlaps the hook (0-{HOOK_S}) or the end card")
    return out


def captions_over_card(cfg):
    """Cover end card with endcard_captions: the last line's captions keep running on top of the card."""
    return bool(cfg.get("endcard")) and cfg.get("endcard_style", "text") == "cover" and cfg.get("endcard_captions", False)


def build_ass(cfg, tl, chunks, over_card=False):
    """The burned-in ASS. over_card=True gives only the captions after the end card starts
    (burned after the cover card overlay, so the payoff stays readable)."""
    lay = layout(cfg)
    CAP_Y, HOOK_Y = lay["caption_y"], lay["hook_y"]
    dur = tl.duration
    end_t = endcard_start(cfg, tl)
    st = ("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, "
          "StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
          f"Style: Cap,{FONT_BLACK},100,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,8,3,5,60,60,0,-1\n"
          f"Style: Hook,{FONT_BLACK},118,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,9,4,5,60,60,0,-1\n"
          f"Style: End,{FONT_BLACK},84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,6,0,5,60,60,0,-1\n"
          f"Style: Tag,{FONT_EXTRABOLD},38,&H000B1006,&H000B1006,{ass_colour(GOLD)},{ass_colour(GOLD)},0,0,0,0,100,100,0,0,3,12,0,9,40,40,0,-1\n"
          f"Style: Dim,{FONT_BLACK},20,&H00000000,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,-1\n")
    out = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
           "[V4+ Styles]\n" + st + "\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    ev = lambda layer, s, e, style, txt: f"Dialogue: {layer},{ass_time(s)},{ass_time(e)},{style},,0,0,0,,{txt}\n"
    if cfg.get("hook") and lay["hook_style"] == "legacy":
        out += ev(5, 0, HOOK_S, "Hook", f"{{\\pos(540,{HOOK_Y})\\fscx70\\fscy70\\t(0,180,\\fscx100\\fscy100)\\fad(0,200)}}"
                  + "\\N".join(gold(x) for x in cfg["hook"]))
    lo, hi = (end_t, dur) if over_card else (0.0, end_t)
    for chunk in chunks:
        gs, ge = max(tl.map(chunk[0]["s"]), lo), min(tl.map(chunk[-1]["e"]), hi)
        if ge <= gs:
            continue
        for j, w in enumerate(chunk):
            s = tl.map(w["s"]) if j else gs
            e = tl.map(chunk[j + 1]["s"]) if j + 1 < len(chunk) else ge
            if e <= s:
                continue
            on = "{\\c" + ass_colour(GOLD) + ("\\fscx112\\fscy112" if w["key"] else "") + "}"
            off = "{\\c&H00FFFFFF\\fscx100\\fscy100}"
            parts = [on + rtl(x["w"]) + off if k == j else rtl(x["w"]) for k, x in enumerate(chunk)]
            pop = "\\fscx82\\fscy82\\t(0,90,\\fscx100\\fscy100)" if j == 0 and not (over_card and s <= lo + 0.01) else ""
            out += ev(1, s, e, "Cap", f"{{\\pos(540,{CAP_Y}){pop}}}" + " ".join(parts))
    if over_card:
        return out
    for a, b, name in cfg.get("tags", []):
        out += ev(4, tl.map(a), min(tl.map(b), end_t), "Tag", "{\\an9\\pos(1024,178)\\fad(150,150)}" + rtl(name))
    if cfg.get("endcard") and cfg.get("endcard_style", "text") == "text":
        out += ev(5, end_t, dur, "Dim", "{\\pos(0,0)\\an7\\c&H000000&\\alpha&H50&\\fad(250,0)\\p1}m 0 0 l 1080 0 1080 1920 0 1920{\\p0}")
        lines = [gold(x) for x in cfg["endcard"]]
        if len(lines) > 2:
            lines[2] = "{\\fs56}" + lines[2]
        out += ev(6, end_t, dur, "End", "{\\pos(540,900)\\fad(250,0)}" + "\\N".join(lines))
        if cfg.get("endcard_arrow"):
            arrow = (f"{{\\an8\\pos(540,{900 + 34 * len(lines) + 40})\\fad(250,0)\\1c{ass_colour(JOURNAL_MUSTARD)}"
                     f"\\3c{ass_colour(JOURNAL_NAVY)}\\bord3\\shad0\\p1}}{ARROW_ASS}{{\\p0}}")
            out += ev(6, end_t, dur, "End", arrow)
    return out


def make_gradient(path):
    import numpy as np
    from PIL import Image
    y = np.arange(1920)[:, None]
    a = np.where(y < 420, 0.55 * (1 - y / 420), 0) + np.where(y > 1050, 0.62 * np.clip((y - 1050) / 600, 0, 1), 0)
    img = np.dstack([np.zeros((1920, 1080))] * 3 + [np.repeat(a, 1080, 1) * 255]).astype(np.uint8)
    Image.fromarray(img, "RGBA").save(path)


def sides(cfg):
    """(base side, [(start, end, side)] cuts to the other host) — also reads the old per-piece side."""
    legacy = [p[3] for p in cfg["pieces"] if len(p) > 3]
    base = cfg.get("base") or (legacy[0] if legacy else "L")
    shots = [tuple(x) for x in cfg.get("shots", [])]
    shots += [(p[0], p[1], p[3]) for p in cfg["pieces"] if len(p) > 3 and p[3] != base]
    return base, [x for x in shots if x[2] != base]


def crop_box(cfg, side):
    if side in cfg.get("crop", {}):
        return cfg["crop"][side]
    cx = cfg.get("crop_x", {}).get(side, 176)
    return [cx + (960 if side == "R" else 0), 0, 608, 1080]


def build_command(cfg, tl):
    name, fps = cfg["name"], cfg.get("fps", 24)
    src = cfg.get("source", "raw.mp4")
    base, shots = sides(cfg)
    other = "R" if base == "L" else "L"
    used = [base] + ([other] if shots else [])
    srcs = {sd: cfg.get("sources", {}).get(sd, src) for sd in used}
    asrc = cfg.get("audio_source", src)
    files = list(dict.fromkeys([srcs[sd] for sd in used] + [asrc]))
    idx = {f: i for i, f in enumerate(files)}
    P = tl.pieces
    gains = tl.gains
    S = max(0.0, min(a for a, _ in P) - 1.0)     # earliest piece: the opening may be a later line
    T = max(b for _, b in P) - S + 1.0
    n = len(P)
    uses = {}
    for sd in used:
        uses[(idx[srcs[sd]], "v")] = uses.get((idx[srcs[sd]], "v"), 0) + n
    uses[(idx[asrc], "a")] = n
    f, taken = "", {}
    for (i, kind), k in uses.items():
        source_filter = "null" if kind == "v" else "aresample=async=1:min_hard_comp=0.01:first_pts=0"
        split_filter = "split" if kind == "v" else "asplit"
        f += (
            f"[{i}:{kind}]{source_filter},{split_filter}={k}"
            + "".join(f"[{kind}{i}_{j}]" for j in range(k)) + ";"
        ) if k > 1 else f"[{i}:{kind}]{source_filter}[{kind}{i}_0];"
    def take(i, kind):
        j = taken.get((i, kind), 0)
        taken[(i, kind)] = j + 1
        return f"[{kind}{i}_{j}]"
    for sd in used:
        x, y, w, h = crop_box(cfg, sd)
        for k, (a, b) in enumerate(P):
            f += (f"{take(idx[srcs[sd]], 'v')}trim=start={a - S:.4f}:end={b - S:.4f},setpts=PTS-STARTPTS,"
                  f"crop={w}:{h}:{x}:{y},scale=1080:1920:flags=lanczos,setsar=1[{sd}{k}];")
        f += "".join(f"[{sd}{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=0[V{sd}0];"
        f += f"[V{sd}0]{'null' if tl.speed == 1.0 else f'setpts=PTS/{tl.speed:g}'}[V{sd}];"
    for k, (a, b) in enumerate(P):
        f += (f"{take(idx[asrc], 'a')}atrim=start={a - S:.4f}:end={b - S:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,"
              f"afade=t=out:st={b - a - 0.015:.4f}:d=0.015,volume={gains[k]}dB[a{k}];")
    f += "".join(f"[a{k}]" for k in range(n)) + f"concat=n={n}:v=0:a=1[ac0];"
    f += f"[ac0]{'anull' if tl.speed == 1.0 else f'atempo={tl.speed:g}'}[ac];"
    if shots:
        en = "+".join(f"between(t,{tl.map(a):.3f},{tl.map(b):.3f})" for a, b, _ in shots)
        f += f"[V{base}][V{other}]overlay=0:0:enable='{en}'[vc];"
    else:
        f += f"[V{base}]null[vc];"
    z = "1.0"
    for t, zz in sorted(cfg.get("zooms", []), key=lambda x: tl.map(x[0])):   # latest OUTPUT time ends up outermost
        z = f"if(gte(it,{tl.map(t):.3f}),{zz},{z})"
    g, lg, hk = len(files), len(files) + 1, len(files) + 2
    strips = bool(cfg.get("hook")) and layout(cfg)["hook_style"] == "strips"
    hook = (f"[s];[{hk}:v]format=rgba,fade=t=out:st={HOOK_S - 0.2:.2f}:d=0.2:alpha=1[hk];"
            f"[s][hk]overlay=0:0:eof_action=pass[s0]") if strips else "[s0]"
    ci = hk + (1 if strips else 0)
    co_in = ""
    for k, (c, (t0, t1)) in enumerate(zip(cfg.get("callouts", []), callout_windows(cfg, tl))):
        (cw, ch), d = c.get("size", (800, 172)), t1 - t0
        y0 = c.get("bottom", 1350) - ch
        hook += (f";[{ci + k}:v]format=rgba,fade=t=in:st=0:d={CALLOUT['fade_in']}:alpha=1,"
                 f"fade=t=out:st={d - CALLOUT['fade_out']:.2f}:d={CALLOUT['fade_out']}:alpha=1,setpts=PTS+{t0:.3f}/TB[co{k}];"
                 f"[s{k}][co{k}]overlay=x={540 - cw // 2}:y='{y0}+{c.get('bob', 7)}*sin(2*PI*{CALLOUT['bob_hz']}*(t-{t0:.3f}))'"
                 f":eof_action=pass[s{k + 1}]")
        co_in += f'-loop 1 -framerate {fps} -t {d:.3f} -i "{name}_callout{k}.png" '
    last = len(cfg.get("callouts", []))
    if cfg.get("endcard") and cfg.get("endcard_style", "text") == "cover":
        e0, e1 = endcard_start(cfg, tl), tl.duration
        ei = ci + last
        aw, ah = cfg.get("_arrow_size", (104, 92))
        hook += (f";[{ei}:v]format=rgba,fade=t=in:st=0:d={XFADE}:alpha=1,setpts=PTS+{e0:.3f}/TB[ec];"
                 f"[s{last}][ec]overlay=0:0:eof_action=pass[ecv];"
                 f"[{ei + 1}:v]format=rgba,fade=t=in:st=0:d={XFADE}:alpha=1,setpts=PTS+{e0:.3f}/TB[ea];"
                 f"[ecv][ea]overlay=x={540 - aw // 2}:y='{cfg.get('_arrow_y', 1180)}+7*sin(2*PI*{CALLOUT['bob_hz']}*(t-{e0:.3f}))'"
                 f":eof_action=pass[s{last}e]")
        if captions_over_card(cfg):
            hook += f";[s{last}e]ass={name}_fb_over.ass:fontsdir={cfg.get('fonts', 'fonts')}[s{last}e2]"
            last = f"{last}e2"
        else:
            last = f"{last}e"
        co_in += (f'-loop 1 -framerate {fps} -t {e1 - e0:.3f} -i "{name}_endcard.png" '
                  f'-loop 1 -framerate {fps} -t {e1 - e0:.3f} -i "{name}_arrow.png" ')
    hook += f";[s{last}]format=yuv420p[v];"
    f += (f"[vc]fps={fps},zoompan=z='{z}':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)*0.35':d=1:s=1080x1920:fps={fps},"
          f"eq=contrast=1.05:saturation=1.1[z];[{g}:v]format=rgba[gr];[z][gr]overlay=0:0[g];"
          f"[{lg}:v]scale=210:-1[lg];[g][lg]overlay=56:150[l];[l]ass={name}_fb.ass:fontsdir={cfg.get('fonts', 'fonts')}"
          f"{hook}[ac]{AUDIO}[a]")
    inputs = " ".join(f'-ss {S:.3f} -t {T:.3f} -i "{p}"' for p in files)
    hook_in = f'-loop 1 -framerate {fps} -t {HOOK_S} -i "{name}_hook.png" ' if strips else ""
    return (f'ffmpeg -v error -y {inputs} -i "{name}_grad.png" -i "{cfg.get("logo", "logo.png")}" {hook_in}{co_in}'
            f'-filter_complex "{f}" -map "[v]" -map "[a]" -c:v libx264 -preset veryfast -crf 17 -g {fps} -keyint_min {fps} '
            f'-r {fps} -c:a aac -b:a 192k -movflags +faststart -t {tl.duration:.4f} "{name}.mp4"\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config"); ap.add_argument("--out-dir", default=".")
    ap.add_argument("--speed", type=speed_arg, default=DEFAULT_SPEED,
                    help=f"video/audio playback speed (default: {DEFAULT_SPEED}; 1.0 disables)")
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8"))
    tl = Timeline([p[:3] for p in cfg["pieces"]], cfg.get("fps", 24), a.speed)
    words_path = os.path.join(os.path.dirname(os.path.abspath(a.config)), cfg["words"])
    chunks = json.load(open(words_path, encoding="utf-8"))
    base = os.path.join(a.out_dir, cfg["name"])
    open(base + "_fb.ass", "w", encoding="utf-8").write(build_ass(cfg, tl, chunks))
    if captions_over_card(cfg):
        open(base + "_fb_over.ass", "w", encoding="utf-8").write(build_ass(cfg, tl, chunks, over_card=True))
    fonts_dir = os.path.join(os.path.dirname(os.path.abspath(a.config)), cfg.get("fonts", "fonts"))
    for k, (c, win) in enumerate(zip(cfg.get("callouts", []), callout_windows(cfg, tl))):
        c["size"] = callout_strip(c["text"], f"{base}_callout{k}.png", os.path.join(fonts_dir, "Heebo-Black.ttf"))
    make_gradient(base + "_grad.png")
    lay = layout(cfg)
    if cfg.get("hook") and lay["hook_style"] == "strips":
        font = os.path.join(os.path.dirname(os.path.abspath(a.config)), cfg.get("fonts", "fonts"), "Heebo-Black.ttf")
        lay["hook_box"] = hook_strips(cfg["hook"], base + "_hook.png", font, lay["hook_y"])
        bad = hook_box_problems(lay["hook_box"], lay["caption_y"])
        if bad:
            raise SystemExit("; ".join(bad) + " - move hook_y or shorten the hook")
    lay["callouts"] = []
    for c, win in zip(cfg.get("callouts", []), callout_windows(cfg, tl)):
        b = c.get("bob", 7)
        box = [c.get("bottom", 1350) - c["size"][1] - b, c.get("bottom", 1350) + b]
        bad = callout_problems(box, win, lay["caption_y"], endcard_start(cfg, tl))
        if bad:
            raise SystemExit("; ".join(bad))
        lay["callouts"].append({"window": [round(win[0], 2), round(win[1], 2)], "box": box})
    lay["duration"] = round(tl.duration, 3)
    lay["speed"] = tl.speed
    lay["endcard_start"] = round(endcard_start(cfg, tl), 3)
    if cfg.get("endcard") and cfg.get("endcard_style", "text") == "cover":
        e = cfg["endcard"]
        logo = os.path.join(os.path.dirname(os.path.abspath(a.config)), cfg.get("logo", "logo.png"))
        card = endcard_cover(base + "_endcard.png", os.path.join(fonts_dir, "Heebo-Black.ttf"), logo, e[0], e[1], e[2])
        cfg["_arrow_size"] = arrow_png(base + "_arrow.png")
        cfg["_arrow_y"] = card["bottom"] + 30
        lay["endcard_box"] = [card["box"][0], cfg["_arrow_y"] + cfg["_arrow_size"][1] + 7]
    open(base + "_fb.sh", "w", encoding="utf-8").write(build_command(cfg, tl))
    json.dump(lay, open(base + "_layout.json", "w"))
    if cfg.get("cards"):
        cards = close_gaps([(tl.map(s), tl.map(e), t) for s, e, t in cfg["cards"]])
        open(base + ".srt", "w", encoding="utf-8").write(build_srt(cards))
    print(f"{cfg['name']}: {tl.duration:.2f} s at {tl.speed:g}x, {len(chunks)} caption chunks")
    for w in check_packaging(cfg, tl.duration, "hook"):
        print("warning:", w)


if __name__ == "__main__":
    main()
