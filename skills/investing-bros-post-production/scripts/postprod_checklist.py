#!/usr/bin/env python3
"""Post-production gate: inspect an episode dir and fail, listing every missing deliverable.

Usage:
  postprod_checklist.py check EP_DIR --episode N [--stage upload|done]
  postprod_checklist.py mark  EP_DIR ITEM --evidence "what you saw, where"
  postprod_checklist.py waive EP_DIR ITEM --by "Amitai HH:MM: <his own words>"

--stage upload (default): everything the full-episode YouTube upload needs.
--stage done: the complete deliverable list ("full treatment").
Marks and waivers live in EP_DIR/extras/postprod-checklist.json.
Exit 0 = pass, 1 = missing items (printed), 2 = usage error.
See ../references/CHECKLIST.md.
"""
import argparse
import json
import re
import sys
from pathlib import Path

TS_RE = re.compile(r"^\s*\u200f?\(?(\d{1,2}:)?\d{1,2}:\d{2}\b", re.M)

# id, stage, label. Items listed in MANUAL can only be satisfied by `mark` (external evidence).
ITEMS = [
    ("audio", "upload", "Edited audio הקלטה-ערוכה-פרק-N.m4a in the episode root"),
    ("transcript", "upload", "extras/transcript/segments.json"),
    ("transcript_doc", "upload", "Google Doc 'תמלול - פרק N' in Drive (mark with its URL)"),
    ("cut_list", "upload", "extras/edit.json + extras/cuts-review/cuts-list.txt + a review clip per cut"),
    ("teaser", "upload", "Combined full-frame cold-open teaser in promo/ (teaser|cold|טיזר in name)"),
    ("teaser_quality", "upload", "extras/teaser-check.log says CAPTIONS OK (build_fullframe_teaser.py --check) + mark: "
     "every moment checked against teaser-rules.md (stands alone, payoff kept, no unexplained names)"),
    ("intro", "upload", "Canonical intro/outro clip fetched into extras/ (*intro*.mp4)"),
    ("full_video", "upload", "video/פרק-N-וידאו.mp4"),
    ("chapters", "upload", "video/תיאור-פרק-N-youtube.txt with >=3 chapter timestamps, shifted past teaser+intro (mark)"),
    ("verify_sync", "upload", "extras/verify_sync.log says SYNC OK and no FAIL"),
    ("titles_description", "upload", "כותרות-פרק-N.txt and תיאור-פרק-N.txt"),
    ("thumbnail_cover", "upload", "thumbnail-פרק-N.jpg and cover-פרק-N.png"),
    ("face_identity", "upload", "Face grids labeled by verified host identity: side mapping checked at the start and "
     "after any swap, every grid eyeballed before it went to Amitai (mark with what you saw)"),
    ("cover_checks", "upload", "extras/cover-check.log: check_cover.py OK for both episode covers with --title/--register "
     "headlines, no FAIL + mark: made by Codex on Amitai's Mac (session/prompt path)"),
    ("segments", "done", "segments/סגמנט-01 and סגמנט-02, each with an .mp4"),
    ("shorts", "done", "Shorts/ with exactly three rendered shorts (.mp4)"),
    ("shorts_covers", "done", "Three Shorts covers (*-cover.jpg) in Shorts/ + mark: face format from real frames, "
     "Codex on Amitai's Mac, check_cover.py OK"),
    ("past_episode_cards", "done", "extras/past-episode-cards.json (find_past_episode_refs.py, max 4, IDs from "
     "investing-bros-show/references/episode-index.json, [] if none) + mark: cards added in Studio at those times"),
    ("redcircle_draft", "done", "RedCircle unpublished draft (mark with the draft URL)"),
    ("old_uploads", "done", "Superseded Private YouTube uploads of this episode's assets deleted, nothing public or "
     "current touched (mark with the deleted IDs, or 'none')"),
]
IDS = [i for i, _, _ in ITEMS]
MANUAL = {"transcript_doc", "redcircle_draft", "face_identity", "old_uploads"}
# file check AND a mark (chapters shifted; teaser moments reviewed; cover provenance)
NEEDS_MARK = {"chapters", "teaser_quality", "cover_checks", "shorts_covers", "past_episode_cards"}
# an item that falls away when Amitai waives its parent
WAIVED_WITH = {"teaser_quality": "teaser", "shorts_covers": "shorts"}


