#!/usr/bin/env python3
"""Post-production gate, compatibility wrapper (deprecated): use investing-bros-producer ->
scripts/pipeline.py (`gate`, `mark`, `waive`). Same CLI as before, so older installed skills keep working:

  postprod_checklist.py check EP_DIR --episode N [--stage upload|review|done]
  postprod_checklist.py mark  EP_DIR ITEM --evidence "what you saw, where"
  postprod_checklist.py waive EP_DIR ITEM --by "<Owner> HH:MM: <the episode owner's own words>"

- The episode has extras/pipeline.json: delegates to pipeline.py (found next to this skill:
  <skills>/investing-bros-producer/scripts/pipeline.py, or $IB_PIPELINE). `check` -> `gate`.
  Without the producer skill installed, `check` reads the state itself and mark/waive refuse
  (pipeline.py is that file's only writer).
- No extras/pipeline.json (an episode started before the pipeline): the old behaviour, marks and
  waivers in extras/postprod-checklist.json.

Stages (each includes the ones before it): upload (default; everything the full-episode YouTube
upload needs), review (production complete, ready for the owner's final review), done (after the
publication obligations). Items and package contracts: episode_gates.py and ../references/CHECKLIST.md.
A waiver must quote the episode owner (episode_owner.py; Amitai when the episode has no state).
Exit 0 = pass, 1 = missing items (printed), 2 = usage error.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from episode_gates import (IDS, ITEMS, MANUAL, NEEDS_MARK, STAGES, WAIVED_WITH, file_check,  # noqa: E402,F401
                           segment_problems, short_problems)
import episode_gates  # noqa: E402

NOTE = ("note: postprod_checklist.py is a compatibility wrapper; use investing-bros-producer -> "
        "pipeline.py gate/mark/waive")


def state_path(ep: Path) -> Path:
    return ep / "extras" / "postprod-checklist.json"


def pipeline_state_path(ep: Path) -> Path:
    return ep / "extras" / "pipeline.json"


def find_pipeline():
    env = os.environ.get("IB_PIPELINE")
    for c in ([Path(env)] if env else []) + [HERE.parents[1] / "investing-bros-producer" / "scripts" / "pipeline.py"]:
        if c.is_file():
            return c
    return None


def load(ep: Path) -> dict:
    p = state_path(ep)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"marked": {}, "waived": {}}


def save(ep: Path, s: dict) -> None:
    p = state_path(ep)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


def pipeline_marks(ep: Path) -> "tuple[dict, dict, int]":
    """Marks, waivers and episode number from extras/pipeline.json (legacy evidence under them)."""
    s = json.loads(pipeline_state_path(ep).read_text(encoding="utf-8"))
    legacy = s.get("legacy") or {}
    marked = {**legacy.get("marked", {}), **{k: v["evidence"] for k, v in s.get("marks", {}).items()}}
    waived = {**legacy.get("waived", {}), **{k: v["quote"] for k, v in s.get("waivers", {}).items()}}
    return marked, waived, int(s["episode"])


def check(ep: Path, n: int, stage: str = "upload"):
    if pipeline_state_path(ep).is_file():
        marked, waived, _ = pipeline_marks(ep)
    else:
        s = load(ep)
        marked, waived = s["marked"], s["waived"]
    return episode_gates.check(ep, n, stage, marked, waived)


def print_rows(rows, missing, stage) -> int:
    for st, item, note in rows:
        print(f"{st:8} {item:20} {note}")
    if missing:
        print(f"\nFAIL ({stage}): {len(missing)} missing: {', '.join(missing)}")
        print("Make them, or get the episode owner's explicit waiver per item. Do not upload / report done.")
        return 1
    print(f"\nPASS ({stage})")
    return 0


def delegate(a, ep: Path) -> int:
    pipe = find_pipeline()
    if a.cmd == "check":
        _, _, n = pipeline_marks(ep)
        if n != a.episode:
            print(f"error: extras/pipeline.json is episode {n}, not {a.episode}", file=sys.stderr)
            return 2
        if pipe is None:
            rows, missing = check(ep, a.episode, a.stage)
            return print_rows(rows, missing, a.stage)
        args = ["gate", str(ep), "--stage", a.stage]
    elif pipe is None:
        print("refused: this episode's state is extras/pipeline.json, written only by pipeline.py; "
              "install investing-bros-producer", file=sys.stderr)
        return 2
    elif a.cmd == "mark":
        args = ["mark", str(ep), a.item, "--evidence", a.evidence]
    else:
        args = ["waive", str(ep), a.item, "--by", a.by]
    r = subprocess.run([sys.executable, str(pipe), *args])
    return r.returncode


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("ep"); c.add_argument("--episode", type=int, required=True)
    c.add_argument("--stage", choices=STAGES, default="upload")
    m = sub.add_parser("mark"); m.add_argument("ep"); m.add_argument("item", choices=IDS); m.add_argument("--evidence", required=True)
    w = sub.add_parser("waive"); w.add_argument("ep"); w.add_argument("item", choices=IDS); w.add_argument("--by", required=True)
    a = ap.parse_args(argv)
    ep = Path(a.ep)
    print(NOTE, file=sys.stderr)
    if pipeline_state_path(ep).is_file():
        return delegate(a, ep)
    if a.cmd == "check":
        rows, missing = check(ep, a.episode, a.stage)
        return print_rows(rows, missing, a.stage)
    s = load(ep)
    if a.cmd == "mark":
        s["marked"][a.item] = a.evidence.strip()
    else:
        import episode_owner
        ok, _owner, msg = episode_owner.check_quote(a.by, ep)
        if not ok:
            print(f"waiver {msg}", file=sys.stderr)
            return 2
        s["waived"][a.item] = a.by.strip()
    save(ep, s)
    print(f"{a.cmd}ed {a.item}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
