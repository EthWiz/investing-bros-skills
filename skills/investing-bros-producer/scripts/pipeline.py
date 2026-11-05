#!/usr/bin/env python3
"""The episode pipeline: one state file, the next step per track, version fingerprints, the retro.

  pipeline.py start   EP --episode N --owner amitai|nadav [--by "<owner's words>"]
  pipeline.py migrate EP --episode N --owner amitai|nadav [--by "<owner's words>"]
  pipeline.py status  EP [--json]
  pipeline.py next    EP [--json]
  pipeline.py advance EP TRACK [STAGE]          # no STAGE: as far as the track goes
  pipeline.py approve EP TRACK STAGE --by "<Owner> HH:MM: <their words>"
  pipeline.py mark    EP ITEM --evidence "what you saw, where"
  pipeline.py waive   EP ITEM --by "<Owner> HH:MM: <their words>"      # ITEM: gate item or TRACK.STAGE
  pipeline.py owner   EP --set amitai|nadav --by "<the owner's words>"
  pipeline.py note    EP [--kind note|owner_fix|handback_returned|workaround] [--track T] "text"
  pipeline.py gate    EP --stage upload|review|done   # the post-production gate on this state
  pipeline.py retro   EP [--last PATH] [--force]
  pipeline.py doctor  [--online]

EP is the episode folder in the Drive layout (a local mirror: root files, extras/, segments/, Shorts/ ...).
State: EP/extras/pipeline.json (references/state-schema.md); this script is its only writer, and the
Producer syncs it to Drive extras/ after every change. Tracks and stages: references/gates.md.

Exit 0 = done / pass, 1 = refused or failed (reasons printed), 2 = usage error.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import episode_gates as G  # noqa: E402
import episode_owner as O  # noqa: E402
import pipeline_state as PS  # noqa: E402

TRACKS = ["main", "seg01", "seg02", "short01", "short02", "short03", "release"]
SHOW_CHANNEL_ID = "UCWIlggXQNDFiyJghl6VB6Xw"  # אחים להשקעות (investing-bros-show -> Roles and accounts)
RANGE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)")
CUT_TAG_RE = re.compile(r"^\[(routine|content)\]\s+\S")
TRACK_MARKS = {"main.endscreen", "seg01.select", "seg02.select", "seg01.nudge", "seg02.nudge", "seg01.links",
               "seg02.links", "short01.pick", "short02.pick", "short03.pick", "release.approval_round", "release.retro"}
MARKABLE = TRACK_MARKS | G.MANUAL | G.NEEDS_MARK
NOTE_KINDS = ["note", "owner_fix", "handback_returned", "workaround"]
P = "python3 <investing-bros-producer>/scripts/pipeline.py"


# ---- context --------------------------------------------------------------------------------------

class Ctx:
    def __init__(self, ep, state):
        self.ep, self.state = Path(ep), state
        self.n = int(state["episode"])
        self.hasher = PS.Hasher(ep)
        legacy = state.get("legacy") or {}
        self.marks = {**legacy.get("marked", {}), **{k: v["evidence"] for k, v in state.get("marks", {}).items()}}
        self.waived = {**legacy.get("waived", {}), **{k: v["quote"] for k, v in state.get("waivers", {}).items()}}
        self.ev = PS.evaluate(ep, state, self.hasher)

    def current(self, key):
        return self.ev.get(key, {}).get("status") == "current"

    def rel(self, p: Path) -> str:
        return str(Path(p).relative_to(self.ep))


def slot(track):
    return track[-2:]


# ---- checks: each returns a list of problems (empty = pass) ----------------------------------------

def items(*ids):
    def f(c):
        return [f"{i}: {r}" for i in ids if (r := G.item_problem(c.ep, c.n, i, c.marks, c.waived))]
    return f


def marks(*ids):
    def f(c):
        return [f"needs `{P} mark EP {i} --evidence ...`" for i in ids if i not in c.marks]
    return f


def cut_list_problems(text: str) -> list:
    """Every cut line in cuts-list.txt is tagged [routine] or [content]. Content cuts are the ones
    the review asks as questions; routine cuts stay on the list too. Blank lines and # comments are not cuts."""
    bad = []
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if not CUT_TAG_RE.match(s):
            bad.append(f"extras/cuts-review/cuts-list.txt:{i}: tag the cut [routine] or [content] "
                       "(content cuts are asked as questions; the whole list stays visible)")
    return bad


def cut_list_check(c):
    probs = files("extras/cuts-review/cuts-list.txt")(c)
    if probs:
        return probs
    return cut_list_problems((c.ep / "extras/cuts-review/cuts-list.txt").read_text(encoding="utf-8"))


def files(*rels):
    def f(c):
        out = []
        for r in rels:
            p = c.ep / r.format(n=c.n)
            if not (p.is_file() and p.stat().st_size > 0):
                out.append(f"missing or empty {r.format(n=c.n)}")
        return out
    return f


def raw_master(c):
    return [] if raw_master_files(c) else ["no raw master in extras/ (investing-bros-episode-raw-untrimmed.m4a/.mp4)"]


def raw_master_files(c):
    return [f"extras/investing-bros-episode-raw-untrimmed.{e}" for e in ("m4a", "mp4")
            if (c.ep / f"extras/investing-bros-episode-raw-untrimmed.{e}").is_file()]


def gate(stage):
    def f(c):
        _, missing = G.check(c.ep, c.n, stage, c.marks, c.waived)
        return [f"the post-production `{stage}` gate is missing: {', '.join(missing)}"] if missing else []
    return f


def record_path(c, track):
    return c.ep / "extras" / "uploads" / f"{track}.json"


def asset_file(c, track) -> "Path | None":
    """The file whose version an upload record must carry: the full video master (the upload is its compressed
    copy, recorded with --source), the segment's .mp4 or the Short's .m4v."""
    if track == "main":
        return c.ep / f"video/פרק-{c.n}-וידאו.mp4"
    kind = "segment" if track.startswith("seg") else "short"
    return G.slot_file(c.ep, kind, slot(track), ".mp4" if kind == "segment" else ".m4v")


def upload_record(track):
    def f(c):
        p = record_path(c, track)
        if not p.is_file():
            return [f"no upload record {c.rel(p)} (yt_upload.py --asset {track} --record ...; Studio: write the "
                    "copied video ID into the record)"]
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            return [f"{c.rel(p)} unreadable"]
        out = []
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", str(r.get("video_id", ""))):
            out.append(f"{c.rel(p)}: no 11-character video_id")
        if r.get("asset") != track:
            out.append(f"{c.rel(p)}: asset is {r.get('asset')!r}, not {track}")
        if r.get("channel") not in (None, SHOW_CHANNEL_ID):
            out.append(f"{c.rel(p)}: uploaded to {r.get('channel')}, not אחים להשקעות")
        if r.get("privacy", "private") != "private":
            out.append(f"{c.rel(p)}: review uploads are Private")
        todo = [s["name"] for s in r.get("steps", []) if s["name"] not in r.get("steps_done", [])]
        if todo:
            out.append(f"{c.rel(p)}: steps not done {todo}: yt_upload.py --resume {c.rel(p)}")
        asset = asset_file(c, track)
        if asset is None or not asset.is_file():
            out.append(f"{track}: no video file to compare {c.rel(p)} with")
        else:
            sha = c.hasher.sha(c.rel(asset))
            if sha not in {r.get("version"), r.get("file_sha256"), r.get("source_sha256")}:
                out.append(f"{c.rel(p)} is the upload of an older version, not the current {c.rel(asset)} "
                           f"(sha256 {sha[:12]}): upload the current file (yt_upload.py moves the old ID to "
                           "superseded). A record made without --source, or by hand after a Studio upload, needs "
                           "source_sha256 = that file's sha256 (once verify_sync.py shows the uploaded copy matches)")
        return out
    return f


