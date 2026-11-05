"""pipeline.py: start/next/advance, approvals tied to versions, stale propagation (with the overlap rule),
migration of an in-flight episode, owner transfer, re-uploads, the retro and doctor."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import pipeline as pl  # noqa: E402
import pipeline_state as ps  # noqa: E402

N = 11
AM = "Amitai 10:00: מאשר"
NA = "Nadav 10:00: מאשר"


def touch(p: Path, text="x"):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def run(*args):
    return pl.main([str(a) for a in args])


def record(ep, track, vid, version="v1"):
    touch(ep / f"extras/uploads/{track}.json", json.dumps({
        "asset": track, "version": version, "channel": pl.SHOW_CHANNEL_ID, "video_id": vid, "privacy": "private",
        "steps": [{"name": "thumbnail"}], "steps_done": ["insert", "thumbnail"], "superseded": []}))


def audio_files(ep, cuts=([500, 520],)):
    touch(ep / "extras/investing-bros-episode-raw-untrimmed.m4a", "raw")
    touch(ep / "extras/transcript/segments.json", "[]")
    touch(ep / "extras/cuts-review/cuts-list.txt", "500-520 the courier call")
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
    touch(ep / f"video/תיאור-פרק-{N}-youtube.txt", "00:00 טיזר\n01:05 חדשות\n20:00 עומק\n")
    touch(ep / "extras/verify_sync.log", "SYNC OK\n")
    touch(ep / "extras/past-episode-cards.json", "[]")
    record(ep, "main", "MAINvid0001")


def started(tmp_path, owner="amitai", by=AM):
    assert run("start", tmp_path, "--episode", N, "--owner", owner, "--by", by) == 0
    return tmp_path


def through_main(ep, by=AM):
    main_files(ep)
    for m in ("transcript_doc", "cover_checks", "face_identity", "teaser_quality", "chapters", "past_episode_cards",
              "main.endscreen"):
        assert run("mark", ep, m, "--evidence", "seen it") == 0
    assert run("advance", ep, "main") == 1                       # stops at cuts_ok (an approval)
    assert run("approve", ep, "main", "cuts_ok", "--by", by) == 0
    assert run("advance", ep, "main") == 1                       # trim, copy; stops at title_ok
    assert run("approve", ep, "main", "title_ok", "--by", by) == 0
    assert run("advance", ep, "main", "art") == 0
    assert run("approve", ep, "main", "art_ok", "--by", by) == 0
    assert run("advance", ep, "main") == 1                       # video, upload; stops at ok
    assert run("approve", ep, "main", "ok", "--by", by) == 0


def ev(ep):
    s = ps.load(ep)
    return ps.evaluate(ep, s)


def test_start_then_next_shows_the_first_step(tmp_path, capsys):
    started(tmp_path)
    capsys.readouterr()
    assert run("next", tmp_path, "--json") == 0
    rows = json.loads(capsys.readouterr().out)
    main = next(r for r in rows if r["track"] == "main")
    assert main["stage"] == "intake" and main["skill"] == "investing-bros-post-production"
    seg = next(r for r in rows if r["track"] == "seg01")
    assert seg["waits"] == "blocked" and seg["blocked_by"] == ["main.trim"]
    assert run("start", tmp_path, "--episode", N, "--owner", "amitai") == 1     # never twice


def test_start_owner_quote_must_be_the_owners(tmp_path):
    assert run("start", tmp_path, "--episode", N, "--owner", "nadav", "--by", AM) == 1
    assert run("start", tmp_path, "--episode", N, "--owner", "nadav") == 0
    assert ps.load(tmp_path)["owner"]["confirmed"] is False


def test_advance_refuses_on_a_failed_check_and_logs_it(tmp_path):
    ep = started(tmp_path)
    assert run("advance", ep, "main", "intake") == 1
    s = ps.load(ep)
    assert s["events"][-1]["kind"] == "check_failed" and "raw master" in s["events"][-1]["detail"]


def test_main_track_end_to_end_and_approvals_need_the_owner(tmp_path, capsys):
    ep = started(tmp_path)
    main_files(ep)
    assert run("advance", ep, "main", "trim") == 1               # needs cuts_ok first
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
    # the owner approves a second cut inside the episode, at raw 720-730
    touch(ep / "extras/cuts-review/cuts-list.txt", "500-520 the courier call\n720-730 a false start")
    e = ev(ep)
    assert e["main.cut_list"]["status"] == "stale" and e["main.cuts_ok"]["status"] == "stale"
    assert e["main.trim"]["status"] == "stale" and e["seg01.render"]["status"] == "stale"
    assert run("advance", ep, "main", "cut_list") == 0
    assert run("advance", ep, "main", "trim") == 1               # cuts_ok is stale: re-approve first
    assert run("approve", ep, "main", "cuts_ok", "--by", AM) == 0
    touch(ep / "extras/edit.json", json.dumps({"start": 10, "end": 2000, "cuts": [[500, 520], [720, 730]]}))
    touch(ep / "extras/cuts-review/cut-02.mp4")
    touch(ep / f"הקלטה-ערוכה-פרק-{N}.m4a", "audio v2")
    assert run("advance", ep, "main", "trim") == 0
    e = ev(ep)
    assert e["main.copy"]["status"] == "stale"                    # chapters map through edit.json
    assert e["main.video"]["status"] == "stale" and e["main.ok"]["status"] == "stale"
    assert e["seg01.render"]["status"] == "current"               # 1200-1600 doesn't touch 720-730
    assert e["short01.render"]["status"] == "stale"               # 700-740 does
    assert run("status", ep) == 0
    stale = [x for x in ps.load(ep)["events"] if x["kind"] == "stale"]
    assert any(x["track"] == "short01" and x["stage"] == "render" for x in stale)
    assert "720.0-730.0" in e["short01.render"]["why"]


def test_reupload_stales_the_approval_and_publish_ok(tmp_path):
    ep = started(tmp_path)
    through_main(ep)
    s = ps.load(ep)
    old = s["stages"]["main.ok"]["version"]
    record(ep, "main", "MAINvid0002", version="v2")              # a fixed master went up again
    e = ev(ep)
    assert e["main.upload"]["status"] == "stale" and e["main.ok"]["status"] == "stale"
    assert run("advance", ep, "main", "upload") == 0
    assert ps.evaluate(ep, ps.load(ep))["main.ok"]["status"] == "stale"
    assert run("approve", ep, "main", "ok", "--by", AM) == 0
    assert ps.load(ep)["stages"]["main.ok"]["version"] != old


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
    assert ev(ep)["main.cut_list"]["status"] == "current" and "main.trim" not in s["stages"]
    assert "Approvals are never imported" in capsys.readouterr().out
    assert run("approve", ep, "main", "cuts_ok", "--by", AM) == 0
    assert run("advance", ep, "main") == 1                      # trim + copy pass, title_ok waits
    assert ev(ep)["main.copy"]["status"] == "current"
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
    s["stages"]["release.approval_round"] = {"state": "done", "version": "sha256:r", "outputs": {}, "inputs": {}}
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
    assert run("advance", ep, "main", "intake") == 1             # a failed check
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
