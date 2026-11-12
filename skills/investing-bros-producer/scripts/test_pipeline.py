"""pipeline.py: start/next/advance, approvals tied to versions, stale propagation (with the overlap rule),
migration of an in-flight episode, owner transfer, re-uploads, the retro and doctor."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import pipeline as pl  # noqa: E402
import pipeline_state as ps  # noqa: E402
import riverside_tracks as rt  # noqa: E402

N = 11
AM = "Amitai 10:00: מאשר"
NA = "Nadav 10:00: מאשר"
RIVER_DUR = 12.0


@pytest.fixture(autouse=True)
def _riverside_duration(monkeypatch):
    """Fixture media is not a real recording; the pull's duration check reads this."""
    monkeypatch.setattr(rt, "probe_duration", lambda path: RIVER_DUR)


def touch(p: Path, text="x"):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def run(*args):
    return pl.main([str(a) for a in args])


def sha(p: Path) -> str:
    import hashlib
    return hashlib.sha256(p.read_bytes()).hexdigest()


def record(ep, track, vid, version=None, superseded=()):
    """An upload record as yt_upload.py writes it; version = the asset file's sha256 (main: --source master)."""
    if version is None:
        version = sha(ep / f"video/פרק-{N}-וידאו.mp4") if track == "main" else "v1"
    touch(ep / f"extras/uploads/{track}.json", json.dumps({
        "asset": track, "version": version, "channel": pl.SHOW_CHANNEL_ID, "video_id": vid, "privacy": "private",
        "steps": [{"name": "thumbnail"}], "steps_done": ["insert", "thumbnail"],
        "superseded": [{"video_id": s} for s in superseded]}))


def riverside_ready(ep: Path):
    """A finished browser pull on disk: Amitai in two parts, Nadav in one.

    Written straight into the pull record so fixtures that have no pipeline.json yet
    (a migrate) still satisfy main.riverside. Duration is RIVER_DUR.
    """
    rows = [
        ("riverside/amitai-1-video.mp4", "Amitai", 1, "video", b"av1"),
        ("riverside/amitai-1-audio.wav", "Amitai", 1, "audio", b"aa1"),
        ("riverside/amitai-2-video.mp4", "Amitai", 2, "video", b"av2"),
        ("riverside/amitai-2-audio.wav", "Amitai", 2, "audio", b"aa2"),
        ("riverside/nadav-1-video.mp4", "Nadav", 1, "video", b"nv1"),
        ("riverside/nadav-1-audio.wav", "Nadav", 1, "audio", b"na1"),
    ]
    by, order = {}, []
    for rel, speaker, part, kind, payload in rows:
        p = ep / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(payload)
        if speaker not in order:
            order.append(speaker)
        by.setdefault(speaker, {}).setdefault(part, {})[kind] = {
            "path": rel, "bytes": len(payload), "duration_s": RIVER_DUR, "quality": "high"}
    speakers = [{"name": name, "parts": [
        {"part": n, "video": parts["video"], "audio": parts["audio"]}
        for n, parts in sorted(by[name].items())]} for name in order]
    rt.save(ep, {"project": f"פרק {N}", "started_at": "2026-11-06T10:00:00+00:00",
                 "last_check_at": "2026-11-06T10:05:00+00:00", "status": "ready", "via": "browser",
                 "drive_upload": False, "interval_minutes": 15, "armed_by": AM,
                 "ready_at": "2026-11-06T10:05:00+00:00", "checks": [], "speakers": speakers})


def audio_files(ep, cuts=([500, 520],)):
    riverside_ready(ep)
    touch(ep / "extras/investing-bros-episode-raw-untrimmed.m4a", "raw")
    touch(ep / "extras/transcript/segments.json", "[]")
    touch(ep / "extras/cuts-review/cuts-list.txt", "[routine] 500-520 the courier call")
    touch(ep / "extras/cuts-review/cut-01.mp4")
    touch(ep / f"הקלטה-ערוכה-פרק-{N}.m4a", "audio")
    touch(ep / "extras/edit.json", json.dumps({"start": 10, "end": 2000, "cuts": [list(c) for c in cuts]}))


def main_files(ep):
    audio_files(ep)
    touch(ep / f"כותרות-פרק-{N}.txt", "1. x\nבחירה סופית: x")
    touch(ep / f"תיאור-פרק-{N}.txt", "desc")
    touch(ep / f"cover-פרק-{N}.png", "png")
    touch(ep / f"thumbnail-פרק-{N}.jpg", "jpg")
    touch(ep / "extras/cover-check.log", f"OK cover-פרק-{N}.png\nOK thumbnail-פרק-{N}.jpg\n")
    touch(ep / "promo/טיזר-פרק-11.mp4", "teaser")
    touch(ep / "extras/teaser-check.log", "CAPTIONS OK\n")
    touch(ep / "extras/investing-bro-intro-with-beat.mp4")
    touch(ep / f"video/פרק-{N}-וידאו.mp4", "video")
    touch(ep / f"video/תיאור-פרק-{N}-youtube.txt", "00:00 טיזר\n01:05 חדשות\n20:00 עומק\n\n"
          "האזינו בספוטיפיי: https://open.spotify.com/show/4fREAemgQDMWIUK58N5Jjk\n")
    touch(ep / "extras/verify_sync.log", "SYNC OK\n")
    touch(ep / "extras/past-episode-cards.json", "[]")
    record(ep, "main", "MAINvid0001")


def started(tmp_path, owner="amitai", by=AM):
    assert run("start", tmp_path, "--episode", N, "--owner", owner, "--by", by) == 0
    return tmp_path