def state_path(ep: Path) -> Path:
    return ep / "extras" / "postprod-checklist.json"


def load(ep: Path) -> dict:
    p = state_path(ep)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"marked": {}, "waived": {}}


def save(ep: Path, s: dict) -> None:
    p = state_path(ep)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


def _find(ep: Path, name: str):
    hits = [p for p in ep.rglob(name) if p.is_file()]
    return hits[0] if hits else None


def file_check(ep: Path, n: int, item: str):
    """Return None when satisfied by files, else a reason string."""
    x = ep / "extras"
    if item == "audio":
        return None if (ep / f"הקלטה-ערוכה-פרק-{n}.m4a").is_file() else "missing edited audio"
    if item == "transcript":
        return None if (x / "transcript" / "segments.json").is_file() else "missing transcript/segments.json"
    if item == "cut_list":
        if not (x / "edit.json").is_file():
            return "missing extras/edit.json"
        try:
            cuts = json.loads((x / "edit.json").read_text(encoding="utf-8")).get("cuts", [])
        except (ValueError, AttributeError):
            return "extras/edit.json unreadable"
        cr = x / "cuts-review"
        if not (cr / "cuts-list.txt").is_file():
            return "missing extras/cuts-review/cuts-list.txt"
        clips = list(cr.glob("*.mp4")) + list(cr.glob("*.m4a")) + list(cr.glob("*.wav"))
        if len(clips) < len(cuts):
            return f"{len(clips)} review clips for {len(cuts)} cuts"
        return None
    if item == "teaser":
        promo = ep / "promo"
        hits = [p for p in promo.glob("*.mp4") if re.search(r"teaser|cold|טיזר", p.name, re.I)] if promo.is_dir() else []
        return None if hits else "no cold-open teaser in promo/"
    if item == "teaser_quality":
        log = x / "teaser-check.log"
        if not log.is_file():
            return "missing extras/teaser-check.log (build_fullframe_teaser.py --check > it)"
        t = log.read_text(encoding="utf-8", errors="replace")
        return None if "CAPTIONS OK" in t and "FAIL" not in t else "teaser captions not OK"
    if item == "cover_checks":
        log = x / "cover-check.log"
        if not log.is_file():
            return "missing extras/cover-check.log (check_cover.py output for both covers)"
        t = log.read_text(encoding="utf-8", errors="replace")
        if "FAIL" in t:
            return "check_cover.py reported FAIL"
        miss = [f for f in (f"thumbnail-פרק-{n}.jpg", f"cover-פרק-{n}.png") if f"OK {f}" not in t]
        return None if not miss else "no check_cover OK for " + ", ".join(miss)
    if item == "shorts_covers":
        sh = ep / "Shorts"
        k = len(list(sh.rglob("*-cover.jpg"))) if sh.is_dir() else 0
        return None if k >= 3 else f"{k}/3 Shorts covers"
    if item == "past_episode_cards":
        c = x / "past-episode-cards.json"
        if not c.is_file():
            return "missing extras/past-episode-cards.json (find_past_episode_refs.py)"
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            import find_past_episode_refs as fr
            idx = Path(__file__).resolve().parents[2] / "investing-bros-show/references/episode-index.json"
            errs = fr.validate(json.loads(c.read_text(encoding="utf-8")), json.loads(idx.read_text(encoding="utf-8")))
        except ValueError:
            return "extras/past-episode-cards.json unreadable"
        return "; ".join(errs) or None
    if item == "intro":
        return None if list(x.glob("*intro*.mp4")) else "no intro clip in extras/"
    if item == "full_video":
        return None if (ep / "video" / f"פרק-{n}-וידאו.mp4").is_file() else "missing video/פרק-N-וידאו.mp4"
    if item == "chapters":
        d = ep / "video" / f"תיאור-פרק-{n}-youtube.txt"
        if not d.is_file():
            return "missing YouTube description"
        if len(TS_RE.findall(d.read_text(encoding="utf-8"))) < 3:
            return "fewer than 3 chapter timestamps"
        return None
    if item == "verify_sync":
        log = x / "verify_sync.log"
        if not log.is_file():
            return "missing extras/verify_sync.log"
        t = log.read_text(encoding="utf-8", errors="replace")
        return None if "SYNC OK" in t and "FAIL" not in t else "verify_sync not OK"
    if item == "titles_description":
        miss = [f for f in (f"כותרות-פרק-{n}.txt", f"תיאור-פרק-{n}.txt") if not (ep / f).is_file()]
        return None if not miss else "missing " + ", ".join(miss)
    if item == "thumbnail_cover":
        miss = [f for f in (f"thumbnail-פרק-{n}.jpg", f"cover-פרק-{n}.png") if not _find(ep, f)]
        return None if not miss else "missing " + ", ".join(miss)
    if item == "segments":
        bad = [s for s in ("סגמנט-01", "סגמנט-02") if not list((ep / "segments" / s).glob("*.mp4"))]
        return None if not bad else "missing " + ", ".join(bad)
    if item == "shorts":
        sh = ep / "Shorts"
        k = len(list(sh.rglob("*.mp4"))) if sh.is_dir() else 0
        return None if k >= 3 else f"{k}/3 shorts"
    return None  # manual items have no file check


