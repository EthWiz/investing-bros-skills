"""verify_sync.py pure helpers."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent))
import verify_sync as vs  # noqa: E402


def test_to_source_after_cuts():
    plan = vs.load_plan(cuts=[(10.0, 12.0), (30.0, 40.0)])
    assert vs.to_source(5, plan) == 5
    assert vs.to_source(10.5, plan) == pytest.approx(12.5)
    assert vs.to_source(29, plan) == pytest.approx(41)  # second cut sits at edited 28


def test_points_cover_before_between_after_and_end():
    plan = vs.load_plan(cuts=[(48.5, 49.3), (80.5, 155.0)])
    pts = vs.check_points(plan, 300.0)
    ats = [c["at"] for c in plan["cuts"]]
    assert any(p < ats[0] for p in pts)
    assert any(ats[0] < p < ats[1] for p in pts)
    assert any(p > ats[1] for p in pts)
    assert max(pts) > 290
    for p in pts:  # clear of every transition
        assert all(not (a - 3.5 < p < a + 1.5) for a in ats)


def test_long_region_gets_several_points():
    pts = vs.check_points(vs.load_plan(), 2797.0)
    assert len(pts) >= 8


def test_xcorr_finds_the_offset():
    rng = np.random.default_rng(0)
    ref = rng.standard_normal(8 * vs.SR)
    seg = ref[int(3.25 * vs.SR):int(5.25 * vs.SR)]
    pos, corr = vs.xcorr_offset(ref, seg)
    assert pos == pytest.approx(3.25, abs=1 / vs.SR)
    assert corr == pytest.approx(1.0, abs=1e-6)


def test_xcorr_score_stays_bounded_next_to_silence():
    rng = np.random.default_rng(1)
    ref = np.concatenate([np.zeros(4 * vs.SR), rng.standard_normal(4 * vs.SR)])
    seg = rng.standard_normal(2 * vs.SR) * 1e-3
    _, corr = vs.xcorr_offset(ref, seg)
    assert corr <= 1.0 + 1e-6


def test_best_shift_and_static_detection():
    rng = np.random.default_rng(2)
    ref = rng.uniform(0, 255, (54, 36, 64))
    shift, err, nxt = vs.best_shift(ref, ref[5:53], pad=3)  # 2 frames late
    assert shift == 2 and err == 0 and not vs.is_static(err, nxt)
    still = np.full((54, 36, 64), 100.0)
    s2, e2, n2 = vs.best_shift(still, still[3:51], pad=3)
    assert vs.is_static(e2, n2)


def _row(t, a=True, v=True, static=False):
    return {"t": t, "ok_a": a, "ok_v": v, "static": static, "ok": a and v}


def test_nothing_measured_fails():
    fails, _ = vs.coverage([], vs.load_plan(cuts=[(10.0, 12.0)]))
    assert fails == ["no points were measured"]
    # only skipped (silent) rows is not a pass either
    fails, _ = vs.coverage([{"t": 3, "src": 3, "error": "silent", "skip": True}], vs.load_plan())
    assert fails


def test_every_kept_region_needs_sound_and_moving_picture():
    plan = vs.load_plan(cuts=[(10.0, 12.0), (30.0, 40.0)])  # cuts at body 10 and 28
    full = [_row(5), _row(15), _row(35)]
    assert vs.coverage(full, plan) == ([], [])
    # region 2 only has a still picture: fails, or warns with --allow-static
    rows = [_row(5), _row(15, static=True), _row(35)]
    fails, warns = vs.coverage(rows, plan)
    assert len(fails) == 1 and "region 2" in fails[0] and "moving picture" in fails[0]
    fails, warns = vs.coverage(rows, plan, allow_static=True)
    assert not fails and len(warns) == 1
    # region 3 has no point at all
    fails, _ = vs.coverage([_row(5), _row(15)], plan)
    assert len(fails) == 1 and "region 3" in fails[0]


def test_coverage_uses_body_time_with_an_offset():
    plan = vs.load_plan(cuts=[(10.0, 12.0)])
    rows = [_row(20 + 5), _row(20 + 15)]  # 20 s cold open + intro before the body
    assert vs.coverage(rows, plan, offset=20)[0] == []
    assert vs.coverage(rows, plan)[0]  # without the offset both land after the cut


def test_planned_duration_is_checked():
    plan = vs.load_plan(cuts=[(10.0, 12.0)], start=0.0, end=100.0)
    assert plan["duration"] == pytest.approx(98.0)
    assert vs.duration_errors(98.0, 98.01, 24, plan["duration"]) == []
    errs = vs.duration_errors(96.0, 96.0, 24, plan["duration"])  # a cut 2 s too long
    assert len(errs) == 1 and "plan expects" in errs[0]
    assert vs.duration_errors(98.0, 97.5, 24, plan["duration"])  # streams end apart
    # assembled: 20 s before the body, 20 s outro after it
    assert vs.duration_errors(138.0, 138.0, 24, 98.0, offset=20, body_end=118.0) == []
    assert vs.duration_errors(138.0, 138.0, 24, 98.0, offset=20, body_end=117.0)
    assert vs.duration_errors(138.0, 138.0, 24, 98.0, offset=20)  # outro not declared


def test_plan_file_duration_is_read():
    p = {"start": 0.0, "end": 50.0, "cuts": [{"out": 10, "in": 11, "removed": 1.0, "at": 10}]}
    assert vs.load_plan(p)["duration"] == pytest.approx(49.0)
    p["duration"] = 49.0
    assert vs.load_plan(p)["duration"] == 49.0