def package(kind, track):
    def f(c):
        return G.slot_problems(c.ep, kind, slot(track))
    return f


def segment_record(track):
    def f(c):
        p = c.ep / "extras" / f"segment-{slot(track)}.json"
        if not p.is_file():
            return [f"no package record extras/segment-{slot(track)}.json (make_segment.py)"]
        r = json.loads(p.read_text(encoding="utf-8"))
        out = [] if r.get("sync") == "SYNC OK" else [f"segment {slot(track)}: verify_sync is {r.get('sync')!r}"]
        mp4 = c.ep / r.get("output", "")
        if not mp4.is_file():
            out.append(f"segment {slot(track)}: {r.get('output')} is not in the episode folder")
        elif r.get("output_sha256") and c.hasher.sha(c.rel(mp4)) != r["output_sha256"]:
            out.append(f"segment {slot(track)}: {r.get('output')} differs from the one make_segment.py rendered")
        return out
    return f


def short_log(track):
    def f(c):
        p = c.ep / "extras" / f"check-short-{slot(track)}.log"
        if not p.is_file():
            return [f"no extras/check-short-{slot(track)}.log (check_short.py ... > that file)"]
        t = p.read_text(encoding="utf-8", errors="replace")
        if "LUFS" not in t:
            return [f"extras/check-short-{slot(track)}.log has no check_short.py result"]
        warns = [ln for ln in t.splitlines() if ln.startswith("warning:")]
        return [f"check_short.py: {w[8:].strip()}" for w in warns]
    return f


def short_cover_file(c, track):
    sh = G.shorts_dir(c.ep)
    hits = sorted(sh.glob(f"שורט-{slot(track)}-*-cover.jpg")) if sh else []
    return hits


def short_cover(track):
    def f(c):
        hits = short_cover_file(c, track)
        if len(hits) != 1 or hits[0].stat().st_size == 0:
            return [f"Shorts/שורט-{slot(track)}-<נושא>-cover.jpg: {len(hits)} found (exactly one, not empty)"]
        log = c.ep / "extras" / "cover-check.log"
        t = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
        if f"OK {hits[0].name}" not in t:
            return [f"no check_cover.py OK for {hits[0].name} in extras/cover-check.log"]
        return []
    return f


def publish_done(c):
    return items("published")(c)


def old_uploads_check(c):
    """The cleanup mark must name every superseded Private ID in the upload records (or the owner waived it)."""
    out = items("old_uploads")(c)
    if out or "old_uploads" in c.waived:
        return out
    left = [x for x in superseded_ids(c) if x.split(": ", 1)[1] not in c.marks.get("old_uploads", "")]
    return [f"old_uploads: the evidence doesn't name superseded {', '.join(left)}; delete them, then mark "
            "old_uploads again with every ID"] if left else []


# ---- outputs (what a stage's version is made of) and data ------------------------------------------

def out_files(*rels):
    return lambda c: [r.format(n=c.n) for r in rels]


def out_marks(*ids):
    return lambda c: [f"mark:{i}" for i in ids]


def join(*fns):
    return lambda c: [x for fn in fns for x in fn(c)]


def out_teaser(c):
    promo = c.ep / "promo"
    if not promo.is_dir():
        return []
    return sorted(c.rel(p) for p in promo.glob("*.mp4") if re.search(r"teaser|cold|טיזר", p.name, re.I))


def out_raw(c):
    return raw_master_files(c)


def out_slot(kind, track, suffixes):
    """The slot's files. The .txt description and the notes file (youtube-*-NN.md: title, description) are
    `text:` outputs: the Spotify link and the status/URL lines publishing fills in are masked, any other
    change stales the package and what was approved of it."""
    def f(c):
        out = []
        for s in suffixes:
            p = G.slot_file(c.ep, kind, slot(track), s)
            if p is not None:
                out.append(("text:" if s == ".txt" else "") + c.rel(p))
        if kind == "segment":
            out.append(f"text:segments/youtube-סגמנט-{slot(track)}.md")
        else:
            sh = G.shorts_dir(c.ep)
            if sh:
                out.append(f"text:{sh.name}/youtube-שורט-{slot(track)}.md")
        return out
    return f


def out_records(c):
    return [f"extras/uploads/{t}.json" for t in TRACKS[:-1]]


def out_segment(track):
    def f(c):
        p = c.ep / "extras" / f"segment-{slot(track)}.json"
        out = [c.rel(p)]
        if p.is_file():
            r = json.loads(p.read_text(encoding="utf-8"))
            if r.get("output"):
                out.append(r["output"])
        return out
    return f


def out_short_cover(track):
    return lambda c: [c.rel(p) for p in short_cover_file(c, track)]


def ranges_from_text(text: str) -> list:
    return [[float(a), float(b)] for a, b in RANGE_RE.findall(text or "") if float(b) > float(a)]


def trim_data(c):
    try:
        e = json.loads((c.ep / "extras" / "edit.json").read_text(encoding="utf-8"))
        return {"edit": {"start": e["start"], "end": e["end"], "cuts": e.get("cuts", [])}}
    except (OSError, ValueError, KeyError):
        return {}


def edit_snapshot(c):
    return ((c.state["stages"].get("main.trim") or {}).get("data") or {}).get("edit")


def render_data_from_mark(mark_id):
    def f(c):
        return {"raw_ranges": ranges_from_text(c.marks.get(mark_id, "")) or None, "edit": edit_snapshot(c)}
    return f


def segment_data(track):
    def f(c):
        p = c.ep / "extras" / f"segment-{slot(track)}.json"
        r = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
        # the picked range minus the segment's own drops: an episode cut inside it counts, so restoring one
        # stales the render (raw_ranges, the kept pieces, is the fallback for records made before)
        return {"raw_ranges": r.get("selected_ranges") or r.get("raw_ranges"), "edit": r.get("edit") or edit_snapshot(c)}
    return f


def upload_data(track):
    def f(c):
        r = json.loads(record_path(c, track).read_text(encoding="utf-8"))
        return {"video_id": r.get("video_id"), "file_sha256": r.get("file_sha256"),
                "superseded": [s.get("video_id") for s in r.get("superseded", [])]}
    return f


# ---- the stage map (references/gates.md) -----------------------------------------------------------

