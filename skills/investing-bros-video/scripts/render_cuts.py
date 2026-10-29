#!/usr/bin/env python3
"""Cut ranges out of a finished video in ONE ffmpeg pass (picture and sound together).

  render_cuts.py SOURCE.mp4 OUT.mp4 --cut OUT_S-IN_S [--cut ...] [--start S] [--end S]
      [--fps auto] [--vx 0.25] [--ax 0.06] [--scale 1920:1080] [--crf 19]
      [--plan-out plan.json] [--dry-run]

Use it to re-cut an already-assembled video (episode 9: a fumbled opening and a false
start removed from the v3 master). A cut `A-B` removes source seconds A..B: A is the
last moment to keep, B the first moment to keep again (both in a pause; times from the
transcript and the waveform).

Why one pass (episode 9's first sample drifted out of sync):
- picture and sound come from the SAME input in ONE filter graph, with the same
  boundaries: never cut or splice the audio separately and mux it back;
- the removed span is snapped to a whole number of frames and the video cut points sit
  on frame boundaries, so the audio removed is exactly the video removed;
- `-reinit_filter 0`: a video joined with `-c copy` from parts whose colour metadata
  differs reconfigures the filter graph mid-stream, which resets `setpts`/`trim`
  counters and silently shifts the picture (v4: +26 s jump at 0:20).

Transitions: `--vx` seconds of video dissolve (xfade) and `--ax` seconds of audio
crossfade (acrossfade), centred on each cut; 0 means a hard cut (concat). Both are
centred, so the output is exactly (end - start - removed) long. Near the start/end or
another cut a transition is shortened to the kept material on each side (down to a hard
cut). After rendering, the picture and the sound are both checked against that length.

`--plan-out` writes the cut plan (frame-snapped times, source<->output map) that
`verify_sync.py` reads. Always run `verify_sync.py` on the result before sending it.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from fractions import Fraction


def probe_fps(path: str) -> Fraction:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=avg_frame_rate", "-of", "default=nw=1:nk=1", path],
                       capture_output=True, text=True, check=True)
    return Fraction(r.stdout.strip())


def probe_duration(path: str) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", path], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def parse_cut(s: str) -> tuple[float, float]:
    a, b = s.split("-", 1)
    a, b = float(a), float(b)
    if b <= a:
        raise argparse.ArgumentTypeError(f"cut {s}: end must be after start")
    return a, b


def _snap(t, fps):
    return float(Fraction(round(Fraction(t) * fps)) / fps)


def plan_cuts(cuts, fps, start=0.0, end=None, vx=0.25, ax=0.06):
    """Frame-snap the cuts and lay out the kept segments.

    Returns a dict with `cuts` (each: audio `out`/`in`, frame-aligned `v_out`/`v_in`,
    `removed` = whole frames, `at` = the cut's time in the output, and the `vx`/`ax`
    transition actually used there) and `segments` (kept source ranges with their
    transition padding). Pure function (tested).

    `start`/`end` are snapped to frames too, so picture and sound have the same length.
    A transition is centred on its cut and takes half its length from each neighbouring
    kept region, so it is clamped to the shorter neighbour (video: to whole frames on
    each side; 0 = hard cut). Without the clamp a cut close to the start/end or to
    another cut gives a negative xfade offset and a picture longer than the sound.
    """
    fps = Fraction(fps)
    fr = 1 / float(fps)
    cuts = sorted(cuts)
    if end is None:
        raise ValueError("end is required")
    if vx < 0 or ax < 0:
        raise ValueError("transition lengths must be >= 0")
    start, end = _snap(start, fps), _snap(end, fps)
    if end <= start:
        raise ValueError("end must be after start")
    out = []
    removed = 0.0
    prev_in = start
    for a, b in cuts:
        if a <= start or b >= end:
            raise ValueError(f"cut {a}-{b} must lie inside {start}-{end}")
        if a < prev_in:
            raise ValueError(f"cut {a}-{b} overlaps the previous cut")
        n_out = round(Fraction(a) * fps)
        n_rm = max(1, round(Fraction(b - a) * fps))
        v_out = float(Fraction(n_out) / fps)
        v_in = float(Fraction(n_out + n_rm) / fps)
        if v_out <= start or v_in >= end or v_out <= prev_v_in(out, start):
            raise ValueError(f"cut {a}-{b} leaves no frame before/after it once snapped to frames (merge it with its neighbour)")
        rm = n_rm * fr
        a_in = a + rm  # audio removes exactly the same span as the video
        out.append({"out": round(a, 9), "in": round(a_in, 9), "requested_in": b,
                    "v_out": round(v_out, 9), "v_in": round(v_in, 9), "removed": round(rm, 9),
                    "removed_frames": n_rm, "at": round(a - start - removed, 9),
                    "v_at": round(v_out - start - removed, 9)})
        removed += rm
        prev_in = a_in
    # kept regions (source seconds) on each side of every cut
    vb = [start] + [x for c in out for x in (c["v_out"], c["v_in"])] + [end]
    ab = [start] + [x for c in out for x in (c["out"], c["in"])] + [end]
    vlen = [vb[2 * k + 1] - vb[2 * k] for k in range(len(out) + 1)]
    alen = [ab[2 * k + 1] - ab[2 * k] for k in range(len(out) + 1)]
    for k, c in enumerate(out):
        room = min(vlen[k], vlen[k + 1])
        half = int(min(vx / 2, room / 2) * float(fps) + 1e-6)  # whole frames per side
        c["vx"] = round(2 * half * fr, 9)
        c["ax"] = round(max(0.0, min(ax, alen[k], alen[k + 1])), 9)
    segs = []
    for k in range(len(out) + 1):
        first, last = k == 0, k == len(out)
        vs = start if first else out[k - 1]["v_in"] - out[k - 1]["vx"] / 2
        as_ = start if first else out[k - 1]["in"] - out[k - 1]["ax"] / 2
        ve = end if last else out[k]["v_out"] + out[k]["vx"] / 2
        ae = end if last else out[k]["out"] + out[k]["ax"] / 2
        segs.append({"v": [round(vs, 9), round(ve, 9)], "a": [round(as_, 9), round(ae, 9)]})
    return {"fps": str(fps), "start": start, "end": end, "vx": vx, "ax": ax, "cuts": out,
            "segments": segs, "duration": round(end - start - removed, 9)}


def prev_v_in(out, start):
    return out[-1]["v_in"] if out else start


def filter_graph(plan, scale=None):
    """One graph: split/asplit of the single input, pts-based trim/atrim, then
    xfade/acrossfade per cut (concat where that cut's transition is 0)."""
    fps = plan["fps"]
    segs, cuts = plan["segments"], plan["cuts"]
    n = len(segs)
    sc = f",scale={scale},setsar=1" if scale else ""
    # Relabel (not convert) every frame as bt709/tv: mixed or missing colour tags
    # in the source then can't make ffmpeg convert pixels or rebuild the graph.
    tag = "setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709"
    f = [f"[0:v]split={n}" + "".join(f"[v{k}]" for k in range(n)),
         f"[0:a]asplit={n}" + "".join(f"[a{k}]" for k in range(n))]
    for k, s in enumerate(segs):
        f.append(f"[v{k}]trim=start={s['v'][0]:.6f}:end={s['v'][1]:.6f},setpts=PTS-STARTPTS,{tag},"
                 f"fps={fps}{sc},format=yuv420p[V{k}]")
        f.append(f"[a{k}]atrim=start={s['a'][0]:.6f}:end={s['a'][1]:.6f},asetpts=PTS-STARTPTS[A{k}]")
    if n == 1:
        f.append("[V0]null[vout]")
        f.append("[A0]anull[aout]")
        return ";".join(f)
    if all(c["vx"] == 0 for c in cuts):
        f.append("".join(f"[V{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=0[vout]")
    else:
        vl = "V0"
        for k, c in enumerate(cuts):
            o = "vout" if k == len(cuts) - 1 else f"X{k}"
            if c["vx"] > 0:
                off = c["v_at"] - c["vx"] / 2
                f.append(f"[{vl}][V{k + 1}]xfade=transition=fade:duration={c['vx']:.6f}:offset={off:.6f},"
                         f"format=yuv420p[{o}]")
            else:
                f.append(f"[{vl}][V{k + 1}]concat=n=2:v=1:a=0[{o}]")
            vl = o
    if all(c["ax"] == 0 for c in cuts):
        f.append("".join(f"[A{k}]" for k in range(n)) + f"concat=n={n}:v=0:a=1[aout]")
    else:
        al = "A0"
        for k, c in enumerate(cuts):
            o = "aout" if k == len(cuts) - 1 else f"Y{k}"
            if c["ax"] > 0:
                f.append(f"[{al}][A{k + 1}]acrossfade=d={c['ax']:.6f}:c1=tri:c2=tri[{o}]")
            else:
                f.append(f"[{al}][A{k + 1}]concat=n=2:v=0:a=1[{o}]")
            al = o
    return ";".join(f)


def check_output(path, plan, tol=None):
    """Picture and sound must both last the planned duration (one frame + AAC padding)."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration",
                        "-of", "json", path], capture_output=True, text=True, check=True)
    d = {s["codec_type"]: float(s["duration"]) for s in json.loads(r.stdout)["streams"]}
    tol = tol if tol is not None else 1 / float(Fraction(plan["fps"])) + 0.03
    errs = []
    if abs(d["video"] - d["audio"]) > tol:
        errs.append(f"video {d['video']:.3f} s vs audio {d['audio']:.3f} s")
    for k in ("video", "audio"):
        if abs(d[k] - plan["duration"]) > tol:
            errs.append(f"{k} {d[k]:.3f} s vs planned {plan['duration']:.3f} s")
    return d, errs


def ffmpeg_cmd(src, dst, plan, scale=None, crf=19, preset="medium"):
    return ["ffmpeg", "-v", "error", "-nostdin", "-y", "-reinit_filter", "0",
            "-t", f"{plan['end'] + 1:.3f}", "-i", src, "-filter_complex", filter_graph(plan, scale),
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-profile:v", "high",
            "-pix_fmt", "yuv420p", "-r", plan["fps"],
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
            "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-movflags", "+faststart", dst]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("out")
    ap.add_argument("--cut", type=parse_cut, action="append", default=[], help="OUT-IN source seconds")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, help="source seconds (default: the whole file)")
    ap.add_argument("--fps", help="default: the source's avg_frame_rate")
    ap.add_argument("--vx", type=float, default=0.25, help="video dissolve seconds (0 = hard cut)")
    ap.add_argument("--ax", type=float, default=0.06, help="audio crossfade seconds (0 = hard cut)")
    ap.add_argument("--scale", help="e.g. 1280:720 for a review sample; default keeps the size")
    ap.add_argument("--crf", type=int, default=19)
    ap.add_argument("--preset", default="medium")
    ap.add_argument("--plan-out", help="write the cut plan JSON (input of verify_sync.py)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    fps = Fraction(a.fps) if a.fps else probe_fps(a.source)
    end = a.end if a.end is not None else probe_duration(a.source)
    plan = plan_cuts(a.cut, fps, a.start, end, a.vx, a.ax)
    plan["source"] = a.source
    plan["output"] = a.out
    for c in plan["cuts"]:
        print(f"cut {c['out']:.3f}-{c['in']:.3f} ({c['removed_frames']} frames, {c['removed']:.3f} s) "
              f"at output {c['at']:.3f}; dissolve {c['vx']:.3f} s, audio crossfade {c['ax']:.3f} s")
        if c["vx"] < a.vx or c["ax"] < a.ax:
            print("  (transition shortened: not enough kept material next to this cut)")
    print(f"output duration {plan['duration']:.3f} s")
    if a.plan_out:
        json.dump(plan, open(a.plan_out, "w"), indent=1, ensure_ascii=False)
    cmd = ffmpeg_cmd(a.source, a.out, plan, a.scale, a.crf, a.preset)
    if a.dry_run:
        print(" ".join(cmd))
        return 0
    subprocess.run(cmd, check=True)
    d, errs = check_output(a.out, plan)
    if errs:
        print("FAIL: output length doesn't match the plan: " + "; ".join(errs))
        return 1
    print(f"wrote {a.out}; now run verify_sync.py {a.source} {a.out} --plan {a.plan_out or 'PLAN.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
