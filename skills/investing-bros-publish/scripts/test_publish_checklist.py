"""publish_checklist.py: order gate, waivers, and the Related-video hard rule."""
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import publish_checklist as pc  # noqa: E402

FULL, S1, S2 = "YL1hdpdcVt8", "N_EaOlbiPAc", "S4P7Lv5PkxU"
SH = ["6Z4joIPUBrM", "mzV4BAzqdD0", "18NfV9ztek4"]


AMITAI = lambda by: (True, "amitai", "ok")  # noqa: E731  (no episode state: Amitai approves)


def state():
    s = pc.build(9, FULL, [S1, S2], SH)
    pc.record_publish_ok(s, "Amitai 21:00: publish ep 9 with all assets", AMITAI)
    return s


def finish(s, group):
    for it in s["items"]:
        if it["group"] == group:
            pc.tick(s, it["id"], "seen")


def test_build_rejects_bad_ids_and_counts():
    with pytest.raises(ValueError):
        pc.build(9, "YL1hdpdcVt", [S1, S2], SH)  # 10 chars
    with pytest.raises(ValueError):
        pc.build(9, FULL, [S1], SH)
    with pytest.raises(ValueError):
        pc.build(9, FULL, [S1, S1], SH)


def test_episode_cannot_go_public_before_redcircle():
    s = state()
    for k in ("channel", "meta", "thumb", "endscreen"):
        pc.tick(s, f"episode.{k}", "seen")
    with pytest.raises(PermissionError):
        pc.tick(s, "episode.public", "switched")
    finish(s, "redcircle")
    pc.tick(s, "episode.public", "switched")


def test_live_needs_public_first():
    s = state()
    with pytest.raises(PermissionError):
        pc.tick(s, "redcircle.live", "feed ok")


def test_short_never_public_without_related_video():
    s = state()
    for g in ("redcircle", "episode", "seg01", "seg02"):
        finish(s, g)
    for k in ("channel", "meta", "srt", "cover", "approval"):
        pc.tick(s, f"short01.{k}", "seen")
    pc.fail(s, "short01.related", "No matching results; only the description link is there")
    with pytest.raises(PermissionError):
        pc.tick(s, "short01.public", "switched")
    with pytest.raises(PermissionError):
        pc.waive(s, "short01.related", "Amitai: fine, the description link is enough")
    assert "FAILED" in pc.render(s)


def test_later_short_waits_for_earlier_short():
    s = state()
    for g in ("redcircle", "episode", "seg01", "seg02"):
        finish(s, g)
    for it in s["items"]:
        if it["group"] == "short02" and it["phase"] == "pre":
            pc.tick(s, it["id"], "seen")
    assert pc.blockers(s, "short02.public")  # short01 still open
    finish(s, "short01")
    assert pc.blockers(s, "short02.public") == []


def test_waivers():
    s = state()
    with pytest.raises(PermissionError):
        pc.waive(s, "short01.cover", "Nadav said ok")
    with pytest.raises(PermissionError):
        pc.waive(s, "short01.cover", "Amitai 22:10: covers from the phone later")
    with pytest.raises(PermissionError):
        pc.waive(s, "episode.thumb", "Amitai 22:10: thumbnail later")
    with pytest.raises(PermissionError):
        pc.waive(s, "episode.live", "Amitai: skip")
    with pytest.raises(PermissionError):
        pc.waive(s, "redcircle.public", "Amitai: skip")


def test_tick_needs_evidence_and_render_marks():
    s = state()
    with pytest.raises(ValueError):
        pc.tick(s, "redcircle.audio", " ")
    pc.tick(s, "redcircle.audio", "Episode 9, season 1, full")
    out = pc.render(s)
    assert "- [x] Edited episode audio uploaded; Episode Number 9" in out
    assert f"https://youtu.be/{SH[2]}" in out
    assert "Still open" in out


