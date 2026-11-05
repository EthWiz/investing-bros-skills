#!/usr/bin/env python3
"""The episode's gate items and their file checks (investing-bros-post-production -> references/CHECKLIST.md).

Used by pipeline.py (investing-bros-producer) and postprod_checklist.py (investing-bros-post-production);
shared by both skills as identical copies (edit them together). It reads files only; marks and waivers
are passed in by the caller.

Stages (each includes the ones before it): upload, review, done.
Package contracts (the show's Drive tree and Naming):
  segments/  flat, exactly slots 01 and 02, one package each:
             סגמנט-NN-<סוג>-<נושא>.mp4 + .txt + -thumb.jpg + youtube-סגמנט-NN.md, none empty;
             slot 01 is the deep dive (סגמנט-01-צלילה-...).
  Shorts/    exactly slots 01-03, one package each:
             שורט-NN-<נושא>.m4v + -cover.jpg + .srt + youtube-שורט-NN.md, none empty
             (a Short is never filed as .mp4).
"""
import json
import re
import sys
from pathlib import Path

TS_RE = re.compile(r"^\s*\u200f?\(?(\d{1,2}:)?\d{1,2}:\d{2}\b", re.M)

STAGES = ["upload", "review", "done"]
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
     "after any swap, every grid eyeballed before it went to the owner (mark with what you saw)"),
    ("cover_checks", "upload", "extras/cover-check.log: check_cover.py OK for both episode covers with --title/--register "
     "headlines, no FAIL + mark: made by Codex on Amitai's Mac (session/prompt path)"),
    ("segments", "review", "segments/: exactly two complete packages, 01 (deep dive) and 02: "
     "סגמנט-NN-<סוג>-<נושא>.mp4 + .txt + -thumb.jpg + youtube-סגמנט-NN.md, none empty"),
    ("shorts", "review", "Shorts/: exactly three complete packages, 01-03: "
     "שורט-NN-<נושא>.m4v + -cover.jpg + .srt + youtube-שורט-NN.md, none empty"),
    ("shorts_covers", "review", "Each Short's -cover.jpg in Shorts/ + mark: face format from real frames, "
     "Codex on Amitai's Mac, check_cover.py OK"),
    ("past_episode_cards", "review", "extras/past-episode-cards.json (find_past_episode_refs.py, max 4, IDs from "
     "investing-bros-show/references/episode-index.json, [] if none) + mark: cards added in Studio at those times"),
    ("redcircle_draft", "review", "RedCircle unpublished draft (mark with the draft URL)"),
    ("published", "done", "extras/publish-checklist.json from investing-bros-publish with every item ticked or waived"),
    ("spotify_links", "done", "Spotify episode URL swapped in for the show link on the episode, both segments and "
     "all three Shorts; check_links.py passed (mark with the URL)"),
    ("old_uploads", "done", "Superseded Private YouTube uploads of this episode's assets deleted, nothing public or "
     "current touched (mark with the deleted IDs, or 'none')"),
]
IDS = [i for i, _, _ in ITEMS]
MANUAL = {"transcript_doc", "redcircle_draft", "face_identity", "old_uploads", "spotify_links"}
# file check AND a mark (chapters shifted; teaser moments reviewed; cover provenance)
NEEDS_MARK = {"chapters", "teaser_quality", "cover_checks", "shorts_covers", "past_episode_cards"}
# an item that falls away when the episode owner waives its parent
WAIVED_WITH = {"teaser_quality": "teaser", "shorts_covers": "shorts"}


def _find(ep: Path, name: str):
    hits = [p for p in ep.rglob(name) if p.is_file()]
    return hits[0] if hits else None


SEG_DIR = "segments"
SEG_VIDEO = re.compile(r"^סגמנט-(\d{2})-(.+)\.mp4$")
SHORT_VIDEO = re.compile(r"^שורט-(\d{2})-(.+)\.(m4v|mp4)$")


def shorts_dir(ep: Path):
    """Shorts/ (the show's name), or an existing lowercase shorts/ (accepted by the show's Shorts rule)."""
    for name in ("Shorts", "shorts"):
        if (ep / name).is_dir():
            return ep / name
    return None


