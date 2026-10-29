"""render_cuts.py: frame-snapped plan and a single-pass graph."""
import json
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import render_cuts as rc  # noqa: E402
import verify_sync as vs  # noqa: E402


def test_episode9_cuts_snap_to_frames():
    p = rc.plan_cuts([(80.5, 155.083333), (48.508333, 49.3)], Fraction(24), 0.0, 375.375)
    c1, c2 = p["cuts"]
    assert (round(c1["v_out"] * 24), round(c1["v_in"] * 24)) == (1164, 1183)
    assert (round(c2["v_out"] * 24), round(c2["v_in"] * 24)) == (1932, 3722)
    for c in p["cuts"]:
        # audio removes exactly the frames the video removes
        assert c["in"] - c["out"] == pytest.approx(c["v_in"] - c["v_out"], abs=1e-6)
        assert c["removed"] * 24 == pytest.approx(round(c["removed"] * 24), abs=1e-6)
    assert p["duration"] == pytest.approx(375.375 - (19 + 1790) / 24, abs=1e-6)
    assert c2["at"] == pytest.approx(80.5 - 19 / 24, abs=1e-6)


def test_overlapping_or_outside_cuts_are_rejected():
    with pytest.raises(ValueError):
        rc.plan_cuts([(10, 20), (15, 30)], 24, 0, 100)
    with pytest.raises(ValueError):
        rc.plan_cuts([(90, 120)], 24, 0, 100)


def test_one_input_one_graph_no_reinit():
    p = rc.plan_cuts([(10, 12)], 25, 0, 60)
    cmd = rc.ffmpeg_cmd("in.mp4", "out.mp4", p)
    assert cmd.count("-i") == 1
    assert cmd[cmd.index("-reinit_filter") + 1] == "0"
    g = cmd[cmd.index("-filter_complex") + 1]
    assert "split=2" in g and "asplit=2" in g
    assert "xfade" in g and "acrossfade" in g
    assert "[vout]" in g and "[aout]" in g


def test_hard_cut_uses_concat():
    p = rc.plan_cuts([(10, 12)], 25, 0, 60, vx=0, ax=0)
    g = rc.filter_graph(p)
    assert "concat=n=2:v=1:a=0[vout]" in g and "concat=n=2:v=0:a=1[aout]" in g


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_render_then_verify_end_to_end(tmp_path):
    src = tmp_path / "src.mp4"
    # moving picture + non-periodic sound so both matches are unambiguous
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=24:duration=40",
                    "-f", "lavfi", "-i", "anoisesrc=d=40:c=pink:r=48000:a=0.3",
                    "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest", str(src)], check=True)
    out, plan = tmp_path / "out.mp4", tmp_path / "plan.json"
    assert rc.main([str(src), str(out), "--cut", "12.3-15.1", "--cut", "25-26", "--end", "38",
                    "--preset", "ultrafast", "--plan-out", str(plan)]) == 0
    p = json.loads(plan.read_text())
    assert vs.main([str(src), str(out), "--plan", str(plan)]) == 0
    # a wrong plan (cut assumed one frame longer) must fail
    p["cuts"][0]["removed"] += 1 / 24
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(p))
    assert vs.main([str(src), str(out), "--plan", str(bad)]) == 1
