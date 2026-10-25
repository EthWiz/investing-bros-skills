#!/usr/bin/env python3
"""Cut and level the clean base for the approved Shorts renderer.

Copy this file and set SRC/TRACKS/K for the selected moment, then run it. Source
times stay unchanged; timemap.json records speed-adjusted output starts.

Picture comes from each host's own Riverside track, never from the side-by-side
episode export: in the recording's Riverside share link, Tracks -> <host> ->
download -> "Aligned video" (CFR MP4). SRC (the episode master) gives the timeline
and the audio. Each piece names the track it shows; the track's offset against SRC
is measured from the audio (or set in TRACK_OFFSETS) and printed.

The script refuses a side-by-side frame as picture (a hard seam down the middle);
--allow-side-by-side overrides that only with Amitai's OK, noted in the hand-back.
"""
import argparse
import json
import math
import os
import subprocess

import numpy as np

SRC = "/workspace/podcast/ep8/episode-master.mp4"  # timeline + audio (segments.json time = SRC time)
# Each host's Riverside "Aligned video" track. Keys are what K's 5th field names.
TRACKS = {"A": "amitai_aligned.mp4", "N": "nadav_aligned.mp4"}
TRACK_OFFSETS = {}  # optional fixed offsets (track time = SRC time + offset); else measured
# (audio_start, audio_end, video_start_delay, crop "w:h:x:y" in track pixels, track key)
# Delayed video is clone-padded. A 3-tuple (a, b, delay) uses SRC's own picture with
# DEFAULT_CROP (single-host sources such as Zoom speaker view only).
K = [(3.60, 14.60, 0, "1080:1920:420:0", "A"), (16.20, 24.80, 0, "1080:1920:380:0", "N")]
DEFAULT_SPEED = 1.25
DEFAULT_CROP = "405:720:415:0"
SEAM_ROWS = 0.6     # share of rows with a jump at the centre column that marks a side-by-side
ENV_RATE = 100      # Hz, audio envelope used for syncing


def speed_value(value):
    speed = float(value)
    if not math.isfinite(speed) or not 0.5 <= speed <= 2.0:
        raise argparse.ArgumentTypeError("speed must be a finite number between 0.5 and 2.0")
    return speed


def piece(p):
    """(a, b, delay, crop, track key or None)."""
    a, b, delay = p[:3]
    crop = p[3] if len(p) > 3 else DEFAULT_CROP
    key = p[4] if len(p) > 4 else None
    if b - a <= 0 or not 0 <= delay < b - a:
        raise ValueError(f"invalid kept range {(a, b, delay)}")
    if len(str(crop).split(":")) != 4:
        raise ValueError(f"crop must be w:h:x:y, got {crop!r}")
    return a, b, delay, crop, key


def build_filter(kept, speed, offsets=None):
    """kept: K entries. offsets: {track key: seconds}. Inputs: 0 = SRC, 1.. = tracks
    in first-use order, then grad.png and logo.png."""
    offsets = offsets or {}
    keys = []
    for p in kept:
        key = piece(p)[4]
        if key is not None and key not in keys:
            keys.append(key)
    gi, li = len(keys) + 1, len(keys) + 2
    fc, streams = [], []
    for i, p in enumerate(kept):
        a, b, delay, crop, key = piece(p)
        vin, shift = (0, 0.0) if key is None else (keys.index(key) + 1, offsets.get(key, 0.0))
        fc.append(
            f"[{vin}:v]trim=start={a + delay + shift:.3f}:end={b + shift:.3f},setpts=PTS-STARTPTS,"
            f"crop={crop},scale=1080:1920:flags=lanczos,setsar=1"
            + (f",tpad=start_duration={delay}:start_mode=clone" if delay else "")
            + f"[v{i}]"
        )
        fc.append(
            f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS,"
            f"afade=t=in:d=0.012,afade=t=out:st={b - a - 0.015:.3f}:d=0.015[a{i}]"
        )
        streams.append(f"[v{i}][a{i}]")
    fc.append("".join(streams) + f"concat=n={len(kept)}:v=1:a=1[vc0][ac0]")
    if speed == 1.0:
        fc.extend(("[vc0]null[vc]", "[ac0]anull[ac]"))
    else:
        fc.extend((f"[vc0]setpts=PTS/{speed:g}[vc]", f"[ac0]atempo={speed:g}[ac]"))
    fc.append(
        f"[vc]fps=24,eq=contrast=1.05:saturation=1.1[z];[{gi}:v]format=rgba[gr];"
        f"[z][gr]overlay=0:0[g];[{li}:v]scale=210:-1[lg];"
        "[g][lg]overlay=56:150,format=yuv420p[v]"
    )
    fc.append(
        "[ac]highpass=f=80,acompressor=threshold=0.06:ratio=2.5:"
        "attack=15:release=250:makeup=1.5,aresample=48000[a]"
    )
    return ";".join(fc), keys