def _nonempty(p: Path) -> bool:
    return p.is_file() and p.stat().st_size > 0


def package_problems(folder, slots, video_re, notes_fmt, companions, what, video_ext):
    """(slot, problem) pairs for one flat folder: exactly one final video per slot, no other slots, every
    companion file present and non-empty. slot is None for a folder-wide problem, "extra" for a slot that
    isn't a standing deliverable. companions(stem) -> the file names that go next to the video."""
    if folder is None or not folder.is_dir():
        return [(None, f"no {what} folder")]
    probs, videos = [], {}
    nested = sorted(p.name for p in folder.iterdir() if p.is_dir())
    for p in sorted(folder.iterdir()):
        if not p.is_file():
            continue
        m = video_re.match(p.name)
        if m:
            if len(m.groups()) > 2 and m.group(3) != video_ext:
                probs.append((m.group(1), f"{p.name}: a Short is filed as .{video_ext} (Drive plays video/x-m4v), "
                              f"never .{m.group(3)}"))
                continue
            videos.setdefault(m.group(1), []).append(p)
    for slot, files in sorted(videos.items()):
        if slot not in slots:
            probs.append(("extra", f"slot {slot} is not a standing deliverable (exactly {', '.join(slots)}): "
                          + ", ".join(f.name for f in files)))
    for slot in slots:
        files = videos.get(slot, [])
        if not files:
            probs.append((slot, f"{what} {slot}: no final video"))
            continue
        if len(files) > 1:
            probs.append((slot, f"{what} {slot}: {len(files)} final candidates ({', '.join(f.name for f in files)}); "
                          "keep only the selected one, move the others to extras/"))
            continue
        v = files[0]
        need = [v.name, *companions(v.name[: -len(video_ext) - 1]), notes_fmt.format(slot)]
        missing = [n for n in need if not (folder / n).is_file()]
        empty = [n for n in need if n not in missing and not _nonempty(folder / n)]
        if missing:
            probs.append((slot, f"{what} {slot}: missing " + ", ".join(missing)))
        if empty:
            probs.append((slot, f"{what} {slot}: empty " + ", ".join(empty)))
    if nested and not any(videos.values()):
        probs.append((None, f"files must sit flat in {folder.name}/ (show Drive tree), not in subfolders: "
                      + ", ".join(nested)))
    return probs


def segment_problems(ep: Path):
    probs = package_problems(ep / SEG_DIR, ["01", "02"], SEG_VIDEO, "youtube-סגמנט-{}.md",
                             lambda stem: [f"{stem}.txt", f"{stem}-thumb.jpg"], "segment", "mp4")
    seg = ep / SEG_DIR
    if seg.is_dir():
        firsts = [p.name for p in seg.glob("סגמנט-01-*.mp4")]
        if len(firsts) == 1 and not firsts[0].startswith("סגמנט-01-צלילה-"):
            probs.append(("01", f"segment 01 is the deep dive: name it סגמנט-01-צלילה-<נושא> (is {firsts[0]})"))
    return probs


def short_problems(ep: Path):
    return package_problems(shorts_dir(ep), ["01", "02", "03"], SHORT_VIDEO, "youtube-שורט-{}.md",
                            lambda stem: [f"{stem}-cover.jpg", f"{stem}.srt"], "short", "m4v")


def slot_problems(ep: Path, kind: str, slot: str) -> list:
    """Problems of one package: kind "segment" or "short", slot "01".."03"."""
    probs = segment_problems(ep) if kind == "segment" else short_problems(ep)
    return [m for s, m in probs if s in (slot, None)]