def check(ep: Path, n: int, stage: str = "upload"):
    s = load(ep)
    wanted = [it for it in ITEMS if stage == "done" or it[1] == "upload"]
    rows, missing = [], []
    for item, _, label in wanted:
        if item in s["waived"]:
            rows.append(("WAIVED", item, s["waived"][item]))
            continue
        parent = WAIVED_WITH.get(item)
        if parent in s["waived"]:
            rows.append(("WAIVED", item, f"with {parent}: {s['waived'][parent]}"))
            continue
        reason = None if item in MANUAL else file_check(ep, n, item)
        if reason is None and (item in MANUAL or item in NEEDS_MARK) and item not in s["marked"]:
            reason = "needs mark --evidence"
        if reason:
            rows.append(("MISSING", item, f"{label} — {reason}"))
            missing.append(item)
        else:
            rows.append(("OK", item, s["marked"].get(item, "")))
    return rows, missing


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("ep"); c.add_argument("--episode", type=int, required=True)
    c.add_argument("--stage", choices=["upload", "done"], default="upload")
    m = sub.add_parser("mark"); m.add_argument("ep"); m.add_argument("item", choices=IDS); m.add_argument("--evidence", required=True)
    w = sub.add_parser("waive"); w.add_argument("ep"); w.add_argument("item", choices=IDS); w.add_argument("--by", required=True)
    a = ap.parse_args(argv)
    ep = Path(a.ep)
    if a.cmd == "check":
        rows, missing = check(ep, a.episode, a.stage)
        for st, item, note in rows:
            print(f"{st:8} {item:20} {note}")
        if missing:
            print(f"\nFAIL ({a.stage}): {len(missing)} missing: {', '.join(missing)}")
            print("Make them, or get Amitai's explicit waiver per item. Do not upload / report done.")
            return 1
        print(f"\nPASS ({a.stage})")
        return 0
    s = load(ep)
    if a.cmd == "mark":
        s["marked"][a.item] = a.evidence.strip()
    else:
        if not a.by.strip().lower().startswith("amitai"):
            print("waiver must quote Amitai: --by \"Amitai HH:MM: ...\"", file=sys.stderr)
            return 2
        s["waived"][a.item] = a.by.strip()
    save(ep, s)
    print(f"{a.cmd}ed {a.item}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
