#!/usr/bin/env python3
"""The publish checklist: one ordered list of checks, ticked one by one, that refuses
to let anything go Public out of order. Its rendered form is the report to the episode owner.

  publish_checklist.py init STATE --episode N --full ID --segments ID ID --shorts ID ID ID
  publish_checklist.py publish-ok STATE --by "<Owner> HH:MM: <the owner's words>"
  publish_checklist.py tick STATE ITEM --evidence "what you saw, where"
  publish_checklist.py fail STATE ITEM --reason "what went wrong"
  publish_checklist.py waive STATE ITEM --by "<Owner> HH:MM: <the owner's words>"
  publish_checklist.py can-public STATE GROUP     # exit 0 only if GROUP may go Public now
  publish_checklist.py set-video STATE GROUP ID    # after a re-upload: the new ID; reopens that group
  publish_checklist.py status STATE                # next open item
  publish_checklist.py render STATE                # Markdown ticked checklist for Amitai

STATE is a JSON file (keep it next to the episode's notes, e.g. extras/publish-checklist.json).
Video IDs are copied from Studio or tool output, never typed.

Groups, in the only allowed order: release, redcircle, episode, seg01, seg02, short01,
short02, short03. `release` holds one item, `release.publish_ok`: the episode owner's OK to
publish, in their words, tied to the video IDs it covers. It is recorded with `publish-ok`
(never `tick`), never waived, and goes stale when a video ID changes. The owner is the one in
the episode's extras/pipeline.json (Amitai when there is none). Each group's checks have a phase:
  pre    - verified in Studio (or RedCircle) while still Private / Unpublished
  public - the switch to Public itself
  live   - verified from outside after the switch (check_live.py)
Rules enforced:
  * A group's `public` item can be ticked only when every item of every earlier group
    and every pre item of its own group is ticked (or waived where waivable).
  * live items can be ticked only after their group's `public` item.
  * channel (the first check of every YouTube video: אחים להשקעות is the active Studio
    channel), public, live, publish_ok and every Short's `related` item can never be waived. A Short whose
    Related video could not be set is `fail`ed and stays Private.
  * With the episode state (extras/pipeline.json next to STATE, investing-bros-producer), every
    `can-public` and every `public` tick re-checks it, each time, against its current revision: the
    pipeline's release.publish_ok must be current, each group's `ok` approval current, and the video
    ID here must be the one in the pipeline's upload record. A re-upload after the approval (a new
    ID) makes that group's checks stale: `set-video` records the new ID and reopens the group, and
    the owner's publish OK has to be given again.
Exit 1 when a command is refused.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ORDER = ["release", "redcircle", "episode", "seg01", "seg02", "short01", "short02", "short03"]
ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")

CHECKS = {
    "release": [
        ("publish_ok", "pre", "The episode owner's OK to publish, in their own words, covering these video IDs"),
    ],
    "redcircle": [
        ("audio", "pre", "Edited episode audio uploaded; Episode Number N, Season 1, type Full"),
        ("copy", "pre", "Title and description pasted from the -rtl files; screenshot shows `?` at the end of the title and chapters in order"),
        ("titles", "pre", "check_titles_match.py passes (YouTube title vs RedCircle title)"),
        ("public", "public", "Published on RedCircle"),
        ("live", "live", "Public episode page shows the title with `?`; `check_live.py redcircle --episode N` passes"),
    ],
    "episode": [
        ("channel", "pre", "Opened from the אחים להשקעות video list (studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw/videos), avatar menu shows אחים להשקעות active (not Grok Bot); re-checked on every edit page"),
        ("meta", "pre", "Title = the plain YouTube title; description pasted plain with the `האזינו בספוטיפיי:` line; check_links.py passes"),
        ("thumb", "pre", "Approved thumbnail set (reopened Details shows it)"),
        ("endscreen", "pre", "End screen: previous episode(s) + Subscribe over the last 20 s, verified in the Editor preview after reopening"),
        ("public", "public", "Full episode switched to Public"),
        ("live", "live", "`check_live.py youtube ID --expect public` passes; watch page shows chapters and right-aligned description"),
    ],
    "segment": [
        ("channel", "pre", "Opened from the אחים להשקעות video list (studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw/videos), avatar menu shows אחים להשקעות active (not Grok Bot); re-checked on every edit page"),
        ("meta", "pre", "Title and description (with `לפרק המלא: <full-episode URL>`) saved; check_links.py passes"),
        ("thumb", "pre", "Approved thumbnail set"),
        ("card", "pre", "One Video card to the full episode at ~0:30, message and teaser `לפרק המלא`, verified after reopening the Editor"),
        ("endscreen", "pre", "End screen: the full episode + Subscribe over the last 20 s, verified after reopening the Editor"),
        ("public", "public", "Segment switched to Public"),
        ("live", "live", "`check_live.py youtube ID --expect public` passes"),
    ],
    "short": [
        ("channel", "pre", "Opened from the אחים להשקעות video list (studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw/videos), avatar menu shows אחים להשקעות active (not Grok Bot); re-checked on every edit page"),
        ("meta", "pre", "Title = cover title; description first line = cover title, episode `&t=` link and Spotify line; check_links.py passes"),
        ("related", "pre", "Related video = the full episode, verified by reopening the Short's edit page (a description link does NOT count)"),
        ("srt", "pre", "Hebrew `.srt` subtitles shown as published in Studio → Subtitles after reopening"),
        ("cover", "pre", "Custom cover set"),
        ("approval", "pre", "The episode owner approved the cut in the approval round (or waived it in their words)"),
        ("public", "public", "Short switched to Public"),
        ("live", "live", "`check_live.py youtube ID --expect public` passes"),
    ],
}
NEVER_WAIVE = {"public", "live", "channel", "publish_ok"}
NEVER_WAIVE_SHORT = {"related"}
TITLES = {"release": "Publish OK", "redcircle": "RedCircle", "episode": "Full episode", "seg01": "Segment 01",
          "seg02": "Segment 02", "short01": "Short 01", "short02": "Short 02", "short03": "Short 03"}


def kind(group: str) -> str:
    return "segment" if group.startswith("seg") else "short" if group.startswith("short") else group


def build(episode: int, full: str, segments: list[str], shorts: list[str]) -> dict:
    ids = [full, *segments, *shorts]
    bad = [i for i in ids if not ID_RE.match(i)]
    if bad:
        raise ValueError(f"not 11-character video IDs (copy them from Studio): {bad}")
    if len(segments) != 2 or len(shorts) != 3:
        raise ValueError("every episode publishes exactly 2 segments and 3 Shorts")
    if len(set(ids)) != len(ids):
        raise ValueError("the same video ID is listed twice")
    vids = {"release": None, "redcircle": None, "episode": full, "seg01": segments[0], "seg02": segments[1],
            "short01": shorts[0], "short02": shorts[1], "short03": shorts[2]}
    items = []
    for g in ORDER:
        for key, phase, label in CHECKS[kind(g)]:
            items.append({"id": f"{g}.{key}", "group": g, "phase": phase,
                          "label": label.replace("Number N", f"Number {episode}").replace("--episode N", f"--episode {episode}"),
                          "state": "open", "note": ""})
    return {"episode": episode, "videos": vids, "items": items}


def upgrade(state: dict) -> dict:
    """A state file made before release.publish_ok existed gets the item, open."""
    if not any(it["id"] == "release.publish_ok" for it in state["items"]):
        key, phase, label = CHECKS["release"][0]
        state["items"].insert(0, {"id": "release.publish_ok", "group": "release", "phase": phase, "label": label,
                                  "state": "open", "note": ""})
        state["videos"].setdefault("release", None)
    return state


def covered_videos(state: dict) -> dict:
    return {g: v for g, v in state["videos"].items() if v}


def publish_ok_problem(state: dict):
    """Why release.publish_ok doesn't hold now, or None."""
    it = _find(state, "release.publish_ok")
    if it["state"] != "ticked":
        return "release.publish_ok: no publish OK from the episode owner yet (publish-ok --by)"
    if it.get("covers") != covered_videos(state):
        return "release.publish_ok: stale, the video IDs changed after the OK; ask the owner again"
    return None


