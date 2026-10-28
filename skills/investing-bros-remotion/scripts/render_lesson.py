#!/usr/bin/env python3
"""Render a crypto-course lesson (the template's 16:9 "Lesson" composition) over its joined base.

Usage:
    python3 render_lesson.py --props props.json --base base.mp4 --fonts fonts/ --logo logo.png \\
        --out lesson.mp4 [--work DIR] [--browser PATH] [--concurrency 4]
    python3 render_lesson.py ... --stills 5,25,38,50,64,90,125,178    # QA frames -> <out>_stills.jpg
    python3 render_lesson.py ... --transitions                        # 2.5 s around every cut -> <out>_transitions.mp4
    python3 render_lesson.py ... --stills 210,236 --vertical          # 9:16 scenes alone -> <out>_vertical_stills.jpg
    python3 render_lesson.py ... --patch                              # re-render only what changed since <out>
    python3 render_lesson.py ... --patch --range 30-72                # after a template change: these seconds

props.json from make_lesson_props.py; base.mp4 from make_lesson_base.py (investing-bros-crypto-course).
Staging, the npm install and the browser lookup are render_short.py's; the scenes' images (the props'
assetSources) are staged into public/assets. --transitions renders, with sound, 1 s before to 1.5 s
after every take cut and layout change and joins them into one file: stills can't show whether a
cut, a glide or a caption change lands on the word. After the full render the sound is lined up
with the base again: Remotion's AAC keeps the encoder's priming as audio (about 43 ms late on lesson 1),
so the delay is measured against the base and the audio track shifted, without re-encoding.
Then run check_lesson.py. A lesson renders at 30 fps,
about 2.6x real time on 10 cores at --concurrency 8 (3:16 took 8.5 min): run it in the background.
Every render leaves `<out>.render.json` (the props, and hashes of the template, base and images), so a later
--patch renders only the stretches whose props changed and splices them into <out> (lesson_patch.py has the rules
and the checks): a new chart or a caption fix takes a minute or two instead of the whole lesson.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lesson_patch  # noqa: E402
from check_lesson import lag_seconds, pcm  # noqa: E402
from render_short import TEMPLATE, common_flags, find_browser, install, stage_assets, stage_project  # noqa: E402

FPS = 30


def render_cmd(out: Path, props: Path, browser=None, concurrency=4):
    return ["npx", "remotion", "render", "src/index.ts", "Lesson", str(out), *common_flags(props, browser),
            "--codec=h264", "--crf=18", f"--concurrency={concurrency}"]


def still_cmd(out: Path, props: Path, frame: int, browser=None, composition="Lesson"):
    return ["npx", "remotion", "still", "src/index.ts", composition, str(out), f"--frame={frame}",
            *common_flags(props, browser)]


def transition_times(props) -> list:
    """Every moment the picture changes by cut or layout: take boundaries and segment boundaries."""
    times = {b["start"] for b in props["beats"][1:]}
    segs = props["segments"]
    times |= {b["start"] for a, b in zip(segs, segs[1:]) if (a["mode"], a.get("zoom")) != (b["mode"], b.get("zoom"))}
    return sorted(round(t, 3) for t in times if 0 < t < props["duration"])


def clip_cmd(out: Path, props: Path, first: int, last: int, browser=None):
    return ["npx", "remotion", "render", "src/index.ts", "Lesson", str(out), *common_flags(props, browser),
            "--codec=h264", "--crf=23", f"--frames={first}-{last}"]


def range_cmd(out: Path, props: Path, first: int, last: int, browser=None, concurrency=4):
    """Frames first..last of the Lesson, muted and with the full render's codec settings, for --patch."""
    return [*render_cmd(out, props, browser, concurrency), f"--frames={first}-{last}", "--muted"]


def patch(out: Path, props: dict, props_path: Path, base: Path, work: Path, browser, concurrency: int, ranges: list):
    sidecar = lesson_patch.sidecar_path(out)
    if not out.is_file() or not sidecar.is_file():
        raise SystemExit(f"error: --patch needs {out.name} and {sidecar.name} from an earlier render; render in full")
    old = json.loads(sidecar.read_text(encoding="utf-8"))
    fp = lesson_patch.fingerprint(props, TEMPLATE / "src", base)
    why = lesson_patch.why_full(old["props"], props, old["fingerprint"], fp, explicit=bool(ranges))
    if why:
        raise SystemExit("error: render in full: " + "; ".join(why))
    ranges = lesson_patch.merge(ranges, props["duration"]) if ranges else lesson_patch.changed_ranges(old["props"], props)
    if not ranges:
        print(f"nothing changed since {out.name}")
        return
    total = lesson_patch.frame_count(out)
    parts = lesson_patch.plan(lesson_patch.snap(ranges, lesson_patch.keyframes(out), total), total)
    prev = out.with_name(f"{out.stem}_prev{out.suffix}")
    out.replace(prev)

    def render(first, last, dst):
        subprocess.run(range_cmd(dst, props_path, first, last, browser, concurrency), cwd=work, check=True)

    try:
        lesson_patch.splice(prev, out, parts, render, out.with_name(f"{out.stem}_patch"))
    except BaseException:
        prev.replace(out)
        raise
    prev.unlink()
    lesson_patch.write_sidecar(out, props, fp)
    redone = sum(b - a for kind, a, b in parts if kind == "render")
    spans = ", ".join(f"{a / FPS:.1f}-{b / FPS:.1f} s" for kind, a, b in parts if kind == "render")
    print(f"patched {spans}: {redone / FPS:.0f} of {total / FPS:.0f} s rendered")