def W(track, name, skill, waits, cmd, check, outputs, needs=(), inputs=(), data=None):
    return {"kind": "work", "track": track, "name": name, "key": f"{track}.{name}", "skill": skill, "waits": waits,
            "cmd": cmd, "check": check, "outputs": outputs, "needs": list(needs) + list(inputs),
            "inputs": list(inputs), "data": data}


def A(track, name, skill, of, ask, of_keys=None, needs=(), inputs=()):
    return {"kind": "approval", "track": track, "name": name, "key": f"{track}.{name}", "skill": skill,
            "waits": "owner", "cmd": ask, "of": of, "of_keys": of_keys,
            "needs": ([of] if of else []) + list(needs) + list(inputs), "inputs": list(inputs)}


def stage_map():
    pp, td, br, vd = ("investing-bros-post-production", "investing-bros-title-description",
                      "investing-bros-brand", "investing-bros-video")
    up, sg, sh, pb = ("investing-bros-episode-upload", "investing-bros-segment-video", "investing-bros-shorts",
                      "investing-bros-publish")
    m = [
        W("main", "intake", pp, "producer", f"<{pp}>/scripts/combine_parts.sh (steps 1-2); raw master into extras/",
          raw_master, out_raw),
        W("main", "master", pp, "producer", f"python3 <{pp}>/scripts/transcribe.py (step 4); then {P} mark EP "
          "transcript_doc --evidence <Doc URL>", items("transcript", "transcript_doc"),
          join(out_files("extras/transcript/segments.json"), out_marks("transcript_doc")), inputs=["main.intake"]),
        W("main", "cut_list", pp, "producer", f"python3 <{pp}>/scripts/find_bounds.py + find_gaps.py (step 5) -> "
          "extras/cuts-review/cuts-list.txt (each cut tagged [routine] or [content]) + a clip per cut",
          cut_list_check, out_files("extras/cuts-review/cuts-list.txt"), inputs=["main.master"]),
        W("main", "trim", pp, "producer", f"<{pp}>/scripts/trim.sh ... --cut A-B (step 6) on the full draft list; "
          "file the audio + edit.json. Do not wait for cuts_ok",
          items("audio", "cut_list"), out_files("הקלטה-ערוכה-פרק-{n}.m4a", "extras/edit.json"),
          inputs=["main.cut_list"], data=trim_data),
        W("main", "copy", td, "producer", f"python3 <{td}>/scripts/check_copy.py ... (steps 1-5)",
          items("titles_description"), out_files("כותרות-פרק-{n}.txt", "תיאור-פרק-{n}.txt"), inputs=["main.trim"]),
        A("main", "cuts_ok", pp, "main.cut_list",
          "the cut list (raw times + the words around each cut; ask each [content] cut as a question and show every line)"),
        A("main", "title_ok", td, "main.copy", "the final title (written after בחירה סופית:)",
          of_keys="כותרות-פרק-{n}.txt"),
        W("main", "art", br, "helper", f"<{br}> steps 3-8 (Codex on Amitai's Mac); check_cover.py >> "
          "extras/cover-check.log", items("thumbnail_cover", "cover_checks", "face_identity"),
          out_files("cover-פרק-{n}.png", "thumbnail-פרק-{n}.jpg"), inputs=["main.title_ok"]),
        A("main", "art_ok", br, "main.art", "the A/B/C pick for the episode cover and thumbnail"),
        W("main", "video", vd, "helper", f"python3 <{vd}>/scripts/build_fullframe_teaser.py; assemble_episode.sh; "
          "verify_sync.py > extras/verify_sync.log",
          items("teaser", "teaser_quality", "intro", "full_video", "verify_sync", "chapters"),
          join(out_teaser, out_files("video/פרק-{n}-וידאו.mp4", "text:video/תיאור-פרק-{n}-youtube.txt")),
          inputs=["main.trim", "main.copy"], needs=["main.cuts_ok"]),
        W("main", "upload", up, "producer", f"python3 <{up}>/scripts/yt_upload.py EP/extras/פרק-N-youtube.mp4 "
          "--source EP/video/פרק-N-וידאו.mp4 ... --asset main --record EP/extras/uploads/main.json; cards; end "
          "screen; then mark main.endscreen",
          join(gate("upload"), upload_record("main"), items("past_episode_cards"), marks("main.endscreen")),
          join(out_files("extras/uploads/main.json"), out_marks("main.endscreen")),
          inputs=["main.video", "main.art_ok", "main.title_ok"], data=upload_data("main")),
        A("main", "ok", up, "main.upload", "the full episode (Private link) in the approval round"),
    ]
    for t in ("seg01", "seg02"):
        n2 = slot(t)
        m += [
            W(t, "select", sg, "helper", f"{P} mark EP {t}.select --evidence \"raw A-B (seconds), cuts, length, "
              "alternative\"", marks(f"{t}.select"), out_marks(f"{t}.select"), needs=["main.trim"],
              data=render_data_from_mark(f"{t}.select")),
            A(t, "range_ok", sg, f"{t}.select", f"segment {n2}'s range"),
            W(t, "render", sg, "helper", f"python3 <{sg}>/scripts/make_segment.py --slot {n2} ...",
              segment_record(t), out_segment(t), inputs=[f"{t}.range_ok", "main.trim"],
              needs=["main.cuts_ok"], data=segment_data(t)),
            W(t, "package", sg, "helper", f"<{sg}> steps 5-9: .txt, -thumb.jpg, youtube-סגמנט-{n2}.md; then mark "
              f"{t}.nudge", join(package("segment", t), marks(f"{t}.nudge")),
              out_slot("segment", t, [".mp4", ".txt", "-thumb.jpg"]), inputs=[f"{t}.render"]),
            A(t, "thumb_ok", br, f"{t}.package", f"the A/B/C pick for segment {n2}'s thumbnail", of_keys="-thumb.jpg"),
            W(t, "upload", sg, "helper", f"yt_upload.py ... --asset {t} --record EP/extras/uploads/{t}.json; card + "
              f"end screen; then mark {t}.links", join(upload_record(t), marks(f"{t}.links")),
              join(out_files(f"extras/uploads/{t}.json"), out_marks(f"{t}.links")),
              inputs=[f"{t}.package", f"{t}.thumb_ok", "main.upload"], data=upload_data(t)),
            A(t, "ok", up, f"{t}.upload", f"segment {n2} (Private link) in the approval round"),
        ]
    for t in ("short01", "short02", "short03"):
        n2 = slot(t)
        m += [
            W(t, "pick", sh, "producer", f"python3 <{sh}>/scripts/score_moments.py ... (step 1); {P} mark EP {t}.pick "
              "--evidence \"raw A-B (seconds), cover title\"", marks(f"{t}.pick"), out_marks(f"{t}.pick"),
              needs=["main.trim"], data=render_data_from_mark(f"{t}.pick")),
            A(t, "pick_ok", sh, f"{t}.pick", f"Short {n2}'s moment (the three picks)"),
            W(t, "render", sh, "producer", f"make_base.py, make_props.py, render_short.py; check_short.py ... > "
              f"EP/extras/check-short-{n2}.log", short_log(t), out_files(f"extras/check-short-{n2}.log"),
              inputs=[f"{t}.pick_ok", "main.trim"], needs=["main.cuts_ok"],
              data=render_data_from_mark(f"{t}.pick")),
            W(t, "cover", br, "helper", f"<{br}> Shorts covers (Codex on Amitai's Mac); check_cover.py --kind "
              "shorts-vertical >> EP/extras/cover-check.log", short_cover(t), out_short_cover(t),
              inputs=[f"{t}.pick_ok"]),
            A(t, "cover_ok", br, f"{t}.cover", f"the A/B/C pick for Short {n2}'s cover"),
            W(t, "package", sh, "producer", f"<{sh}> step 7: the four files in Shorts/",
              package("short", t), out_slot("short", t, [".m4v", "-cover.jpg", ".srt"]),
              inputs=[f"{t}.render", f"{t}.cover_ok"]),
            # Related video waits for the publish checklist (`related`, never waived): the full episode is
            # still Private here, and the Short only goes Public after it is live
            W(t, "upload", sh, "producer", f"yt_upload.py ... --asset {t} --record EP/extras/uploads/{t}.json; "
              ".srt in Studio (Related video is set before Public: investing-bros-publish `related`)",
              upload_record(t), out_files(f"extras/uploads/{t}.json"),
              inputs=[f"{t}.package", "main.upload"], data=upload_data(t)),
            A(t, "ok", up, f"{t}.upload", f"Short {n2} (Private link) in the approval round; this is its cut approval"),
        ]
    uploads = [f"{t}.upload" for t in TRACKS[:-1]]
    oks = [f"{t}.ok" for t in TRACKS[:-1]]
    m += [
        W("release", "redcircle_draft", up, "producer", f"<{up}> step 2; then {P} mark EP redcircle_draft "
          "--evidence <draft URL>", items("redcircle_draft"), out_marks("redcircle_draft"),
          inputs=["main.trim", "main.title_ok", "main.copy"]),
        W("release", "review_gate", pp, "producer", f"{P} gate EP --stage review", gate("review"), lambda c: [],
          inputs=uploads + ["release.redcircle_draft"]),
        W("release", "approval_round", up, "producer", f"<{up}> step 3b: one Telegram message; then {P} mark EP "
          "release.approval_round --evidence \"<file, time>\"", marks("release.approval_round"),
          out_marks("release.approval_round"), inputs=["release.review_gate"]),
        A("release", "publish_ok", pb, None, "the OK to publish, naming what may go Public",
          needs=["release.approval_round"], inputs=oks),
        W("release", "publish", pb, "producer", f"python3 <{pb}>/scripts/publish_checklist.py ... (every item)",
          publish_done, out_files("extras/publish-checklist.json"), inputs=["release.publish_ok"]),
        W("release", "spotify_links", pb, "producer", f"<{pb}> step 7; then {P} mark EP spotify_links --evidence <URL>",
          items("spotify_links"), out_marks("spotify_links"), inputs=["release.publish"]),
        W("release", "old_uploads", up, "producer", f"delete the superseded Private IDs ({P} status lists them); "
          f"then {P} mark EP old_uploads --evidence \"<IDs or none>\"", old_uploads_check,
          join(out_marks("old_uploads"), out_records), needs=["release.publish"]),
        W("release", "retro", "investing-bros-producer", "producer", f"{P} retro EP; hand it to "
          f"investing-bros-skill-change; then {P} mark EP release.retro --evidence \"<PR/issue links>\"",
          join(files("extras/retro-פרק-{n}.md"), marks("release.retro")),
          join(out_files("extras/retro-פרק-{n}.md"), out_marks("release.retro")),
          needs=["release.spotify_links", "release.old_uploads"]),
    ]
    return m