def to_upload(ep, by=AM):
    """Draft trim through the Private upload. Art is on the video as option A; the pick is still open."""
    main_files(ep)
    for m in ("transcript_doc", "cover_checks", "face_identity", "teaser_quality", "chapters", "past_episode_cards",
              "main.endscreen"):
        assert run("mark", ep, m, "--evidence", "seen it") == 0
    assert run("advance", ep, "main") == 1                       # draft trim + copy; stops at cuts_ok
    assert run("approve", ep, "main", "cuts_ok", "--by", by) == 0
    assert run("advance", ep, "main") == 1                       # stops at title_ok
    assert run("approve", ep, "main", "title_ok", "--by", by) == 0
    assert run("advance", ep, "main") == 1                       # art, video, upload (option A); stops at art_ok
    assert ps.load(ep)["stages"]["main.upload"]["state"] == "done"
    assert "main.art_ok" not in ps.load(ep)["stages"]


def through_main(ep, by=AM):
    to_upload(ep, by)
    assert run("approve", ep, "main", "art_ok", "--by", by) == 0
    assert run("advance", ep, "main") == 1                       # stops at ok
    assert run("approve", ep, "main", "ok", "--by", by) == 0


def ev(ep):
    s = ps.load(ep)
    return ps.evaluate(ep, s)


def test_approve_on_a_mark_stage_points_to_mark(tmp_path, capsys):
    started(tmp_path)
    assert run("approve", tmp_path, "release", "approval_round", "--by", AM) == 2
    err = capsys.readouterr().err
    assert "is not an approval stage" in err
    assert "mark EP release.approval_round" in err


def test_start_then_next_shows_the_first_step(tmp_path, capsys):
    started(tmp_path)
    capsys.readouterr()
    assert run("next", tmp_path, "--json") == 0
    rows = json.loads(capsys.readouterr().out)
    main = next(r for r in rows if r["track"] == "main")
    assert main["stage"] == "riverside" and main["skill"] == "investing-bros-post-production"
    assert "polling routine" in main["command"] and "10-20" in main["command"]
    assert "secure fill" in main["command"] and "busy loop" in main["command"]
    seg = next(r for r in rows if r["track"] == "seg01")
    assert seg["waits"] == "blocked" and seg["blocked_by"] == ["main.trim"]
    assert run("start", tmp_path, "--episode", N, "--owner", "amitai") == 1     # never twice


def test_waived_riverside_lets_intake_use_a_local_master(tmp_path):
    ep = started(tmp_path)
    touch(ep / "extras/investing-bros-episode-raw-untrimmed.m4a", "raw")
    assert run("advance", ep, "main", "intake") == 1
    assert run("waive", ep, "main.riverside", "--by", "Amitai 10:05: בלי ריברסייד, הקבצים אצלי") == 0
    assert run("advance", ep, "main", "intake") == 0


def test_start_owner_quote_must_be_the_owners(tmp_path):
    assert run("start", tmp_path, "--episode", N, "--owner", "nadav", "--by", AM) == 1
    assert run("start", tmp_path, "--episode", N, "--owner", "nadav") == 0
    assert ps.load(tmp_path)["owner"]["confirmed"] is False


def test_advance_refuses_on_a_failed_check_and_logs_it(tmp_path):
    ep = started(tmp_path)
    assert run("advance", ep, "main", "riverside") == 1
    s = ps.load(ep)
    assert s["events"][-1]["kind"] == "check_failed" and "riverside" in s["events"][-1]["detail"].lower()
    riverside_ready(ep)
    assert run("advance", ep, "main", "riverside") == 0
    assert run("advance", ep, "main", "intake") == 1
    s = ps.load(ep)
    assert s["events"][-1]["kind"] == "check_failed" and "raw master" in s["events"][-1]["detail"]


def test_main_track_end_to_end_and_approvals_need_the_owner(tmp_path, capsys):
    ep = started(tmp_path)
    main_files(ep)
    assert run("advance", ep, "main", "trim") == 1               # cut_list has not passed yet
    assert run("approve", ep, "main", "cuts_ok", "--by", AM) == 1   # cut_list not passed yet
    through_main(ep)
    e = ev(ep)
    assert all(e[f"main.{k}"]["status"] == "current" for k in ("trim", "video", "upload", "ok"))
    assert ps.load(ep)["stages"]["main.upload"]["data"]["video_id"] == "MAINvid0001"
    assert run("approve", ep, "seg01", "range_ok", "--by", NA) == 1  # Nadav isn't the owner


def test_new_cut_stales_main_and_only_overlapping_renders(tmp_path):
    ep = started(tmp_path)
    through_main(ep)
    # segment 01 covers raw 1200-1600, Short 01 covers raw 700-740
    assert run("mark", ep, "seg01.select", "--evidence", "raw 1200-1600, no cuts, 6:40") == 0
    assert run("approve", ep, "seg01", "range_ok", "--by", AM) == 1   # select not advanced yet
    assert run("advance", ep, "seg01", "select") == 0
    assert run("approve", ep, "seg01", "range_ok", "--by", AM) == 0
    touch(ep / "segments/סגמנט-01-צלילה-זהב.mp4", "seg")
    touch(ep / "extras/segment-01.json", json.dumps({
        "sync": "SYNC OK", "output": "segments/סגמנט-01-צלילה-זהב.mp4", "raw_ranges": [[1200, 1600]],
        "edit": {"start": 10, "end": 2000, "cuts": [[500, 520]]}}))
    assert run("advance", ep, "seg01", "render") == 0
    assert run("mark", ep, "short01.pick", "--evidence", "raw 700-740, cover: CoreWeave בסכנה?") == 0
    assert run("advance", ep, "short01", "pick") == 0
    assert run("approve", ep, "short01", "pick_ok", "--by", AM) == 0
    touch(ep / "extras/check-short-01.log", "s.mp4: 41.2 s, -14.0 LUFS, peak -1.6 dB -> strip.jpg\n")
    assert run("advance", ep, "short01", "render") == 0
    # a restore in review: the list changes, trim runs again on the draft, renders wait for cuts_ok
    touch(ep / "extras/cuts-review/cuts-list.txt",
          "[routine] 500-520 the courier call\n[content] 720-730 a false start — drop it?\n")
    e = ev(ep)
    assert e["main.cut_list"]["status"] == "stale" and e["main.cuts_ok"]["status"] == "stale"
    assert e["main.trim"]["status"] == "stale" and e["seg01.render"]["status"] == "stale"
    touch(ep / "extras/edit.json", json.dumps({"start": 10, "end": 2000, "cuts": [[500, 520], [720, 730]]}))
    touch(ep / "extras/cuts-review/cut-02.mp4")
    touch(ep / f"הקלטה-ערוכה-פרק-{N}.m4a", "audio v2")
    assert run("advance", ep, "main", "cut_list") == 0
    assert run("advance", ep, "main", "trim") == 0               # the draft trim does not wait for cuts_ok
    assert ps.load(ep)["stages"]["main.cuts_ok"]["state"] == "approved"
    assert ev(ep)["main.cuts_ok"]["status"] == "stale"
    assert run("advance", ep, "main", "copy") == 0               # re-copy only; nothing is re-rendered yet
    e = ev(ep)
    assert e["main.title_ok"]["status"] == "current"             # chapters moved; the titles file did not
    assert e["main.video"]["status"] == "stale" and e["main.ok"]["status"] == "stale"
    assert e["seg01.render"]["status"] == "current"               # 1200-1600 doesn't touch 720-730
    assert e["short01.render"]["status"] == "stale"               # 700-740 does
    assert run("advance", ep, "main", "video") == 1              # cuts_ok gates the render
    assert run("advance", ep, "short01", "render") == 1
    assert run("approve", ep, "main", "cuts_ok", "--by", AM) == 0
    assert run("advance", ep, "short01", "render") == 0
    assert run("status", ep) == 0
    stale = [x for x in ps.load(ep)["events"] if x["kind"] == "stale"]
    assert any(x["track"] == "short01" and x["stage"] == "render" for x in stale)
    assert "720.0-730.0" in e["short01.render"]["why"]


