#!/usr/bin/env python3
"""Cut and level the clean base for the approved Shorts renderer.

Copy this file and set SRC/K for the selected moment, then run it. Source times
stay unchanged; timemap.json records speed-adjusted output starts.
"""
import argparse
import json
import math
import os
import subprocess

SRC = "/workspace/podcast/ep3/src_clip3_993s.mp4"
# (audio_start, audio_end, video_start_delay); delayed video is clone-padded.
K = [(3.60, 14.60, 0), (34.30, 49.70, 0), (49.85, 51.60, 0),
     (54.40, 65.55, 0.15), (66.75, 71.20, 0), (79.55, 81.00, 0)]
DEFAULT_SPEED = 1.25


def speed_value(value):
    speed = float(value)
    if not math.isfinite(speed) or not 0.5 <= speed <= 2.0:
        raise argparse.ArgumentTypeError("speed must be a finite number between 0.5 and 2.0")
    return speed


def build_filter(kept, speed):
    fc, streams = [], []
    for i, (a, b, delay) in enumerate(kept):
        duration = b - a
        if duration <= 0 or not 0 <= delay < duration:
            raise ValueError(f"invalid kept range {(a, b, delay)}")
        fc.append(
            f"[0:v]trim=start={a + delay:.3f}:end={b:.3f},setpts=PTS-STARTPTS,"
            "crop=405:720:415:0,scale=1080:1920:flags=lanczos,setsar=1"
            + (f",tpad=start_duration={delay}:start_mode=clone" if delay else "")
            + f"[v{i}]"
        )
        fc.append(
            f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS,"
            f"afade=t=in:d=0.012,afade=t=out:st={duration - 0.015:.3f}:d=0.015[a{i}]"
        )
        streams.append(f"[v{i}][a{i}]")
    fc.append("".join(streams) + f"concat=n={len(kept)}:v=1:a=1[vc0][ac0]")
    if speed == 1.0:
        fc.extend(("[vc0]null[vc]", "[ac0]anull[ac]"))
    else:
        fc.extend((f"[vc0]setpts=PTS/{speed:g}[vc]", f"[ac0]atempo={speed:g}[ac]"))
    fc.append(
        "[vc]fps=24,eq=contrast=1.05:saturation=1.1[z];[1:v]format=rgba[gr];"
        "[z][gr]overlay=0:0[g];[2:v]scale=210:-1[lg];"
        "[g][lg]overlay=56:150,format=yuv420p[v]"
    )
    fc.append(
        "[ac]highpass=f=80,acompressor=threshold=0.06:ratio=2.5:"
        "attack=15:release=250:makeup=1.5,aresample=48000[a]"
    )
    return ";".join(fc)


def time_map(kept, speed):
    output, mapped = 0.0, []
    for a, b, _ in kept:
        mapped.append([a, b, output])
        output += (b - a) / speed
    return mapped, output


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--speed", type=speed_value, default=DEFAULT_SPEED,
                    help=f"video/audio playback speed (default: {DEFAULT_SPEED}; 1.0 disables)")
    ap.add_argument("--output", required=True, help="destination <name>_clean.mp4")
    ap.add_argument("--timemap", default="timemap.json")
    args = ap.parse_args()
    if not os.path.isfile(SRC):
        raise SystemExit(f"error: source not found: {SRC}; copy this script and set SRC/K first")

    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-i", SRC, "-loop", "1", "-i", "grad.png", "-i", "logo.png",
        "-filter_complex", build_filter(K, args.speed), "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-g", "24", "-r", "24",
        "-c:a", "pcm_s24le", "-shortest", "pre.mov"
    ], check=True)
    log = subprocess.run([
        "ffmpeg", "-i", "pre.mov", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json",
        "-f", "null", "-"
    ], capture_output=True, text=True).stderr
    measured = json.loads(log[log.rindex("{"):log.rindex("}") + 1])
    audio_filter = (
        "loudnorm=I=-14:TP=-1.5:LRA=9:"
        f"measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:"
        f"measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:"
        f"offset={measured['target_offset']}:linear=true,aresample=48000"
    )
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-i", "pre.mov", "-af", audio_filter,
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", args.output
    ], check=True)
    mapped, duration = time_map(K, args.speed)
    with open(args.timemap, "w") as f:
        json.dump(mapped, f)
    print(f"dur {duration:.3f} s at {args.speed:g}x")


if __name__ == "__main__":
    main()
