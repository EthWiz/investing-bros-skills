"""The Riverside pull: owner message, temporary polling routine, browser dashboard only."""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import pipeline as pl  # noqa: E402
import pipeline_state as ps  # noqa: E402
import riverside_tracks as rt  # noqa: E402

T0 = datetime(2026, 11, 6, 18, 0, tzinfo=timezone.utc)
AM = "Amitai 18:00: הפרק הוקלט"
NA = "Nadav 18:00: הפרק הוקלט"
DUR = 30.0


def own(ep: Path, name="amitai"):
    p = ep / "extras" / "pipeline.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text(json.dumps({"schema_version": 1, "episode": 11, "owner": {"name": name}}), encoding="utf-8")
    return ep


def files_for(ep: Path, rows):
    """rows: (rel, payload). Returns a ready listing."""
    tracks = []
    for rel, speaker, part, kind, payload in rows:
        path = ep / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        tracks.append({"speaker": speaker, "part": part, "kind": kind, "quality": "high", "status": "ready",
                       "path": rel, "bytes": len(payload), "duration_s": DUR})
    return {"participants": ["Amitai", "Nadav"], "tracks": tracks}


def split_rows():
    return [
        ("riverside/amitai-1-video.mp4", "Amitai", 1, "video", b"av1"),
        ("riverside/amitai-1-audio.wav", "Amitai", 1, "audio", b"aa1-bytes"),
        ("riverside/amitai-2-video.mp4", "Amitai", 2, "video", b"av2"),
        ("riverside/amitai-2-audio.wav", "Amitai", 2, "audio", b"aa2"),
        ("riverside/nadav-1-video.mp4", "Nadav", 1, "video", b"nv1"),
        ("riverside/nadav-1-audio.wav", "Nadav", 1, "audio", b"na1"),
    ]


def arm(ep, every=15, by=AM, now=T0):
    own(ep)
    return rt.begin(ep, "פרק 11", by, every=every, now=now)


def test_interval_is_about_15_and_only_10_to_20():
    assert rt.POLL_DEFAULT_MIN == 15
    assert rt.interval_minutes(10) == 10 and rt.interval_minutes(20) == 20
    for bad in (9, 21, 0, 1):
        with pytest.raises(ValueError):
            rt.interval_minutes(bad)


def test_owner_message_arms_once_and_does_not_reset(tmp_path):
    m = arm(tmp_path)
    assert m["armed_by"] == AM and m["interval_minutes"] == 15 and m["via"] == "browser"
    assert m["drive_upload"] is False and m["status"] == "waiting"
    again = rt.begin(tmp_path, "other", AM, every=10, now=T0 + timedelta(hours=1))
    assert again["started_at"] == m["started_at"] and again["interval_minutes"] == 15
    assert again["project"] == "פרק 11"
    own_nadav = tmp_path / "other"
    own(own_nadav, "nadav")
    with pytest.raises(ValueError):
        rt.begin(own_nadav, "פרק 11", AM, now=T0)
    assert rt.begin(own_nadav, "פרק 11", NA, now=T0)["armed_by"] == NA


def test_no_message_and_no_pipeline_do_not_arm(tmp_path):
    with pytest.raises(ValueError):
        rt.begin(tmp_path, "פרק 11", AM, now=T0)
    own(tmp_path)
    with pytest.raises(ValueError):
        rt.begin(tmp_path, "פרק 11", "  ", now=T0)


def test_first_check_is_now_then_the_routine_waits(tmp_path):
    arm(tmp_path, every=15)
    first = rt.due(tmp_path, T0)
    assert first["action"] == "check" and first["disarm"] is False
    recorded = rt.checked(tmp_path, T0)
    assert recorded["action"] == "scheduled" and recorded["disarm"] is False
    assert recorded["next_check_at"] == rt.iso(T0 + timedelta(minutes=15))
    early = rt.due(tmp_path, T0 + timedelta(minutes=14))
    assert early["action"] == "wait" and early["disarm"] is False
    refused = rt.checked(tmp_path, T0 + timedelta(minutes=14))
    assert refused["error"] and rt.load(tmp_path)["last_check_at"] == rt.iso(T0)
    nxt = rt.due(tmp_path, T0 + timedelta(minutes=15))
    assert nxt["action"] == "check" and nxt["disarm"] is False


