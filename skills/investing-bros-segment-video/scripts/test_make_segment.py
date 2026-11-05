"""make_segment.py: raw-transcript ranges map to the right source passage (raw master or the assembled
episode with its teaser + intro offset), episode cuts are refused unless allowed, and the package and its
record are written from the show's own scripts (faked here; render_cuts/verify_sync have their own tests)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import make_segment as ms  # noqa: E402

EDIT = {"start": 12.0, "end": 2700.0, "cuts": [[1605.0, 1645.2]]}   # episode 8: the courier call
OFFSET = 62.375                                                      # teaser + intro


def test_selection_after_an_internal_cut_maps_into_the_assembled_episode():
    p = ms.plan_segment(EDIT, (1800.0, 2200.0), source_type="assembled", offset=OFFSET)
    # edited time = raw - start - the 40.2 s cut before it; + the teaser/intro offset
    assert p["source_start"] == pytest.approx(OFFSET + 1800.0 - 12.0 - 40.2)
    assert p["source_end"] == pytest.approx(OFFSET + 2200.0 - 12.0 - 40.2)
    assert p["source_cuts"] == [] and p["length"] == 400.0


def test_the_same_selection_from_the_raw_master_is_raw_time():
    p = ms.plan_segment(EDIT, (1800.0, 2200.0), source_type="raw")
    assert (p["source_start"], p["source_end"]) == (1800.0, 2200.0)


def test_crossing_an_episode_cut_is_refused_unless_allowed():
    with pytest.raises(ms.Refused, match="crosses"):
        ms.plan_segment(EDIT, (1500.0, 1900.0), source_type="assembled", offset=OFFSET)
    raw = ms.plan_segment(EDIT, (1500.0, 1900.0), source_type="raw", allow_cut=True)
    assert raw["source_cuts"] == [[1605.0, 1645.2]]                       # removed from the segment too
    assert raw["raw_ranges"] == [[1500.0, 1605.0], [1645.2, 1900.0]]
    asm = ms.plan_segment(EDIT, (1500.0, 1900.0), source_type="assembled", offset=OFFSET, allow_cut=True)
    assert asm["source_cuts"] == []                                        # already gone from the episode
    assert asm["source_end"] - asm["source_start"] == pytest.approx(400.0 - 40.2)


def test_range_inside_a_cut_or_outside_the_episode_is_refused():
    with pytest.raises(ms.Refused, match="inside the episode cut"):
        ms.plan_segment(EDIT, (1620.0, 1900.0), source_type="raw", allow_cut=True)
    with pytest.raises(ms.Refused, match="outside the episode"):
        ms.plan_segment(EDIT, (5.0, 300.0), source_type="raw")


def test_drops_map_to_source_seconds():
    p = ms.plan_segment(EDIT, (1800.0, 2200.0), drops=[(1900.0, 1930.5)], source_type="assembled", offset=OFFSET)
    base = OFFSET - 12.0 - 40.2
    assert p["source_cuts"] == [[pytest.approx(base + 1900.0), pytest.approx(base + 1930.5)]]
    assert p["raw_ranges"] == [[1800.0, 1900.0], [1930.5, 2200.0]] and p["length"] == pytest.approx(369.5)
    with pytest.raises(ms.Refused, match="inside the range"):
        ms.plan_segment(EDIT, (1800.0, 2200.0), drops=[(2190.0, 2210.0)])


def test_loudness_gain_is_held_under_the_true_peak():
    assert ms.gain_db(-16.2, -3.0) == 0.0
    assert ms.gain_db(-19.0, -4.0) == 2.5            # +3 would put the peak at -1.0
    assert ms.gain_db(-13.0, -0.5) == -3.0
    assert ms.parse_loudness("  I:         -17.1 LUFS\n  Peak:        -2.3 dBFS\n") == (-17.1, -2.3)


def test_final_check_points_avoid_the_nudge():
    pts = ms.check_points(420.0)
    assert pts[0] == 5.0 and not [p for p in pts if 28 <= p <= 37] and pts[-1] == 415.0


def episode(tmp_path):
    (tmp_path / "extras").mkdir()
    (tmp_path / "extras/edit.json").write_text(json.dumps(EDIT), encoding="utf-8")
    for n, text in (("title.txt", "זהב: מה באמת מגבה את הכסף שלך?"), ("desc.txt", "תיאור"), ("thumb.jpg", "jpg")):
        (tmp_path / n).write_text(text, encoding="utf-8")
    return tmp_path


class FakeRun:
    def __init__(self, sync=True):
        self.cmds, self.sync = [], sync

    def __call__(self, cmd, log=None):
        self.cmds.append(cmd)
        name = Path(cmd[1]).name if cmd[0] == sys.executable else cmd[0]
        if name == "ffmpeg" and "-filter_complex" in cmd:
            Path(cmd[-1]).write_bytes(b"final")
            return 0, ""
        if name == "ffmpeg":
            return 0, "I: -17.0 LUFS\nPeak: -4.0 dBFS\n"
        if name == "ffprobe":
            return 0, "400.0\n"
        if name == "render_cuts.py":
            return 0, "wrote"
        if name == "verify_sync.py":
            return (0, "SYNC OK") if self.sync else (1, "SYNC FAILED")
        raise AssertionError(cmd)


def args(ep, *extra):
    return [str(ep), "--slot", "01", "--type", "צלילה", "--topic", "זהב", "--range", "1800-2200",
            "--source", str(ep / "video/פרק-8-וידאו.mp4"), "--source-type", "assembled", "--offset", str(OFFSET),
            "--title-file", str(ep / "title.txt"), "--description-file", str(ep / "desc.txt"),
            "--thumb", str(ep / "thumb.jpg"), *extra]


def test_package_and_record(tmp_path):
    ep = episode(tmp_path)
    fake = FakeRun()
    assert ms.main(args(ep), runner=fake) == 0
    seg = ep / "segments"
    assert sorted(p.name for p in seg.iterdir()) == sorted(
        ["סגמנט-01-צלילה-זהב.mp4", "סגמנט-01-צלילה-זהב.txt", "סגמנט-01-צלילה-זהב-thumb.jpg", "youtube-סגמנט-01.md"])
    rec = json.loads((ep / "extras/segment-01.json").read_text(encoding="utf-8"))
    assert rec["sync"] == rec["sync_final"] == "SYNC OK" and rec["raw_ranges"] == [[1800.0, 2200.0]]
    assert rec["source_start"] == pytest.approx(OFFSET + 1800 - 12 - 40.2) and rec["edit"] == EDIT
    assert rec["output"] == "segments/סגמנט-01-צלילה-זהב.mp4" and rec["loudness"]["gain_db"] == 1.0
    render = next(c for c in fake.cmds if Path(c[1]).name == "render_cuts.py")
    assert render[render.index("--start") + 1] == f"{rec['source_start']}"
    burn = next(c for c in fake.cmds if "-filter_complex" in c)
    assert "volume=1.0dB" in burn and "between(t,30.0,35.0)" in " ".join(burn)


def test_refuses_a_second_final_video_for_the_slot_and_unsynced_cuts(tmp_path):
    ep = episode(tmp_path)
    (ep / "segments").mkdir()
    (ep / "segments/סגמנט-01-צלילה-ישן.mp4").write_bytes(b"old")
    assert ms.main(args(ep), runner=FakeRun()) == 1
    (ep / "segments/סגמנט-01-צלילה-ישן.mp4").unlink()
    assert ms.main(args(ep), runner=FakeRun(sync=False)) == 1
    assert not (ep / "extras/segment-01.json").exists()


def test_segment_01_is_the_deep_dive_and_assembled_needs_an_offset(tmp_path):
    ep = episode(tmp_path)
    a = args(ep)
    a[a.index("צלילה")] = "רעיון"
    assert ms.main(a, runner=FakeRun()) == 1
    a = args(ep)
    i = a.index("--offset")
    del a[i:i + 2]
    assert ms.main(a, runner=FakeRun()) == 1


def test_dry_run_prints_the_plan(tmp_path, capsys):
    ep = episode(tmp_path)
    assert ms.main(args(ep, "--dry-run"), runner=FakeRun()) == 0
    out = capsys.readouterr().out
    assert "render_cuts.py" in out and "verify_sync.py" in out and not (ep / "segments").exists()