def record_publish_ok(state: dict, by: str, owner_check) -> None:
    ok, owner, msg = owner_check(by)
    if not ok:
        raise PermissionError(f"refused: publish OK {msg}")
    it = _find(state, "release.publish_ok")
    it.update(state="ticked", note=by.strip(), owner=owner, covers=covered_videos(state))


TRACK = {"redcircle": "release", "episode": "main", "seg01": "seg01", "seg02": "seg02",
         "short01": "short01", "short02": "short02", "short03": "short03"}


def pipeline_problems(checklist_path: Path, state: dict) -> "dict | None":
    """{group: [problems]} (key "*" for the release) from the episode's extras/pipeline.json, read now;
    None when the episode has no pipeline state (older episodes)."""
    sys.path.insert(0, str(Path(__file__).parent))
    import pipeline_state as PS
    sp = PS.find_state_near(checklist_path)
    if sp is None:
        return None
    ep = PS.episode_dir_of(sp)
    ps = PS.load(ep)
    ev = PS.evaluate(ep, ps)
    stages = ps.get("stages", {})
    out = {"*": []}
    pok = ev.get("release.publish_ok", {"status": "missing", "why": "not given"})
    if pok["status"] != "current":
        out["*"].append(f"pipeline.json (revision {ps.get('revision')}): release.publish_ok is {pok['status']}"
                        + (f" ({pok['why']})" if pok.get("why") else "") + "; ask the episode owner again")
    for g, t in TRACK.items():
        probs = []
        if t != "release":
            okv = ev.get(f"{t}.ok", {"status": "missing", "why": ""})
            if okv["status"] != "current":
                probs.append(f"{t}.ok is {okv['status']}" + (f" ({okv['why']})" if okv.get("why") else ""))
            cur = ((stages.get(f"{t}.upload") or {}).get("data") or {}).get("video_id")
            if cur != state["videos"].get(g):
                probs.append(f"{g}: the checklist has {state['videos'].get(g)}, the current upload is {cur} "
                             f"(re-uploaded): `set-video STATE {g} <ID copied from the record>` and re-check")
        out[g] = probs
    return out