def test_reupload_stales_the_approval_and_publish_ok(tmp_path):
    ep = started(tmp_path)
    through_main(ep)
    s = ps.load(ep)
    old = s["stages"]["main.ok"]["version"]
    touch(ep / f"video/פרק-{N}-וידאו.mp4", "video v2")          # a fixed master
    e = ev(ep)
    assert e["main.video"]["status"] == "stale" and e["main.ok"]["status"] == "stale"
    assert run("advance", ep, "main", "video") == 0
    assert run("advance", ep, "main", "upload") == 1             # the record is still the old video's
    assert "older version" in ps.load(ep)["events"][-1]["detail"]
    record(ep, "main", "MAINvid0002", superseded=["MAINvid0001"])  # the fixed master went up again
    assert run("advance", ep, "main", "upload") == 0
    assert ps.evaluate(ep, ps.load(ep))["main.ok"]["status"] == "stale"
    assert run("approve", ep, "main", "ok", "--by", AM) == 0
    assert ps.load(ep)["stages"]["main.ok"]["version"] != old


def test_draft_trim_and_cuts_ok_gates_renders(tmp_path, capsys):
    ep = started(tmp_path)
    audio_files(ep)
    touch(ep / f"כותרות-פרק-{N}.txt", "1. x\nבחירה סופית: x")
    touch(ep / f"תיאור-פרק-{N}.txt", "desc")
    assert run("mark", ep, "transcript_doc", "--evidence", "https://docs.google.com/x") == 0
    assert run("advance", ep, "main") == 1
    s = ps.load(ep)
    assert s["stages"]["main.trim"]["state"] == "done"
    assert "main.cut_list" in s["stages"]["main.trim"]["inputs"]
    assert "main.cuts_ok" not in s["stages"]["main.trim"]["inputs"]
    assert "main.cuts_ok" not in s["stages"] and s["stages"]["main.copy"]["state"] == "done"
    capsys.readouterr()
    assert run("next", ep, "--json") == 0
    rows = json.loads(capsys.readouterr().out)
    main = next(r for r in rows if r["track"] == "main")
    assert main["waits"] == "owner" and main["approvals"] == ["cuts_ok", "title_ok"]
    # an untagged line does not pass the cut list
    assert pl.cut_list_problems("500-520 silence\n")
    assert pl.cut_list_problems("[routine] 12.0-20.0 silence\n[content] 1605-1645 the courier call\n# note\n") == []
    # renders wait for cuts_ok; select and pick do not
    touch(ep / f"video/פרק-{N}-וידאו.mp4", "video")
    touch(ep / f"video/תיאור-פרק-{N}-youtube.txt", "00:00 a\n01:00 b\n02:00 c\n")
    touch(ep / "promo/טיזר.mp4", "t")
    touch(ep / "extras/teaser-check.log", "CAPTIONS OK\n")
    touch(ep / "extras/x-intro.mp4", "i")
    touch(ep / "extras/verify_sync.log", "SYNC OK\n")
    for m in ("teaser_quality", "chapters"):
        assert run("mark", ep, m, "--evidence", "seen") == 0
    assert run("advance", ep, "main", "video") == 1
    assert run("mark", ep, "seg01.select", "--evidence", "raw 100-200, no cuts") == 0
    assert run("advance", ep, "seg01", "select") == 0
    assert run("approve", ep, "seg01", "range_ok", "--by", AM) == 0
    touch(ep / "extras/segment-01.json", json.dumps({"sync": "SYNC OK", "output": "segments/סגמנט-01-צלילה-x.mp4"}))
    touch(ep / "segments/סגמנט-01-צלילה-x.mp4", "seg")
    assert run("advance", ep, "seg01", "render") == 1
    assert run("mark", ep, "short01.pick", "--evidence", "raw 100-140, cover: x") == 0
    assert run("advance", ep, "short01", "pick") == 0
    assert run("approve", ep, "short01", "pick_ok", "--by", AM) == 0
    touch(ep / "extras/check-short-01.log", "s.mp4: 41.2 s, -14.0 LUFS\n")
    assert run("advance", ep, "short01", "render") == 1