SPEC = {s["key"]: s for s in stage_map()}


# ---- state ----------------------------------------------------------------------------------------

def new_state(n: int, owner: str, quote: "str | None") -> dict:
    s = {"schema_version": PS.SCHEMA_VERSION, "episode": n, "revision": 0, "created_at": PS.now(),
         "owner": {"name": owner, "quote": quote or "", "set_at": PS.now(), "confirmed": bool(quote)},
         "owner_history": [{"from": None, "to": owner, "quote": quote or "", "at": PS.now()}],
         "stages": {}, "marks": {}, "waivers": {}, "stale_seen": [], "events": []}
    PS.add_event(s, "start", detail=f"owner {owner}" + ("" if quote else " (unconfirmed)"))
    return s


def need_state(ep):
    s = PS.load(ep)
    if s is None:
        raise SystemExit(f"no {PS.state_file(ep)}: run `{P} start EP --episode N --owner ...` "
                         "(or `migrate` for an episode started before the pipeline)")
    return s


def owner_quote_ok(state, quote, who=None):
    """The quote must be in the episode owner's words (or `who`'s)."""
    owner = who or state["owner"]["name"]
    speaker = O.speaker(quote)
    if not (quote or "").strip() or speaker is None:
        return False, f'quote the episode owner ({owner}): --by "{owner.title()} HH:MM: <their words>"'
    if speaker != owner:
        return False, f"{speaker.title()} is not this episode's owner ({owner}); only the owner approves or waives"
    return True, ""


def log_stale(c: Ctx) -> bool:
    seen = set(c.state.setdefault("stale_seen", []))
    new = False
    for key, v in c.ev.items():
        if v["status"] != "stale":
            continue
        tag = f"{key}@{c.state['stages'][key].get('version')}"
        if tag not in seen:
            t, _, st = key.partition(".")
            PS.add_event(c.state, "stale", t, st, v["why"])
            c.state["stale_seen"].append(tag)
            new = True
    return new


def stage_status(c: Ctx, key: str):
    if key in c.state["stages"]:
        return c.ev[key]["status"], c.ev[key]["why"]
    return "missing", ""


def unmet(c: Ctx, spec) -> list:
    return [k for k in spec["needs"] if not c.current(k)]


def do_advance(ep, c: Ctx, key: str, quiet=False) -> "tuple[bool, list]":
    spec = SPEC[key]
    if spec["kind"] == "approval":
        return False, [f"{key} is an approval: `{P} approve EP {spec['track']} {spec['name']} --by ...`"]
    blocked = unmet(c, spec)
    if blocked:
        return False, ["waits for " + ", ".join(f"{b} ({stage_status(c, b)[0]})" for b in blocked)]
    probs = spec["check"](c)
    if probs:
        PS.add_event(c.state, "check_failed", spec["track"], spec["name"], "; ".join(probs)[:500])
        return False, probs
    rels = spec["outputs"](c)
    outs = PS.current_outputs(ep, dict.fromkeys(rels), PS.all_marks(c.state), c.hasher)
    inputs = {k: c.state["stages"][k]["version"] for k in spec["inputs"] if k in c.state["stages"]}
    rec = {"state": "done", "at": PS.now(), "outputs": outs, "inputs": inputs,
           "version": PS.version_of(outs, inputs)}
    if spec.get("data"):
        rec["data"] = spec["data"](c)
    old = c.state["stages"].get(key)
    c.state["stages"][key] = rec
    kind = "advance" if not old else ("rerun" if old.get("version") != rec["version"] else "advance")
    if not old or old.get("version") != rec["version"]:
        PS.add_event(c.state, kind, spec["track"], spec["name"], rec["version"][:19])
    c.ev = PS.evaluate(ep, c.state, c.hasher)
    return True, []


