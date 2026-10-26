#!/usr/bin/env python3
"""Render a crypto-course lesson (the template's 16:9 "Lesson" composition) over its joined base.

Usage:
    python3 render_lesson.py --props props.json --base base.mp4 --fonts fonts/ --logo logo.png \\
        --out lesson.mp4 [--work DIR] [--browser PATH] [--concurrency 4]
    python3 render_lesson.py ... --stills 5,25,38,50,64,90,125,178    # QA frames -> <out>_stills.jpg

props.json from make_lesson_props.py; base.mp4 from make_lesson_base.py (investing-bros-crypto-course).
Staging, the npm install and the browser lookup are render_short.py's. A lesson renders at 30 fps,
about 2.6x real time on 10 cores at --concurrency 8 (3:16 took 8.5 min): run it in the background.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_short import common_flags, find_browser, install, stage_assets, stage_project  # noqa: E402

FPS = 30


def render_cmd(out: Path, props: Path, browser=None, concurrency=4):
    return ["npx", "remotion", "render", "src/index.ts", "Lesson", str(out), *common_flags(props, browser),
            "--codec=h264", "--crf=18", f"--concurrency={concurrency}"]


def still_cmd(out: Path, props: Path, frame: int, browser=None):
    return ["npx", "remotion", "still", "src/index.ts", "Lesson", str(out), f"--frame={frame}",
            *common_flags(props, browser)]


def contact_sheet(paths, labels, out: Path, cols=3):
    from PIL import Image, ImageDraw
    w, h = 640, 360
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
    a = ap.parse_args(argv)
    out = Path(a.out).resolve()
    work = Path(a.work).resolve() if a.work else out.parent / "remotion"
    props_path = Path(a.props).resolve()
    props = json.loads(props_path.read_text(encoding="utf-8"))
    if stage_project(work):
        install(work)
    stage_assets(work, Path(a.base), Path(a.fonts), Path(a.logo))
    browser = find_browser(a.browser)
    if not browser:
        print("note: no local headless Chrome found; Remotion will try to download one", file=sys.stderr)
    if a.stills:
        secs = [float(s) for s in a.stills.split(",")]
        shots = []
        for s in secs:
            if s > props["duration"]:
                raise SystemExit(f"error: still at {s} s is past the end ({props['duration']} s)")
            png = out.with_name(f"{out.stem}_still_{s:g}.png")
            subprocess.run(still_cmd(png, props_path, round(s * FPS), browser), cwd=work, check=True)
            shots.append(png)
        sheet = out.with_name(f"{out.stem}_stills.jpg")
        contact_sheet(shots, [f"{s:g}s" for s in secs], sheet)
        print(sheet)
        return 0
    subprocess.run(render_cmd(out, props_path, browser, a.concurrency), cwd=work, check=True)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
