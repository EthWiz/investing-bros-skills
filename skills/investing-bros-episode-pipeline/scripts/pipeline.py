#!/usr/bin/env python3
"""Track one episode through the Investing Bros pipeline, stage by stage.

The state lives in EP/pipeline.json, so any agent (or a new session) can pick
up where the last one stopped. Copy it to the episode's Drive extras/ folder at
every hand-back.

Usage:
  pipeline.py init   EP --episode N [--no-video] [--no-midform] [--no-thumbnail] [--no-share]
  pipeline.py status EP                      # table + the next stage(s) to work on
  pipeline.py set    EP STAGE STATUS [--approved-by NAME] [--note TEXT] [--link URL]
  pipeline.py report EP                      # markdown for the hand-back / Drive extras/

STATUS is one of: todo, doing, review, done, skipped.
  review   = finished, waiting for the approver named in the stage
  done     = needs --approved-by for stages that have an approver
  skipped  = only for optional stages
A stage can't start (doing/review/done) before the stages it depends on are done or skipped.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

STATUSES = ("todo", "doing", "review", "done", "skipped")
CLOSED = ("done", "skipped")

# id, title, skill(s), depends on, approver, optional, local outputs expected under EP (any-of groups)
STAGES = [
    {"id": "intake", "title": "Confirm N, fetch the parts and host tracks",
     "skill": "investing-bros-post-production (steps 1-2)", "deps": [], "approver": None,
     "optional": False, "outputs": [["parts"]]},
    {"id": "edit", "title": "Audio edit: level, transcribe, cut list, trim, loudness",
     "skill": "investing-bros-post-production (steps 3-5)", "deps": ["intake"], "approver": "Nadav",
     "optional": False,
     "outputs": [["investing-bros-episode-edited.m4a", "investing-bros-episode-edited.mp3"],
                 ["edit.json"], ["transcript/segments.json"]]},
    {"id": "copy", "title": "Titles + description as .txt, check_copy.py --spotify",
     "skill": "investing-bros-title-description", "deps": ["edit"], "approver": "Amitai",
     "optional": False, "outputs": [["titles.txt"], ["description.txt"]]},
    {"id": "video", "title": "Cold opens + intro + full video episode",
     "skill": "investing-bros-teaser, investing-bros-post-production (step 8)", "deps": ["edit"],
     "approver": "Nadav", "optional": True, "outputs": []},
    {"id": "shorts", "title": "5 shorts, a cover each, .srt, YouTube notes, in Drive shorts/",
     "skill": "investing-bros-shorts (+ investing-bros-hyperframes)", "deps": ["edit"],
     "approver": "Nadav", "optional": False, "outputs": []},
    {"id": "midform", "title": "Mid-form highlights (5-10 min), in Drive mid-form/",
     "skill": "investing-bros-shorts (Mid-form)", "deps": ["edit"], "approver": "Nadav",
     "optional": True, "outputs": []},
    {"id": "thumbnail", "title": "YouTube thumbnail prompt + headline",
     "skill": "investing-bros-cover-art", "deps": ["copy"], "approver": "Amitai",
     "optional": True, "outputs": []},
    {"id": "review", "title": "Drive folder complete + review ping",
     "skill": "investing-bros-post-production (steps 9-10)",
     "deps": ["copy", "video", "shorts", "midform", "thumbnail"], "approver": "Amitai",
     "optional": False, "outputs": []},
    {"id": "upload", "title": "RedCircle draft + YouTube uploads as private",
     "skill": "investing-bros-episode-upload", "deps": ["review"], "approver": None,
     "optional": False, "outputs": []},
    {"id": "publish", "title": "Go live, then check Spotify, RedCircle and YouTube",
     "skill": "investing-bros-episode-upload (Publish and check)", "deps": ["upload"],
     "approver": "Amitai", "optional": False, "outputs": []},
    {"id": "share", "title": "WhatsApp share of the live episode",
     "skill": "investing-bros-share-new-episode", "deps": ["publish"], "approver": "Amitai",
     "optional": True, "outputs": []},
    {"id": "learnings", "title": "Learnings PR to investing-bros-skills",
     "skill": "AGENTS.md -> Editing the skills", "deps": ["publish", "share"], "approver": None,
     "optional": False, "outputs": []},
]
BY_ID = {s["id"]: s for s in STAGES}
# Approver that must be named exactly (anything public needs Amitai's OK).
STRICT_APPROVER = {"publish": "Amitai", "share": "Amitai"}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def new_state(episode: int, skip=()) -> dict:
    stages = {}
    for s in STAGES:
        status = "skipped" if s["id"] in skip else "todo"
        stages[s["id"]] = {"status": status, "approved_by": None, "notes": [], "links": [],
                           "updated": None}
    return {"episode": episode, "created": _now(), "stages": stages}


def blocking_deps(state: dict, stage_id: str) -> list:
    return [d for d in BY_ID[stage_id]["deps"] if state["stages"][d]["status"] not in CLOSED]


def missing_outputs(ep: Path, stage_id: str) -> list:
    missing = []
    for group in BY_ID[stage_id]["outputs"]:
        if not any((ep / p).exists() for p in group):
            missing.append(" or ".join(group))
    return missing


def set_status(state: dict, stage_id: str, status: str, approved_by=None, note=None, link=None,
               ep: Path = None) -> list:
    """Apply a status change. Returns warnings; raises ValueError when a rule is broken."""
    if stage_id not in BY_ID:
        raise ValueError(f"unknown stage '{stage_id}' (stages: {', '.join(BY_ID)})")
    if status not in STATUSES:
        raise ValueError(f"unknown status '{status}' (one of: {', '.join(STATUSES)})")
    spec, st = BY_ID[stage_id], state["stages"][stage_id]
    warnings = []
    if status == "skipped" and not spec["optional"]:
        raise ValueError(f"'{stage_id}' is not optional; it can't be skipped")
    if status in ("doing", "review", "done"):
        blocked = blocking_deps(state, stage_id)
        if blocked:
            raise ValueError(f"'{stage_id}' waits for: {', '.join(blocked)}")
    if status == "done" and spec["approver"]:
        if not approved_by:
            raise ValueError(f"'{stage_id}' needs --approved-by ({spec['approver']} approves it); "
                             "use 'review' while waiting")
        strict = STRICT_APPROVER.get(stage_id)
        if strict and approved_by.strip().lower() != strict.lower():
            raise ValueError(f"'{stage_id}' can only be approved by {strict}")
    if status == "done" and ep is not None:
        for m in missing_outputs(ep, stage_id):
            warnings.append(f"warn: {stage_id}: expected {m} in {ep} (fine if it lives on another machine)")
    st["status"] = status
    st["updated"] = _now()
    if approved_by:
        st["approved_by"] = approved_by
    if note:
        st["notes"].append(note)
    if link:
        st["links"].append(link)
    return warnings


def next_stages(state: dict) -> list:
    out = []
    for s in STAGES:
        st = state["stages"][s["id"]]["status"]
        if st in ("todo", "doing", "review") and not blocking_deps(state, s["id"]):
            out.append(s["id"])
    return out


def render(state: dict) -> str:
    lines = [f"# פרק {state['episode']}: pipeline", "",
             "| # | Stage | Status | Approved by | Skill | Notes / links |", "|---|---|---|---|---|---|"]
    for i, s in enumerate(STAGES):
        st = state["stages"][s["id"]]
        extra = "; ".join(st["notes"] + st["links"])
        appr = st["approved_by"] or (f"({s['approver']})" if s["approver"] else "")
        lines.append(f"| {i} | {s['id']}: {s['title']} | {st['status']} | {appr} | {s['skill']} | {extra} |")
    nxt = next_stages(state)
    lines += ["", "Next: " + (", ".join(nxt) if nxt else "nothing open, the episode is through the pipeline")]
    return "\n".join(lines) + "\n"


def _load(ep: Path) -> dict:
    path = ep / "pipeline.json"
    if not path.is_file():
        raise SystemExit(f"error: {path} not found; run 'pipeline.py init {ep} --episode N' first")
    return json.loads(path.read_text(encoding="utf-8"))


def _save(ep: Path, state: dict) -> None:
    (ep / "pipeline.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init")
    p.add_argument("ep", type=Path)
    p.add_argument("--episode", type=int, required=True, help="episode number as Amitai stated it")
    for opt in ("video", "midform", "thumbnail", "share"):
        p.add_argument(f"--no-{opt}", action="store_true", help=f"skip the optional '{opt}' stage")
    p.add_argument("--force", action="store_true", help="overwrite an existing pipeline.json")
    p = sub.add_parser("status")
    p.add_argument("ep", type=Path)
    p = sub.add_parser("report")
    p.add_argument("ep", type=Path)
    p = sub.add_parser("set")
    p.add_argument("ep", type=Path)
    p.add_argument("stage")
    p.add_argument("status")
    p.add_argument("--approved-by")
    p.add_argument("--note")
    p.add_argument("--link")
    a = ap.parse_args(argv)

    if a.cmd == "init":
        a.ep.mkdir(parents=True, exist_ok=True)
        if (a.ep / "pipeline.json").exists() and not a.force:
            print(f"error: {a.ep / 'pipeline.json'} exists; use 'status' (or --force to start over)")
            return 1
        skip = [o for o in ("video", "midform", "thumbnail", "share") if getattr(a, f"no_{o}")]
        state = new_state(a.episode, skip)
        _save(a.ep, state)
        print(render(state), end="")
        return 0

    state = _load(a.ep)
    if a.cmd in ("status", "report"):
        print(render(state), end="")
        return 0

    try:
        for w in set_status(state, a.stage, a.status, a.approved_by, a.note, a.link, a.ep):
            print(w)
    except ValueError as e:
        print(f"error: {e}")
        return 1
    _save(a.ep, state)
    print(f"{a.stage}: {a.status}")
    print("Next: " + (", ".join(next_stages(state)) or "nothing open"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
