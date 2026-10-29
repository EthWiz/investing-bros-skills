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


def _xfade_offsets(g):
    import re
    return [(float(d), float(o)) for d, o in re.findall(r"xfade=transition=fade:duration=([\d.]+):offset=(-?[\d.]+)", g)]


def test_transition_next_to_the_start_is_clamped_not_negative():
    # Codex review: at 24 fps `--cut 0.05-1` gave a negative xfade offset and a
    # picture 83 ms longer than the sound.
    p = rc.plan_cuts([(0.05, 1.0)], Fraction(24), 0.0, 10.0)
    c = p["cuts"][0]
    assert c["vx"] == 0  # only one frame kept before the cut: hard video cut
    assert c["ax"] == pytest.approx(0.05)  # audio crossfade fits the 50 ms kept
    g = rc.filter_graph(p)
    assert "xfade" not in g and "concat=n=2:v=1:a=0[vout]" in g
    for s in p["segments"]:
        assert s["v"][0] >= 0 and s["a"][0] >= 0


@pytest.mark.parametrize("cuts", [[(0.2, 1.0)], [(5.0, 6.0), (6.1, 7.0)], [(1.0, 9.9)], [(0.3, 0.4), (0.5, 0.6)]])
def test_every_xfade_fits_its_inputs(cuts):
    p = rc.plan_cuts(cuts, Fraction(24), 0.0, 10.0)
    segs = p["segments"]
    left = segs[0]["v"][1] - segs[0]["v"][0]
    for k, c in enumerate(p["cuts"]):
        right = segs[k + 1]["v"][1] - segs[k + 1]["v"][0]
        assert c["vx"] <= 0.25 + 1e-9 and c["ax"] <= 0.06 + 1e-9
        assert round(c["vx"] / 2 * 24, 6).is_integer()  # whole frames per side
        if c["vx"]:
            off = c["v_at"] - c["vx"] / 2
            assert off >= -1e-9 and off + c["vx"] <= left + 1e-6 and c["vx"] <= right + 1e-6
        left = left + right - c["vx"]
    assert left == pytest.approx(p["duration"], abs=1e-6)  # picture length == planned length


def test_cuts_that_meet_once_snapped_are_rejected():
    with pytest.raises(ValueError):
        rc.plan_cuts([(5.0, 5.03), (5.03, 6.0)], Fraction(24), 0.0, 10.0)


def _src(tmp_path, dur=40):
    src = tmp_path / "src.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=size=320x180:rate=24:duration={dur}",
                    "-f", "lavfi", "-i", f"anoisesrc=d={dur}:c=pink:r=48000:a=0.3",
                    "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest", str(src)], check=True)
    return src


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_cut_next_to_the_start_keeps_picture_and_sound_equal(tmp_path):
    src = _src(tmp_path, 12)
    out, plan = tmp_path / "out.mp4", tmp_path / "plan.json"
    assert rc.main([str(src), str(out), "--cut", "0.05-1", "--end", "10", "--preset", "ultrafast",
                    "--plan-out", str(plan)]) == 0
    p = json.loads(plan.read_text())
    d, errs = rc.check_output(str(out), p)
    assert not errs
    assert abs(d["video"] - d["audio"]) <= 1 / 24 + 0.03
    assert d["video"] == pytest.approx(p["duration"], abs=1 / 24)
    # the 50 ms before the cut can't be measured: fails unless explicitly allowed
    assert vs.main([str(src), str(out), "--plan", str(plan)]) == 1
    assert vs.main([str(src), str(out), "--plan", str(plan), "--allow-static"]) == 0


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_assembled_body_window_is_verified(tmp_path):
    """A cold open/intro before and an outro after the edited body: --offset/--body-end."""
    src = _src(tmp_path, 30)
    body, plan = tmp_path / "body.mp4", tmp_path / "plan.json"
    assert rc.main([str(src), str(body), "--cut", "10-12", "--end", "28", "--preset", "ultrafast",
                    "--plan-out", str(plan)]) == 0
    ep = tmp_path / "ep.mp4"
    g = ("color=c=navy:s=320x180:r=24:d=4[i];anoisesrc=d=4:c=brown:r=48000:a=0.2[ia];"
         "color=c=red:s=320x180:r=24:d=3[o];anoisesrc=d=3:c=white:r=48000:a=0.2[oa];"
         "[1:v]setsar=1[b];[1:a]aresample=48000[ba];"
         "[i][ia][b][ba][o][oa]concat=n=3:v=1:a=1[v][a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "nullsrc=s=16x16:d=0.1", "-i", str(body),
                    "-filter_complex", g, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "ultrafast",
                    "-c:a", "aac", str(ep)], check=True)
    base = [str(src), str(ep), "--plan", str(plan)]
    assert vs.main(base + ["--offset", "4", "--body-end", "30"]) == 0
    assert vs.main(base) == 1  # without the mapping the intro is taken for the body
    assert vs.main(base + ["--offset", "4.5", "--body-end", "30.5"]) == 1  # wrong offset