def test_art_swap_stales_the_pick_not_the_upload(tmp_path):
    ep = started(tmp_path)
    to_upload(ep)
    jpg = ep / f"thumbnail-פרק-{N}.jpg"
    jpg.write_text("option B", encoding="utf-8")
    e = ev(ep)
    assert e["main.art"]["status"] == "stale" and e["main.upload"]["status"] == "current"
    assert run("advance", ep, "main", "art") == 0          # the promoted file, before the approval
    assert run("approve", ep, "main", "art_ok", "--by", AM) == 0
    rec = ps.load(ep)["stages"]["main.art_ok"]
    assert rec["of_hashes"][f"thumbnail-פרק-{N}.jpg"] == sha(jpg)
    assert run("approve", ep, "main", "ok", "--by", AM) == 0
    jpg.write_text("option C", encoding="utf-8")           # a later change of mind
    e = ev(ep)
    assert e["main.art_ok"]["status"] == "stale" and e["main.ok"]["status"] == "current"
    assert e["main.upload"]["status"] == "current"
    # the segment thumbnail is not part of the package fingerprint
    assert run("mark", ep, "seg01.select", "--evidence", "raw 100-200, no cuts") == 0
    assert run("advance", ep, "seg01", "select") == 0
    assert run("approve", ep, "seg01", "range_ok", "--by", AM) == 0
    touch(ep / "segments/סגמנט-01-צלילה-זהב.mp4", "seg")
    touch(ep / "segments/סגמנט-01-צלילה-זהב.txt", "title")
    touch(ep / "segments/סגמנט-01-צלילה-זהב-thumb.jpg", "option A")
    touch(ep / "segments/youtube-סגמנט-01.md", "notes")
    touch(ep / "extras/segment-01.json", json.dumps({"sync": "SYNC OK", "output": "segments/סגמנט-01-צלילה-זהב.mp4"}))
    assert run("advance", ep, "seg01", "render") == 0
    assert run("mark", ep, "seg01.nudge", "--evidence", "0:31 clear") == 0
    assert run("advance", ep, "seg01", "package") == 0
    outs = ps.load(ep)["stages"]["seg01.package"]["outputs"]
    assert not any(str(k).endswith("-thumb.jpg") for k in outs)
    thumb = ep / "segments/סגמנט-01-צלילה-זהב-thumb.jpg"
    thumb.write_text("option B", encoding="utf-8")
    assert ev(ep)["seg01.package"]["status"] == "current"
    record(ep, "seg01", "SEGvid00001", version=sha(ep / "segments/סגמנט-01-צלילה-זהב.mp4"))
    assert run("mark", ep, "seg01.links", "--evidence", "card + end screen") == 0
    assert run("advance", ep, "seg01", "upload") == 0
    assert run("approve", ep, "seg01", "thumb_ok", "--by", AM) == 0
    picked = ps.load(ep)["stages"]["seg01.thumb_ok"]
    assert picked["of_keys"] == ["segments/סגמנט-01-צלילה-זהב-thumb.jpg"]
    assert picked["of_hashes"]["segments/סגמנט-01-צלילה-זהב-thumb.jpg"] == sha(thumb)
    thumb.write_text("option C", encoding="utf-8")
    e = ev(ep)
    assert e["seg01.thumb_ok"]["status"] == "stale"
    assert e["seg01.package"]["status"] == "current" and e["seg01.upload"]["status"] == "current"
    assert "main.art_ok" not in pl.SPEC["main.upload"]["inputs"]
    assert "seg01.thumb_ok" not in pl.SPEC["seg01.upload"]["inputs"]
    assert "short01.cover_ok" not in pl.SPEC["short01.package"]["inputs"]
    assert pl.SPEC["short01.cover"]["inputs"] == ["short01.pick_ok"]
    assert "main.title_ok" in pl.SPEC["short01.cover"]["needs"]
    for key in ("main.art_ok", "seg01.thumb_ok", "short01.cover_ok", "main.cuts_ok"):
        assert key in pl.SPEC["release.publish_ok"]["inputs"]
    assert "main.cuts_ok" not in pl.SPEC["seg01.render"]["inputs"]
    assert "main.cuts_ok" not in pl.SPEC["main.video"]["inputs"]


def test_description_or_chapters_change_does_not_stale_title_ok(tmp_path):
    """title_ok fingerprints only כותרות-פרק-N.txt. Restoring a cut shifts chapters in the
    description (and the YouTube chapter file); that must not force another title round."""
    ep = started(tmp_path)
    through_main(ep)
    rec = ps.load(ep)["stages"]["main.title_ok"]
    assert rec["of_keys"] == [f"כותרות-פרק-{N}.txt"]
    touch(ep / f"תיאור-פרק-{N}.txt", "00:00 פתיחה\n01:22 חדשות אחרי שחזור\n")
    e = ev(ep)
    assert e["main.copy"]["status"] == "stale"
    assert e["main.title_ok"]["status"] == "current"
    d = ep / f"video/תיאור-פרק-{N}-youtube.txt"
    touch(d, d.read_text(encoding="utf-8").replace("01:05 חדשות", "01:22 חדשות"))
    e = ev(ep)
    assert e["main.video"]["status"] == "stale" and e["main.title_ok"]["status"] == "current"
    touch(ep / f"כותרות-פרק-{N}.txt", "1. y\nבחירה סופית: y")
    assert ev(ep)["main.title_ok"]["status"] == "stale"


