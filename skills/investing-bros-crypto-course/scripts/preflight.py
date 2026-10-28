#!/usr/bin/env python3
"""Check this machine can run a lesson stage before starting it (minutes of Whisper or rendering).

Usage:
    python3 preflight.py --stage transcribe|base|render|deliver [--fonts FONTS] [--logo LOGO]
        [--template DIR] [--work DIR] [--json]

Per stage, what it needs and what it checks:
  transcribe  ffmpeg, the `whisper` command and its large-v3-turbo model in ~/.cache/whisper (or --model-dir)
  base        ffmpeg and ffprobe; swiftc for a `vision` background (optional: only a lesson with one needs it)
  render      ffmpeg, ffprobe, Node 18+ with npx, the Remotion template with its package-lock.json (or the
              work folder's node_modules from an earlier run), numpy and Pillow in this Python, the static
              Heebo TTFs (--fonts) and the logo (--logo), and free disk (a 10-minute lesson needs about 3 GB)
  deliver     rclone with a `show:` remote (optional: without it, files are staged for Amitai to drag in)
Every stage also reports the free disk. It installs nothing, downloads nothing, opens no sign-in page and
prints no secret: it only looks. Exit 1 when something a stage needs is missing; an optional item that is
missing is reported but doesn't fail. --json prints the same results for a script to read.
"""
import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent.parent / "investing-bros-remotion" / "template"
FONTS = ("Heebo-SemiBold.ttf", "Heebo-ExtraBold.ttf", "Heebo-Black.ttf")
RENDER_DISK_GB = 3.0
STAGES = ("transcribe", "base", "render", "deliver")


def item(name, ok, detail, fix="", required=True):
    return {"name": name, "ok": bool(ok), "required": required, "detail": detail, "fix": "" if ok else fix}


