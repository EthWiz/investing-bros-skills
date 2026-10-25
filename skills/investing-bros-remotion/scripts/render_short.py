#!/usr/bin/env python3
"""Render a short with the Remotion template: stage, install, render, write the layout file.

Usage:
    python3 render_short.py --props props.json --base clean.mp4 --fonts fonts/ --logo logo.png \\
        --out short.mp4 [--work DIR] [--browser PATH] [--concurrency 2]
    python3 render_short.py ... --stills 1,9.5,12,17,27      # QA frames -> <out>_stills.jpg, no video

--work (default: <out dir>/remotion) gets a copy of template/ and its node_modules (npm ci,
once). The base video, Heebo TTFs (brand.py fonts) and logo.png are staged into public/.
Chrome: --browser, else $REMOTION_BROWSER_EXECUTABLE, else a Playwright headless shell if
one is installed, else Remotion downloads its own. Writes <out>_layout.json for
check_short.py (no end card: the short ends on the payoff with the CTA).
"""
import argparse
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "template"
FONTS = ("Heebo-SemiBold.ttf", "Heebo-ExtraBold.ttf", "Heebo-Black.ttf")
FPS = 24
BROWSER_GLOBS = (
    "/opt/pw-browsers/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell",
    "~/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell",
    "~/.cache/ms-playwright/chromium_headless_shell-*/chrome-linux/headless_shell",
    "~/Library/Caches/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-mac-arm64/chrome-headless-shell",
)


def find_browser(explicit=None, env=None, globs=BROWSER_GLOBS):
    env = os.environ if env is None else env
    if explicit:
        return explicit
    if env.get("REMOTION_BROWSER_EXECUTABLE"):
        return env["REMOTION_BROWSER_EXECUTABLE"]
    for pattern in globs:
        hits = sorted(glob.glob(os.path.expanduser(pattern)))
        if hits:
            return hits[-1]
    return None


def stage_project(work: Path, template: Path = TEMPLATE) -> bool:
    """Copy the template into work (keeping an existing node_modules). True if npm ci is needed."""
    work.mkdir(parents=True, exist_ok=True)
    for item in template.iterdir():
        if item.name in ("node_modules", "out", "public"):
            continue
        dst = work / item.name
        if item.is_dir():
            shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(item, dst)
        else:
            shutil.copy2(item, dst)
    (work / "public").mkdir(exist_ok=True)
    lock = (work / "package-lock.json").read_bytes()
    stamp = work / "node_modules" / ".template-lock-sha256"
    digest = hashlib.sha256(lock).hexdigest()
    return not (stamp.is_file() and stamp.read_text().strip() == digest)


def install(work: Path):
    subprocess.run(["npm", "ci", "--no-audit", "--no-fund"], cwd=work, check=True)
    digest = hashlib.sha256((work / "package-lock.json").read_bytes()).hexdigest()
    (work / "node_modules" / ".template-lock-sha256").write_text(digest)


def stage_assets(work: Path, base: Path, fonts: Path, logo: Path):
    missing = [f for f in FONTS if not (fonts / f).is_file()]
    if missing:
        raise SystemExit(f"error: {fonts} lacks {', '.join(missing)} (make them with brand.py fonts)")
    pub = work / "public"
    (pub / "fonts").mkdir(parents=True, exist_ok=True)
    shutil.copy2(base, pub / "base.mp4")
    for f in FONTS:
        shutil.copy2(fonts / f, pub / "fonts" / f)
    shutil.copy2(logo, pub / "logo.png")


def common_flags(props: Path, browser):
    flags = [f"--props={props}", "--log=error"]
    if browser:
        flags.append(f"--browser-executable={browser}")
    return flags


def render_cmd(out: Path, props: Path, browser=None, concurrency=2):
    return ["npx", "remotion", "render", "src/index.ts", "Short", str(out), *common_flags(props, browser),
            "--codec=h264", "--crf=18", f"--concurrency={concurrency}"]


def still_cmd(out: Path, props: Path, frame: int, browser=None):
    return ["npx", "remotion", "still", "src/index.ts", "Short", str(out), f"--frame={frame}",
            *common_flags(props, browser)]


def layout(props: dict) -> dict:
    # No end card: the short ends on the payoff, so check_short.py checks the tail for dead air.
    return {"duration": round(props["baseDuration"], 3), "silent_endcard_seconds": 0.0, "hook_style": "remotion"}


def contact_sheet(paths, labels, out: Path):
    from PIL import Image, ImageDraw
    w, h = 270, 480
    sheet = Image.new("RGB", (w * len(paths), h), "white")
    for i, (p, lab) in enumerate(zip(paths, labels)):
        im = Image.open(p).convert("RGB").resize((w, h))
        ImageDraw.Draw(im).text((6, h - 18), lab, fill="red")
        sheet.paste(im, (i * w, 0))
    sheet.save(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--props", required=True)
    ap.add_argument("--base", required=True, help="clean base from make_base.py")
    ap.add_argument("--fonts", required=True, help="folder with the static Heebo TTFs")
    ap.add_argument("--logo", required=True, help="solid newspaper logo (investing-bros-brand assets/logo-solid.png)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--work")
    ap.add_argument("--browser")
    ap.add_argument("--concurrency", type=int, default=2)
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
            png = out.with_name(f"{out.stem}_still_{s:g}.png")
            subprocess.run(still_cmd(png, props_path, round(s * FPS), browser), cwd=work, check=True)
            shots.append(png)
        sheet = out.with_name(f"{out.stem}_stills.jpg")
        contact_sheet(shots, [f"{s:g}s" for s in secs], sheet)
        print(sheet)
        return 0
    subprocess.run(render_cmd(out, props_path, browser, a.concurrency), cwd=work, check=True)
    lay = out.with_name(f"{out.stem}_layout.json")
    lay.write_text(json.dumps(layout(props)), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