def measured_delay(video: Path, base: Path, at=2.0, seconds=3.0):
    return lag_seconds(pcm(base, at, seconds), pcm(video, at, seconds))


def shift_audio_cmd(src: Path, dst: Path, delay: float):
    return ["ffmpeg", "-v", "error", "-y", "-i", str(src), "-itsoffset", f"{-delay:.6f}", "-i", str(src),
            "-map", "0:v:0", "-map", "1:a:0", "-c", "copy", "-movflags", "+faststart", str(dst)]


def line_up_audio(out: Path, base: Path, tolerance=0.005):
    delay = measured_delay(out, base)
    if delay is None or abs(delay) <= tolerance:
        return 0.0
    raw = out.with_name(f"{out.stem}_unsynced{out.suffix}")
    out.replace(raw)
    subprocess.run(shift_audio_cmd(raw, out, delay), check=True)
    raw.unlink()
    return delay


def stage_scene_assets(work: Path, props: dict):
    for key, rel in props.get("assets", {}).items():
        dst = work / "public" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(props["assetSources"][key], dst)


def contact_sheet(paths, labels, out: Path, cols=3, vertical=False):
    from PIL import Image, ImageDraw
    w, h = (360, 640) if vertical else (640, 360)
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (w * cols, h * rows), "white")
    for i, (p, lab) in enumerate(zip(paths, labels)):
        im = Image.open(p).convert("RGB").resize((w, h))
        ImageDraw.Draw(im).text((8, h - 20), lab, fill="red")
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    sheet.save(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--props", required=True)
    ap.add_argument("--base", required=True, help="joined takes from make_lesson_base.py")
    ap.add_argument("--fonts", required=True, help="folder with the static Heebo TTFs (brand.py fonts)")
    ap.add_argument("--logo", required=True, help="investing-bros-brand assets/logo-solid.png")
    ap.add_argument("--out", required=True)
    ap.add_argument("--work")
    ap.add_argument("--browser")
    ap.add_argument("--concurrency", type=int, default=max(1, min(8, (os.cpu_count() or 2) - 2)))
    ap.add_argument("--stills", help="comma-separated seconds: render QA stills instead of the video")
    ap.add_argument("--transitions", action="store_true", help="render 2.5 s around every cut instead of the video")
    ap.add_argument("--vertical", action="store_true",
                    help="with --stills: the 9:16 LessonScenes composition (scenes marked vertical only)")
    ap.add_argument("--patch", action="store_true",
                    help="re-render only what changed since the last render of --out, and splice it in")
    ap.add_argument("--range", help="with --patch: the seconds to re-render, e.g. 30-72,100-110")
    a = ap.parse_args(argv)
    if a.vertical and not a.stills:
        ap.error("--vertical needs --stills")
    if a.range and not a.patch:
        ap.error("--range needs --patch")
    out = Path(a.out).resolve()
    work = Path(a.work).resolve() if a.work else out.parent / "remotion"
    props_path = Path(a.props).resolve()
    props = json.loads(props_path.read_text(encoding="utf-8"))
    if stage_project(work):
        install(work)
    stage_assets(work, Path(a.base), Path(a.fonts), Path(a.logo))
    stage_scene_assets(work, props)
    browser = find_browser(a.browser)
    if not browser:
        print("note: no local headless Chrome found; Remotion will try to download one", file=sys.stderr)
    if a.stills:
        secs = [float(s) for s in a.stills.split(",")]
        shots = []
        for s in secs:
            if s > props["duration"]:
                raise SystemExit(f"error: still at {s} s is past the end ({props['duration']} s)")
            tag = "_vertical" if a.vertical else ""
            png = out.with_name(f"{out.stem}{tag}_still_{s:g}.png")
            subprocess.run(still_cmd(png, props_path, round(s * FPS), browser, "LessonScenes" if a.vertical else "Lesson"),
                           cwd=work, check=True)
            shots.append(png)
        sheet = out.with_name(f"{out.stem}{'_vertical' if a.vertical else ''}_stills.jpg")
        contact_sheet(shots, [f"{s:g}s" for s in secs], sheet, cols=4 if a.vertical else 3, vertical=a.vertical)
        print(sheet)
        return 0
    if a.transitions:
        last_frame = round(props["duration"] * FPS) - 1
        clips = []
        for t in transition_times(props):
            clip = out.with_name(f"{out.stem}_cut_{t:07.2f}.mp4")
            first, last = max(0, round((t - 1.0) * FPS)), min(last_frame, round((t + 1.5) * FPS))
            subprocess.run(clip_cmd(clip, props_path, first, last, browser), cwd=work, check=True)
            clips.append(clip)
        listing = out.with_name(f"{out.stem}_transitions.txt")
        listing.write_text("".join(f"file '{c}'\n" for c in clips), encoding="utf-8")
        joined = out.with_name(f"{out.stem}_transitions.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
                        "-c", "copy", str(joined)], check=True)
        print(joined)
        return 0
    if a.patch:
        ranges = [lesson_patch.parse_range(r) for r in a.range.split(",")] if a.range else []
        patch(out, props, props_path, Path(a.base), work, browser, a.concurrency, ranges)
        print(out)
        return 0
    subprocess.run(render_cmd(out, props_path, browser, a.concurrency), cwd=work, check=True)
    delay = line_up_audio(out, Path(a.base))
    if delay:
        print(f"audio was {delay * 1000:+.0f} ms off the base; shifted back")
    lesson_patch.write_sidecar(out, props, lesson_patch.fingerprint(props, TEMPLATE / "src", Path(a.base)))
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