def test_publication_edits_do_not_stale_what_was_approved(tmp_path):
    ep = started(tmp_path)
    through_main(ep)
    d = ep / f"video/תיאור-פרק-{N}-youtube.txt"
    touch(d, d.read_text(encoding="utf-8").replace("show/4fREAemgQDMWIUK58N5Jjk", "episode/7abcDEF"))  # step 7 swap
    e = ev(ep)
    assert e["main.video"]["status"] == "current" and e["main.ok"]["status"] == "current"
    touch(d, d.read_text(encoding="utf-8").replace("01:05 חדשות", "01:10 חדשות"))               # a real change
    assert ev(ep)["main.video"]["status"] == "stale"
    # a Short's notes: the status/URL lines publishing writes are masked, the title and description are not
    notes = ep / "Shorts/youtube-שורט-01.md"
    touch(ep / "Shorts/שורט-01-x.m4v", "short")
    touch(notes, "## Title\nזהב?\n\n## Description\nזהב?\n- status: Private\n- URL: (pending)\n")
    c = pl.Ctx(ep, ps.load(ep))
    keys = pl.out_slot("short", "short01", [".m4v"])(c)
    assert keys == ["Shorts/שורט-01-x.m4v", "text:Shorts/youtube-שורט-01.md"]
    before = ps.current_outputs(ep, dict.fromkeys(keys), {})
    touch(notes, notes.read_text(encoding="utf-8").replace("- status: Private\n- URL: (pending)",
                                                           "- status: Public 21:40\n- URL: https://youtube.com/shorts/abc"))
    assert ps.current_outputs(ep, dict.fromkeys(keys), {}) == before
    touch(notes, notes.read_text(encoding="utf-8").replace("## Title\nזהב?", "## Title\nכסף?"))
    assert ps.current_outputs(ep, dict.fromkeys(keys), {}) != before
    notes.unlink()
    assert ps.current_outputs(ep, dict.fromkeys(keys), {})["text:Shorts/youtube-שורט-01.md"] is None


def test_short_upload_needs_no_related_video_before_the_episode_is_public(tmp_path):
    ep = started(tmp_path)
    touch(ep / "Shorts/שורט-01-x.m4v", "short")
    record(ep, "short01", "SHORTvid001", version=sha(ep / "Shorts/שורט-01-x.m4v"))
    c = pl.Ctx(ep, ps.load(ep))
    assert pl.SPEC["short01.upload"]["check"](c) == []           # Related video: the publish checklist's `related`
    touch(ep / "Shorts/שורט-01-x.m4v", "short v2")
    c = pl.Ctx(ep, ps.load(ep))
    assert "older version" in pl.SPEC["short01.upload"]["check"](c)[0]


def test_old_uploads_must_name_every_superseded_id_and_reopen_on_a_new_one(tmp_path):
    ep = started(tmp_path)
    touch(ep / "segments/סגמנט-01-צלילה-זהב.mp4", "seg")
    record(ep, "seg01", "SEGvid00002", superseded=["SEGvid00001"])
    assert run("mark", ep, "old_uploads", "--evidence", "none") == 0
    c = pl.Ctx(ep, ps.load(ep))
    assert "SEGvid00001" in pl.old_uploads_check(c)[0]
    assert run("mark", ep, "old_uploads", "--evidence", "deleted SEGvid00001 in Studio 21:40") == 0
    c = pl.Ctx(ep, ps.load(ep))
    assert pl.old_uploads_check(c) == []
    before = pl.SPEC["release.old_uploads"]["outputs"](c)
    assert "extras/uploads/seg01.json" in before                 # a later re-upload changes it: cleanup reopens


def test_segment_watches_its_picked_range_not_only_the_kept_pieces(tmp_path):
    ep = started(tmp_path)
    touch(ep / "extras/segment-01.json", json.dumps({
        "raw_ranges": [[100, 200], [220, 300]], "selected_ranges": [[100, 300]],
        "edit": {"start": 10, "end": 2000, "cuts": [[200, 220]]}}))
    c = pl.Ctx(ep, ps.load(ep))
    data = pl.segment_data("seg01")(c)
    restored = {"start": 10, "end": 2000, "cuts": []}
    assert ps.overlaps(data["raw_ranges"], ps.changed_spans(data["edit"], restored))


def test_waivers_by_owner_and_never_for_approvals(tmp_path):
    ep = started(tmp_path)
    assert run("waive", ep, "main.cuts_ok", "--by", AM) == 1
    assert run("waive", ep, "teaser", "--by", NA) == 1
    assert run("waive", ep, "teaser", "--by", "Amitai 09:12: no teaser this time") == 0
    assert run("waive", ep, "seg02.package", "--by", "Amitai 09:13: skip") == 0
    assert ps.load(ep)["stages"]["seg02.package"]["state"] == "waived"


def test_owner_transfer_only_in_the_owners_words(tmp_path):
    ep = started(tmp_path)
    assert run("owner", ep, "--set", "nadav", "--by", "Nadav 11:00: אני לוקח") == 1
    assert run("owner", ep, "--set", "nadav", "--by", "Amitai 11:01: נדב לוקח את הפרק הזה") == 0
    s = ps.load(ep)
    assert s["owner"]["name"] == "nadav" and s["owner_history"][-1]["quote"].startswith("Amitai 11:01")
    audio_files(ep)
    run("mark", ep, "transcript_doc", "--evidence", "https://docs.google.com/x")
    assert run("advance", ep, "main") == 1
    assert run("approve", ep, "main", "cuts_ok", "--by", AM) == 1
    assert run("approve", ep, "main", "cuts_ok", "--by", NA) == 0


def test_unconfirmed_owner_can_be_confirmed_by_the_named_brother(tmp_path):
    assert run("start", tmp_path, "--episode", N, "--owner", "amitai") == 0
    assert run("owner", tmp_path, "--set", "nadav", "--by", "Nadav 09:00: הפרק שלי") == 0
    assert ps.load(tmp_path)["owner"] == {**ps.load(tmp_path)["owner"], "name": "nadav", "confirmed": True}