def test_ten_and_twenty_minute_gaps_are_the_edges(tmp_path):
    arm(tmp_path, every=10)
    rt.checked(tmp_path, T0)
    assert rt.due(tmp_path, T0 + timedelta(minutes=10))["action"] == "check"
    arm(tmp_path / "slow", every=20)
    rt.checked(tmp_path / "slow", T0)
    assert rt.due(tmp_path / "slow", T0 + timedelta(minutes=19))["action"] == "wait"
    assert rt.due(tmp_path / "slow", T0 + timedelta(minutes=20))["action"] == "check"


def test_six_hours_gives_up_and_disarms(tmp_path):
    arm(tmp_path)
    rt.checked(tmp_path, T0)
    almost = rt.due(tmp_path, T0 + timedelta(hours=6) - timedelta(seconds=1))
    assert almost["action"] == "check" and almost["disarm"] is False
    done = rt.due(tmp_path, T0 + timedelta(hours=6))
    assert done["action"] == "give_up" and done["disarm"] is True and "episode owner" in done["alert"]
    assert rt.load(tmp_path)["status"] == "gave_up"
    assert rt.due(tmp_path, T0 + timedelta(hours=7))["disarm"] is True


def test_a_fast_interval_in_the_file_is_refused(tmp_path):
    arm(tmp_path)
    m = rt.load(tmp_path)
    m["interval_minutes"] = 1
    rt.save(tmp_path, m)
    with pytest.raises(ValueError):
        rt.due(tmp_path, T0)


def test_split_session_keeps_every_part_and_checks_size_and_duration(tmp_path, monkeypatch):
    monkeypatch.setattr(rt, "probe_duration", lambda path: DUR)
    arm(tmp_path)
    listing = files_for(tmp_path, split_rows())
    # one part still processing: not ready, and nothing is saved as ready
    pending = json.loads(json.dumps(listing))
    pending["tracks"][2]["status"] = "processing"
    assert any("not a ready" in p for p in rt.commit(tmp_path, pending, T0))
    assert rt.load(tmp_path)["status"] == "waiting"
    assert rt.commit(tmp_path, listing, T0 + timedelta(minutes=20)) == []
    m = rt.load(tmp_path)
    assert m["status"] == "ready" and m["drive_upload"] is False and m["via"] == "browser"
    amitai = next(s for s in m["speakers"] if s["name"] == "Amitai")
    assert [p["part"] for p in amitai["parts"]] == [1, 2]
    assert rt.due(tmp_path, T0 + timedelta(minutes=40))["action"] == "ready"
    assert rt.due(tmp_path, T0 + timedelta(minutes=40))["disarm"] is True
    # a short file fails the size check; a drifted duration fails the tolerance
    bad = json.loads(json.dumps(listing))
    bad["tracks"][0]["bytes"] = 1
    m["status"] = "waiting"
    m["speakers"] = []
    rt.save(tmp_path, m)
    assert any("size" in p for p in rt.commit(tmp_path, bad, T0))
    monkeypatch.setattr(rt, "probe_duration", lambda path: DUR + 1.5)
    assert any("duration" in p for p in rt.commit(tmp_path, listing, T0))
    monkeypatch.setattr(rt, "probe_duration", lambda path: DUR + 0.4)
    assert rt.commit(tmp_path, listing, T0) == []


def test_paths_secrets_and_drive_upload_are_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(rt, "probe_duration", lambda path: DUR)
    arm(tmp_path)
    listing = files_for(tmp_path, split_rows())
    escaped = json.loads(json.dumps(listing))
    escaped["tracks"][0]["path"] = "riverside/../../outside.mp4"
    assert any("riverside/" in p for p in rt.commit(tmp_path, escaped, T0))
    planted = "planted-value-should-not-leak"
    secret = json.loads(json.dumps(listing))
    secret["pass" + "word"] = planted
    problems = rt.commit(tmp_path, secret, T0)
    assert problems and planted not in "\n".join(problems)
    assert planted not in (tmp_path / rt.MANIFEST_REL).read_text(encoding="utf-8")
    assert rt.commit(tmp_path, listing, T0) == []
    m = rt.load(tmp_path)
    m["drive_upload"] = True
    rt.save(tmp_path, m)
    assert any("Drive" in p for p in rt.verify_episode(tmp_path))
    m["drive_upload"] = False
    m["via"] = "export"
    rt.save(tmp_path, m)
    assert any("browser" in p for p in rt.verify_episode(tmp_path))