def track_keys(track):
    return [k for k, s in SPEC.items() if s["track"] == track]


def advance_track(ep, c: Ctx, track: str) -> list:
    """Advance every work stage of the track in order until one fails or waits on an approval."""
    report = []
    for key in track_keys(track):
        st, _ = stage_status(c, key)
        if st == "current":
            continue
        if SPEC[key]["kind"] == "approval":
            report.append((key, "waits for the owner's approval"))
            break
        ok, probs = do_advance(ep, c, key)
        report.append((key, "passed" if ok else "; ".join(probs)))
        if not ok:
            break
    return report


# ---- next / status --------------------------------------------------------------------------------

def _approval_ask(ready) -> str:
    bits = []
    for key, _, _ in ready:
        spec = SPEC[key]
        bits.append(f"{spec['cmd']} ({P} approve EP {spec['track']} {spec['name']} "
                    "--by \"<Owner> HH:MM: <their words>\")")
    return "ask in the next review round: " + "; ".join(bits)


def _approval_row(track, ready) -> dict:
    names = [SPEC[k]["name"] for k, _, _ in ready]
    return {"track": track, "stage": ", ".join(names), "status": ready[0][1], "why": ready[0][2],
            "skill": SPEC[ready[0][0]]["skill"], "waits": "owner", "blocked_by": [],
            "command": _approval_ask(ready), "approvals": names}


def next_steps(c: Ctx) -> list:
    """One row per track. Ready approvals on that track are listed together (round 1 can hold the cut
    list and the title at once). An approval that is not a prerequisite of the next work does not hide it."""
    out = []
    for track in TRACKS:
        ready = []
        hold = None
        for key in track_keys(track):
            st, why = stage_status(c, key)
            if st == "current":
                continue
            spec = SPEC[key]
            blocked = unmet(c, spec)
            if spec["kind"] == "approval" and not blocked:
                ready.append((key, st, why))
                continue
            hold = (key, st, why, blocked, spec)
            break
        if hold is None and not ready:
            out.append({"track": track, "stage": "done", "status": "current", "why": "", "skill": "",
                        "waits": "", "blocked_by": [], "command": "", "approvals": []})
            continue
        if ready and (hold is None or hold[3]):
            out.append(_approval_row(track, ready))
            continue
        key, st, why, blocked, spec = hold
        ext = [b for b in blocked if not b.startswith(track + ".")]
        cmd = f"{spec['cmd']}; then {P} advance EP {track} {spec['name']}"
        if ready:
            cmd += ". Also " + _approval_ask(ready)
        out.append({"track": track, "stage": spec["name"], "status": st, "why": why, "skill": spec["skill"],
                    "waits": "blocked" if ext else spec["waits"], "blocked_by": ext, "command": cmd,
                    "approvals": [SPEC[k]["name"] for k, _, _ in ready]})
    return out


def superseded_ids(c: Ctx) -> list:
    ids = []
    for t in TRACKS[:-1]:
        p = record_path(c, t)
        if p.is_file():
            r = json.loads(p.read_text(encoding="utf-8"))
            ids += [f"{t}: {s.get('video_id')}" for s in r.get("superseded", [])]
    return ids


def cmd_status(ep, a):
    s = need_state(ep)
    c = Ctx(ep, s)
    if log_stale(c):
        PS.save(ep, s)
    if a.json:
        print(json.dumps({"revision": s["revision"], "owner": s["owner"], "stages": c.ev}, ensure_ascii=False, indent=1))
        return 0
    o = s["owner"]
    print(f"episode {s['episode']}  owner {o['name']}{'' if o.get('confirmed') else ' (UNCONFIRMED: ask in the next round)'}"
          f"  revision {s['revision']}")
    sym = {"current": "✓", "stale": "~", "missing": "·", "failed": "✗"}
    for track in TRACKS:
        cells = []
        for key in track_keys(track):
            st, _ = stage_status(c, key)
            if s["stages"].get(key, {}).get("state") == "waived":
                cells.append(f"W {SPEC[key]['name']}")
            else:
                cells.append(f"{sym.get(st, '?')} {SPEC[key]['name']}")
        print(f"{track:8} " + "  ".join(cells))
    stale = [(k, v["why"]) for k, v in c.ev.items() if v["status"] == "stale"]
    for k, why in stale:
        print(f"  stale {k}: {why}")
    if s.get("legacy"):
        print(f"  legacy evidence from {s['legacy']['source']}: marks {sorted(s['legacy'].get('marked', {}))}, "
              f"waivers {sorted(s['legacy'].get('waived', {}))}")
    sup = superseded_ids(c)
    if sup:
        print("  superseded Private uploads (delete once the new one is verified): " + ", ".join(sup))
    return 0


def cmd_next(ep, a):
    s = need_state(ep)
    c = Ctx(ep, s)
    if log_stale(c):
        PS.save(ep, s)
    rows = next_steps(c)
    if not s["owner"].get("confirmed"):
        rows.insert(0, {"track": "release", "stage": "owner", "status": "missing", "why": "owner unconfirmed",
                        "skill": "investing-bros-show", "waits": "owner", "blocked_by": [],
                        "command": f"ask who owns the episode; {P} owner EP --set NAME --by \"<their words>\""})
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return 0
    for r in rows:
        if r["stage"] == "done":
            print(f"{r['track']:8} done")
            continue
        why = f" ({r['status']}{': ' + r['why'] if r['why'] else ''})" if r["status"] != "missing" else ""
        wait = f"blocked by {', '.join(r['blocked_by'])}" if r["blocked_by"] else f"waits: {r['waits']}"
        print(f"{r['track']:8} {r['stage']:15} {r['skill']:32} {wait}{why}\n{'':9}{r['command']}")
    return 0


# ---- commands -------------------------------------------------------------------------------------

def cmd_start(ep, a):
    if PS.state_file(ep).exists():
        print(f"{PS.state_file(ep)} exists; use status / next", file=sys.stderr)
        return 1
    if a.by:
        ok, msg = owner_quote_ok({"owner": {"name": a.owner}}, a.by)
        if not ok:
            print(f"refused: {msg}", file=sys.stderr)
            return 1
    s = new_state(a.episode, a.owner, a.by)
    if (Path(ep) / "extras" / "postprod-checklist.json").is_file():
        print("note: extras/postprod-checklist.json exists; `migrate` imports it as legacy evidence", file=sys.stderr)
    print(f"started episode {a.episode}, owner {a.owner} -> {PS.save(ep, s)}")
    return 0