def pipeline_blockers(checklist_path: Path, state: dict, group: str) -> list:
    probs = pipeline_problems(checklist_path, state)
    if probs is None:
        return []
    gi = ORDER.index(group)
    return probs["*"] + [p for g in ORDER[1:gi + 1] for p in probs.get(g, [])]


def set_video(state: dict, group: str, vid: str) -> None:
    if group not in ORDER or group in ("release", "redcircle"):
        raise ValueError(f"{group} has no YouTube video")
    if not ID_RE.match(vid):
        raise ValueError(f"not an 11-character video ID (copy it from the upload record): {vid}")
    if vid in [v for g, v in state["videos"].items() if g != group]:
        raise ValueError("that video ID belongs to another group")
    old = state["videos"][group]
    state["videos"][group] = vid
    for it in state["items"]:
        if it["group"] == group:
            it.update(state="open", note=f"reopened: video {old} -> {vid}")


def _find(state: dict, item_id: str) -> dict:
    for it in state["items"]:
        if it["id"] == item_id:
            return it
    raise KeyError(f"no item {item_id!r}; run `status` to see the ids")


def done(it: dict) -> bool:
    return it["state"] in ("ticked", "waived")


def blockers(state: dict, item_id: str) -> list[str]:
    """Items that must be done before item_id may be ticked."""
    it = _find(state, item_id)
    g, phase = it["group"], it["phase"]
    if phase == "pre":
        return []
    if phase == "public" and publish_ok_problem(state):
        return ["release.publish_ok"]
    pub = _find(state, f"{g}.public")
    if phase == "live":
        return [] if done(pub) else [pub["id"]]
    gi = ORDER.index(g)
    return [x["id"] for x in state["items"]
            if not done(x) and (ORDER.index(x["group"]) < gi or (x["group"] == g and x["phase"] == "pre"))]


def tick(state: dict, item_id: str, evidence: str) -> None:
    if item_id == "release.publish_ok":
        raise PermissionError("refused: record the owner's OK with publish-ok --by, not tick")
    if not evidence.strip():
        raise ValueError("a tick needs --evidence: what you saw and where")
    b = blockers(state, item_id)
    if b:
        raise PermissionError(f"refused: {item_id} is blocked by {', '.join(b)}")
    it = _find(state, item_id)
    it.update(state="ticked", note=evidence.strip())


def fail(state: dict, item_id: str, reason: str) -> None:
    _find(state, item_id).update(state="failed", note=reason.strip())


def waive(state: dict, item_id: str, by: str, owner_check=None) -> None:
    it = _find(state, item_id)
    key = item_id.split(".", 1)[1]
    if key in NEVER_WAIVE or (kind(it["group"]) == "short" and key in NEVER_WAIVE_SHORT):
        raise PermissionError(f"refused: {item_id} can never be waived")
    ok, _owner, msg = (owner_check or _default_owner_check)(by)
    if not ok:
        raise PermissionError(f"refused: a waiver {msg}")
    it.update(state="waived", note=by.strip())


