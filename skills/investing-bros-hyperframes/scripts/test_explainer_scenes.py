"""Regression checks for explanatory motion, source timing, and safe graphics."""
import json
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from build_composition import build


def scenes():
    return [
        {"type":"money_roles", "start":102, "end":118, "kicker":"אם קל למצוא זהב",
         "trade_label":"מסחר", "save_label":"חיסכון", "conclusion":"מסחר ≠ שימור ערך",
         "abundant_at":103, "save_at":106, "trade_at":110, "conclusion_at":115},
        {"type":"coin_dilution", "start":102, "end":118, "kicker":"דילול מטבע",
         "before_label":"מטבע זהב", "after_label":"מטבע עם סגסוגת", "metal_label":"מתכות זולות",
         "conclusion":"פחות זהב במטבע", "mix_at":106, "conclusion_at":112},
        {"type":"currency_trust", "start":102, "end":118, "kicker":"מה יש לי בכיס?",
         "value":500, "bank_label":"הבנק הפדרלי", "trust_label":"אמון", "conclusion":"הדולר נשען על אמון",
         "amount_at":103, "bank_at":105, "bank_label_at":107, "trust_at":108, "conclusion_at":112},
    ]


@pytest.mark.parametrize("card", scenes())
def test_scene_shows_a_source_timed_mechanism_without_external_assets(card):
    index, files, storyboard, _ = build({"pieces":[[100,120]],"fps":24,"layout":"overlay",
                                         "panel_scale":0.84,"panel_left":20,"panel_top":280,"cards":[card]})
    assert len(files) == 1 and storyboard["cards"][0]["type"] == card["type"]
    assert "scale:0.84" in index and "left:20px;top:280px" in index
    assert "https://" not in index
    assert "http://" not in index.replace("http://www.w3.org/2000/svg", "")
    assert "<svg" in files["c1"] and "<radialGradient" in files["c1"]
    assert "strokeDashoffset" in index                         # a connection is visibly drawn
    assert card["conclusion"] in index
    assert "%" not in re.sub(r"<[^>]*>|\{[^}]*\}", "", files["c1"])
    if card["type"] == "money_roles":
        assert "#c1-save-cross" in index and "#c1-payment" in index
        assert '"x": 185' in index and '"strokeDashoffset": 0' in index
    elif card["type"] == "coin_dilution":
        assert "#c1-mixture" in index and "#c1-filing5" in index
        assert "#c1-mixture'" in index and '"opacity": 1' in index
        assert "½" not in files["c1"] and "50%" not in files["c1"]
    else:
        assert "$500" in index and "#c1-trust-line" in index and "#c1-bank-light" in index
        assert '"cx": 608' in index
        assert "top:78px" in index                           # total above cash, not a fake denomination


def test_empty_or_end_only_composition_cannot_pass_as_an_animated_short():
    for cards in ([], [{"type":"end", "start":118, "end":120, "lines":["סיום"]}]):
        with pytest.raises(ValueError, match="informative HyperFrames animation"):
            build({"pieces":[[100,120]],"cards":cards})


def test_scene_keeps_hypothesis_and_maps_after_internal_cut():
    card = scenes()[0]
    card.update(start=110, end=118, abundant_at=110.2, save_at=111, trade_at=113, conclusion_at=116)
    index, _, sb, _ = build({"pieces":[[100,105],[110,120]],"cards":[card],"layout":"overlay"})
    assert sb["cards"][0]["startSec"] == 5
    assert "אם קל למצוא זהב" in index
    assert "#c1-save-cross'" in index and ",6.0);" in index


def test_trust_amount_must_be_a_positive_spoken_number():
    card = dict(scenes()[2], value="made up")
    with pytest.raises(ValueError, match="positive spoken amount"):
        build({"pieces":[[100,120]],"cards":[card]})