def test_migrate_imports_legacy_evidence_never_approvals_then_resumes(tmp_path, capsys):
    ep = tmp_path
    main_files(ep)
    touch(ep / "extras/postprod-checklist.json", json.dumps({
        "marked": {"transcript_doc": "https://docs.google.com/x", "chapters": "shifted +65s",
                   "teaser_quality": "ok", "cover_checks": "Codex", "face_identity": "ok",
                   "past_episode_cards": "none", "redcircle_draft": "https://app.redcircle.com/x"},
        "waived": {"face_identity": "Amitai 09:12: no faces this time"}}))
    assert run("migrate", ep, "--episode", N, "--owner", "amitai") == 0
    s = ps.load(ep)
    assert s["legacy"]["marked"]["chapters"] == "shifted +65s"
    assert not [k for k, v in s["stages"].items() if v["state"] == "approved"]
    assert ev(ep)["main.cut_list"]["status"] == "current" and ev(ep)["main.trim"]["status"] == "current"
    assert ev(ep)["main.copy"]["status"] == "current" and "main.cuts_ok" not in s["stages"]
    assert "Approvals are never imported" in capsys.readouterr().out
    assert run("approve", ep, "main", "cuts_ok", "--by", AM) == 0
    assert run("advance", ep, "main") == 1                      # stops at title_ok; trim already passed on the draft
    assert "main.title_ok" not in ps.load(ep)["stages"]
    assert ps.load(ep)["owner"]["confirmed"] is False
    assert run("gate", ep, "--stage", "upload") == 0             # legacy marks and waivers still count as evidence
    run("next", ep)
    assert "owner" in capsys.readouterr().out


def test_postprod_gate_runs_on_the_pipeline_state(tmp_path):
    ep = started(tmp_path)
    through_main(ep)
    assert run("gate", ep, "--stage", "upload") == 0
    assert run("gate", ep, "--stage", "review") == 1


def test_publish_ok_covers_every_ok_and_goes_stale(tmp_path):
    ep = started(tmp_path)
    s = ps.load(ep)
    # fake every track's ok and the approval round as recorded (their own checks are tested above)
    for t in pl.TRACKS[:-1]:
        s["stages"][f"{t}.upload"] = {"state": "done", "version": f"sha256:{t}", "outputs": {}, "inputs": {},
                                      "data": {"video_id": f"{t:<11}"[:11].replace(" ", "x")}}
        s["stages"][f"{t}.ok"] = {"state": "approved", "of": f"{t}.upload", "of_version": f"sha256:{t}",
                                  "version": f"sha256:{t}", "inputs": {}}
    s["stages"]["main.cuts_ok"] = {"state": "approved", "version": "sha256:cuts", "inputs": {}}
    s["stages"]["release.approval_round"] = {"state": "done", "version": "sha256:r", "outputs": {}, "inputs": {}}
    for key in ("main.art_ok", "seg01.thumb_ok", "seg02.thumb_ok",
                "short01.cover_ok", "short02.cover_ok", "short03.cover_ok"):
        s["stages"][key] = {"state": "approved", "version": f"sha256:{key}", "inputs": {}}
    ps.save(ep, s)
    assert run("approve", ep, "release", "publish_ok", "--by", AM) == 0
    s = ps.load(ep)
    assert s["stages"]["release.publish_ok"]["data"]["videos"]["short02"] == "short02xxxx"
    assert ev(ep)["release.publish_ok"]["status"] == "current"
    s["stages"]["short02.upload"]["version"] = "sha256:reuploaded"
    ps.save(ep, s)
    assert ev(ep)["release.publish_ok"]["status"] == "stale"


def test_note_kinds_and_retro_classification(tmp_path):
    ep = started(tmp_path)
    run("note", ep, "--kind", "owner_fix", "--track", "main", "the title had an en dash – again")
    run("note", ep, "--kind", "workaround", "Drive upload stalled; used the chunked handoff")
    run("note", ep, "--kind", "handback_returned", "--track", "seg02", "nudge covered Nadav's eyes")
    run("note", ep, "--kind", "owner_fix", "spelling: ספייסאקס")
    riverside_ready(ep)
    assert run("advance", ep, "main", "riverside") == 0
    assert run("advance", ep, "main", "intake") == 1             # a failed check (no raw master yet)
    assert run("retro", ep) == 1                                 # not live yet
    assert run("retro", ep, "--force") == 0
    text = (ep / f"extras/retro-פרק-{N}.md").read_text(encoding="utf-8")
    assert "| script check |" in text and "| GitHub issue |" in text and "| show fact |" in text
    assert "| one line in the owning skill |" in text and "## Waits on the owner" in text
    assert pl.classify({"kind": "waiver", "detail": "x"})[0] == "no action"


def test_retro_flags_repeats_from_the_last_one(tmp_path):
    ep = started(tmp_path / "פרק 11 — x")
    prev = tmp_path / "פרק 10 — y" / "extras" / "retro-פרק-10.md"
    touch(prev, "| # | Finding | Stage | Class | Why |\n|---|---|---|---|---|\n"
                "| 1 | check_failed: raw | main.intake | one line in the owning skill | x |\n")
    riverside_ready(ep)
    assert run("advance", ep, "main", "riverside") == 0
    assert run("advance", ep, "main", "intake") == 1
    assert run("retro", ep, "--force") == 0
    text = (ep / f"extras/retro-פרק-{N}.md").read_text(encoding="utf-8")
    assert "(repeat)" in text and "retro-פרק-10.md" in text


def test_doctor_never_prints_secrets(tmp_path):
    secret = "123456:SECRET-TOKEN-VALUE"

    def fake(cmd, timeout=20):
        return {"ffmpeg": (0, "ffmpeg version 9.0.2 Copyright"), "node": (0, "v22.1.0"),
                "rclone": (0, "show:\n")}.get(cmd[0], (1, "no"))
    rows, rc = pl.doctor(run=fake, env={"TELEGRAM_BOT_TOKEN": secret, "TELEGRAM_CHAT_ID": "-1"},
                         home=tmp_path, skills_root=tmp_path)
    text = "\n".join(" ".join(r) for r in rows)
    assert secret not in text and "-1" not in text.split("Telegram env")[1].split("\n")[0]
    assert dict((r[1], r[0]) for r in rows)["ffmpeg"] == "WARN" and rc == 0
    assert dict((r[1], r[0]) for r in rows)["rclone `show` remote"] == "OK"