def test_cli_roundtrip(tmp_path, capsys):
    f = tmp_path / "c.json"
    assert pc.main(["init", str(f), "--episode", "9", "--full", FULL, "--segments", S1, S2, "--shorts", *SH]) == 0
    assert pc.main(["init", str(f), "--episode", "9", "--full", FULL, "--segments", S1, S2, "--shorts", *SH]) == 1
    assert pc.main(["can-public", str(f), "episode"]) == 1
    assert pc.main(["tick", str(f), "episode.public", "--evidence", "x"]) == 1
    assert pc.main(["tick", str(f), "redcircle.audio", "--evidence", "ok"]) == 0
    assert pc.main(["publish-ok", str(f), "--by", "Amitai 21:00: publish all"]) == 0
    assert pc.main(["status", str(f)]) == 0
    assert "redcircle.copy" in capsys.readouterr().out


def test_channel_check_first_and_never_waived():
    s = state()
    for g in ("episode", "seg01", "seg02", "short01", "short02", "short03"):
        first = next(x for x in s["items"] if x["group"] == g)
        assert first["id"] == f"{g}.channel"
        with pytest.raises(PermissionError):
            pc.waive(s, f"{g}.channel", "Amitai: skip it")
    finish(s, "redcircle")
    for k in ("meta", "thumb", "endscreen"):
        pc.tick(s, f"episode.{k}", "seen")
    assert pc.blockers(s, "episode.public") == ["episode.channel"]


def test_no_pinned_comment_items():
    # Amitai, 2026-11-01: no pinned comments on segments or Shorts.
    s = state()
    assert not [x for x in s["items"] if x["id"].endswith(".pin") or x["phase"] == "post"]


def test_publish_ok_comes_first_and_is_never_ticked_or_waived():
    s = pc.build(9, FULL, [S1, S2], SH)
    assert s["items"][0]["id"] == "release.publish_ok"
    for k in ("audio", "copy", "titles"):
        pc.tick(s, f"redcircle.{k}", "seen")
    assert pc.blockers(s, "redcircle.public") == ["release.publish_ok"]
    with pytest.raises(PermissionError):
        pc.tick(s, "release.publish_ok", "Amitai said go")
    with pytest.raises(PermissionError):
        pc.waive(s, "release.publish_ok", "Amitai 21:00: skip")
    pc.record_publish_ok(s, "Amitai 21:00: publish", AMITAI)
    assert pc.blockers(s, "redcircle.public") == []


def test_publish_ok_goes_stale_when_a_video_id_changes():
    s = state()
    s["videos"]["short02"] = "AAAAAAAAAAA"   # Short 02 re-uploaded after the OK
    assert "stale" in pc.publish_ok_problem(s)
    assert pc.blockers(s, "redcircle.public") == ["release.publish_ok"]


def test_old_state_files_get_the_publish_ok_item(tmp_path):
    s = pc.build(9, FULL, [S1, S2], SH)
    s["items"] = [x for x in s["items"] if x["group"] != "release"]
    del s["videos"]["release"]
    f = tmp_path / "c.json"
    f.write_text(json.dumps(s), encoding="utf-8")
    assert pc.main(["can-public", str(f), "redcircle"]) == 1


def test_owner_from_episode_state(tmp_path):
    ex = tmp_path / "extras"
    ex.mkdir()
    (ex / "pipeline.json").write_text(json.dumps({"schema_version": 1, "owner": {"name": "nadav"}}), encoding="utf-8")
    f = ex / "publish-checklist.json"
    assert pc.main(["init", str(f), "--episode", "9", "--full", FULL, "--segments", S1, S2, "--shorts", *SH]) == 0
    assert pc.main(["publish-ok", str(f), "--by", "Amitai 21:00: go"]) == 1       # not this episode's owner
    assert pc.main(["publish-ok", str(f), "--by", "Nadav 21:02: מאשר לפרסם הכל"]) == 0
    assert pc.main(["waive", str(f), "short01.cover", "--by", "נדב 21:06: בסדר"]) == 1   # a cover is never waived
    assert pc.main(["waive", str(f), "short01.approval", "--by", "Amitai 21:05: fine"]) == 1
    assert pc.main(["waive", str(f), "short01.approval", "--by", "נדב 21:06: בסדר"]) == 0
    st = json.loads(f.read_text(encoding="utf-8"))
    assert st["items"][0]["owner"] == "nadav" and st["items"][0]["covers"]["episode"] == FULL


# ---- with the episode state (extras/pipeline.json from investing-bros-producer) ----

import pipeline_state as ps  # noqa: E402

TRACKS = {"episode": "main", "seg01": "seg01", "seg02": "seg02", "short01": "short01", "short02": "short02",
          "short03": "short03"}