def cmd_migrate(ep, a):
    if PS.state_file(ep).exists():
        print(f"{PS.state_file(ep)} exists already", file=sys.stderr)
        return 1
    if a.by:
        ok, msg = owner_quote_ok({"owner": {"name": a.owner}}, a.by)
        if not ok:
            print(f"refused: {msg}", file=sys.stderr)
            return 1
    s = new_state(a.episode, a.owner, a.by)
    legacy = Path(ep) / "extras" / "postprod-checklist.json"
    if legacy.is_file():
        old = json.loads(legacy.read_text(encoding="utf-8"))
        s["legacy"] = {"source": "extras/postprod-checklist.json", "sha256": PS.digest(old),
                       "imported_at": PS.now(), "marked": old.get("marked", {}), "waived": old.get("waived", {})}
    PS.add_event(s, "migrate", detail="legacy " + ("imported" if legacy.is_file() else "none"))
    c = Ctx(ep, s)
    for track in TRACKS:
        for key, res in advance_track(ep, c, track):
            print(f"{key:24} {res}")
    PS.save(ep, s)
    print("Approvals are never imported: record the ones already given with `approve ... --by` from the chat, "
          "or ask for them in the next review round.")
    return 0


def cmd_advance(ep, a):
    s = need_state(ep)
    c = Ctx(ep, s)
    if a.track not in TRACKS:
        print(f"unknown track {a.track}; tracks: {TRACKS}", file=sys.stderr)
        return 2
    if a.stage:
        key = f"{a.track}.{a.stage}"
        if key not in SPEC:
            print(f"unknown stage {key}; {a.track}: {[SPEC[k]['name'] for k in track_keys(a.track)]}", file=sys.stderr)
            return 2
        ok, probs = do_advance(ep, c, key)
        log_stale(c)
        PS.save(ep, s)
        if not ok:
            print(f"REFUSED {key}:\n  " + "\n  ".join(probs))
            return 1
        print(f"passed {key} ({s['stages'][key]['version'][:19]})")
        return 0
    rep = advance_track(ep, c, a.track)
    log_stale(c)
    PS.save(ep, s)
    for key, res in rep:
        print(f"{key:24} {res}")
    return 0 if all(r == "passed" for _, r in rep) else 1


def cmd_approve(ep, a):
    s = need_state(ep)
    key = f"{a.track}.{a.stage}"
    spec = SPEC.get(key)
    if not spec or spec["kind"] != "approval":
        print(f"{key} is not an approval stage", file=sys.stderr)
        return 2
    ok, msg = owner_quote_ok(s, a.by)
    if not ok:
        print(f"refused: {msg}", file=sys.stderr)
        return 1
    c = Ctx(ep, s)
    blocked = unmet(c, spec)
    if blocked:
        print(f"refused: {key} needs {', '.join(f'{b} ({stage_status(c, b)[0]})' for b in blocked)} first",
              file=sys.stderr)
        return 1
    rec = {"state": "approved", "at": PS.now(), "by": s["owner"]["name"], "quote": a.by.strip()}
    if spec["of"]:
        of = s["stages"][spec["of"]]
        if spec["of_keys"]:
            pat = spec["of_keys"].format(n=s["episode"])
            keys = [k for k in of.get("outputs", {}) if str(k).endswith(pat)]
            if not keys:
                print(f"refused: {key} fingerprints only outputs ending with {pat}; "
                      f"{spec['of']} has none", file=sys.stderr)
                return 1
            rec.update(of=spec["of"], of_keys=keys,
                       of_version=PS.version_of({k: of["outputs"][k] for k in keys}))
        else:
            rec.update(of=spec["of"], of_version=of["version"])
        rec["version"] = rec["of_version"]
    rec["inputs"] = {k: s["stages"][k]["version"] for k in spec["inputs"] if k in s["stages"]}
    if key == "release.publish_ok":
        rec["data"] = {"videos": {t: ((s["stages"].get(f"{t}.upload") or {}).get("data") or {}).get("video_id")
                                  for t in TRACKS[:-1]}}
        rec["version"] = PS.version_of({}, {**rec["inputs"], "videos": rec["data"]["videos"]})
    s["stages"][key] = rec
    PS.add_event(s, "approval", spec["track"], spec["name"], a.by.strip()[:200])
    PS.save(ep, s)
    print(f"approved {key} ({rec['version'][:19]})")
    return 0


def cmd_mark(ep, a):
    s = need_state(ep)
    if a.item not in MARKABLE:
        print(f"unknown mark {a.item}; marks: {sorted(MARKABLE)}", file=sys.stderr)
        return 2
    if not a.evidence.strip():
        print("a mark needs --evidence: what you saw and where", file=sys.stderr)
        return 2
    s["marks"][a.item] = {"evidence": a.evidence.strip(), "at": PS.now()}
    PS.add_event(s, "mark", a.item.split(".")[0] if a.item in TRACK_MARKS else "", a.item, a.evidence.strip()[:200])
    PS.save(ep, s)
    print(f"marked {a.item}")
    return 0


def cmd_waive(ep, a):
    s = need_state(ep)
    ok, msg = owner_quote_ok(s, a.by)
    if not ok:
        print(f"refused: {msg}", file=sys.stderr)
        return 1
    if a.item in SPEC:
        spec = SPEC[a.item]
        if spec["kind"] == "approval":
            print(f"refused: {a.item} is an approval; approvals are given, never waived", file=sys.stderr)
            return 1
        s["stages"][a.item] = {"state": "waived", "at": PS.now(), "version": "waived", "quote": a.by.strip(),
                               "by": s["owner"]["name"], "outputs": {}, "inputs": {}}
    elif a.item not in G.IDS:
        print(f"unknown item {a.item}; gate items {G.IDS} or TRACK.STAGE", file=sys.stderr)
        return 2
    s["waivers"][a.item] = {"quote": a.by.strip(), "by": s["owner"]["name"], "at": PS.now()}
    PS.add_event(s, "waiver", "", a.item, a.by.strip()[:200])
    PS.save(ep, s)
    print(f"waived {a.item}")
    return 0


def cmd_owner(ep, a):
    s = need_state(ep)
    cur = s["owner"]
    allowed = [cur["name"]] if cur.get("confirmed") else [cur["name"], a.set]
    who = O.speaker(a.by)
    if who not in allowed:
        need = " or ".join(x.title() for x in dict.fromkeys(allowed))
        print(f"refused: ownership changes only in the owner's words: --by \"{need} HH:MM: ...\"", file=sys.stderr)
        return 1
    s["owner_history"].append({"from": cur["name"], "to": a.set, "quote": a.by.strip(), "at": PS.now()})
    s["owner"] = {"name": a.set, "quote": a.by.strip(), "set_at": PS.now(), "confirmed": True}
    PS.add_event(s, "owner_change", detail=f"{cur['name']} -> {a.set}: {a.by.strip()[:200]}")
    PS.save(ep, s)
    print(f"owner: {a.set}")
    return 0


def cmd_note(ep, a):
    s = need_state(ep)
    PS.add_event(s, a.kind, a.track or "", "", a.text.strip())
    PS.save(ep, s)
    print(f"noted ({a.kind})")
    return 0


