#!/usr/bin/env python3
"""Measure A/V sync of an edited video against its source, before it goes to anyone.

  verify_sync.py SOURCE.mp4 EDITED.mp4 [--plan plan.json | --cut A-B ... --start S --end E]
      [--offset S [--body-end E]] [--points 5,30,...] [--audio-tol-ms 5]
      [--allow-static] [--json report.json]

Checks, at several points before, between and after every cut and near the end:
- audio: cross-correlates 2 s of the edited audio against the source around where that
  moment should be; the offset must be 0 ms (within --audio-tol-ms);
- video: matches a 48-frame run of the edited picture against the source (shift −3..+3
  frames); the shift must be 0 and the match close (--max-err). A single frame is NOT enough (episode 9: one frame looked
  right while the picture ran 0.5 s ahead).
- the edited file's audio and video streams end together, and both last the planned
  length (within one frame + AAC padding);
- every kept region (before, between and after the cuts) has at least one point where
  the sound was measured and one where a MOVING picture matched. A region with none
  (too short, silent, or a still picture) is unverified and fails the check; pass
  `--allow-static` only after looking at and listening to it yourself (it then prints
  a warning instead).
Exits 1 on any failure, also when nothing could be measured at all.

Assembled episode (cold open/teaser + intro + body + outro): the edit is the body
only. `--offset S` says the body starts S seconds into EDITED.mp4 (find it with
`find_offset_and_shift.py` or from the assembly log), and `--body-end E` where it
ends (the outro starts). Points are taken inside that window only and the window's
length is checked against the plan; without `--body-end` the body runs to the end.

Without --plan/--cut the edit is the identity: use that to check an upload copy
(e.g. the ~1 GB YouTube re-encode) against its master.
`--plan` is the JSON `render_cuts.py --plan-out` writes.
Needs ffmpeg/ffprobe and numpy.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

import numpy as np

SR = 8000
SILENCE = 0.005  # RMS below about -46 dBFS: too quiet to cross-correlate
W, H = 64, 36


# ---------------------------------------------------------------- pure helpers (tested)
def load_plan(plan=None, cuts=(), start=0.0, end=None):
    """Normalise to {'start', 'cuts': [{'out', 'in', 'removed', 'at'}], 'duration'}
    (source seconds; duration = expected edited length, None when the end is unknown)."""
    if plan:
        dur = plan.get("duration")
        if dur is None and plan.get("end") is not None:
            dur = plan["end"] - plan.get("start", 0.0) - sum(c["removed"] for c in plan["cuts"])
        return {"start": plan.get("start", 0.0), "cuts": plan["cuts"], "duration": dur}
    out, removed = [], 0.0
    for a, b in sorted(cuts):
        out.append({"out": a, "in": b, "removed": b - a, "at": a - start - removed})
        removed += b - a
    return {"start": start, "cuts": out, "duration": None if end is None else end - start - removed}


def region_of(t, plan):
    """Index of the kept region (0 = before the first cut) holding body time t."""
    return sum(1 for c in plan["cuts"] if t >= c["at"])


def duration_errors(vdur, adur, fps, expected=None, offset=0.0, body_end=None):
    """Stream ends and planned length, within one frame + AAC padding."""
    tol = 1.0 / fps + 0.03
    errs = []
    if abs(vdur - adur) > tol:
        errs.append(f"audio and video durations differ by {abs(vdur - adur):.3f} s")
    if expected is not None:
        if body_end is not None:
            got, what = body_end - offset, "body window"
        else:
            got, what = min(vdur, adur) - offset, "edited body"
        if abs(got - expected) > tol:
            errs.append(f"{what} is {got:.3f} s, the plan expects {expected:.3f} s")
    if body_end is not None and body_end > min(vdur, adur) + tol:
        errs.append(f"--body-end {body_end:.3f} is past the end of the file")
    return errs


def coverage(rows, plan, offset=0.0, allow_static=False):
    """(failures, warnings) for the measured rows: nothing measured, or a kept region
    without a measured sound point or a moving-picture point."""
    fails, warns = [], []
    if not rows:
        return ["no points were measured"], warns
    n = len(plan["cuts"]) + 1
    has_a, has_v = [False] * n, [False] * n
    for r in rows:
        if "error" in r:
            continue
        k = region_of(r["t"] - offset, plan)
        if r.get("ok_a"):
            has_a[k] = True
        if r.get("ok_v") and not r.get("static"):
            has_v[k] = True
    for k in range(n):
        miss = [w for w, ok in (("sound", has_a[k]), ("moving picture", has_v[k])) if not ok]
        if not miss:
            continue
        lo = 0.0 if k == 0 else plan["cuts"][k - 1]["at"]
        hi = plan["cuts"][k]["at"] if k < n - 1 else None
        where = f"kept region {k + 1} (body {lo:.2f}-" + (f"{hi:.2f})" if hi is not None else "end)")
        msg = f"{where}: no {' or '.join(miss)} point verified"
        if allow_static:
            warns.append(msg + " (allowed by --allow-static: check it by eye and ear)")
        else:
            fails.append(msg + "; add --points there, or check it by eye and pass --allow-static")
    return fails, warns


def to_source(t, plan):
    """Edited time -> source time. Points inside a transition have no single answer."""
    s = t + plan["start"]
    for c in plan["cuts"]:
        if t >= c["at"]:
            s += c["removed"]
    return s


def check_points(plan, duration, margin=1.5, span=2.0, every=300.0):
    """Points in every kept region (its start, end, and every ~`every` s between) plus
    near the end of the file, each at least `margin` s from a cut so transitions don't
    blur the measurement."""
    bounds = [0.0] + [c["at"] for c in plan["cuts"]] + [duration]
    pts = []
    for lo, hi in zip(bounds, bounds[1:]):
        a, b = lo + (margin if lo > 0 else 1.0), hi - margin - span
        if b < a:
            if hi - lo > span:
                pts.append(round((lo + hi - span) / 2, 3))
            continue
        n = max(1, min(8, int((b - a) // every)))
        pts += [round(a + (b - a) * i / (n + 1), 3) for i in range(n + 2)]
    late = duration - span - 3.0
    if late > 0 and all(abs(late - p) > 1 for p in pts):
        pts.append(round(late, 3))
    return sorted(set(p for p in pts if p >= 0))


def region_start(t, plan, margin=1.5):
    """Earliest edited time in the same kept region as t (to step back from silence)."""
    lo = 0.0
    for c in plan["cuts"]:
        if c["at"] <= t:
            lo = c["at"] + margin
    return lo


def xcorr_offset(ref, seg, sr=SR):
    """Index (in s) of the best normalised cross-correlation of seg inside ref, and its score."""
    n = len(ref) + len(seg)
    nfft = 1 << (n - 1).bit_length()
    c = np.fft.irfft(np.fft.rfft(ref, nfft) * np.conj(np.fft.rfft(seg, nfft)), nfft)[: len(ref) - len(seg) + 1]
    e = np.cumsum(np.concatenate([[0.0], ref ** 2]))
    sn = np.linalg.norm(seg) + 1e-9
    # floor the window energy so near-silent stretches of ref can't blow the score up
    win = np.maximum(np.sqrt(np.maximum(e[len(seg):] - e[: len(ref) - len(seg) + 1], 0)), 0.05 * sn)
    c = c / win / sn
    i = int(np.argmax(c))
    return i / sr, float(c[i])


def best_shift(ref, seq, pad):
    """ref = frames starting `pad` frames before the expected position; returns
    (shift, err, next_err) for the best match of seq at shifts -pad..+pad."""
    errs = []
    for s in range(-pad, pad + 1):
        o = pad + s
        if o < 0 or o + len(seq) > len(ref):
            errs.append(np.inf)
            continue
        errs.append(float(np.abs(ref[o:o + len(seq)] - seq).mean()))
    k = int(np.argmin(errs))
    nxt = sorted(errs)[1] if len(errs) > 1 else np.inf
    return k - pad, errs[k], nxt


def is_static(err, nxt, max_err=4.0):
    """A match whose neighbours fit almost as well: the picture barely moves."""
    return err <= max_err and nxt - err < 0.15


def rms(x):
    return float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0


# ---------------------------------------------------------------- media access
def audio(path, t, dur):
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(t, 0):.4f}", "-i", path, "-t", f"{dur:.4f}",
                        "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(b, np.float32).astype(float)


def frames(path, t, n):
    # raw luma plane, so differing range/matrix tags cannot shift the values
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(t, 0):.4f}", "-i", path, "-frames:v", str(n),
                        "-vf", f"scale={W}:{H},format=yuv420p,extractplanes=y", "-f", "rawvideo", "-"], capture_output=True).stdout
    return np.frombuffer(b, np.uint8).reshape(-1, H, W).astype(float)


def stream_info(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration,avg_frame_rate",
                        "-of", "json", path], capture_output=True, text=True, check=True)
    st = json.loads(r.stdout)["streams"]
    v = next(s for s in st if s["codec_type"] == "video")
    a = next(s for s in st if s["codec_type"] == "audio")
    num, den = v["avg_frame_rate"].split("/")
    if "duration" not in v or "duration" not in a:  # e.g. mkv: only the container knows
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", path], capture_output=True, text=True, check=True)
        v.setdefault("duration", r.stdout.strip())
        a.setdefault("duration", r.stdout.strip())
    return float(v["duration"]), float(a["duration"]), float(num) / float(den)


def measure(src, edited, plan, points, fps, audio_tol_ms=5.0, nframes=48, pad=3, max_err=4.0, offset=0.0):
    """points are body times; rows carry edited times (`t` = body time + offset)."""
    rows = []
    for b0 in points:
        # Silence (or a held end card) can't be cross-correlated: step back up to 30 s
        # inside the same kept region until there is sound.
        b, lo = b0, region_start(b0, plan)
        t = b + offset
        seg = audio(edited, t, 2.0)
        while len(seg) and rms(seg) < SILENCE and b - 5 >= max(lo, b0 - 30):
            b -= 5
            t = b + offset
            seg = audio(edited, t, 2.0)
        s = to_source(b, plan)
        r0 = max(0.0, s - 3.0)
        ref = audio(src, r0, 8.0)
        if len(seg) < SR or len(ref) <= len(seg) or rms(seg) < SILENCE:
            rows.append({"t": t, "src": s, "error": "silent: audio not measurable here", "skip": True})
            continue
        pos, corr = xcorr_offset(ref, seg)
        a_ms = 1000 * (r0 + pos - s)
        seq = frames(edited, t, nframes)
        refv = frames(src, s - pad / fps, len(seq) + 2 * pad)
        shift, err, nxt = best_shift(refv, seq, pad) if len(seq) else (None, None, None)
        static = shift is not None and is_static(err, nxt, max_err)
        ok_a = abs(a_ms) <= audio_tol_ms and corr > 0.5
        ok_v = shift is not None and err <= max_err and (shift == 0 or static)
        rows.append({"t": t, "src": round(s, 3), "audio_ms": round(a_ms, 1), "corr": round(corr, 3),
                     "shift": shift, "err": err, "next": nxt, "static": static,
                     "ok_a": bool(ok_a), "ok_v": bool(ok_v), "ok": bool(ok_a and ok_v)})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("edited")
    ap.add_argument("--plan", help="plan JSON from render_cuts.py --plan-out")
    ap.add_argument("--cut", action="append", default=[], help="A-B source seconds removed (no plan)")
    ap.add_argument("--start", type=float, default=0.0, help="source second where the edit starts (no plan)")
    ap.add_argument("--end", type=float, help="source second where the edit ends (no plan; default: source end)")
    ap.add_argument("--offset", type=float, default=0.0,
                    help="edited second where the body starts (cold open/teaser/intro before it)")
    ap.add_argument("--body-end", type=float, help="edited second where the body ends (outro after it)")
    ap.add_argument("--points", help="comma-separated BODY times (edited time minus --offset)")
    ap.add_argument("--audio-tol-ms", type=float, default=5.0)
    ap.add_argument("--max-err", type=float, default=4.0,
                    help="mean grey-level error (0-255, 64x36) above which the pictures don't match")
    ap.add_argument("--allow-static", action="store_true",
                    help="an unverifiable kept region (still picture, silence, too short) passes with a warning; "
                         "only after checking it by eye and ear")
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    cuts = [tuple(float(x) for x in c.split("-", 1)) for c in a.cut]
    raw = json.load(open(a.plan)) if a.plan else None
    end = a.end
    if raw is None and end is None:
        end = min(stream_info(a.source)[:2])  # identity/--cut: the edit runs to the source's end
    plan = load_plan(raw, cuts, a.start, end)
    vdur, adur, fps = stream_info(a.edited)
    body_dur = (a.body_end if a.body_end is not None else min(vdur, adur)) - a.offset
    pts = [float(x) for x in a.points.split(",")] if a.points else check_points(plan, body_dur)
    rows = measure(a.source, a.edited, plan, pts, fps, a.audio_tol_ms, max_err=a.max_err, offset=a.offset)
    print(f"edited: video {vdur:.3f} s, audio {adur:.3f} s, {fps:g} fps; body from {a.offset:.3f} s; "
          f"cuts at body " + (", ".join(f"{c['at']:.2f}" for c in plan["cuts"]) or "none"))
    print(f"{'t':>9} {'source':>9} {'audio_ms':>8} {'corr':>5} {'shift':>5}  result")
    bad = 0
    for r in rows:
        if "error" in r:
            print(f"{r['t']:9.2f} {r['src']:9.2f}  {r['error']}")
            continue
        tag = "ok" if r["ok"] else "FAIL"
        if r["err"] is not None and r["err"] > a.max_err:
            tag += f" (picture doesn't match the source here: error {r['err']:.1f})"
        elif r["static"]:
            tag += " (static picture: video shift not measurable)"
        print(f"{r['t']:9.2f} {r['src']:9.2f} {r['audio_ms']:+8.1f} {r['corr']:5.2f} {r['shift']:+5d}  {tag}")
        bad += not r["ok"]
    problems = duration_errors(vdur, adur, fps, plan["duration"], a.offset, a.body_end)
    fails, warns = coverage(rows, plan, a.offset, a.allow_static)
    problems += fails
    for w in warns:
        print(f"WARN: {w}")
    for p in problems:
        print(f"FAIL: {p}")
    if a.json:
        json.dump({"rows": rows, "video_duration": vdur, "audio_duration": adur, "failures": problems,
                   "warnings": warns}, open(a.json, "w"), indent=1, default=float)
    ok = bad == 0 and not problems
    print("SYNC OK" if ok else "SYNC FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
