"""publish_checklist.py: order gate, waivers, and the Related-video hard rule."""
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
    pc.waive(s, "short01.cover", "Amitai 22:10: covers from the phone later")
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
    assert pc.main(["waive", str(f), "short01.cover", "--by", "Amitai 21:05: fine"]) == 1
    assert pc.main(["waive", str(f), "short01.cover", "--by", "נדב 21:06: בסדר"]) == 0
    st = json.loads(f.read_text(encoding="utf-8"))
    assert st["items"][0]["owner"] == "nadav" and st["items"][0]["covers"]["episode"] == FULL


# ---- with the episode state (extras/pipeline.json from investing-bros-producer) ----

import pipeline_state as ps  # noqa: E402

TRACKS = {"episode": "main", "seg01": "seg01", "seg02": "seg02", "short01": "short01", "short02": "short02",
          "short03": "short03"}
IDS = {"episode": FULL, "seg01": S1, "seg02": S2, "short01": SH[0], "short02": SH[1], "short03": SH[2]}


def pipeline_episode(tmp_path):
    """An episode whose pipeline has every upload approved and the owner's publish OK (records only)."""
    st = {"schema_version": 1, "episode": 9, "revision": 0, "owner": {"name": "nadav", "confirmed": True},
          "stages": {}, "marks": {}, "waivers": {}, "events": []}
    for g, t in TRACKS.items():
        st["stages"][f"{t}.upload"] = {"state": "done", "version": f"sha256:{t}-v1", "outputs": {}, "inputs": {},
                                       "data": {"video_id": IDS[g]}}
        st["stages"][f"{t}.ok"] = {"state": "approved", "of": f"{t}.upload", "of_version": f"sha256:{t}-v1",
                                   "version": f"sha256:{t}-v1", "inputs": {}}
    st["stages"]["release.publish_ok"] = {"state": "approved", "version": "sha256:p",
                                          "inputs": {f"{t}.ok": f"sha256:{t}-v1" for t in TRACKS.values()}}
    ps.save(tmp_path, st)
    f = tmp_path / "extras" / "publish-checklist.json"
    assert pc.main(["init", str(f), "--episode", "9", "--full", FULL, "--segments", S1, S2, "--shorts", *SH]) == 0
    assert pc.main(["publish-ok", str(f), "--by", "Nadav 21:02: מאשר לפרסם"]) == 0
    return f


def reupload(ep, track, vid):
    """What pipeline.py records after `advance TRACK upload` on a new upload record."""
    st = ps.load(ep)
    st["stages"][f"{track}.upload"].update(version=f"sha256:{track}-v2", data={"video_id": vid})
    ps.save(ep, st)


def tick_group(f, g):
    st = json.loads(f.read_text(encoding="utf-8"))
    for it in st["items"]:
        if it["group"] == g and it["phase"] == "pre":
            assert pc.main(["tick", str(f), it["id"], "--evidence", "seen"]) == 0


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
    assert all(x["state"] == "ticked" for x in st["items"] if x["group"] == "episode")   # already live: untouched
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