def _default_owner_check(by: str):
    """No episode state known: the approver is Amitai."""
    sys.path.insert(0, str(Path(__file__).parent))
    import episode_owner
    return episode_owner.check_quote(by, Path("/nonexistent-episode"))


def owner_check_for(path: Path):
    sys.path.insert(0, str(Path(__file__).parent))
    import episode_owner
    return lambda by: episode_owner.check_quote(by, path)


def render(state: dict) -> str:
    box = {"ticked": "[x]", "waived": "[x]", "open": "[ ]", "failed": "[ ]"}
    lines = [f"Publish checklist, episode {state['episode']}"]
    for g in ORDER:
        vid = state["videos"].get(g)
        head = TITLES[g] + (f" ({vid}, https://youtu.be/{vid})" if vid else "")
        lines += ["", f"**{head}**"]
        for it in (x for x in state["items"] if x["group"] == g):
            tag = {"waived": " (waived)", "failed": " FAILED"}.get(it["state"], "")
            note = f": {it['note']}" if it["note"] else ""
            lines.append(f"- {box[it['state']]} {it['label']}{tag}{note}")
    open_ = [x["id"] for x in state["items"] if not done(x)]
    lines += ["", "All checks done." if not open_ else f"Still open or failed: {', '.join(open_)}"]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("state"); p.add_argument("--episode", type=int, required=True)
    p.add_argument("--full", required=True); p.add_argument("--segments", nargs=2, required=True)
    p.add_argument("--shorts", nargs=3, required=True); p.add_argument("--force", action="store_true")
    p = sub.add_parser("publish-ok"); p.add_argument("state"); p.add_argument("--by", required=True)
    for name, extra in (("tick", "--evidence"), ("fail", "--reason"), ("waive", "--by")):
        p = sub.add_parser(name); p.add_argument("state"); p.add_argument("item"); p.add_argument(extra, required=True)
    p = sub.add_parser("can-public"); p.add_argument("state"); p.add_argument("group", choices=ORDER)
    p = sub.add_parser("set-video"); p.add_argument("state"); p.add_argument("group", choices=ORDER); p.add_argument("id")
    for name in ("status", "render"):
        p = sub.add_parser(name); p.add_argument("state")
    a = ap.parse_args(argv)
    path = Path(a.state)
    try:
        if a.cmd == "init":
            if path.exists() and not a.force:
                raise FileExistsError(f"{path} exists; it holds ticks already (use --force to start over)")
            path.write_text(json.dumps(build(a.episode, a.full, a.segments, a.shorts), ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"created {path}")
            return 0
        state = upgrade(json.loads(path.read_text(encoding="utf-8")))
        if a.cmd == "publish-ok":
            record_publish_ok(state, a.by, owner_check_for(path))
            path.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
            print("publish-ok: release.publish_ok covers " + ", ".join(f"{g} {v}" for g, v in covered_videos(state).items()))
        elif a.cmd == "set-video":
            set_video(state, a.group, a.id)
            path.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"set-video: {a.group} {a.id}; its checks are open again and the publish OK must be given again")
        elif a.cmd in ("tick", "fail", "waive"):
            if a.cmd == "tick" and _find(state, a.item)["phase"] == "public":
                pb = pipeline_blockers(path, state, _find(state, a.item)["group"])
                if pb:
                    raise PermissionError(f"refused: {a.item}: " + "; ".join(pb))
            {"tick": lambda: tick(state, a.item, a.evidence), "fail": lambda: fail(state, a.item, a.reason),
             "waive": lambda: waive(state, a.item, a.by, owner_check_for(path))}[a.cmd]()
            path.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"{a.cmd}: {a.item}")
        elif a.cmd == "can-public":
            b = blockers(state, f"{a.group}.public")
            pb = pipeline_blockers(path, state, a.group)
            print("yes" if not (b or pb) else "NO, " + "; ".join((["open: " + ", ".join(b)] if b else []) + pb))
            return 0 if not (b or pb) else 1
        elif a.cmd == "status":
            nxt = next((x for x in state["items"] if not done(x)), None)
            print("all done" if nxt is None else f"next: {nxt['id']} [{nxt['state']}] {nxt['label']}")
        else:
            print(render(state))
    except (PermissionError, ValueError, KeyError, FileExistsError) as e:
        print(e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