IDS = {"episode": FULL, "seg01": S1, "seg02": S2, "short01": SH[0], "short02": SH[1], "short03": SH[2]}


ART_BYTES = b"art-bytes"
ART_SHA = hashlib.sha256(ART_BYTES).hexdigest()
ART = {"episode": ("main", "main.art_ok", "thumbnail.jpg"),
       "seg01": ("seg01", "seg01.thumb_ok", "seg01-thumb.jpg"),
       "seg02": ("seg02", "seg02.thumb_ok", "seg02-thumb.jpg"),
       "short01": ("short01", "short01.cover_ok", "short01-cover.jpg"),
       "short02": ("short02", "short02.cover_ok", "short02-cover.jpg"),
       "short03": ("short03", "short03.cover_ok", "short03-cover.jpg")}


def pipeline_episode(tmp_path):
    """An episode whose pipeline has every upload approved and the owner's publish OK (records only)."""
    st = {"schema_version": 1, "episode": 9, "revision": 0, "owner": {"name": "nadav", "confirmed": True},
          "stages": {}, "marks": {}, "waivers": {}, "events": []}
    for g, t in TRACKS.items():
        st["stages"][f"{t}.upload"] = {"state": "done", "version": f"sha256:{t}-v1", "outputs": {}, "inputs": {},
                                       "data": {"video_id": IDS[g]}}
        st["stages"][f"{t}.ok"] = {"state": "approved", "of": f"{t}.upload", "of_version": f"sha256:{t}-v1",
                                   "version": f"sha256:{t}-v1", "inputs": {}}
    uploads = tmp_path / "extras" / "uploads"
    uploads.mkdir(parents=True)
    for g, (asset, stage, name) in ART.items():
        st["stages"][stage] = {"state": "approved", "version": f"sha256:{stage}", "inputs": {},
                               "of_hashes": {name: ART_SHA}}
        (tmp_path / name).write_bytes(ART_BYTES)
        (uploads / f"{asset}-thumb.json").write_text(json.dumps(
            {"asset": asset, "video_id": IDS[g], "file": name, "sha256": ART_SHA}), encoding="utf-8")
    st["stages"]["release.publish_ok"] = {"state": "approved", "version": "sha256:p",
                                          "inputs": {f"{t}.ok": f"sha256:{t}-v1" for t in TRACKS.values()}}
    ps.save(tmp_path, st)
    f = tmp_path / "extras" / "publish-checklist.json"
    assert pc.main(["init", str(f), "--episode", "9", "--full", FULL, "--segments", S1, S2, "--shorts", *SH]) == 0
    assert pc.main(["publish-ok", str(f), "--by", "Nadav 21:02: מאשר לפרסם"]) == 0
    return f


def reupload(ep, track, vid):
    """What pipeline.py records after `advance TRACK upload` on a new upload record.
    The same approved image is set on the new video (--set-thumbnail rewrites the side record)."""
    st = ps.load(ep)
    st["stages"][f"{track}.upload"].update(version=f"sha256:{track}-v2", data={"video_id": vid})
    ps.save(ep, st)
    side = ep / "extras" / "uploads" / f"{track}-thumb.json"
    if side.is_file():
        rec = json.loads(side.read_text(encoding="utf-8"))
        rec["video_id"] = vid
        side.write_text(json.dumps(rec), encoding="utf-8")


def tick_group(f, g):
    st = json.loads(f.read_text(encoding="utf-8"))
    for it in st["items"]:
        if it["group"] == g and it["phase"] == "pre" and not it["id"].endswith((".thumb", ".cover")):
            assert pc.main(["tick", str(f), it["id"], "--evidence", "seen"]) == 0


