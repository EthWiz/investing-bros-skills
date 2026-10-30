"""publish_checklist.py: order gate, waivers, and the Related-video hard rule."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import publish_checklist as pc  # noqa: E402

FULL, S1, S2 = "YL1hdpdcVt8", "N_EaOlbiPAc", "S4P7Lv5PkxU"
SH = ["6Z4joIPUBrM", "mzV4BAzqdD0", "18NfV9ztek4"]


def state():
    return pc.build(9, FULL, [S1, S2], SH)


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
    for k in ("meta", "srt", "cover", "approval"):
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
    assert pc.main(["status", str(f)]) == 0
    assert "redcircle.copy" in capsys.readouterr().out