def test_unknown_marks_and_stages_are_usage_errors(tmp_path):
    ep = started(tmp_path)
    assert run("mark", ep, "main.whatever", "--evidence", "x") == 2
    assert run("advance", ep, "main", "nope") == 2
    with pytest.raises(SystemExit):
        run("advance", ep)


def test_cuts_ok_change_stales_publish_ok_not_an_untouched_render(tmp_path):
    """publish_ok records the current cuts_ok. A render does not, so a cut outside its picture stays current."""
    ep = started(tmp_path)
    s = ps.load(ep)
    s["stages"]["main.cut_list"] = {"state": "done", "version": "sha256:cuts", "outputs": {}, "inputs": {}}
    s["stages"]["main.cuts_ok"] = {"state": "approved", "of": "main.cut_list", "of_version": "sha256:cuts",
                                   "version": "sha256:cuts", "inputs": {}}
    for t in pl.TRACKS[:-1]:
        s["stages"][f"{t}.upload"] = {"state": "done", "version": f"sha256:{t}", "outputs": {}, "inputs": {},
                                      "data": {"video_id": f"{t:<11}"[:11].replace(" ", "x")}}
        s["stages"][f"{t}.ok"] = {"state": "approved", "of": f"{t}.upload", "of_version": f"sha256:{t}",
                                  "version": f"sha256:{t}", "inputs": {}}
    s["stages"]["release.approval_round"] = {"state": "done", "version": "sha256:r", "outputs": {}, "inputs": {}}
    for key in ("main.art_ok", "seg01.thumb_ok", "seg02.thumb_ok",
                "short01.cover_ok", "short02.cover_ok", "short03.cover_ok"):
        s["stages"][key] = {"state": "approved", "version": f"sha256:{key}", "inputs": {}}
    s["stages"]["seg01.render"] = {"state": "done", "version": "sha256:render", "outputs": {}, "inputs": {}}
    ps.save(ep, s)
    assert run("approve", ep, "release", "publish_ok", "--by", AM) == 0
    assert ps.load(ep)["stages"]["release.publish_ok"]["inputs"]["main.cuts_ok"] == "sha256:cuts"
    s = ps.load(ep)
    s["stages"]["main.cut_list"]["version"] = "sha256:newcuts"
    ps.save(ep, s)
    e = ev(ep)
    assert e["main.cuts_ok"]["status"] == "stale"
    assert e["release.publish_ok"]["status"] == "stale" and "cuts_ok" in e["release.publish_ok"]["why"]
    assert e["seg01.render"]["status"] == "current"


def test_backfill_art_records_hashes_without_changing_the_version(tmp_path, capsys):
    ep = started(tmp_path)
    through_main(ep)
    s = ps.load(ep)
    art = s["stages"]["main.art_ok"]
    art_version = art["version"]
    art["of_hashes"] = "legacy"          # an older approval: no usable file hash, and this must not crash
    ps.save(ep, s)
    assert ev(ep)["main.art_ok"]["status"] == "current"
    touch(ep / f"cover-פרק-{N}.png", "different")
    assert run("backfill-art", ep, "main", "art_ok", "--by", AM) == 1
    assert "stale" in capsys.readouterr().err
    touch(ep / f"cover-פרק-{N}.png", "png")
    assert run("backfill-art", ep, "main", "art_ok", "--by", NA) == 1
    assert run("backfill-art", ep, "main", "art_ok", "--by", AM) == 0
    s = ps.load(ep)
    assert s["stages"]["main.art_ok"]["version"] == art_version
    hashes = s["stages"]["main.art_ok"]["of_hashes"]
    assert hashes[f"thumbnail-פרק-{N}.jpg"] == sha(ep / f"thumbnail-פרק-{N}.jpg")
    assert "backfill" in s["stages"]["main.art_ok"] and s["stages"]["main.art_ok"]["backfill"]["quote"] == AM
    thumb = ep / "segments/סגמנט-01-צלילה-זהב-thumb.jpg"
    touch(thumb, "option A")
    s["stages"]["seg01.package"] = {"state": "done", "version": "sha256:pkg", "outputs": {}, "inputs": {}}
    s["stages"]["seg01.thumb_ok"] = {"state": "approved", "of": "seg01.package", "of_version": "sha256:pkg",
                                     "version": "sha256:pkg", "inputs": {}}
    ps.save(ep, s)
    assert run("backfill-art", ep, "seg01", "thumb_ok", "--by", AM) == 0
    s = ps.load(ep)
    assert s["stages"]["seg01.thumb_ok"]["version"] == "sha256:pkg"
    assert s["stages"]["seg01.thumb_ok"]["of_hashes"][str(thumb.relative_to(ep))] == sha(thumb)
    for t in pl.TRACKS[:-1]:
        if f"{t}.ok" not in s["stages"]:
            s["stages"][f"{t}.upload"] = {"state": "done", "version": f"sha256:{t}", "outputs": {}, "inputs": {},
                                          "data": {"video_id": f"{t:<11}"[:11].replace(" ", "x")}}
            s["stages"][f"{t}.ok"] = {"state": "approved", "of": f"{t}.upload", "of_version": f"sha256:{t}",
                                      "version": f"sha256:{t}", "inputs": {}}
    for key in ("seg02.thumb_ok", "short01.cover_ok", "short02.cover_ok", "short03.cover_ok"):
        s["stages"][key] = {"state": "approved", "version": f"sha256:{key}", "inputs": {}}
    s["stages"]["release.approval_round"] = {"state": "done", "version": "sha256:r", "outputs": {}, "inputs": {}}
    ps.save(ep, s)
    assert run("approve", ep, "release", "publish_ok", "--by", AM) == 0
    assert ev(ep)["release.publish_ok"]["status"] == "current"
    thumb.write_text("option B", encoding="utf-8")
    e = ev(ep)
    assert e["seg01.package"]["status"] == "current"
    assert e["seg01.thumb_ok"]["status"] == "stale"
    assert e["release.publish_ok"]["status"] == "stale"


