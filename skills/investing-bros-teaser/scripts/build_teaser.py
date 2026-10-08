#!/usr/bin/env python3
"""Build a one-host 16:9 teaser (cold open) from an edit decision list (JSON).

Usage:
    python3 build_teaser.py teaser.json [--out-dir DIR]

Layout: the host's half of the side-by-side recording at native size
(960x1080, no upscaling) next to a branded panel — logo, episode label,
large captions, host name. The host stays on the side they sit in the
recording, so the cut into the episode doesn't jump.

Writes NAME.ass and NAME.sh. NAME.sh renders:
  seg_NAME.mp4   video only, encoded with the same settings as the episode
                 body (so assemble_episode.sh can join it with -c copy)
  aseg_NAME.wav  the matching audio, frame-exact length
  OUT            both muxed — the standalone teaser to review / post

teaser.json (times are seconds on the SOURCE timeline; pieces may be in any order):
{
  "name": "teaser_nadav",
  "out": "טיזר 1 - נדב.mp4",
  "source": "raw.mp4",
  "audio_source": "ep_audio.wav",   # the LEVELED episode audio (level_audio.sh), same timeline;
                                    # omit to use the source audio + per-piece gain
  "fps": 24,
  "host": "right",                  # which half of the recording the host sits in
  "frame": "frame_panel_left.png",  # brand.py frame panel-left (host right) / panel-right (host left)
  "fonts": "fonts",
  "label": "פרק 6 · טוקניזציה ובלוקצ'יין",
  "speaker": "נדב רסקין",
  "pieces": [[2217.05, 2233.0], [1452.88, 1460.0]],
  "cards": [[2217.05, 2218.5, "בחיים שלי לא הייתי מאמין"], ...]   # | = line break, [..] = emerald
}
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brand import EMERALD, PANEL, WHITE, ass_colour  # noqa: E402
from clip_captions import rtl  # noqa: E402

EM, WH = "{\\c&H" + ass_colour(EMERALD)[4:] + "&}", "{\\c&H" + ass_colour(WHITE)[4:] + "&}"
# Must match assemble_episode.sh so all episode segments join without re-encoding.
X264 = "-c:v libx264 -preset veryfast -crf 19 -profile:v high -level 4.0 -pix_fmt yuv420p -g 48 -video_track_timescale 24000"


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


class Timeline:
    def __init__(self, pieces, fps):
        self.pieces = [(snap(p[0], fps), snap(p[1], fps)) for p in pieces]
        self.gains = [float(p[2]) if len(p) > 2 else 0.0 for p in pieces]
        self.duration = sum(b - a for a, b in self.pieces)

    def map(self, t: float) -> float:
        out = 0.0
        for a, b in self.pieces:
            if a - 0.05 <= t <= b + 0.05:
                return min(max(out + (t - a), out), out + (b - a))
            out += b - a
        raise ValueError(f"time {t} is not inside any piece")


def build_ass(cfg, tl: Timeline) -> str:
    cx = 480 if cfg["host"] == "right" else 1440
    L = PANEL
    green = ass_colour(EMERALD)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TSub,Heebo ExtraBold,74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,0,3,5,0,0,0,-1
Style: Label,Heebo SemiBold,42,{green},{green},&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,8,0,0,0,-1
Style: Name,Heebo ExtraBold,50,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,2,0,0,0,-1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    d = tl.duration
    ev = [f"Dialogue: 1,{ass_time(0)},{ass_time(d)},Label,,0,0,0,,{{\\pos({cx},{L['label_y']})\\fad(250,0)}}{rtl(cfg['label'])}",
          f"Dialogue: 1,{ass_time(0)},{ass_time(d)},Name,,0,0,0,,{{\\pos({cx},{L['name_y']})\\fad(250,0)}}{rtl(cfg['speaker'])}"]
    cards = [[tl.map(a), tl.map(b), t] for a, b, t in cfg["cards"]]
    for i in range(len(cards) - 1):
        gap = cards[i + 1][0] - cards[i][1]
        if 0 < gap < 0.35 or gap < 0:
            cards[i][1] = cards[i + 1][0]
    for s, e, t in cards:
        text = "\\N".join(highlight(rtl(x)) for x in t.split("|"))
        ev.append(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},TSub,,0,0,0,,{{\\pos({cx},{L['caption_y']})}}{text}")
    return head + "\n".join(ev) + "\n"


def build_command(cfg, tl: Timeline) -> str:
    name, src, fps = cfg["name"], cfg.get("source", "raw.mp4"), cfg.get("fps", 24)
    P, n = tl.pieces, len(tl.pieces)
    crop = "crop=iw/2:ih:iw/2:0" if cfg["host"] == "right" else "crop=iw/2:ih:0:0"
    vx = 960 if cfg["host"] == "right" else 0
    ins = "".join(f' -ss {max(0.0, a - 2):.4f} -t {b - a + 4:.4f} -i "{src}"' for a, b in P)
    ins += f' -i "{cfg.get("frame", "frame.png")}"'
    vf = ""
    for i, (a, b) in enumerate(P):
        d, pre = b - a, min(2.0, a)
        fin = f"fade=t=in:st=0:d={0.3 if i == 0 else 0.08},"
        fout = f"fade=t=out:st={d - 0.08:.4f}:d=0.08," if i < n - 1 else ""
        vf += f"[{i}:v]trim=start={pre:.4f}:duration={d:.4f},setpts=PTS-STARTPTS,{crop},{fin}{fout}format=yuv420p[p{i}];"
    vf += "".join(f"[p{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[vc];"
    vf += (f"[{n}:v]loop=-1:1:0,fps={fps},trim=duration={tl.duration:.4f},setpts=PTS-STARTPTS,format=yuv420p[bg];"
           f"[bg][vc]overlay={vx}:0:shortest=1[y];[y]ass={name}.ass:fontsdir={cfg.get('fonts', 'fonts')},format=yuv420p[vout]")
    cmd = f'ffmpeg -v error -y{ins} -filter_complex "{vf}" -map "[vout]" -an {X264} -r {fps} "seg_{name}.mp4"\n'

    asrc = cfg.get("audio_source")
    parts = ""
    for i, (a, b) in enumerate(P):
        d = b - a
        gain = "" if asrc else f",volume={tl.gains[i]}dB"
        parts += (f"[s{i}]atrim=start={a:.4f}:end={b:.4f},asetpts=PTS-STARTPTS,afade=t=in:d={0.3 if i == 0 else 0.012},"
                  f"afade=t=out:st={d - 0.015:.4f}:d=0.015{gain}[q{i}];")
    split = f"[0:a]asplit={n}" + "".join(f"[s{i}]" for i in range(n)) + ";" if n > 1 else "[0:a]anull[s0];"
    tail = "" if asrc else ",loudnorm=I=-16:TP=-1.5:LRA=11"
    ac = split + parts + "".join(f"[q{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1{tail},apad,atrim=duration={tl.duration:.4f}[aout]"
    cmd += f'ffmpeg -v error -y -i "{asrc or src}" -filter_complex "{ac}" -map "[aout]" -c:a pcm_s16le -ar 48000 -ac 2 "aseg_{name}.wav"\n'
    cmd += f'ffmpeg -v error -y -i "seg_{name}.mp4" -i "aseg_{name}.wav" -c:v copy -c:a aac -b:a 192k -movflags +faststart "{cfg.get("out", name + ".mp4")}"\n'
    return cmd


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--out-dir", default=".")
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8"))
    tl = Timeline(cfg["pieces"], cfg.get("fps", 24))
    base = os.path.join(a.out_dir, cfg["name"])
    open(base + ".ass", "w", encoding="utf-8").write(build_ass(cfg, tl))
    open(base + ".sh", "w", encoding="utf-8").write(build_command(cfg, tl))
    print(f"{cfg['name']}: {tl.duration:.2f} s ({round(tl.duration * cfg.get('fps', 24))} frames), {len(tl.pieces)} piece(s)")
    if not 15 <= tl.duration <= 30:
        print(f"warning: a per-host teaser should be 15–30 s (is {tl.duration:.1f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
