#!/usr/bin/env python3
"""Cut the clean input clip for a HyperFrames short: kept pieces, host framing, levelled audio.

Usage:
    python3 make_input.py short.json [--out-dir DIR] [--speed 1.25]     # writes NAME_input.sh

HyperFrames' talking-head-recut layer plays its input clip untouched, so every
edit happens here, in ffmpeg: the cuts (pieces), which host is on screen
(shots), and the sound. The result is the 1080x1216 picture that sits at the top
of the 1080x1920 composition — no captions, no graphics.

short.json keys used here (times are seconds on the SOURCE timeline):
  name, source (side-by-side recording), fps (24),
  pieces  [[start, end, gain_dB?], ...]   kept ranges, cut at pauses
  shots   [[start, end, "L"|"R"], ...]     which half of the recording fills the frame
  audio_source  optional: the LEVELLED episode WAV (same timeline as source);
                without it the source audio is levelled here (gain per piece + compressor)
The same file feeds build_composition.py (captions, cards, end card).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_short import DEFAULT_SPEED, playback_speed, speed_arg  # noqa: E402

# Riverside exports are often mono AAC; without an explicit output layout ffmpeg fails with
# "Cannot select channel layout for the link between filters aresample and format_out".
STEREO = "aformat=sample_fmts=fltp:channel_layouts=stereo"
X264 = "-c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p"
CROP = {"L": "crop=iw/2:ih:0:0", "R": "crop=iw/2:ih:iw/2:0"}
VIDEO_W, VIDEO_H = 1080, 1216     # one half (960x1080) of a 1920x1080 recording, scaled ~1.125x (even height for x264)


def snap(t: float, fps: float) -> float:
    return round(t * fps) / fps


def pieces_of(cfg):
    fps = cfg.get("fps", 24)
    out = []
    for p in cfg["pieces"]:
        a, b = snap(p[0], fps), snap(p[1], fps)
        if b <= a:
            raise ValueError(f"empty piece {p}")
        out.append((a, b, float(p[2]) if len(p) > 2 else 0.0))
    return out


def out_time(pieces, t: float, speed=1.0) -> float:
    speed = playback_speed(speed)
    o = 0.0
    for a, b, _ in pieces:
        if a - 0.05 <= t <= b + 0.05:
            return min(max(o + (t - a) / speed, o), o + (b - a) / speed)
        o += (b - a) / speed
    raise ValueError(f"time {t} is not inside any piece")


def build_command(cfg, speed=1.0) -> str:
    speed = playback_speed(speed)
    fps = cfg.get("fps", 24)
    P = pieces_of(cfg)
    n = len(P)
    src = cfg.get("source", "raw.mp4")
    asrc = cfg.get("audio_source")
    base = cfg.get("base", "L")
    other = "R" if base == "L" else "L"
    vt = "".join(f"[0:v]trim=start={a:.4f}:end={b:.4f},setpts=PTS-STARTPTS[v{i}];" for i, (a, b, _) in enumerate(P))
    ain = "1:a" if asrc else "0:a"
    at = "".join(
        f"[{ain}]aresample=async=1:min_hard_comp=0.01:first_pts=0,"
        f"atrim=start={a:.4f}:end={b:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,"
        f"afade=t=out:st={b - a - 0.015:.4f}:d=0.015{'' if asrc else f',volume={g}dB'}[a{i}];"
        for i, (a, b, g) in enumerate(P))
    cat = "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc0][ac0];"
    if speed == 1.0:
        tempo = "[vc0]null[vc];[ac0]anull[ac];"
    else:
        tempo = f"[vc0]setpts=PTS/{speed:g}[vc];[ac0]atempo={speed:g}[ac];"
    shots = cfg.get("shots", [[P[0][0], P[-1][1], base]])
    en = "+".join(f"between(t,{out_time(P, a, speed):.3f},{out_time(P, b, speed):.3f})"
                  for a, b, side in shots if side == other) or "0"
    vf = (f"[vc]split[x1][x2];[x1]{CROP[base]},scale={VIDEO_W}:{VIDEO_H}:flags=lanczos[B];"
          f"[x2]{CROP[other]},scale={VIDEO_W}:{VIDEO_H}:flags=lanczos[O];[B][O]overlay=0:0:enable='{en}',fps={fps},format=yuv420p[v];")
    if asrc:
        af = "[ac]volume=2dB,alimiter=limit=0.89:level=disabled,aresample=48000," + STEREO + "[a]"   # -16 LUFS episode -> ~-14 for social
    else:
        af = ("[ac]highpass=f=80,acompressor=threshold=0.06:ratio=2.5:attack=15:release=250:makeup=1.5,"
              "loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000," + STEREO + "[a]")
    inputs = f'-i "{src}"' + (f' -i "{asrc}"' if asrc else "")
    # -g = fps: every second seekable, otherwise the renderer freezes frames on seek
    return (f'ffmpeg -v error -y {inputs} -filter_complex "{vt}{at}{cat}{tempo}{vf}{af}" -map "[v]" -map "[a]" '
            f'{X264} -r {fps} -g {fps} -keyint_min {fps} -c:a aac -b:a 192k -movflags +faststart "{cfg["name"]}_input.mp4"\n')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--speed", type=speed_arg, default=DEFAULT_SPEED,
                    help=f"video/audio playback speed (default: {DEFAULT_SPEED}; 1.0 disables)")
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8"))
    path = os.path.join(a.out_dir, cfg["name"] + "_input.sh")
    open(path, "w", encoding="utf-8").write(build_command(cfg, a.speed))
    dur = sum(b - a for a, b, _ in pieces_of(cfg)) / a.speed
    print(f"{path}: {dur:.2f} s at {a.speed:g}x, {len(cfg['pieces'])} piece(s)")
    from build_short import LENGTH_LIMIT, LENGTH_TARGET
    if not LENGTH_TARGET[0] <= dur <= LENGTH_TARGET[1]:
        hard = not LENGTH_LIMIT[0] <= dur <= LENGTH_LIMIT[1]
        print(f"warning: {dur:.1f} s is outside the {LENGTH_TARGET[0]}–{LENGTH_TARGET[1]} s target"
              + ("" if hard else "; say why in the hand-back"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