def time_map(kept, speed):
    output, mapped = 0.0, []
    for p in kept:
        a, b = p[0], p[1]
        mapped.append([a, b, output])
        output += (b - a) / speed
    return mapped, output


# ---------- guard: side-by-side picture ----------
def seam_share(gray):
    """Share of rows whose brightness jumps across the centre column far more than
    across the columns next to it (a hard seam = a two-host side-by-side frame)."""
    g = np.asarray(gray, dtype=np.float32)
    if g.ndim != 2 or g.shape[1] < 32 or g.shape[1] / g.shape[0] < 1.6:
        return 0.0
    c = g.shape[1] // 2
    diffs = np.abs(np.diff(g[:, c - 8:c + 8], axis=1))      # 15 columns, seam at index 7
    seam = diffs[:, 7]
    local = np.median(np.delete(diffs, [6, 7, 8], axis=1), axis=1)
    return float(np.mean(seam > 3 * local + 4))


def frame_gray(path, t, width=640):
    out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1",
                          "-vf", f"scale={width}:-2,format=gray", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    h = len(out) // width
    return np.frombuffer(out[:h * width], np.uint8).reshape(h, width)


def looks_side_by_side(path, times):
    shares = [seam_share(frame_gray(path, t)) for t in times]
    return min(shares) >= SEAM_ROWS, shares


# ---------- sync: track offset from audio ----------
def envelope(x, sr, rate=ENV_RATE):
    hop = sr // rate
    n = len(x) // hop
    e = np.sqrt((np.asarray(x[:n * hop], np.float64).reshape(n, hop) ** 2).mean(1))
    return (e - e.mean()) / (e.std() + 1e-9)


def envelope_offset(master, track, sr, search=3.0):
    """Seconds to add to master time to get track time, and the match score (0-1).
    master: audio of [t0, t1]; track: audio of [t0 - search, t1 + search]."""
    m, t = envelope(master, sr), envelope(track, sr)
    lags = np.arange(0, len(t) - len(m) + 1)
    scores = np.array([np.dot(m, t[k:k + len(m)]) / len(m) for k in lags])
    k = int(scores.argmax())
    return round(k / ENV_RATE - search, 3), float(scores[k])


def audio(path, start, dur, sr=8000):
    out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(start, 0):.3f}", "-t", f"{dur:.3f}",
                          "-i", path, "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, np.int16)


def measure_offset(track, a, b, search=3.0, sr=8000):
    return envelope_offset(audio(SRC, a, b - a, sr), audio(track, a - search, b - a + 2 * search, sr), sr, search)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--speed", type=speed_value, default=DEFAULT_SPEED,
                    help=f"video/audio playback speed (default: {DEFAULT_SPEED}; 1.0 disables)")
    ap.add_argument("--output", required=True, help="destination <name>_clean.mp4")
    ap.add_argument("--timemap", default="timemap.json")
    ap.add_argument("--allow-side-by-side", action="store_true",
                    help="use a side-by-side picture anyway (only with Amitai's OK; say so in the hand-back)")
    args = ap.parse_args()
    if not os.path.isfile(SRC):
        raise SystemExit(f"error: source not found: {SRC}; copy this script and set SRC/TRACKS/K first")
    kept = [piece(p) for p in K]
    used = [k for k in dict.fromkeys(p[4] for p in kept) if k is not None]
    for key in used:
        if not os.path.isfile(TRACKS.get(key, "")):
            raise SystemExit(f"error: track {key!r} not found: {TRACKS.get(key)}")

    pictures = [(TRACKS[k], [p[0] + TRACK_OFFSETS.get(k, 0.0) + 1 for p in kept if p[4] == k]) for k in used]
    if any(p[4] is None for p in kept):
        pictures.append((SRC, [p[0] + 1 for p in kept if p[4] is None]))
    for path, times in pictures:
        bad, shares = looks_side_by_side(path, times[:3])
        if bad and not args.allow_side_by_side:
            raise SystemExit(
                f"error: {path} looks like a side-by-side export (seam in {min(shares):.0%} of rows). "
                "Use each host's own Riverside track: share link -> Tracks -> <host> -> Aligned video.")
        if bad:
            print(f"warning: side-by-side picture allowed for {path}; list it in the hand-back")

    offsets = {}
    for key in used:
        if key in TRACK_OFFSETS:
            offsets[key] = TRACK_OFFSETS[key]
            continue
        a, b = next((p[0], p[1]) for p in kept if p[4] == key)
        off, score = measure_offset(TRACKS[key], a, b)
        print(f"track {key}: offset {off:+.3f} s (match {score:.2f})")
        if score < 0.5:
            raise SystemExit(f"error: could not sync track {key} (match {score:.2f}); set TRACK_OFFSETS[{key!r}]")
        offsets[key] = off

    graph, keys = build_filter(K, args.speed, offsets)
    inputs = ["-i", SRC]
    for key in keys:
        inputs += ["-i", TRACKS[key]]
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", *inputs, "-loop", "1", "-i", "grad.png", "-i", "logo.png",
        "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
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
