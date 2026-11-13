#!/usr/bin/env python3
"""The episode side-by-side video: Riverside's native export first, tracks only as a fallback.

  sbs_master.py decide        EP
  sbs_master.py commit-export EP --file riverside/side-by-side.mp4
  sbs_master.py export-failed EP --reason "Couldn't download your edit (4k and 1080p)"
  sbs_master.py build-from-tracks EP --left FILE --right FILE [--dry-run]
  sbs_master.py verify        EP

Default method: download Riverside's native side-by-side export in the browser
(riverside-pull.md). Riverside has no Drive or email export. That file is the
16:9 episode master. Building a side-by-side from per-speaker tracks is only a
fallback when that export failed (Couldn't download your edit, the Exports tab
never loads, Export is disabled). The fallback does not run automatically: it
needs the episode owner's approval each time, recorded with

  pipeline.py approve EP main sbs_fallback_ok --by "<Owner> HH:MM: <their words>"

which stores who approved and when in extras/pipeline.json. Raw footage stays
off Drive when main.riverside passed. Riverside is read/download only; never
delete a studio, project or recording.

Exit 0 = allowed / recorded. Exit 1 = refused. Exit 2 = usage.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pipeline_state as PS  # noqa: E402

VIA_EXPORT = "riverside_export"
VIA_TRACKS = "tracks"
APPROVAL_KEY = "main.sbs_fallback_ok"
RECORD_REL = "extras/sbs-master.json"
MASTER_REL = "extras/investing-bros-episode-raw-untrimmed.mp4"
EXPORT_CANDIDATES = (
    "riverside/side-by-side.mp4",
    "riverside/side-by-side-1080p.mp4",
    "riverside/side-by-side-export.mp4",
)
FAILURE_EXAMPLES = (
    "Couldn't download your edit",
    "Exports tab never loads",
    "Export disabled",
)
STATUS_FAILED = "export_failed"
STATUS_READY = "ready"


def method_order():
    """Native export is always tried first; the track build is only the fallback."""
    return (VIA_EXPORT, VIA_TRACKS)


def default_method():
    return VIA_EXPORT


def record_path(ep) -> Path:
    return Path(ep) / RECORD_REL


def load_record(ep):
    p = record_path(ep)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        raise ValueError(f"{RECORD_REL} unreadable") from e


def save_record(ep, rec: dict) -> Path:
    p = record_path(ep)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(p)
    return p


def load_state(ep):
    p = Path(ep) / "extras" / "pipeline.json"
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def approval_record(state) -> "dict | None":
    rec = ((state or {}).get("stages") or {}).get(APPROVAL_KEY) or {}
    if rec.get("state") == "approved":
        return rec
    return None


def approval_summary(state) -> "dict | None":
    rec = approval_record(state)
    if not rec:
        return None
    return {"by": rec.get("by"), "at": rec.get("at"), "quote": rec.get("quote")}


def find_native_export(ep) -> "str | None":
    """A downloaded native Riverside side-by-side file, if one is in the episode folder."""
    rec = None
    try:
        rec = load_record(ep)
    except ValueError:
        rec = None
    candidates = []
    if rec and rec.get("via") == VIA_EXPORT and rec.get("source"):
        candidates.append(rec["source"])
    if rec and rec.get("via") == VIA_EXPORT and rec.get("path"):
        candidates.append(rec["path"])
    candidates.extend(EXPORT_CANDIDATES)
    seen = set()
    for rel in candidates:
        rel = str(rel).replace("\\", "/").lstrip("./")
        if not rel or rel in seen:
            continue
        seen.add(rel)
        p = Path(ep) / rel
        if p.is_file() and p.stat().st_size > 0:
            return rel
    return None


def export_failed(ep) -> bool:
    rec = load_record(ep) or {}
    return rec.get("status") == STATUS_FAILED or bool(rec.get("failure"))


def fallback_pending(ep, state=None) -> bool:
    """True when the native export has failed and the track-build is not yet approved."""
    if find_native_export(ep):
        return False
    if not export_failed(ep):
        rec = load_record(ep) or {}
        if rec.get("via") != VIA_TRACKS:
            return False
    return approval_record(state if state is not None else load_state(ep)) is None


def decide(ep, state=None) -> dict:
    """Which method to use, and whether it is allowed right now."""
    state = state if state is not None else load_state(ep)
    export = find_native_export(ep)
    if export:
        return {
            "method": VIA_EXPORT,
            "allowed": True,
            "needs_approval": False,
            "fallback_pending": False,
            "path": export,
            "reason": "native Riverside side-by-side export is present; use it as the episode master",
        }
    approval = approval_summary(state)
    failed = export_failed(ep)
    if failed or (load_record(ep) or {}).get("via") == VIA_TRACKS:
        if approval:
            return {
                "method": VIA_TRACKS,
                "allowed": True,
                "needs_approval": False,
                "fallback_pending": False,
                "approval": approval,
                "reason": "native export failed; track-build fallback is allowed with the owner's approval",
            }
        return {
            "method": VIA_TRACKS,
            "allowed": False,
            "needs_approval": True,
            "fallback_pending": True,
            "reason": "native Riverside side-by-side export failed; the track-build fallback needs the "
                      f"episode owner's approval each time (`pipeline.py approve EP {APPROVAL_KEY} "
                      "--by \"<Owner> HH:MM: <their words>\")",
        }
    return {
        "method": VIA_EXPORT,
        "allowed": False,
        "needs_approval": False,
        "fallback_pending": False,
        "reason": "native Riverside side-by-side export is not in riverside/ yet; download it first. "
                  "Do not build a side-by-side from tracks until that export has failed and the "
                  "episode owner has approved the fallback",
    }


def _inside(ep, rel: str, folder=None) -> str:
    raw = str(rel).replace("\\", "/").strip()
    if not raw or raw.startswith(("/", "~")) or ".." in Path(raw).parts:
        raise ValueError(f"path must stay inside the episode folder: {rel}")
    if folder and not raw.startswith(folder.rstrip("/") + "/") and raw != folder.rstrip("/"):
        # Allow extras/ or riverside/ as required by callers; just normalize.
        pass
    path = (Path(ep) / raw).resolve()
    path.relative_to(Path(ep).resolve())
    return Path(*Path(raw).parts).as_posix()


def commit_export(ep, source: str, now=None) -> dict:
    """Record that the native export is the side-by-side master. Copies it to the raw mp4 path if needed."""
    rel = _inside(ep, source)
    src = Path(ep) / rel
    if not src.is_file() or src.stat().st_size <= 0:
        raise ValueError(f"native export is missing or empty: {rel}")
    dest = Path(ep) / MASTER_REL
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.resolve() != src.resolve():
        if dest.exists() and dest.resolve() != src.resolve():
            # Never overwrite a different raw master in place; the post-production rule.
            raise ValueError(f"{MASTER_REL} already exists; refusing to overwrite")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    rec = {
        "via": VIA_EXPORT,
        "status": STATUS_READY,
        "source": rel,
        "path": MASTER_REL,
        "bytes": dest.stat().st_size,
        "at": now or PS.now(),
    }
    save_record(ep, rec)
    return rec


def record_export_failed(ep, reason: str, now=None) -> dict:
    reason = (reason or "").strip()
    if not reason:
        raise ValueError("export-failed needs --reason (what failed in Riverside)")
    rec = {
        "via": VIA_EXPORT,
        "status": STATUS_FAILED,
        "failure": reason,
        "at": now or PS.now(),
    }
    save_record(ep, rec)
    return rec


def tracks_build_problems(ep, state=None) -> list:
    """Why a track-build must not run. Empty means it is allowed."""
    plan = decide(ep, state)
    if plan["method"] == VIA_EXPORT and plan.get("path"):
        return ["native Riverside side-by-side export is present; use it, do not build from tracks"]
    if plan["method"] == VIA_EXPORT and not plan["allowed"]:
        return [plan["reason"]]
    if not plan["allowed"] or plan.get("needs_approval"):
        return [plan["reason"]]
    return []


def build_from_tracks(ep, left: str, right: str, dry_run=False, now=None) -> dict:
    """Compose a side-by-side from per-speaker tracks. Refused without a current owner approval."""
    state = load_state(ep)
    problems = tracks_build_problems(ep, state)
    if problems:
        raise ValueError(problems[0])
    left_rel = _inside(ep, left)
    right_rel = _inside(ep, right)
    for rel in (left_rel, right_rel):
        p = Path(ep) / rel
        if not p.is_file() or p.stat().st_size <= 0:
            raise ValueError(f"track is missing or empty: {rel}")
    dest = Path(ep) / MASTER_REL
    if dest.exists():
        raise ValueError(f"{MASTER_REL} already exists; refusing to overwrite")
    approval = approval_summary(state)
    rec = {
        "via": VIA_TRACKS,
        "status": "planned" if dry_run else STATUS_READY,
        "source": {"left": left_rel, "right": right_rel},
        "path": MASTER_REL,
        "approved_by": approval["by"],
        "approved_at": approval["at"],
        "quote": approval["quote"],
        "at": now or PS.now(),
    }
    if dry_run:
        rec["dry_run"] = True
        return rec
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
        "-i", str(Path(ep) / left_rel), "-i", str(Path(ep) / right_rel),
        "-filter_complex",
        "[0:v]scale=960:1080:force_original_aspect_ratio=decrease,"
        "pad=960:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24[l];"
        "[1:v]scale=960:1080:force_original_aspect_ratio=decrease,"
        "pad=960:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24[r];"
        "[l][r]hstack=inputs=2[v];"
        "[0:a][1:a]amix=inputs=2:duration=longest:normalize=0[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        str(dest),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise ValueError(f"ffmpeg could not build the side-by-side: {e}") from e
    if r.returncode != 0:
        raise ValueError("ffmpeg failed to build the side-by-side from tracks: "
                         + (r.stderr or r.stdout or "no output")[:500])
    rec["bytes"] = dest.stat().st_size
    rec["status"] = STATUS_READY
    save_record(ep, rec)
    return rec


def verify_master(ep, state=None) -> list:
    """Problems with a present side-by-side / raw video master. Empty if only audio exists, or if the mp4 is valid."""
    state = state if state is not None else load_state(ep)
    dest = Path(ep) / MASTER_REL
    if not dest.is_file():
        return []
    try:
        rec = load_record(ep)
    except ValueError as e:
        return [str(e)]
    if rec is None:
        return [f"{MASTER_REL} is present but {RECORD_REL} is missing: record the native "
                "Riverside export with sbs_master.py commit-export, or (only after that "
                f"export failed and the owner approved {APPROVAL_KEY}) build-from-tracks"]
    via = rec.get("via")
    if via == VIA_EXPORT:
        if rec.get("status") == STATUS_FAILED:
            return ["a native-export failure is recorded, but the raw video master is present "
                    "without a finished export or an approved track-build"]
        src = rec.get("source") or rec.get("path")
        if not src:
            return [f"{RECORD_REL} has via={VIA_EXPORT} but no source path"]
        return []
    if via == VIA_TRACKS:
        if approval_record(state) is None:
            return [f"{MASTER_REL} was built from tracks, but {APPROVAL_KEY} is not approved; "
                    "the track-build fallback needs the episode owner's approval each time"]
        return []
    return [f"{RECORD_REL} via must be {VIA_EXPORT} or {VIA_TRACKS}, not {via!r}"]


def _print_plan(plan: dict) -> int:
    print(json.dumps(plan, ensure_ascii=False, indent=1))
    if plan.get("allowed"):
        return 0
    return 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("decide"); d.add_argument("ep")
    c = sub.add_parser("commit-export"); c.add_argument("ep"); c.add_argument("--file", required=True)
    f = sub.add_parser("export-failed"); f.add_argument("ep"); f.add_argument("--reason", required=True)
    b = sub.add_parser("build-from-tracks"); b.add_argument("ep")
    b.add_argument("--left", required=True); b.add_argument("--right", required=True)
    b.add_argument("--dry-run", action="store_true")
    v = sub.add_parser("verify"); v.add_argument("ep")
    a = p.parse_args(argv)
    try:
        if a.cmd == "decide":
            return _print_plan(decide(a.ep))
        if a.cmd == "commit-export":
            rec = commit_export(a.ep, a.file)
            print(json.dumps(rec, ensure_ascii=False, indent=1))
            return 0
        if a.cmd == "export-failed":
            rec = record_export_failed(a.ep, a.reason)
            print(json.dumps(rec, ensure_ascii=False, indent=1))
            return 0
        if a.cmd == "build-from-tracks":
            rec = build_from_tracks(a.ep, a.left, a.right, dry_run=a.dry_run)
            print(json.dumps(rec, ensure_ascii=False, indent=1))
            return 0
        if a.cmd == "verify":
            probs = verify_master(a.ep)
            if probs:
                print("\n".join(probs), file=sys.stderr)
                return 1
            print("ok")
            return 0
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
