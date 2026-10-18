#!/usr/bin/env python3
"""House style (episode 7 "option D" base): full-screen host, word-by-word gold captions.

Usage:
    python3 build_fullbleed.py short.json [--out-dir DIR]   # writes NAME_fb.ass, NAME_grad.png, NAME_fb.sh
    bash NAME_fb.sh                                         # run where source, logo.png and fonts/ are

The output (1080x1920, keyframe every second) is a finished short, and also the
input video for a HyperFrames overlay with 1-2 animated explainer panels
(investing-bros-hyperframes). Times are on the SOURCE timeline.

short.json:
{
  "name": "short3_asteroid", "source": "raw.mp4", "fps": 24,
  "pieces": [[2106.02, 2154.45, 0.0]],          # kept ranges in PLAY order, optional gain dB; a payoff line may go
                                                #   first (payoff-first open), pieces must not overlap
  "base": "R", "shots": [[2140.0, 2141.5, "L"]], # who fills the screen; shots = cuts to the other host (reactions)
  "crop_x": {"L": 176, "R": 170},               # x of the 608-px 9:16 crop inside each 960-px half (face_crop.py suggests it)
  "sources": {"L": "amitai.mp4", "R": "nadav.mp4"},   # optional: each host's own high-res Riverside track
  "crop": {"L": [656, 0, 1215, 2160]},          # optional: crop box per side in that source's pixels (x, y, w, h)
  "audio_source": "raw.mp4",                    # optional: audio file on the same timeline (default: source)
  "tags": [[2106.05, 2109.5, "נדב רסקין"]],      # name tag (top right)
  "words": "aligned.json",                      # from align_words.py (proofread caption text + whisper timing)
  "hook": ["אסטרואיד אחד", "[יכול להכפיל]", "[את הזהב בעולם?]"],   # first ~2.7 s, faithful paraphrase
  "hook_s": 2.7,                                # optional: how long the hook title stays
  "zooms": [[2114.5, 1.13], [2119.0, 1.0]],     # punch-ins: from this source time, this zoom (1.0 = none)
  "badge": "מתוך פרק 7",                        # small pill under the logo after the hook, to the end card
  "endcard": ["למה מדינות קונות זהב?", "[בפרק 7 המלא]", "חפשו: אחים להשקעות"],
                                                # open loop the episode really answers, then where; 2-3 lines
  "endcard_s": 2.8,                             # optional: end card length; captions keep running under it
  "logo": "logo.png", "fonts": "fonts"
}
[..] = gold. Captions: 2-3 words at a time, the spoken word gold, centre at y=1290
(above the Reels/Shorts UI). Logo top-left (56,150), 210 px wide. Also writes NAME.srt from
"cards" for the platform's subtitle field. Check the export with check_short.py.

Checks while building: an em or en dash in any on-screen text is an error (show rule);
warnings for a stretch with no visual change (cut, shot or zoom) longer than MAX_STATIC_S,
an end-card line that is too long, and a length outside 30-60 s.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brand import ass_colour  # noqa: E402
from build_short import Timeline, ass_time, build_srt, close_gaps  # noqa: E402
from clip_captions import rtl  # noqa: E402

GOLD = (245, 183, 31)                       # house accent #F5B71F (investing-bros-show)
G = "{\\c" + ass_colour(GOLD) + "}"
W = "{\\c&H00FFFFFF}"
CAP_Y, HOOK_Y, END_S, HOOK_S = 1290, 700, 2.8, 2.7
BADGE_Y = 290                               # top of the "מתוך פרק N" pill: the 210-px logo at (56,150) ends near y=260
MAX_STATIC_S = 6.0                          # longest stretch with no cut, shot change or zoom before a warning
END_LINE = 24                               # characters per end-card line (Heebo Black 84 px on 1080)
DASHES = ("\u2014", "\u2013")              # em / en dash: never on screen (investing-bros-show -> Hebrew)
AUDIO = ("highpass=f=80,acompressor=threshold=0.06:ratio=2.5:attack=15:release=250:makeup=1.5,"
         "loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo")


def gold(s):
    return rtl(s).replace("[", G).replace("]", W)


def on_screen_text(cfg, chunks):
    """Every string that ends up burned into the picture or the .srt."""
    out = list(cfg.get("hook", [])) + list(cfg.get("endcard", [])) + [t for *_, t in cfg.get("tags", [])]
    out += [cfg["badge"]] if cfg.get("badge") else []
    out += [t for *_, t in cfg.get("cards", [])] + [w["w"] for c in chunks for w in c]
    return out


def check_text(cfg, chunks):
    """Errors (list of str) for text that must never be on screen."""
    return [f"dash on screen (use a comma or a plain hyphen): {t}" for t in on_screen_text(cfg, chunks)
            if any(d in t for d in DASHES)]


def visual_changes(cfg, tl):
    """Output times where the picture changes: hook end, jump cuts, shot cuts, zoom steps, end card."""
    ts = {0.0, tl.duration, cfg.get("hook_s", HOOK_S) if cfg.get("hook") else 0.0,
          max(0.0, tl.duration - cfg.get("endcard_s", END_S)) if cfg.get("endcard") else tl.duration}
    out = 0.0
    for a, b in tl.pieces[:-1]:
        out += b - a
        ts.add(out)
    for a, b, _ in sides(cfg)[1]:
        ts.update((tl.map(a), tl.map(b)))
    ts.update(tl.map(t) for t, _ in cfg.get("zooms", []))
    return sorted(ts)


def pacing_warnings(cfg, tl, limit=MAX_STATIC_S):
    ts = visual_changes(cfg, tl)
    return [f"{b - a:.1f} s with no cut, shot change or zoom ({a:.1f}-{b:.1f} s): add a zoom step or a reaction shot"
            for a, b in zip(ts, ts[1:]) if b - a > limit]


def endcard_warnings(cfg):
    lines = cfg.get("endcard", [])
    out = []
    if lines and not 2 <= len(lines) <= 3:
        out.append("end card: use 2-3 lines (open loop, where to find the episode)")
    out += [f"end-card line longer than {END_LINE} characters: {x}" for x in lines
            if len(x.replace("[", "").replace("]", "")) > END_LINE]
    return out


def build_ass(cfg, tl, chunks):
    dur = tl.duration
    end_t = max(0.0, dur - cfg.get("endcard_s", END_S)) if cfg.get("endcard") else dur
    hook_s = cfg.get("hook_s", HOOK_S)
    st = ("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, "
          "StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
          "Style: Cap,Heebo Black,100,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,8,3,5,60,60,0,-1\n"
          "Style: Hook,Heebo Black,118,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,9,4,5,60,60,0,-1\n"
          "Style: End,Heebo Black,84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,6,0,5,60,60,0,-1\n"
          f"Style: Tag,Heebo ExtraBold,38,&H000B1006,&H000B1006,{ass_colour(GOLD)},{ass_colour(GOLD)},0,0,0,0,100,100,0,0,3,12,0,9,40,40,0,-1\n"
          f"Style: Badge,Heebo ExtraBold,44,{ass_colour(GOLD)},{ass_colour(GOLD)},&H400B1006,&H400B1006,0,0,0,0,100,100,0,0,3,12,0,7,0,0,0,-1\n"
          "Style: Dim,Heebo Black,20,&H00000000,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,-1\n")
    out = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
           "[V4+ Styles]\n" + st + "\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    ev = lambda layer, s, e, style, txt: f"Dialogue: {layer},{ass_time(s)},{ass_time(e)},{style},,0,0,0,,{txt}\n"
    if cfg.get("hook"):
        # pops in from 88 %: frame 0 already reads (it is the frame the feed and the YouTube frame picker show)
        out += ev(5, 0, hook_s, "Hook", f"{{\\pos(540,{HOOK_Y})\\fscx88\\fscy88\\t(0,140,\\fscx100\\fscy100)\\fad(0,200)}}"
                  + "\\N".join(gold(x) for x in cfg["hook"]))
    cap_end = dur if cfg.get("endcard_captions", True) else end_t   # the last line stays captioned under the end card
    for chunk in chunks:
        gs, ge = tl.map(chunk[0]["s"]), min(tl.map(chunk[-1]["e"]), cap_end)
        if gs >= cap_end:
            continue
        for j, w in enumerate(chunk):
            s = tl.map(w["s"]) if j else gs
            e = min(tl.map(chunk[j + 1]["s"]) if j + 1 < len(chunk) else ge, cap_end)
            if e <= s:
                continue
            on = "{\\c" + ass_colour(GOLD) + ("\\fscx112\\fscy112" if w["key"] else "") + "}"
            off = "{\\c&H00FFFFFF\\fscx100\\fscy100}"
            parts = [on + rtl(x["w"]) + off if k == j else rtl(x["w"]) for k, x in enumerate(chunk)]
            pop = "\\fscx82\\fscy82\\t(0,90,\\fscx100\\fscy100)" if j == 0 else ""
            out += ev(7, s, e, "Cap", f"{{\\pos(540,{CAP_Y}){pop}}}" + " ".join(parts))
    for a, b, name in cfg.get("tags", []):
        out += ev(4, tl.map(a), min(tl.map(b), end_t), "Tag", "{\\an9\\pos(1024,178)\\fad(150,150)}" + rtl(name))
    if cfg.get("badge"):
        start = hook_s if cfg.get("hook") else 0.0
        if start < end_t:
            out += ev(4, start, end_t, "Badge", f"{{\\an7\\pos(68,{cfg.get('badge_y', BADGE_Y)})\\fad(200,150)}}" + gold(cfg["badge"]))
    if cfg.get("endcard"):
        out += ev(5, end_t, dur, "Dim", "{\\pos(0,0)\\an7\\c&H000000&\\alpha&H50&\\fad(250,0)\\p1}m 0 0 l 1080 0 1080 1920 0 1920{\\p0}")
        lines = [gold(x) for x in cfg["endcard"]]
        if len(lines) > 2:
            lines[2] = "{\\fs56}" + lines[2]
        out += ev(6, end_t, dur, "End", "{\\pos(540,900)\\fad(250,0)}" + "\\N".join(lines))
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
    P = tl.pieces
    gains = tl.gains
    n = len(P)
    # Runs of pieces in source order share one input window per file (split + trim, as before). A piece that
    # plays before earlier source time (payoff-first open) starts a new run with its own seek: one window
    # for everything would make ffmpeg buffer every decoded frame in between (OOM on a real recording).
    runs = [[0]]
    for k in range(1, n):
        (runs[-1].append(k) if P[k][0] >= P[k - 1][1] - 1e-6 else runs.append([k]))
    run_of = {k: r for r, ks in enumerate(runs) for k in ks}
    windows = [(max(0.0, min(P[k][0] for k in ks) - 1.0), max(P[k][1] for k in ks)) for ks in runs]
    inputs = [(r, fl) for r in range(len(runs)) for fl in files]
    idx = {key: i for i, key in enumerate(inputs)}
    uses = {}
    for k in range(n):
        for sd in used:
            key = (idx[(run_of[k], srcs[sd])], "v")
            uses[key] = uses.get(key, 0) + 1
        key = (idx[(run_of[k], asrc)], "a")
        uses[key] = uses.get(key, 0) + 1
    f, taken = "", {}
    for (i, kind), k in uses.items():
        f += (f"[{i}:{kind}]{'split' if kind == 'v' else 'asplit'}={k}" + "".join(f"[{kind}{i}_{j}]" for j in range(k)) + ";") if k > 1 \
            else f"[{i}:{kind}]{'null' if kind == 'v' else 'anull'}[{kind}{i}_0];"
    def take(i, kind):
        j = taken.get((i, kind), 0)
        taken[(i, kind)] = j + 1
        return f"[{kind}{i}_{j}]"
    for sd in used:
        x, y, w, h = crop_box(cfg, sd)
        for k, (a, b) in enumerate(P):
            S = windows[run_of[k]][0]
            f += (f"{take(idx[(run_of[k], srcs[sd])], 'v')}trim=start={a - S:.4f}:end={b - S:.4f},setpts=PTS-STARTPTS,"
                  f"crop={w}:{h}:{x}:{y},scale=1080:1920:flags=lanczos,setsar=1[{sd}{k}];")
        f += "".join(f"[{sd}{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=0[V{sd}];"
    for k, (a, b) in enumerate(P):
        S = windows[run_of[k]][0]
        f += (f"{take(idx[(run_of[k], asrc)], 'a')}atrim=start={a - S:.4f}:end={b - S:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,"
              f"afade=t=out:st={b - a - 0.015:.4f}:d=0.015,volume={gains[k]}dB[a{k}];")
    f += "".join(f"[a{k}]" for k in range(n)) + f"concat=n={n}:v=0:a=1[ac];"
    if shots:
        en = "+".join(f"between(t,{tl.map(a):.3f},{tl.map(b):.3f})" for a, b, _ in shots)
        f += f"[V{base}][V{other}]overlay=0:0:enable='{en}'[vc];"
    else:
        f += f"[V{base}]null[vc];"
    z = "1.0"
    for t, zz in sorted(cfg.get("zooms", []), key=lambda x: tl.map(x[0])):   # latest OUTPUT time ends up outermost
        z = f"if(gte(it,{tl.map(t):.3f}),{zz},{z})"
    g, lg = len(inputs), len(inputs) + 1
    f += (f"[vc]fps={fps},zoompan=z='{z}':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)*0.35':d=1:s=1080x1920:fps={fps},"
          f"eq=contrast=1.05:saturation=1.1[z];[{g}:v]format=rgba[gr];[z][gr]overlay=0:0[g];"
          f"[{lg}:v]scale=210:-1[lg];[g][lg]overlay=56:150[l];[l]ass={name}_fb.ass:fontsdir={cfg.get('fonts', 'fonts')},format=yuv420p[v];"
          f"[ac]{AUDIO}[a]")
    ins = " ".join(f'-ss {windows[r][0]:.3f} -t {windows[r][1] - windows[r][0] + 1.0:.3f} -i "{fl}"' for r, fl in inputs)
    return (f'ffmpeg -v error -y {ins} -i "{name}_grad.png" -i "{cfg.get("logo", "logo.png")}" '
            f'-filter_complex "{f}" -map "[v]" -map "[a]" -c:v libx264 -preset veryfast -crf 17 -g {fps} -keyint_min {fps} '
            f'-r {fps} -c:a aac -b:a 192k -movflags +faststart -t {tl.duration:.4f} "{name}.mp4"\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config"); ap.add_argument("--out-dir", default=".")
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8"))
    tl = Timeline([p[:3] for p in cfg["pieces"]], cfg.get("fps", 24))
    overlaps = check_pieces(tl)
    words_path = os.path.join(os.path.dirname(os.path.abspath(a.config)), cfg["words"])
    chunks = json.load(open(words_path, encoding="utf-8"))
    errors = overlaps + check_text(cfg, chunks)
    if errors:
        for e in errors:
            print("error:", e)
        sys.exit(1)
    base = os.path.join(a.out_dir, cfg["name"])
    open(base + "_fb.ass", "w", encoding="utf-8").write(build_ass(cfg, tl, chunks))
    make_gradient(base + "_grad.png")
    open(base + "_fb.sh", "w", encoding="utf-8").write(build_command(cfg, tl))
    if cfg.get("cards"):
        cards = close_gaps(sorted((tl.map(s), tl.map(e), t) for s, e, t in cfg["cards"]))
        open(base + ".srt", "w", encoding="utf-8").write(build_srt(cards))
    print(f"{cfg['name']}: {tl.duration:.2f} s, {len(chunks)} caption chunks")
    for w in pacing_warnings(cfg, tl) + endcard_warnings(cfg):
        print("warning:", w)
    if not 30 <= tl.duration <= 60:
        print(f"warning: {tl.duration:.1f} s is outside 30-60 s")


def check_pieces(tl):
    """Pieces may play out of source order, but two pieces must not share source time (map() would be ambiguous)."""
    ps = sorted(tl.pieces)
    return [f"pieces overlap in source time: {a}-{b} and {c}-{d}" for (a, b), (c, d) in zip(ps, ps[1:]) if c < b]


if __name__ == "__main__":
    main()
