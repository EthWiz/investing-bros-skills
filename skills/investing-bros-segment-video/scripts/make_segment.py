#!/usr/bin/env python3
"""Make one segment package from a raw-transcript range: cut, nudge, loudness, sync check, Drive files.

  make_segment.py EP --slot 01|02 --type צלילה --topic זהב --range A-B [--drop A-B ...] [--allow-cut]
                  --source FILE --source-type raw|assembled [--offset S]
                  [--title-file F --description-file F] [--thumb F] [--nudge PNG] [--force] [--dry-run]

Times are RAW TRANSCRIPT seconds (the timeline of extras/transcript/segments.json), the same for
every source:
- `--source-type raw`: FILE is the raw master video (extras/investing-bros-episode-raw-untrimmed.mp4);
  source time = raw time.
- `--source-type assembled`: FILE is the full video episode (video/פרק-N-וידאו.mp4); `--offset` = the
  second the body starts in it (teaser + intro, from the assembly log). Source time = offset + the
  edited time of the raw time (edit_map.py on extras/edit.json).
A range that crosses one of the episode's internal cuts (edit.json "cuts") is refused unless
`--allow-cut`: from the raw master the cut is then removed from the segment too; the assembled video
no longer has it. `--drop A-B` removes a tangent inside the segment (raw seconds, in a pause).

Steps (each with the show's own scripts, copied into this skill):
1. render_cuts.py: cut picture and sound in one pass, frame-snapped (`--plan-out`);
2. verify_sync.py against the source with that plan: must say SYNC OK;
3. the burned-in nudge (assets/nudge-overlay.png from nudge_overlay.py) at 30.0-35.0 s with a 0.3 s
   fade, and the loudness gain to the episode's -16 LUFS (true peak <= -1.5 dBTP), in one encode;
4. verify_sync.py of the final file against the cut (points outside the nudge window): SYNC OK;
5. the package in EP/segments/ (show Drive tree): סגמנט-NN-<סוג>-<נושא>.mp4, .txt (title, blank line,
   description) when given, -thumb.jpg when given, youtube-סגמנט-NN.md; and the package record
   EP/extras/segment-NN.json (ranges, mapping, edit snapshot, plan, sync results, loudness, sha256s),
   which investing-bros-producer reads.
Exit 0 = package made, 1 = refused or a check failed, 2 = usage error.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import edit_map  # noqa: E402

TARGET_LUFS, MAX_TP = -16.0, -1.5
NUDGE_START, NUDGE_END, FADE = 30.0, 35.0, 0.3


class Refused(Exception):
    pass


def parse_range(text: str):
    a, b = edit_map.parse_cut(text)
    if b <= a:
        raise Refused(f"range {text}: end must be after start")
    return a, b


def edit_cuts_inside(edit: dict, a: float, b: float):
    """Episode cuts the raw range [a, b] crosses; refuses a range that starts or ends inside one."""
    inside = []
    for c, d in sorted(map(tuple, edit.get("cuts", []))):
        if c < a < d or c < b < d:
            raise Refused(f"the range {a}-{b} starts or ends inside the episode cut {c}-{d}; move it to a pause "
                          "outside the cut")
        if a <= c and d <= b:
            inside.append((c, d))
    return inside


def plan_segment(edit: dict, rng, drops=(), source_type="raw", offset=0.0, allow_cut=False) -> dict:
    """Map a raw-transcript range (and drops inside it) to source seconds. Pure (tested)."""
    a, b = rng
    start, end = float(edit["start"]), float(edit["end"])
    if a < start or b > end:
        raise Refused(f"the range {a}-{b} is outside the episode ({start}-{end} raw)")
    crossed = edit_cuts_inside(edit, a, b)
    if crossed and not allow_cut:
        raise Refused("the range crosses the episode's internal cut(s) "
                      + ", ".join(f"{c}-{d}" for c, d in crossed) + "; pick a range without one, or pass --allow-cut")
    drops = sorted(tuple(d) for d in drops)
    for x, y in drops:
        if not (a < x < y < b):
            raise Refused(f"drop {x}-{y} must lie inside the range {a}-{b}")
    removed_raw = sorted(set(drops) | set(crossed))
    for (x1, y1), (x2, y2) in zip(removed_raw, removed_raw[1:]):
        if x2 < y1:
            raise Refused(f"drop {x2}-{y2} overlaps {x1}-{y1}")
    if source_type == "raw":
        to_src = (lambda t: t)
        src_cuts = [list(c) for c in removed_raw]
    elif source_type == "assembled":
        cuts = edit.get("cuts", [])

        def to_src(t):
            e = edit_map.raw_to_edited(t, start, end, cuts)
            if e is None:
                raise Refused(f"raw {t} is not in the edited episode (inside a cut)")
            return round(offset + e, 6)
        for x, y in drops:
            edit_cuts_inside(edit, x, y)  # a drop endpoint inside an episode cut is refused
        src_cuts = [[to_src(x), to_src(y)] for x, y in drops]
    else:
        raise Refused("source type is raw or assembled")
    def minus(removed):
        out, cur = [], a
        for x, y in removed:
            out.append([cur, x])
            cur = y
        out.append([cur, b])
        return out
    kept = minus(removed_raw)
    # the picked range minus the segment's own drops (episode cuts inside stay in): what the Producer watches,
    # so a new cut there, or restoring a crossed one, makes this render stale
    selected = minus(drops)
    return {"raw_range": [a, b], "raw_drops": [list(d) for d in drops], "episode_cuts_crossed": [list(c) for c in crossed],
            "raw_ranges": kept, "selected_ranges": selected, "source_type": source_type, "offset": offset if source_type == "assembled" else 0.0,
            "source_start": to_src(a), "source_end": to_src(b), "source_cuts": src_cuts,
            "length": round(sum(y - x for x, y in kept), 3)}


# ---- commands ---------------------------------------------------------------------------------------

def render_cmd(source, out, plan, plan_out):
    cmd = [sys.executable, str(HERE / "render_cuts.py"), str(source), str(out),
           "--start", f"{plan['source_start']}", "--end", f"{plan['source_end']}", "--plan-out", str(plan_out)]
    for x, y in plan["source_cuts"]:
        cmd += ["--cut", f"{x}-{y}"]
    return cmd


def verify_cmd(source, edited, plan_file=None, points=None):
    cmd = [sys.executable, str(HERE / "verify_sync.py"), str(source), str(edited)]
    if plan_file:
        cmd += ["--plan", str(plan_file)]
    if points:
        cmd += ["--points", ",".join(f"{p:g}" for p in points)]
    return cmd


def check_points(duration: float) -> list:
    """Identity-check points for the final file, outside the nudge window (the overlay changes the picture)."""
    pts = [p for p in (5.0, 15.0, 45.0) if p < duration - 3]
    t = 120.0
    while t < duration - 5:
        pts.append(t)
        t += 120.0
    pts.append(max(1.0, round(duration - 5.0, 1)))
    return sorted({p for p in pts if not (NUDGE_START - 2 <= p <= NUDGE_END + 2)})


def gain_db(lufs: float, true_peak: float) -> float:
    """Gain to -16 LUFS, held back so the true peak stays <= -1.5 dBTP; 0 when within 0.5 LU and the peak is
    already under the ceiling (a peak over it is always brought down, however small the cut)."""
    g = min(TARGET_LUFS - lufs, MAX_TP - true_peak)
    if true_peak > MAX_TP:
        return round(g, 2)
    return 0.0 if abs(g) < 0.5 else round(g, 2)


def parse_loudness(log: str):
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", log)
    p = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", log)
    if not i or not p:
        raise Refused("could not read the loudness (ffmpeg ebur128)")
    return float(i[-1]), float(p[-1])


def loudness_cmd(path):
    return ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0", "-af", "ebur128=peak=true",
            "-f", "null", "-"]


def burn_cmd(cut, nudge, out, gain):
    fc = (f"[1:v][0:v]scale2ref[n][v];[n]format=rgba,fade=t=in:st={NUDGE_START}:d={FADE}:alpha=1,"
          f"fade=t=out:st={NUDGE_END - FADE}:d={FADE}:alpha=1[nf];"
          f"[v][nf]overlay=0:0:shortest=1:enable='between(t,{NUDGE_START},{NUDGE_END})'[out]")
    audio = ["-c:a", "copy"] if gain == 0 else ["-af", f"volume={gain}dB", "-c:a", "aac", "-b:a", "192k"]
    return ["ffmpeg", "-y", "-hide_banner", "-i", str(cut), "-loop", "1", "-i", str(nudge), "-filter_complex", fc,
            "-map", "[out]", "-map", "0:a:0", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-pix_fmt", "yuv420p", *audio, "-movflags", "+faststart", str(out)]


def duration_cmd(path):
    return ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def run(cmd, log=None):
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = (r.stdout or "") + (r.stderr or "")
    if log:
        Path(log).write_text(out, encoding="utf-8")
    return r.returncode, out


# ---- the package --------------------------------------------------------------------------------------

def names(slot, typ, topic):
    stem = f"סגמנט-{slot}-{typ}-{topic}"
    return stem, {"mp4": f"{stem}.mp4", "txt": f"{stem}.txt", "thumb": f"{stem}-thumb.jpg",
                  "notes": f"youtube-סגמנט-{slot}.md"}


def check_slot_free(seg: Path, slot: str, stem: str, force: bool):
    others = sorted(p.name for p in seg.glob(f"סגמנט-{slot}-*.mp4") if p.name != f"{stem}.mp4")
    if others:
        raise Refused(f"segments/ already has a final video for slot {slot}: {', '.join(others)}; move it to "
                      "extras/ first (one final candidate per slot)")
    if (seg / f"{stem}.mp4").exists() and not force:
        raise Refused(f"segments/{stem}.mp4 exists; --force replaces it")


def notes_text(slot, typ, plan, title):
    m = lambda t: edit_map.mmss(t)  # noqa: E731
    return "\n".join([
        f"# סגמנט {slot}",
        f"- type: {typ}",
        f"- title: {title or '(from the .txt once chosen)'}",
        f"- raw range: {plan['raw_range'][0]}-{plan['raw_range'][1]} s"
        + (f", dropped {plan['raw_drops']}" if plan["raw_drops"] else "")
        + (f", episode cuts inside {plan['episode_cuts_crossed']}" if plan["episode_cuts_crossed"] else ""),
        f"- length: {m(plan['length'])}",
        "- status: made; Private upload pending (investing-bros-episode-upload, yt_upload.py --asset seg" + slot + ")",
        "- URL: (copy it from the upload record)", ""])


def make(a, runner=run) -> dict:
    ep = Path(a.ep)
    edit = json.loads((ep / "extras" / "edit.json").read_text(encoding="utf-8")) if not a.edit else \
        json.loads(Path(a.edit).read_text(encoding="utf-8"))
    if a.source_type == "assembled" and a.offset is None:
        raise Refused("--source-type assembled needs --offset (teaser + intro seconds, from the assembly log)")
    plan = plan_segment(edit, parse_range(a.range), [parse_range(d) for d in a.drop], a.source_type,
                        a.offset or 0.0, a.allow_cut)
    seg = ep / "segments"
    work = Path(a.work) if a.work else ep / "extras" / f"segment-{a.slot}"
    stem, files = names(a.slot, a.type, a.topic)
    check_slot_free(seg, a.slot, stem, a.force)
    if a.slot == "01" and a.type != "צלילה":
        raise Refused("segment 01 is the deep dive: --type צלילה")
    nudge = Path(a.nudge) if a.nudge else HERE.parent / "assets" / "nudge-overlay.png"
    cut, plan_file, final = work / f"{stem}-cut.mp4", work / f"{stem}.plan.json", seg / files["mp4"]
    cmds = {"render": render_cmd(a.source, cut, plan, plan_file),
            "verify_cut": verify_cmd(a.source, cut, plan_file)}
    if a.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=1))
        for k, c in cmds.items():
            print(f"{k}: {' '.join(c)}")
        print(f"then: loudness, nudge {NUDGE_START}-{NUDGE_END} s, verify_sync final vs cut, package in {seg}")
        return {"plan": plan, "cmds": cmds}
    work.mkdir(parents=True, exist_ok=True)
    seg.mkdir(parents=True, exist_ok=True)
    rc, out = runner(cmds["render"], work / "render.log")
    if rc:
        raise Refused(f"render_cuts.py failed (see {work / 'render.log'})")
    rc, out = runner(cmds["verify_cut"], work / "verify-cut.log")
    sync = "SYNC OK" if rc == 0 and "SYNC OK" in out else "SYNC FAILED"
    if sync != "SYNC OK":
        raise Refused(f"verify_sync.py: the cut is not in sync (see {work / 'verify-cut.log'})")
    _, out = runner(loudness_cmd(cut))
    lufs, tp = parse_loudness(out)
    g = gain_db(lufs, tp)
    rc, _ = runner(burn_cmd(cut, nudge, final, g), work / "burn.log")
    if rc:
        raise Refused(f"burning the nudge failed (see {work / 'burn.log'})")
    rc, out = runner(duration_cmd(final))
    dur = float(out.strip().splitlines()[-1]) if rc == 0 and out.strip() else plan["length"]
    rc, out = runner(verify_cmd(cut, final, points=check_points(dur)), work / "verify-final.log")
    sync_final = "SYNC OK" if rc == 0 and "SYNC OK" in out else "SYNC FAILED"
    if sync_final != "SYNC OK":
        raise Refused(f"verify_sync.py: the final file drifted from the cut (see {work / 'verify-final.log'})")
    title = Path(a.title_file).read_text(encoding="utf-8").strip() if a.title_file else ""
    if a.title_file and a.description_file:
        desc = Path(a.description_file).read_text(encoding="utf-8").strip()
        (seg / files["txt"]).write_text(f"{title}\n\n{desc}\n", encoding="utf-8")
    if a.thumb:
        shutil.copyfile(a.thumb, seg / files["thumb"])
    (seg / files["notes"]).write_text(notes_text(a.slot, a.type, plan, title), encoding="utf-8")
    made = {k: f"segments/{v}" for k, v in files.items() if (seg / v).is_file()}
    rec = {**plan, "slot": a.slot, "type": a.type, "topic": a.topic,
           "edit": {"start": edit["start"], "end": edit["end"], "cuts": edit.get("cuts", [])},
           "source": str(a.source), "plan_file": str(plan_file), "sync": sync, "sync_final": sync_final,
           "loudness": {"lufs": lufs, "true_peak": tp, "gain_db": g, "target": TARGET_LUFS},
           "nudge": {"file": nudge.name, "start": NUDGE_START, "end": NUDGE_END}, "duration": dur,
           "output": f"segments/{files['mp4']}", "output_sha256": sha256(final),
           "files": {k: {"path": p, "sha256": sha256(ep / p)} for k, p in made.items()},
           "made_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (ep / "extras" / f"segment-{a.slot}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1),
                                                          encoding="utf-8")
    missing = [k for k in ("txt", "thumb") if k not in made]
    print(f"made {final} ({edit_map.mmss(dur)}), {sync}, {lufs:.1f} LUFS {g:+.1f} dB; record "
          f"extras/segment-{a.slot}.json" + (f"; still to add: {', '.join(missing)}" if missing else ""))
    return rec


def parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ep", help="the episode folder (Drive layout)")
    ap.add_argument("--slot", choices=["01", "02"], required=True)
    ap.add_argument("--type", required=True, help="Hebrew type word for the file name (01: צלילה)")
    ap.add_argument("--topic", required=True, help="Hebrew topic word(s) for the file name, joined with -")
    ap.add_argument("--range", required=True, help="raw transcript seconds A-B")
    ap.add_argument("--drop", action="append", default=[], help="raw A-B removed inside the segment (repeatable)")
    ap.add_argument("--allow-cut", action="store_true", help="the range may cross an episode cut")
    ap.add_argument("--source", required=True)
    ap.add_argument("--source-type", choices=["raw", "assembled"], required=True)
    ap.add_argument("--offset", type=float, help="assembled: the second the body starts (teaser + intro)")
    ap.add_argument("--edit", help="edit.json (default EP/extras/edit.json)")
    ap.add_argument("--title-file"); ap.add_argument("--description-file"); ap.add_argument("--thumb")
    ap.add_argument("--nudge", help="overlay PNG (default assets/nudge-overlay.png)")
    ap.add_argument("--work", help="work folder (default EP/extras/segment-NN/)")
    ap.add_argument("--force", action="store_true"); ap.add_argument("--dry-run", action="store_true")
    return ap


def main(argv=None, runner=run) -> int:
    a = parser().parse_args(argv)
    try:
        make(a, runner)
    except Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    except (ValueError, KeyError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