def version_of(cmd, run=None):
    run = run or subprocess.run
    try:
        out = run(cmd, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = (out.stdout or out.stderr).strip()
    return text.splitlines()[0] if out.returncode == 0 and text else None


def check_tool(name, args=("-version",), fix="", required=True, which=None, run=None):
    which = which or shutil.which
    path = which(name)
    if not path:
        return item(name, False, "not found on PATH", fix, required)
    return item(name, True, version_of([path, *args], run) or path, required=required)


def check_node(which=None, run=None):
    which, run = which or shutil.which, run or subprocess.run
    path = which("node")
    if not path or not which("npx"):
        return item("node", False, "node or npx not on PATH", "install Node 18 or newer (brew install node)")
    v = version_of([path, "--version"], run) or ""
    m = re.match(r"v(\d+)", v)
    return item("node", bool(m and int(m.group(1)) >= 18), v or path, "Node 18 or newer is needed (brew upgrade node)")


def check_modules(names=("numpy", "PIL"), find=importlib.util.find_spec, which=shutil.which):
    missing = [n for n in names if find(n) is None]
    # Amitai's Mac: the system python has neither, and uv runs a script with them without installing anything
    fix = ("run the render scripts as `uv run --with numpy --with pillow python SCRIPT ...` (nothing installed)"
           if which("uv") else f"{sys.executable} -m pip install numpy pillow (in a venv)")
    return item("python modules", not missing, f"{sys.executable}: " + (f"missing {', '.join(missing)}" if missing else "numpy, Pillow"), fix)


def check_template(template: Path, work=None):
    if work and (Path(work) / "node_modules" / "remotion").is_dir():
        return item("remotion template", True, f"installed in {work}")
    ok = (template / "package.json").is_file() and (template / "package-lock.json").is_file()
    return item("remotion template", ok, f"{template}: " + ("npm ci will run on the first render (needs the npm registry)"
                                                             if ok else "package.json or package-lock.json missing"),
                "use an intact investing-bros-remotion skill")


# one folder for every lesson, so the fonts are made once per machine
FONT_FIX = ("download Heebo[wght].ttf (https://github.com/google/fonts/raw/main/ofl/heebo/Heebo%5Bwght%5D.ttf), then `brand.py fonts Heebo[wght].ttf ~/.cache/investing-bros/fonts` (investing-bros-shorts) and pass that folder")


def check_fonts(fonts):
    if not fonts:
        return item("fonts", False, "no --fonts folder given", FONT_FIX)
    missing = [f for f in FONTS if not (Path(fonts) / f).is_file()]
    return item("fonts", not missing, f"{fonts}: " + (f"missing {', '.join(missing)}" if missing else "Heebo SemiBold, ExtraBold, Black"),
                FONT_FIX)


def check_logo(logo):
    ok = bool(logo) and Path(logo).is_file()
    return item("logo", ok, logo or "no --logo given", "investing-bros-brand assets/logo-solid.png")


def check_whisper(model_dir: Path, which=None):
    which = which or shutil.which
    path = which("whisper")
    model = model_dir / "large-v3-turbo.pt"
    if not path:
        return item("whisper", False, "the whisper command isn't on PATH", "brew install openai-whisper, or transcribe_clip.py "
                    "(investing-bros-shorts)")
    return item("whisper", model.is_file(), f"{path}; model {'found' if model.is_file() else 'missing'} at {model}",
                "the model downloads on first use; ask before fetching 1.6 GB")


def check_rclone(which=None, run=None):
    which, run = which or shutil.which, run or subprocess.run
    path = which("rclone")
    if not path:
        return item("rclone", False, "not installed: stage files locally for Amitai to drag into Drive",
                    "optional: investing-bros-show environment -> uploading to Drive", required=False)
    try:
        remotes = run([path, "listremotes"], capture_output=True, text=True, timeout=20).stdout.split()
    except (OSError, subprocess.TimeoutExpired):
        remotes = []
    return item("rclone", "show:" in remotes, f"{path}; remotes: {' '.join(remotes) or 'none'}",
                "optional: rclone config create show drive scope=drive", required=False)


def check_disk(folder: Path, need_gb: float, usage=shutil.disk_usage):
    free = usage(str(folder)).free / 1e9
    return item("disk", free >= need_gb, f"{free:.1f} GB free in {folder}", f"free at least {need_gb:.0f} GB")


def run_checks(stage, fonts=None, logo=None, template=TEMPLATE, work=None, model_dir=None, where=Path(".")):
    model_dir = model_dir or Path(os.path.expanduser("~/.cache/whisper"))
    out = []
    if stage in ("transcribe", "base", "render"):
        out.append(check_tool("ffmpeg", fix="brew install ffmpeg"))
    if stage in ("base", "render"):
        out.append(check_tool("ffprobe", fix="brew install ffmpeg"))
    if stage == "base":
        out.append(check_tool("swiftc", ("--version",), "needed only for a vision background: xcode-select --install",
                              required=False))
    if stage == "transcribe":
        out.append(check_whisper(model_dir))
    if stage == "render":
        out += [check_node(), check_modules(), check_template(template, work), check_fonts(fonts), check_logo(logo)]
    if stage == "deliver":
        out.append(check_rclone())
    out.append(check_disk(where, RENDER_DISK_GB if stage == "render" else 0.5))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", required=True, choices=STAGES)
    ap.add_argument("--fonts")
    ap.add_argument("--logo")
    ap.add_argument("--template", default=str(TEMPLATE))
    ap.add_argument("--work", help="the render work folder, if an earlier run installed node_modules there")
    ap.add_argument("--model-dir")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    results = run_checks(a.stage, a.fonts, a.logo, Path(a.template), a.work, Path(a.model_dir) if a.model_dir else None,
                         Path(a.work or "."))
    failed = [r for r in results if r["required"] and not r["ok"]]
    if a.json:
        print(json.dumps({"stage": a.stage, "python": sys.executable, "ok": not failed, "checks": results},
                         ensure_ascii=False, indent=1))
    else:
        for r in results:
            mark = "ok  " if r["ok"] else ("FAIL" if r["required"] else "opt ")
            print(f"{mark}  {r['name']:<18} {r['detail']}" + (f"\n      fix: {r['fix']}" if r["fix"] else ""))
        print(f"{a.stage}: " + ("ready" if not failed else f"{len(failed)} missing"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