def test_script_does_not_loop_or_offer_another_pull_path():
    text = Path(rt.__file__).read_text(encoding="utf-8").lower()
    assert "time.sleep" not in text and "while true" not in text
    assert "connector" not in text and "mcp" not in text
    assert rt.SIGN_IN_URL == "https://riverside.fm"
    assert rt.STUDIO_ORIGIN == "https://riverside.com"
    assert "delete" not in rt.COMMANDS
    with pytest.raises(ValueError):
        rt.refuse_destructive("delete the studio recording")
    rt.refuse_destructive("delete or disable the temporary polling routine")
    assert rt.probe_duration(Path("/tmp/does-not-exist-riverside.mp4")) is None


def test_cli_arms_and_does_not_print_a_secret(tmp_path, capsys):
    own(tmp_path)
    assert rt.main(["begin", str(tmp_path), "--project", "פרק 11", "--by", AM,
                    "--every", "15", "--now", rt.iso(T0)]) == 0
    out = capsys.readouterr().out
    assert "action: armed" in out and "interval_minutes: 15" in out
    assert rt.main(["begin", str(tmp_path), "--project", "פרק 11", "--by", AM,
                    "--every", "10", "--now", rt.iso(T0)]) == 0
    assert "already_armed" in capsys.readouterr().out
    assert rt.main(["due", str(tmp_path), "--now", rt.iso(T0)]) == 0
    assert "disarm: false" in capsys.readouterr().out
    listing = tmp_path / "listing.json"
    body = {"tracks": []}
    body["pass" + "word"] = "planted-value-should-not-leak"
    listing.write_text(json.dumps(body), encoding="utf-8")
    assert rt.main(["commit", str(tmp_path), "--listing", str(listing), "--now", rt.iso(T0)]) == 1
    err = capsys.readouterr().err
    assert "planted-value-should-not-leak" not in err
    assert rt.main(["due", str(tmp_path), "--now", rt.iso(T0 + timedelta(hours=6))]) == 1
    gave = capsys.readouterr().out
    assert "disarm: true" in gave and "episode owner" in gave


def test_advance_records_tracks_and_a_changed_file_goes_stale(tmp_path, monkeypatch):
    monkeypatch.setattr(rt, "probe_duration", lambda path: DUR)
    ep = tmp_path
    assert pl.main(["start", str(ep), "--episode", "11", "--owner", "amitai", "--by", AM]) == 0
    rt.begin(ep, "פרק 11", AM, now=T0)
    assert rt.commit(ep, files_for(ep, split_rows()), T0) == []
    assert pl.main(["advance", str(ep), "main", "riverside"]) == 0
    data = ps.load(ep)["stages"]["main.riverside"]["data"]
    assert data["via"] == "browser" and data["drive_upload"] is False
    assert data["armed_by"] == AM and data["interval_minutes"] == 15
    amitai = [t for t in data["tracks"] if t["speaker"] == "Amitai"]
    assert {t["part"] for t in amitai} == {1, 2}
    assert len(amitai) == 4
    (ep / "riverside/amitai-2-audio.wav").write_bytes(b"changed")
    assert ps.evaluate(ep, ps.load(ep))["main.riverside"]["status"] == "stale"
    cmd = pl.RIVERSIDE_CMD.lower()
    assert "connector" not in cmd and "mcp" not in cmd
    assert "15 minutes" in pl.RIVERSIDE_CMD and "10-20" in pl.RIVERSIDE_CMD
    assert "polling routine" in pl.RIVERSIDE_CMD and "6 hours" in pl.RIVERSIDE_CMD
