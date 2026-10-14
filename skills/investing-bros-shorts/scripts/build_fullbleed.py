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
  "pieces": [[2106.02, 2154.45, 0.0, "R"]],     # kept range, gain dB, which half (L/R) fills the screen
  "crop_x": {"L": 176, "R": 170},               # x of the 608-px-wide 9:16 crop inside each 960-px half (face centred)
  "words": "aligned.json",                      # from align_words.py (proofread caption text + whisper timing)
  "hook": ["אסטרואיד אחד", "[יכול להכפיל]", "[את הזהב בעולם?]"],   # first ~2.7 s, faithful paraphrase
  "zooms": [[2114.5, 1.13], [2119.0, 1.0]],     # punch-ins: from this source time, this zoom (1.0 = none)
  "endcard": ["לפרק המלא", "[אחים להשקעות · פרק 7]", "עקבו לעוד שורטים"],
  "logo": "logo.png", "fonts": "fonts"
}
[..] = gold. Captions: 2-3 words at a time, the spoken word gold, centre at y=1290
(above the Reels/Shorts UI). Logo top-left (56,150), 210 px wide.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brand import ass_colour  # noqa: E402
from build_short import Timeline, ass_time  # noqa: E402
from clip_captions import rtl  # noqa: E402

GOLD = (245, 183, 31)                       # house accent #F5B71F (investing-bros-show)
G = "{\\c" + ass_colour(GOLD) + "}"
W = "{\\c&H00FFFFFF}"
CAP_Y, HOOK_Y, END_S = 1290, 700, 2.8
AUDIO = ("highpass=f=80,acompressor=threshold=0.06:ratio=2.5:attack=15:release=250:makeup=1.5,"
         "loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo")


def gold(s):
    return rtl(s).replace("[", G).replace("]", W)


def build_ass(cfg, tl, chunks):
    dur = tl.duration
    end_t = max(0.0, dur - END_S)
    st = ("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, "
          "StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
          "Style: Cap,Heebo Black,100,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,8,3,5,60,60,0,-1\n"
          "Style: Hook,Heebo Black,118,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,9,4,5,60,60,0,-1\n"
          "Style: End,Heebo Black,84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,6,0,5,60,60,0,-1\n"
          "Style: Dim,Heebo Black,20,&H00000000,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,-1\n")
    out = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
           "[V4+ Styles]\n" + st + "\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    ev = lambda layer, s, e, style, txt: f"Dialogue: {layer},{ass_time(s)},{ass_time(e)},{style},,0,0,0,,{txt}\n"
    if cfg.get("hook"):
        out += ev(5, 0, 2.7, "Hook", f"{{\\pos(540,{HOOK_Y})\\fscx70\\fscy70\\t(0,180,\\fscx100\\fscy100)\\fad(0,200)}}"
                  + "\\N".join(gold(x) for x in cfg["hook"]))
    for chunk in chunks:
        gs, ge = tl.map(chunk[0]["s"]), min(tl.map(chunk[-1]["e"]), end_t)
        if gs >= end_t:
            continue
        for j, w in enumerate(chunk):
            s = tl.map(w["s"]) if j else gs
            e = tl.map(chunk[j + 1]["s"]) if j + 1 < len(chunk) else ge
            if e <= s:
                continue
            on = "{\\c" + ass_colour(GOLD) + ("\\fscx112\\fscy112" if w["key"] else "") + "}"
            off = "{\\c&H00FFFFFF\\fscx100\\fscy100}"
            parts = [on + rtl(x["w"]) + off if k == j else rtl(x["w"]) for k, x in enumerate(chunk)]
            pop = "\\fscx82\\fscy82\\t(0,90,\\fscx100\\fscy100)" if j == 0 else ""
            out += ev(1, s, e, "Cap", f"{{\\pos(540,{CAP_Y}){pop}}}" + " ".join(parts))
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


def build_command(cfg, tl):
    name, src, fps = cfg["name"], cfg.get("source", "raw.mp4"), cfg.get("fps", 24)
    P = [(a, b, float(p[2]) if len(p) > 2 else 0.0, p[3] if len(p) > 3 else "L") for (a, b), p in zip(tl.pieces, cfg["pieces"])]
    S = max(0.0, P[0][0] - 1.0)
    T = max(b for _, b, _, _ in P) - S + 1.0
    cx = cfg.get("crop_x", {"L": 176, "R": 176})
    n = len(P)
    f = ""
    for i, (a, b, g, side) in enumerate(P):
        x = cx[side] + (960 if side == "R" else 0)
        f += (f"[0:v]trim=start={a - S:.4f}:end={b - S:.4f},setpts=PTS-STARTPTS,crop=608:1080:{x}:0,"
              f"scale=1080:1920:flags=lanczos[v{i}];")
        f += (f"[0:a]atrim=start={a - S:.4f}:end={b - S:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,"
              f"afade=t=out:st={b - a - 0.015:.4f}:d=0.015,volume={g}dB[a{i}];")
    f += "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac];"
    z = "1.0"
    for t, zz in sorted(cfg.get("zooms", [])):          # latest time ends up outermost
        z = f"if(gte(it,{tl.map(t):.3f}),{zz},{z})"
    f += (f"[vc]fps={fps},zoompan=z='{z}':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)*0.35':d=1:s=1080x1920:fps={fps},"
          f"eq=contrast=1.05:saturation=1.1[z];[1:v]format=rgba[gr];[z][gr]overlay=0:0[g];"
          f"[2:v]scale=210:-1[lg];[g][lg]overlay=56:150[l];[l]ass={name}_fb.ass:fontsdir={cfg.get('fonts', 'fonts')},format=yuv420p[v];"
          f"[ac]{AUDIO}[a]")
    return (f'ffmpeg -v error -y -ss {S:.3f} -t {T:.3f} -i "{src}" -i "{name}_grad.png" -i "{cfg.get("logo", "logo.png")}" '
            f'-filter_complex "{f}" -map "[v]" -map "[a]" -c:v libx264 -preset veryfast -crf 17 -g {fps} -keyint_min {fps} '
            f'-r {fps} -c:a aac -b:a 192k -movflags +faststart -t {tl.duration:.4f} "{name}.mp4"\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config"); ap.add_argument("--out-dir", default=".")
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8"))
    tl = Timeline([p[:3] if len(p) > 3 else p for p in cfg["pieces"]], cfg.get("fps", 24))
    words_path = os.path.join(os.path.dirname(os.path.abspath(a.config)), cfg["words"])
    chunks = json.load(open(words_path, encoding="utf-8"))
    base = os.path.join(a.out_dir, cfg["name"])
    open(base + "_fb.ass", "w", encoding="utf-8").write(build_ass(cfg, tl, chunks))
    make_gradient(base + "_grad.png")
    open(base + "_fb.sh", "w", encoding="utf-8").write(build_command(cfg, tl))
    print(f"{cfg['name']}: {tl.duration:.2f} s, {len(chunks)} caption chunks")
    if not 30 <= tl.duration <= 60:
        print(f"warning: {tl.duration:.1f} s is outside 30–60 s")


if __name__ == "__main__":
    main()
