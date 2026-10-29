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