def slot_file(ep: Path, kind: str, slot: str, suffix: str):
    """The slot's file with this suffix (".mp4", "-thumb.jpg", ".m4v", "-cover.jpg", ".srt", ".txt"), or None."""
    folder = ep / SEG_DIR if kind == "segment" else shorts_dir(ep)
    if folder is None or not folder.is_dir():
        return None
    word = "סגמנט" if kind == "segment" else "שורט"
    hits = sorted(p for p in folder.glob(f"{word}-{slot}-*{suffix}") if p.is_file()
                  and (suffix in ("-thumb.jpg", "-cover.jpg") or not p.name.endswith(("-thumb.jpg", "-cover.jpg"))))
    return hits[0] if len(hits) == 1 else None


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
        sh = shorts_dir(ep)
        if sh is None:
            return "no Shorts/ folder"
        bad = [f"{v.name[:-4]}-cover.jpg" for v in sorted(sh.glob("שורט-*.m4v"))
               if not _nonempty(sh / f"{v.name[:-4]}-cover.jpg")]
        k = len([v for v in sh.glob("שורט-*.m4v")])
        if k != 3:
            return f"{k}/3 Shorts (.m4v) to match covers to"
        return None if not bad else "missing or empty " + ", ".join(bad)
    if item == "past_episode_cards":
        c = x / "past-episode-cards.json"
        if not c.is_file():
            return "missing extras/past-episode-cards.json (find_past_episode_refs.py)"
        here = Path(__file__).resolve().parent
        for d in (here, here.parents[1] / "investing-bros-post-production" / "scripts"):
            sys.path.insert(0, str(d))
        try:
            import find_past_episode_refs as fr
        except ImportError:
            return "can't validate extras/past-episode-cards.json: install investing-bros-post-production"
        try:
            idx = here.parents[1] / "investing-bros-show/references/episode-index.json"
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
        out = []
        for f in (f"thumbnail-פרק-{n}.jpg", f"cover-פרק-{n}.png"):
            if _nonempty(ep / f):
                continue
            elsewhere = _find(ep, f)
            out.append(f"{f} is in {elsewhere.parent.relative_to(ep)}/, move it to the episode root" if elsewhere
                       else f"missing {f} in the episode root")
        return "; ".join(out) or None
    if item == "segments":
        return "; ".join(m for _, m in segment_problems(ep)) or None
    if item == "shorts":
        return "; ".join(m for _, m in short_problems(ep)) or None
    if item == "published":
        f = x / "publish-checklist.json"
        if not f.is_file():
            return "missing extras/publish-checklist.json (investing-bros-publish)"
        try:
            items = json.loads(f.read_text(encoding="utf-8"))["items"]
        except (ValueError, KeyError, TypeError):
            return "extras/publish-checklist.json unreadable"
        open_ = [i["id"] for i in items if i.get("state") not in ("ticked", "waived")]
        return None if items and not open_ else f"publish checklist still open: {', '.join(open_[:6])}"
    return None  # manual items have no file check


def check(ep: Path, n: int, stage: str = "upload", marked=None, waived=None):
    """rows [(status, item, note)], missing [item]: every item of `stage` and the stages before it."""
    marked, waived = marked or {}, waived or {}
    if stage not in STAGES:
        raise ValueError(f"stage must be one of {STAGES}")
    wanted = [it for it in ITEMS if STAGES.index(it[1]) <= STAGES.index(stage)]
    rows, missing = [], []
    for item, _, label in wanted:
        reason = item_problem(ep, n, item, marked, waived)
        if reason is None:
            note = waived.get(item) or (f"with {WAIVED_WITH[item]}: {waived[WAIVED_WITH[item]]}"
                                        if WAIVED_WITH.get(item) in waived else None)
            rows.append(("WAIVED", item, note) if note else ("OK", item, marked.get(item, "")))
        else:
            rows.append(("MISSING", item, f"{label} — {reason}"))
            missing.append(item)
    return rows, missing


def item_problem(ep: Path, n: int, item: str, marked=None, waived=None):
    """None when the item passes (or is waived), else why not."""
    marked, waived = marked or {}, waived or {}
    if item in waived or WAIVED_WITH.get(item) in waived:
        return None
    reason = None if item in MANUAL else file_check(ep, n, item)
    if reason is None and (item in MANUAL or item in NEEDS_MARK) and item not in marked:
        reason = "needs mark --evidence"
    return reason
