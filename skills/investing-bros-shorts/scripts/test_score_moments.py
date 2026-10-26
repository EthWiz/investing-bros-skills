"""Tests for score_moments.py and the packaging checks in build_short.py."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from build_short import Timeline, check_packaging  # noqa: E402
from score_moments import pace_score, rank, starts_on_filler  # noqa: E402

SEGS = [
    {"start": 0.0, "end": 10.0, "text": " ".join(["מילה"] * 25)},     # 2.5 words/s
    {"start": 10.0, "end": 20.0, "text": " ".join(["מילה"] * 25)},
    {"start": 20.0, "end": 30.0, "text": "אז " + " ".join(["מילה"] * 34)},   # 3.5 words/s
    {"start": 30.0, "end": 60.0, "text": " ".join(["מילה"] * 75)},
]


def cand(start, end, hook, **kw):
    return {"start": start, "end": end, "title": f"c{start}",
            "scores": {"hook": hook, "standalone": 3, "payoff": 3, "friction": 1}, **kw}


def test_rank_orders_by_total_and_flags():
    rows = rank(SEGS, [cand(0, 30, 2), cand(20, 30, 5)])
    assert rows[0]["start"] == 20                       # higher hook and faster pace win
    assert rows[0]["pace"] > rows[1]["pace"]
    assert "filler opener" in rows[0]["flags"]
    assert "9 s after 1.15x" in rows[0]["flags"]         # duration is checked after house speed
    assert rows[1]["flags"] == []


def test_missing_scores_are_an_error():
    with pytest.raises(ValueError):
        rank(SEGS, [{"start": 0, "end": 30, "scores": {"hook": 4}}])


def test_pace_and_filler():
    assert pace_score(0.7) == 1 and pace_score(1.0) == 3 and pace_score(1.3) == 5
    assert starts_on_filler("אז, מה קרה בשוק?") and not starts_on_filler("אסטרואיד אחד יכול")


def test_pieces_may_move_but_not_repeat():
    assert Timeline([[50, 55], [10, 30]], 24).map(52) == pytest.approx(2, abs=0.05)
    with pytest.raises(ValueError):
        Timeline([[20, 25], [10, 30]], 24)


def test_packaging_warnings():
    good = {"hook": ["x"], "endcard": ["בפרק המלא: למה דווקא זהב?", "[אחים להשקעות]"]}
    assert check_packaging(good, 32, "hook") == []
    assert len(check_packaging(good, 52, "hook")) == 1   # over target, under limit
    bad = check_packaging({"endcard": ["לפרק המלא"]}, 70, "hook")
    assert len(bad) == 3                                 # length, no hook, generic end card


def test_candidate_speed_can_be_disabled():
    rows = rank(SEGS, [cand(0, 20, 5)], speed=1.0)
    assert not rows[0]["flags"]
