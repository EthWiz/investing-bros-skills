#!/usr/bin/env python3
"""The publish checklist: one ordered list of checks, ticked one by one, that refuses
to let anything go Public out of order. Its rendered form is the report to Amitai.

  publish_checklist.py init STATE --episode N --full ID --segments ID ID --shorts ID ID ID
  publish_checklist.py tick STATE ITEM --evidence "what you saw, where"
  publish_checklist.py fail STATE ITEM --reason "what went wrong"
  publish_checklist.py waive STATE ITEM --by "Amitai, <time>: <his words>"
  publish_checklist.py can-public STATE GROUP     # exit 0 only if GROUP may go Public now
  publish_checklist.py status STATE                # next open item
  publish_checklist.py render STATE                # Markdown ticked checklist for Amitai

STATE is a JSON file (keep it next to the episode's notes, e.g. extras/publish-checklist.json).
Video IDs are copied from Studio or tool output, never typed.

Groups, in the only allowed order: redcircle, episode, seg01, seg02, short01, short02,
short03. Each group's checks have a phase:
  pre    - verified in Studio (or RedCircle) while still Private / Unpublished
  public - the switch to Public itself
  live   - verified from outside after the switch (check_live.py)
  post   - after Public (pinned comment)
Rules enforced:
  * A group's `public` item can be ticked only when every item of every earlier group
    and every pre item of its own group is ticked (or waived where waivable).
  * live and post items can be ticked only after their group's `public` item.
  * public, live and every Short's `related` item can never be waived. A Short whose
    Related video could not be set is `fail`ed and stays Private.
Exit 1 when a command is refused.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ORDER = ["redcircle", "episode", "seg01", "seg02", "short01", "short02", "short03"]
ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")

CHECKS = {
    "redcircle": [
        ("audio", "pre", "Edited episode audio uploaded; Episode Number N, Season 1, type Full"),
        ("copy", "pre", "Title and description pasted from the -rtl files; screenshot shows `?` at the end of the title and chapters in order"),
        ("titles", "pre", "check_titles_match.py passes (YouTube title vs RedCircle title)"),
        ("public", "public", "Published on RedCircle"),
        ("live", "live", "Public episode page shows the title with `?`; `check_live.py redcircle --episode N` passes"),
    ],
    "episode": [
        ("channel", "pre", "Studio header shows אחים להשקעות (channel UCWIlggXQNDFiyJghl6VB6Xw), not Grok Bot"),
        ("meta", "pre", "Title = the plain YouTube title; description pasted plain with the `האזינו בספוטיפיי:` line; check_links.py passes"),
        ("thumb", "pre", "Approved thumbnail set (reopened Details shows it)"),
        ("endscreen", "pre", "End screen: previous episode(s) + Subscribe over the last 20 s, verified in the Editor preview after reopening"),
        ("public", "public", "Full episode switched to Public"),
        ("live", "live", "`check_live.py youtube ID --expect public` passes; watch page shows chapters and right-aligned description"),
    ],
    "segment": [
        ("meta", "pre", "Title and description (with `לפרק המלא: <full-episode URL>`) saved; check_links.py passes"),
        ("thumb", "pre", "Approved thumbnail set"),
        ("card", "pre", "One Video card to the full episode at ~0:30, message and teaser `לפרק המלא`, verified after reopening the Editor"),
        ("endscreen", "pre", "End screen: the full episode + Subscribe over the last 20 s, verified after reopening the Editor"),
        ("public", "public", "Segment switched to Public"),
        ("live", "live", "`check_live.py youtube ID --expect public` passes"),
        ("pin", "post", "Comment `לפרק המלא: <full-episode URL>` posted AS אחים להשקעות (not Grok Bot) and pinned"),
    ],
    "short": [
        ("meta", "pre", "Title = cover title; description first line = cover title, episode `&t=` link and Spotify line; check_links.py passes"),
        ("related", "pre", "Related video = the full episode, verified by reopening the Short's edit page (a description link does NOT count)"),
        ("srt", "pre", "Hebrew `.srt` subtitles shown as published in Studio → Subtitles after reopening"),
        ("cover", "pre", "Custom cover set"),
        ("approval", "pre", "Nadav approved the cut (or Amitai waived it in chat)"),
        ("public", "public", "Short switched to Public"),
        ("live", "live", "`check_live.py youtube ID --expect public` passes"),
        ("pin", "post", "Full-episode comment posted AS אחים להשקעות (not Grok Bot) and pinned"),
    ],
}
NEVER_WAIVE = {"public", "live"}
NEVER_WAIVE_SHORT = {"related"}
TITLES = {"redcircle": "RedCircle", "episode": "Full episode", "seg01": "Segment 01",
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
    vids = {"redcircle": None, "episode": full, "seg01": segments[0], "seg02": segments[1],
            "short01": shorts[0], "short02": shorts[1], "short03": shorts[2]}
    items = []
    for g in ORDER:
        for key, phase, label in CHECKS[kind(g)]:
            items.append({"id": f"{g}.{key}", "group": g, "phase": phase,
                          "label": label.replace("Number N", f"Number {episode}").replace("--episode N", f"--episode {episode}"),
                          "state": "open", "note": ""})
    return {"episode": episode, "videos": vids, "items": items}


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
    pub = _find(state, f"{g}.public")
    if phase in ("live", "post"):
        return [] if done(pub) else [pub["id"]]
    gi = ORDER.index(g)
    return [x["id"] for x in state["items"]
            if not done(x) and (ORDER.index(x["group"]) < gi or (x["group"] == g and x["phase"] == "pre"))]


def tick(state: dict, item_id: str, evidence: str) -> None:
    if not evidence.strip():
        raise ValueError("a tick needs --evidence: what you saw and where")
    b = blockers(state, item_id)
    if b:
        raise PermissionError(f"refused: {item_id} is blocked by {', '.join(b)}")
    it = _find(state, item_id)
    it.update(state="ticked", note=evidence.strip())


def fail(state: dict, item_id: str, reason: str) -> None:
    _find(state, item_id).update(state="failed", note=reason.strip())


def waive(state: dict, item_id: str, by: str) -> None:
    it = _find(state, item_id)
    key = item_id.split(".", 1)[1]
    if key in NEVER_WAIVE or (kind(it["group"]) == "short" and key in NEVER_WAIVE_SHORT):
        raise PermissionError(f"refused: {item_id} can never be waived")
    if "amitai" not in by.lower():
        raise PermissionError("refused: only Amitai can waive a check; quote his message in --by")
    it.update(state="waived", note=by.strip())


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
    for name, extra in (("tick", "--evidence"), ("fail", "--reason"), ("waive", "--by")):
        p = sub.add_parser(name); p.add_argument("state"); p.add_argument("item"); p.add_argument(extra, required=True)
    p = sub.add_parser("can-public"); p.add_argument("state"); p.add_argument("group", choices=ORDER)
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
        state = json.loads(path.read_text(encoding="utf-8"))
        if a.cmd in ("tick", "fail", "waive"):
            {"tick": lambda: tick(state, a.item, a.evidence), "fail": lambda: fail(state, a.item, a.reason),
             "waive": lambda: waive(state, a.item, a.by)}[a.cmd]()
            path.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"{a.cmd}: {a.item}")
        elif a.cmd == "can-public":
            b = blockers(state, f"{a.group}.public")
            print("yes" if not b else "NO, open: " + ", ".join(b))
            return 0 if not b else 1
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