def cmd_gate(ep, a):
    s = PS.load(ep)
    if s is None:
        print(f"no {PS.state_file(ep)}", file=sys.stderr)
        return 2
    c = Ctx(ep, s)
    rows, missing = G.check(c.ep, c.n, a.stage, c.marks, c.waived)
    for st, item, note in rows:
        print(f"{st:8} {item:20} {note}")
    if missing:
        print(f"\nFAIL ({a.stage}): {len(missing)} missing: {', '.join(missing)}")
        print("Make them, or get the episode owner's explicit waiver per item. Do not upload / report done.")
        return 1
    print(f"\nPASS ({a.stage})")
    return 0


# ---- retro ----------------------------------------------------------------------------------------

SCRIPTABLE = ("dash", "—", "–", "timestamp", "chapter", "length", "duration", "lufs", "loud", "sync", "caption",
              "link", "title", "rtl", "size", "format", "name", "naming", "סימן שאלה", "מקף")
FACTS = ("spelling", "spelled", "איות", "account", "channel id", "limit", "decided", "decision", "always", "never")
ENV = ("network", "drive", "mac", "quota", "token", "auth", "oauth", "captcha", "browser", "timeout", "rclone")


def classify(e: dict) -> "tuple[str, str]":
    kind, d = e["kind"], (e.get("detail") or "").lower()
    if kind == "check_failed":
        return "one line in the owning skill", "a check caught it; prevent it upstream in the step that made it"
    if kind == "owner_fix":
        if any(w in d for w in FACTS):
            return "show fact", "a decision or fact to keep in investing-bros-show"
        if any(w in d for w in SCRIPTABLE):
            return "script check", "a script could catch this before the owner sees it"
        return "one line in the owning skill", "the step missed what the owner wanted"
    if kind == "handback_returned":
        return "one line in the owning skill", "the helper's skill missed a step"
    if kind == "workaround":
        if any(w in d for w in ENV):
            return "GitHub issue", "an environment limit nobody could fix during the run"
        return "script check", "a script lacked a feature: propose the change as a PR"
    if kind == "stale":
        return "no action", "expected rework after a change upstream"
    if kind == "rerun":
        return "no action", "a stage made again"
    if kind == "waiver":
        return "no action", "the owner's decision for this episode"
    return "no action", "a note"


def parse_time(t):
    try:
        return datetime.fromisoformat(t)
    except (TypeError, ValueError):
        return None


def last_retro(ep: Path, n: int, given=None):
    if given:
        return Path(given) if Path(given).is_file() else None
    for p in sorted(ep.parent.glob(f"פרק {n - 1}*/extras/retro-פרק-{n - 1}.md")):
        return p
    return None


def previous_findings(path) -> set:
    out = set()
    if path:
        for ln in Path(path).read_text(encoding="utf-8").splitlines():
            cells = [x.strip() for x in ln.strip().strip("|").split("|")]
            if len(cells) >= 5 and cells[0].isdigit():
                out.add((cells[2], cells[3]))
    return out


def build_retro(ep: Path, s: dict, last=None) -> str:
    n = s["episode"]
    events = s.get("events", [])
    problems = [e for e in events if e["kind"] in ("check_failed", "owner_fix", "handback_returned", "workaround",
                                                   "stale", "waiver")]
    prev = previous_findings(last)
    lines = [f"# תחקיר פרק {n} (episode {n} retro)", "",
             f"Drafted by `pipeline.py retro` from `extras/pipeline.json` (revision {s.get('revision')}, "
             f"{len(events)} events). The Producer checks every finding, then hands the list to "
             "`investing-bros-skill-change`, which opens the PRs and issues; the owner gets one message with the links.",
             "", "## What went wrong, by stage", ""]
    by_stage = {}
    for e in problems:
        by_stage.setdefault(f"{e['track']}.{e['stage']}".strip("."), []).append(e)
    if not by_stage:
        lines.append("Nothing failed, was sent back or was worked around.")
    for st, evs in sorted(by_stage.items()):
        lines.append(f"### {st or '(episode)'}")
        for e in evs:
            lines.append(f"- {e['at'][:16]} {e['kind']}: {e.get('detail', '')}")
        lines.append("")
    lines += ["## Where time went", "", "| Track | First event | Last event | Hours |", "|---|---|---|---|"]
    for t in TRACKS:
        ts = [parse_time(e["at"]) for e in events if e.get("track") == t and parse_time(e["at"])]
        if ts:
            lines.append(f"| {t} | {min(ts):%Y-%m-%d %H:%M} | {max(ts):%Y-%m-%d %H:%M} | "
                         f"{(max(ts) - min(ts)).total_seconds() / 3600:.1f} |")
    lines += ["", "## Waits on the owner", "", "| Approval | Ready | Approved | Hours |", "|---|---|---|---|"]
    for key, rec in s.get("stages", {}).items():
        if rec.get("state") != "approved":
            continue
        ready = max([parse_time(s["stages"][k].get("at")) for k in SPEC[key]["needs"]
                     if k in s["stages"] and parse_time(s["stages"][k].get("at"))] or [None], key=lambda x: x or datetime.min)
        got = parse_time(rec.get("at"))
        hours = f"{(got - ready).total_seconds() / 3600:.1f}" if ready and got else "?"
        lines.append(f"| {key} | {ready:%m-%d %H:%M} | {got:%m-%d %H:%M} | {hours} |" if ready and got
                     else f"| {key} | ? | {rec.get('at', '?')[:16]} | ? |")
    findings = []
    for e in problems:
        cls, why = classify(e)
        st = f"{e['track']}.{e['stage']}".strip(".")
        skill = SPEC.get(st, {}).get("skill", "")
        findings.append((e, st, cls, why, skill, (st, cls) in prev))
    repeats = [f for f in findings if f[5]]
    lines += ["", "## Repeats from the last retro", ""]
    lines.append(f"From `{last}`:" if last else "No earlier retro found (pass --last PATH).")
    lines += [f"- {st}: {cls}" for _, st, cls, _, _, _ in repeats] or (["- none"] if last else [])
    lines += ["", "## Findings", "", "| # | Finding | Stage | Class | Owning skill / reason |", "|---|---|---|---|---|"]
    for i, (e, st, cls, why, skill, rep) in enumerate(findings, 1):
        detail = (e.get("detail") or "").replace("|", "/")[:160]
        lines.append(f"| {i} | {e['kind']}: {detail}{' (repeat)' if rep else ''} | {st} | {cls} | "
                     f"{skill + ': ' if skill else ''}{why} |")
    if not findings:
        lines.append("| 0 | nothing to learn this episode | - | no action | no failures, fixes or workarounds |")
    return "\n".join(lines) + "\n"


def cmd_retro(ep, a):
    s = need_state(ep)
    c = Ctx(ep, s)
    live = all(c.current(k) for k in ("release.spotify_links", "release.old_uploads"))
    if not live and not a.force:
        print("refused: the retro runs after every track is live (release.spotify_links and old_uploads); "
              "--force drafts it early", file=sys.stderr)
        return 1
    n = s["episode"]
    out = Path(ep) / "extras" / f"retro-פרק-{n}.md"
    last = last_retro(Path(ep), n, a.last)
    out.write_text(build_retro(Path(ep), s, last), encoding="utf-8")
    PS.add_event(s, "retro", "release", "retro", str(out.name))
    PS.save(ep, s)
    print(f"wrote {out}\nnext: hand it to investing-bros-skill-change, then "
          f"{P} mark EP release.retro --evidence \"<PR/issue links>\" and {P} advance EP release retro")
    return 0