def test_thumbnail_record_replaces_the_hand_tick(tmp_path, capsys):
    f = pipeline_episode(tmp_path)
    tick_group(f, "redcircle")
    assert pc.main(["can-public", str(f), "redcircle"]) == 0
    assert pc.main(["tick", str(f), "redcircle.public", "--evidence", "published"]) == 0
    assert pc.main(["tick", str(f), "redcircle.live", "--evidence", "live"]) == 0
    tick_group(f, "episode")
    assert pc.main(["tick", str(f), "episode.thumb", "--evidence", "seen"]) == 1
    assert pc.main(["can-public", str(f), "episode"]) == 0          # the record stands in for the tick
    side = tmp_path / "extras" / "uploads" / "main-thumb.json"
    rec = json.loads(side.read_text(encoding="utf-8"))
    rec["sha256"] = "ff" * 32
    side.write_text(json.dumps(rec), encoding="utf-8")
    assert pc.main(["can-public", str(f), "episode"]) == 1
    assert "not the approved pick" in capsys.readouterr().out
    rec["sha256"] = ART_SHA
    side.write_text(json.dumps(rec), encoding="utf-8")
    out = pc.render(json.loads(f.read_text(encoding="utf-8")), f)
    assert "thumbnail record" in out


def test_pipeline_ok_lets_the_release_through(tmp_path, capsys):
    f = pipeline_episode(tmp_path)
    tick_group(f, "redcircle")
    assert pc.main(["can-public", str(f), "redcircle"]) == 0


def test_reupload_after_approval_makes_its_checks_stale(tmp_path, capsys):
    f = pipeline_episode(tmp_path)
    tick_group(f, "redcircle")
    reupload(tmp_path, "seg01", "NEWseg01vid")
    assert pc.main(["can-public", str(f), "redcircle"]) == 1          # the publish OK is stale for everything
    out = capsys.readouterr().out
    assert "release.publish_ok is stale" in out
    assert pc.main(["can-public", str(f), "seg01"]) == 1
    out = capsys.readouterr().out
    assert "seg01.ok is stale" in out and "re-uploaded" in out
    assert pc.main(["tick", str(f), "redcircle.public", "--evidence", "published"]) == 1


def test_reupload_during_a_partial_publication(tmp_path, capsys):
    f = pipeline_episode(tmp_path)
    for g in ("redcircle", "episode"):
        tick_group(f, g)
        assert pc.main(["can-public", str(f), g]) == 0
        assert pc.main(["tick", str(f), f"{g}.public", "--evidence", "switched"]) == 0
        assert pc.main(["tick", str(f), f"{g}.live", "--evidence", "check_live ok"]) == 0
    tick_group(f, "seg01")
    reupload(tmp_path, "seg01", "NEWseg01vid")                         # seg01 fixed and uploaded again
    assert pc.main(["can-public", str(f), "seg01"]) == 1
    assert pc.main(["set-video", str(f), "seg01", "NEWseg01vid"]) == 0
    st = json.loads(f.read_text(encoding="utf-8"))
    assert all(x["state"] == "open" for x in st["items"] if x["group"] == "seg01")
    assert all(x["state"] == "ticked" for x in st["items"]
               if x["group"] == "episode" and x["id"] != "episode.thumb")   # already live: untouched
    assert next(x["state"] for x in st["items"] if x["id"] == "episode.thumb") == "open"
    # the owner approves the new segment and gives the publish OK again
    ep_state = ps.load(tmp_path)
    ep_state["stages"]["seg01.ok"].update(of_version="sha256:seg01-v2", version="sha256:seg01-v2")
    ep_state["stages"]["release.publish_ok"]["inputs"]["seg01.ok"] = "sha256:seg01-v2"
    ps.save(tmp_path, ep_state)
    assert pc.main(["can-public", str(f), "seg01"]) == 1               # the checklist's own OK is stale too
    assert pc.main(["publish-ok", str(f), "--by", "Nadav 22:10: גם הסגמנט החדש מאושר"]) == 0
    assert pc.main(["can-public", str(f), "seg01"]) == 1               # seg01's checks were reopened
    tick_group(f, "seg01")
    assert pc.main(["can-public", str(f), "seg01"]) == 0


def finish_public(f, g):
    tick_group(f, g)
    assert pc.main(["can-public", str(f), g]) == 0, g
    assert pc.main(["tick", str(f), f"{g}.public", "--evidence", "switched"]) == 0
    live = f"{g}.live"
    st = json.loads(Path(f).read_text(encoding="utf-8"))
    if any(x["id"] == live for x in st["items"]):
        assert pc.main(["tick", str(f), live, "--evidence", "live"]) == 0


