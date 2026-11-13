"""sbs_master.py: native Riverside export is first; track-build is blocked without owner approval."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import pipeline as pl  # noqa: E402
import pipeline_state as ps  # noqa: E402
import sbs_master as sbs  # noqa: E402

N = 11
AM = "Amitai 10:00: מאשר"
FAIL = "Couldn't download your edit (4k and 1080p); Exports tab never loads"


def touch(p: Path, data=b"x"):
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        p.write_text(data, encoding="utf-8")
    else:
        p.write_bytes(data)


def started(tmp_path, by=AM):
    assert pl.main(["start", str(tmp_path), "--episode", str(N), "--owner", "amitai", "--by", by]) == 0
    return tmp_path


def test_method_order_is_native_export_then_tracks():
    assert sbs.method_order() == (sbs.VIA_EXPORT, sbs.VIA_TRACKS)
    assert sbs.default_method() == sbs.VIA_EXPORT
    assert sbs.APPROVAL_KEY == "main.sbs_fallback_ok"
    assert sbs.APPROVAL_KEY in pl.SPEC
    assert pl.SPEC[sbs.APPROVAL_KEY]["kind"] == "approval"
    assert pl.SPEC[sbs.APPROVAL_KEY]["of"] == "main.riverside"
    assert pl.SPEC[sbs.APPROVAL_KEY].get("when") == "sbs_fallback"


def test_decide_prefers_native_export_even_if_fallback_was_approved(tmp_path):
    ep = started(tmp_path)
    touch(ep / "riverside/side-by-side.mp4", b"sbs-export")
    # A leftover approval must not override the native file.
    rec = {"state": "approved", "by": "amitai", "at": "2026-11-13T08:00:00+02:00",
           "quote": AM, "of": "main.riverside", "version": "waived"}
    # even with a fabricated approval in a bare state:
    state = {"stages": {sbs.APPROVAL_KEY: rec}}
    plan = sbs.decide(ep, state)
    assert plan["method"] == sbs.VIA_EXPORT
    assert plan["allowed"] is True
    assert plan["needs_approval"] is False
    assert plan["path"] == "riverside/side-by-side.mp4"
    assert sbs.tracks_build_problems(ep, state)
    assert "use it" in sbs.tracks_build_problems(ep, state)[0]


def test_track_build_blocked_without_failure_or_approval(tmp_path):
    ep = started(tmp_path)
    plan = sbs.decide(ep)
    assert plan["method"] == sbs.VIA_EXPORT
    assert plan["allowed"] is False
    assert plan["needs_approval"] is False
    assert plan["fallback_pending"] is False
    assert "download it first" in plan["reason"]
    assert sbs.tracks_build_problems(ep)
    with pytest.raises(ValueError, match="download it first|Do not build"):
        sbs.build_from_tracks(ep, "riverside/amitai.mp4", "riverside/nadav.mp4", dry_run=True)


def test_track_build_blocked_after_failure_until_owner_approves(tmp_path):
    ep = started(tmp_path)
    sbs.record_export_failed(ep, FAIL)
    plan = sbs.decide(ep)
    assert plan["method"] == sbs.VIA_TRACKS
    assert plan["allowed"] is False
    assert plan["needs_approval"] is True
    assert plan["fallback_pending"] is True
    assert sbs.fallback_pending(ep) is True
    touch(ep / "riverside/amitai.mp4", b"L")
    touch(ep / "riverside/nadav.mp4", b"R")
    with pytest.raises(ValueError, match="approval"):
        sbs.build_from_tracks(ep, "riverside/amitai.mp4", "riverside/nadav.mp4", dry_run=True)


def test_track_build_allowed_with_owner_approval_after_failure(tmp_path, capsys):
    ep = started(tmp_path)
    sbs.record_export_failed(ep, FAIL)
    # Approval is of main.riverside, so the pull (or a waiver) has to be current first.
    assert pl.main(["approve", str(ep), "main", "sbs_fallback_ok", "--by",
                    "Amitai 11:00: תבנה מהטראקים"]) == 1
    assert pl.main(["waive", str(ep), "main.riverside", "--by",
                    "Amitai 10:05: בלי ריברסייד, הקבצים אצלי"]) == 0
    assert pl.main(["approve", str(ep), "main", "sbs_fallback_ok", "--by",
                    "Amitai 11:00: תבנה מהטראקים"]) == 0
    out = capsys.readouterr()
    state = ps.load(ep)
    rec = state["stages"][sbs.APPROVAL_KEY]
    assert rec["state"] == "approved"
    assert rec["by"] == "amitai"
    assert rec["at"]
    assert "תבנה מהטראקים" in rec["quote"]
    plan = sbs.decide(ep, state)
    assert plan["method"] == sbs.VIA_TRACKS
    assert plan["allowed"] is True
    assert plan["needs_approval"] is False
    assert plan["fallback_pending"] is False
    assert plan["approval"]["by"] == "amitai"
    touch(ep / "riverside/amitai.mp4", b"L")
    touch(ep / "riverside/nadav.mp4", b"R")
    built = sbs.build_from_tracks(ep, "riverside/amitai.mp4", "riverside/nadav.mp4", dry_run=True)
    assert built["via"] == sbs.VIA_TRACKS
    assert built["approved_by"] == "amitai"
    assert built["approved_at"] == rec["at"]
    assert "תבנה מהטראקים" in built["quote"]
    assert not (ep / sbs.MASTER_REL).exists()  # dry-run does not write the master


def test_approve_refused_until_the_native_export_has_failed(tmp_path, capsys):
    ep = started(tmp_path)
    assert pl.main(["waive", str(ep), "main.riverside", "--by",
                    "Amitai 10:05: בלי ריברסייד, הקבצים אצלי"]) == 0
    capsys.readouterr()
    assert pl.main(["approve", str(ep), "main", "sbs_fallback_ok", "--by",
                    "Amitai 11:00: תבנה מהטראקים"]) == 1
    err = capsys.readouterr().err
    assert "export failed" in err.lower() or "sbs_master.py export-failed" in err


def test_intake_accepts_native_export_master_without_approval(tmp_path):
    ep = started(tmp_path)
    assert pl.main(["waive", str(ep), "main.riverside", "--by",
                    "Amitai 10:05: בלי ריברסייד, הקבצים אצלי"]) == 0
    touch(ep / "riverside/side-by-side.mp4", b"sbs-export")
    sbs.commit_export(ep, "riverside/side-by-side.mp4")
    touch(ep / "extras/investing-bros-episode-raw-untrimmed.m4a", "raw")
    assert pl.main(["advance", str(ep), "main", "intake"]) == 0
    data = (ps.load(ep)["stages"]["main.intake"].get("outputs") or {})
    assert sbs.RECORD_REL in data
    assert sbs.MASTER_REL in data


def test_intake_blocks_track_built_master_without_approval(tmp_path):
    ep = started(tmp_path)
    assert pl.main(["waive", str(ep), "main.riverside", "--by",
                    "Amitai 10:05: בלי ריברסייד, הקבצים אצלי"]) == 0
    sbs.record_export_failed(ep, FAIL)
    # Forge a track-built master record without going through build-from-tracks.
    touch(ep / sbs.MASTER_REL, b"composed")
    sbs.save_record(ep, {"via": sbs.VIA_TRACKS, "status": sbs.STATUS_READY, "path": sbs.MASTER_REL})
    touch(ep / "extras/investing-bros-episode-raw-untrimmed.m4a", "raw")
    assert pl.main(["advance", str(ep), "main", "intake"]) == 1
    assert "sbs_fallback_ok" in (ps.load(ep)["events"][-1].get("detail") or "")


def test_intake_allows_track_built_master_with_approval(tmp_path):
    ep = started(tmp_path)
    assert pl.main(["waive", str(ep), "main.riverside", "--by",
                    "Amitai 10:05: בלי ריברסייד, הקבצים אצלי"]) == 0
    sbs.record_export_failed(ep, FAIL)
    assert pl.main(["approve", str(ep), "main", "sbs_fallback_ok", "--by",
                    "Amitai 11:00: תבנה מהטראקים"]) == 0
    touch(ep / sbs.MASTER_REL, b"composed")
    sbs.save_record(ep, {"via": sbs.VIA_TRACKS, "status": sbs.STATUS_READY, "path": sbs.MASTER_REL,
                         "approved_by": "amitai"})
    touch(ep / "extras/investing-bros-episode-raw-untrimmed.m4a", "raw")
    assert pl.main(["advance", str(ep), "main", "intake"]) == 0


def test_verify_requires_a_record_when_the_mp4_exists(tmp_path):
    ep = started(tmp_path)
    touch(ep / sbs.MASTER_REL, b"mystery")
    probs = sbs.verify_master(ep)
    assert probs and "commit-export" in probs[0]
    # audio-only intake still has nothing to verify
    (ep / sbs.MASTER_REL).unlink()
    touch(ep / "extras/investing-bros-episode-raw-untrimmed.m4a", "raw")
    assert sbs.verify_master(ep) == []


def test_next_does_not_ask_for_fallback_approval_on_the_native_path(tmp_path, capsys):
    ep = started(tmp_path)
    assert pl.main(["waive", str(ep), "main.riverside", "--by",
                    "Amitai 10:05: בלי ריברסייד, הקבצים אצלי"]) == 0
    capsys.readouterr()
    assert pl.main(["next", str(ep), "--json"]) == 0
    main = next(r for r in json.loads(capsys.readouterr().out) if r["track"] == "main")
    assert main["stage"] == "intake"
    assert "sbs_fallback_ok" not in main.get("approvals", [])
    sbs.record_export_failed(ep, FAIL)
    assert pl.main(["next", str(ep), "--json"]) == 0
    main = next(r for r in json.loads(capsys.readouterr().out) if r["track"] == "main")
    assert "sbs_fallback_ok" in main.get("approvals", []) or "sbs_fallback_ok" in main.get("command", "")