# ---- doctor ---------------------------------------------------------------------------------------

def _run(cmd, timeout=20):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as e:
        return 127, type(e).__name__


def doctor(online=False, run=_run, env=None, home=None, skills_root=None) -> "tuple[list, int]":
    env = os.environ if env is None else env
    home = Path(home or Path.home())
    root = Path(skills_root or HERE.parents[1])
    rows = []

    def add(status, what, detail):
        rows.append((status, what, detail))

    rc, out = run(["ffmpeg", "-version"])
    if rc:
        add("FAIL", "ffmpeg", "not found")
    else:
        first = out.splitlines()[0] if out else "?"
        add("WARN" if "9.0.2" in first else "OK", "ffmpeg", first + (" (issue #87: -21 ms at the first render_cuts "
                                                                     "checkpoint)" if "9.0.2" in first else ""))
    font_dirs = [home / "Library/Fonts", Path("/Library/Fonts"), Path("/usr/share/fonts"), home / ".fonts",
                 home / ".local/share/fonts"]
    heebo = [p for d in font_dirs if d.is_dir() for p in d.rglob("Heebo*.ttf")]
    add("OK" if heebo else "WARN", "Heebo", f"{len(heebo)} font file(s)" if heebo else
        "not installed (investing-bros-show -> references/environment.md)")
    rc, out = run(["node", "--version"])
    add("OK" if not rc else "WARN", "node", out.strip() or "not found (Remotion needs Node 18+)")
    tpl = root / "investing-bros-remotion" / "template" / "node_modules"
    add("OK" if tpl.is_dir() else "WARN", "Remotion template", "installed" if tpl.is_dir() else
        "npm ci in <investing-bros-remotion>/template")
    chrome = list((tpl / ".remotion").glob("chrome-headless-shell*")) if tpl.is_dir() else []
    add("OK" if chrome else "WARN", "Chrome headless shell", "present" if chrome else
        "not downloaded yet (Remotion fetches it on the first render)")
    rc, _ = run([sys.executable, "-c", "import faster_whisper"])
    models = list((home / ".cache/huggingface/hub").glob("models--*faster-whisper*"))
    add("OK" if not rc and models else "WARN", "Whisper", ("faster-whisper " + ("ok" if not rc else "missing")) +
        f", {len(models)} model(s) cached")
    rc, out = run(["rclone", "listremotes"])
    add("OK" if not rc and "show:" in out else "WARN", "rclone `show` remote",
        "present" if not rc and "show:" in out else "missing (drive.sh in investing-bros-shorts)")
    tg = [k for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID") if env.get(k)]
    add("OK" if len(tg) == 2 else "WARN", "Telegram env", "both set (values not shown)" if len(tg) == 2 else
        "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not both set (or pass send_telegram.py --env FILE)")
    tok = Path(env.get("YT_UPLOADER_DIR", home / ".config/youtube-uploader")) / "token.json"
    if not tok.is_file():
        add("WARN", "YouTube API", f"no token at {tok} (Studio fallback)")
    elif online:
        yt = root / "investing-bros-episode-upload" / "scripts" / "yt_upload.py"
        rc, out = run([sys.executable, str(yt), "--check-auth"], 60)
        good = f"({SHOW_CHANNEL_ID})" in out and "AUTH_OK" in out
        add("OK" if good else "FAIL", "YouTube API", "token ok, active channel אחים להשקעות" if good else
            "token refresh or channel check failed: rerun yt_auth.py and pick the brand channel")
    else:
        add("OK", "YouTube API", "token present (--online checks the active channel)")
    versions = sorted({(p.read_text(encoding="utf-8").strip()) for p in root.glob("investing-bros-*/VERSION")})
    if not versions:
        add("OK", "skills version", "a git checkout (no VERSION files)")
    else:
        status, detail = ("WARN", f"installed skills differ: {versions}") if len(versions) > 1 else ("OK", versions[0])
        if online:
            rc, out = run(["gh", "release", "view", "skills-latest", "--repo", "EthWiz/investing-bros-skills",
                           "--json", "body", "-q", ".body"], 30)
            if not rc and versions[0] not in out:
                status, detail = "WARN", f"installed {versions[0]}; the latest release differs: re-install"
            elif rc:
                detail += " (latest release not reachable)"
        add(status, "skills version", detail)
    return rows, (1 if any(r[0] == "FAIL" for r in rows) else 0)


def cmd_doctor(_ep, a):
    rows, rc = doctor(online=a.online)
    for st, what, detail in rows:
        print(f"{st:5} {what:22} {detail}")
    return rc


# ---- main -----------------------------------------------------------------------------------------

def parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("start", "migrate"):
        p = sub.add_parser(name); p.add_argument("ep"); p.add_argument("--episode", type=int, required=True)
        p.add_argument("--owner", choices=sorted(O.NAMES), required=True); p.add_argument("--by")
    for name in ("status", "next"):
        p = sub.add_parser(name); p.add_argument("ep"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("advance"); p.add_argument("ep"); p.add_argument("track"); p.add_argument("stage", nargs="?")
    p = sub.add_parser("approve"); p.add_argument("ep"); p.add_argument("track"); p.add_argument("stage")
    p.add_argument("--by", required=True)
    p = sub.add_parser("mark"); p.add_argument("ep"); p.add_argument("item"); p.add_argument("--evidence", required=True)
    p = sub.add_parser("waive"); p.add_argument("ep"); p.add_argument("item"); p.add_argument("--by", required=True)
    p = sub.add_parser("owner"); p.add_argument("ep"); p.add_argument("--set", choices=sorted(O.NAMES), required=True)
    p.add_argument("--by", required=True)
    p = sub.add_parser("note"); p.add_argument("ep"); p.add_argument("text")
    p.add_argument("--kind", choices=NOTE_KINDS, default="note"); p.add_argument("--track", choices=TRACKS)
    p = sub.add_parser("gate"); p.add_argument("ep"); p.add_argument("--stage", choices=G.STAGES, default="upload")
    p = sub.add_parser("retro"); p.add_argument("ep"); p.add_argument("--last"); p.add_argument("--force", action="store_true")
    p = sub.add_parser("doctor"); p.add_argument("--online", action="store_true")
    return ap


def main(argv=None) -> int:
    a = parser().parse_args(argv)
    fn = {"start": cmd_start, "migrate": cmd_migrate, "status": cmd_status, "next": cmd_next,
          "advance": cmd_advance, "approve": cmd_approve, "mark": cmd_mark, "waive": cmd_waive,
          "owner": cmd_owner, "note": cmd_note, "gate": cmd_gate, "retro": cmd_retro, "doctor": cmd_doctor}[a.cmd]
    try:
        return fn(Path(getattr(a, "ep", ".") or "."), a)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