def _packages(ep):
    for nn, stem in (("01", "סגמנט-01-צלילה-זהב"), ("02", "סגמנט-02-רעיון-טסלה")):
        touch(ep / f"segments/{stem}.mp4", "seg")
        touch(ep / f"segments/{stem}.txt", "txt")
        touch(ep / f"segments/{stem}-thumb.jpg", f"thumb-{nn}")
        touch(ep / f"segments/youtube-סגמנט-{nn}.md", "notes")
    for nn, stem in (("01", "שורט-01-סוויפט"), ("02", "שורט-02-זהב"), ("03", "שורט-03-טסלה")):
        touch(ep / f"Shorts/{stem}.m4v", "short")
        touch(ep / f"Shorts/{stem}-cover.jpg", f"cover-{nn}")
        touch(ep / f"Shorts/{stem}.srt", "srt")
        touch(ep / f"Shorts/youtube-שורט-{nn}.md", "notes")
    log = ep / "extras/cover-check.log"
    extra = "".join(f"OK שורט-{nn}-x-cover.jpg\n" for nn in ("01", "02", "03"))
    log.write_text(log.read_text(encoding="utf-8") + extra, encoding="utf-8")


def test_publish_finishes_when_thumbnail_records_match(tmp_path, capsys):
    """Open thumb/cover items count as ticked for the publish gate when the record matches.
    A failed one does not, so release.publish, spotify_links, old_uploads, retro and done can finish."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "investing-bros-publish" / "scripts"))
    import publish_checklist as pcl
    ep = started(tmp_path)
    through_main(ep)
    _packages(ep)
    assert run("mark", ep, "shorts_covers", "--evidence", "three covers checked") == 0
    assert run("mark", ep, "redcircle_draft", "--evidence", "https://app.redcircle.com/draft") == 0
    vids = {"main": "MAINvid0001", "seg01": "SEG01vid001", "seg02": "SEG02vid001",
            "short01": "SH01vid0001", "short02": "SH02vid0001", "short03": "SH03vid0001"}
    files = {
        "seg01": ep / "segments/סגמנט-01-צלילה-זהב-thumb.jpg",
        "seg02": ep / "segments/סגמנט-02-רעיון-טסלה-thumb.jpg",
        "short01": ep / "Shorts/שורט-01-סוויפט-cover.jpg",
        "short02": ep / "Shorts/שורט-02-זהב-cover.jpg",
        "short03": ep / "Shorts/שורט-03-טסלה-cover.jpg",
    }
    s = ps.load(ep)
    jpg = next(k for k in s["stages"]["main.art_ok"]["of_hashes"] if str(k).endswith(".jpg"))
    side = {("main", vids["main"], jpg): s["stages"]["main.art_ok"]["of_hashes"][jpg]}
    for t, path in files.items():
        rel = str(path.relative_to(ep))
        digest = sha(path)
        stage = f"{t}.thumb_ok" if t.startswith("seg") else f"{t}.cover_ok"
        s["stages"][stage] = {"state": "approved", "version": f"sha256:{stage}", "inputs": {},
                              "of_hashes": {rel: digest}}
        s["stages"][f"{t}.upload"] = {"state": "done", "version": f"sha256:{t}", "outputs": {}, "inputs": {},
                                      "data": {"video_id": vids[t]}}
        s["stages"][f"{t}.ok"] = {"state": "approved", "of": f"{t}.upload", "of_version": f"sha256:{t}",
                                  "version": f"sha256:{t}", "inputs": {}}
        side[(t, vids[t], rel)] = digest
    s["stages"]["release.approval_round"] = {"state": "done", "version": "sha256:round", "outputs": {}, "inputs": {}}
    ps.save(ep, s)
    for (asset, vid, _rel), digest in side.items():
        touch(ep / f"extras/uploads/{asset}-thumb.json", json.dumps(
            {"asset": asset, "video_id": vid, "file": "pick.jpg", "sha256": digest}))
    assert run("approve", ep, "release", "publish_ok", "--by", AM) == 0
    f = ep / "extras/publish-checklist.json"
    assert pcl.main(["init", str(f), "--episode", str(N), "--full", vids["main"],
                     "--segments", vids["seg01"], vids["seg02"],
                     "--shorts", vids["short01"], vids["short02"], vids["short03"]]) == 0
    assert pcl.main(["publish-ok", str(f), "--by", AM]) == 0
    for _ in range(80):
        st = json.loads(f.read_text(encoding="utf-8"))
        nxt = next((x for x in st["items"] if x["state"] == "open" and not x["id"].endswith((".thumb", ".cover"))), None)
        if nxt is None:
            break
        assert pcl.main(["tick", str(f), nxt["id"], "--evidence", "seen"]) == 0, nxt["id"]
    else:
        raise AssertionError("checklist tick did not finish")
    assert pcl.main(["fail", str(f), "episode.thumb", "--reason", "details showed the wrong frame"]) == 0
    assert run("advance", ep, "release", "publish") == 1
    refused = capsys.readouterr()
    assert "episode.thumb" in refused.out + refused.err
    st = json.loads(f.read_text(encoding="utf-8"))
    for it in st["items"]:
        if it["id"] == "episode.thumb":
            it.update(state="open", note="")
    f.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    assert run("advance", ep, "release", "publish") == 0
    assert run("mark", ep, "spotify_links", "--evidence", "https://open.spotify.com/episode/abc") == 0
    assert run("advance", ep, "release", "spotify_links") == 0
    assert run("mark", ep, "old_uploads", "--evidence", "none") == 0
    assert run("advance", ep, "release", "old_uploads") == 0
    assert run("retro", ep) == 0
    assert run("mark", ep, "release.retro", "--evidence", "https://github.com/EthWiz/investing-bros-skills/pull/91") == 0
    assert run("advance", ep, "release", "retro") == 0
    assert run("gate", ep, "--stage", "done") == 0
    e = ev(ep)
    assert all(e[k]["status"] == "current" for k in
               ("release.publish", "release.spotify_links", "release.old_uploads", "release.retro"))