def test_failed_thumbnail_blocks_public_even_when_the_record_matches(tmp_path, capsys):
    f = pipeline_episode(tmp_path)
    finish_public(f, "redcircle")
    tick_group(f, "episode")
    assert pc.main(["fail", str(f), "episode.thumb", "--reason", "wrong frame"]) == 0
    assert pc.main(["can-public", str(f), "episode"]) == 1
    assert "episode.thumb is failed" in capsys.readouterr().out
    rendered = pc.render(json.loads(f.read_text(encoding="utf-8")), f)
    line = next(ln for ln in rendered.splitlines() if "Approved thumbnail" in ln)
    assert line.startswith("- [ ]") and "FAILED" in line and "thumbnail record" not in line
    st = json.loads(f.read_text(encoding="utf-8"))
    for it in st["items"]:
        if it["id"] == "episode.thumb":
            it.update(state="open", note="")
    f.write_text(json.dumps(st), encoding="utf-8")
    for g in ("episode", "seg01", "seg02"):
        finish_public(f, g)
    tick_group(f, "short01")
    assert pc.main(["fail", str(f), "short01.cover", "--reason", "phone cover is the wrong frame"]) == 0
    assert pc.main(["can-public", str(f), "short01"]) == 1
    assert "short01.cover is failed" in capsys.readouterr().out


def test_manual_thumbnail_record_needs_the_owner_and_is_not_a_waiver(tmp_path, capsys):
    f = pipeline_episode(tmp_path)
    img = tmp_path / "thumbnail.jpg"
    shot = tmp_path / "extras" / "phone.png"
    shot.write_bytes(b"screenshot")
    quote = "Nadav 21:40: שמתי את הקאבר מהטלפון"
    base = ["record-thumb", str(f), "--asset", "main", "--thumbnail", str(img), "--video-id", FULL]
    assert pc.main(base + ["--evidence", str(tmp_path / "missing.png"), "--by", quote]) == 1
    assert pc.main(base + ["--evidence", str(shot), "--by", "Amitai 21:40: אני"]) == 1
    before = json.loads(f.read_text(encoding="utf-8"))["items"]
    assert pc.main(base + ["--evidence", str(shot), "--by", quote]) == 0
    after = json.loads(f.read_text(encoding="utf-8"))["items"]
    assert before == after and next(x["state"] for x in after if x["id"] == "episode.thumb") == "open"
    rec = json.loads((tmp_path / "extras/uploads/main-thumb.json").read_text(encoding="utf-8"))
    assert rec["manual"] is True and rec["sha256"] == ART_SHA and rec["video_id"] == FULL
    assert rec["quote"] == quote and rec["evidence"].endswith("phone.png")
    assert not (tmp_path / "extras/uploads/main.json").is_file()
    rec["quote"] = ""
    (tmp_path / "extras/uploads/main-thumb.json").write_text(json.dumps(rec), encoding="utf-8")
    finish_public(f, "redcircle")
    tick_group(f, "episode")
    assert pc.main(["can-public", str(f), "episode"]) == 1
    assert "owner" in capsys.readouterr().out
    assert pc.main(base + ["--evidence", str(shot), "--by", quote]) == 0
    assert pc.main(["can-public", str(f), "episode"]) == 0
    assert pc.main(["waive", str(f), "episode.thumb", "--by", quote]) == 1
    st = json.loads(f.read_text(encoding="utf-8"))
    assert next(x["state"] for x in st["items"] if x["id"] == "episode.thumb") == "open"


def test_art_approval_without_a_file_hash_does_not_pass_or_crash(tmp_path, capsys):
    f = pipeline_episode(tmp_path)
    st = ps.load(tmp_path)
    st["stages"]["main.art_ok"]["of_hashes"] = None
    ps.save(tmp_path, st)
    finish_public(f, "redcircle")
    tick_group(f, "episode")
    assert pc.main(["can-public", str(f), "episode"]) == 1
    refused = capsys.readouterr().out
    assert "no file hash" in refused and "backfill-art" in refused
    st = ps.load(tmp_path)
    st["stages"]["main.art_ok"]["of_hashes"] = ["not-a-dict"]
    ps.save(tmp_path, st)
    assert pc.main(["can-public", str(f), "episode"]) == 1
    assert "Traceback" not in capsys.readouterr().out
    assert ps.evaluate(tmp_path, ps.load(tmp_path))["main.art_ok"]["status"] == "current"
