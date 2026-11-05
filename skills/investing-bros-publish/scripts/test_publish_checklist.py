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
