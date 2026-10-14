"""Tests for build_fullbleed.py. Run: python3 -m pytest skills/investing-bros-shorts/scripts"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from build_fullbleed import build_ass, build_command  # noqa: E402
from build_short import Timeline  # noqa: E402

REF = os.path.join(os.path.dirname(__file__), "..", "references")
CFG = json.load(open(os.path.join(REF, "ep7-asteroid-fullbleed.json"), encoding="utf-8"))
CHUNKS = json.load(open(os.path.join(REF, CFG["words"]), encoding="utf-8"))


def _tl():
    return Timeline([p[:3] for p in CFG["pieces"]], 24)


def test_zooms_latest_is_outermost():
    cmd = build_command(CFG, _tl())
    z = cmd.split("zoompan=z='")[1].split("'")[0]
    assert z.startswith("if(gte(it,41.250),1.1,")          # 2147.25 - 2106.0
    assert "crop=608:1080:1130:0" in cmd and "channel_layouts=stereo" in cmd and "-g 24" in cmd


def test_ass_highlights_one_word_at_a_time_in_gold_rtl():
    ass = build_ass(CFG, _tl(), CHUNKS)
    caps = [l for l in ass.splitlines() if ",Cap," in l]
    assert caps and all(l.count("&H001FB7F5") == 1 for l in caps)     # exactly one gold word per event
    import re
    assert not any("}" in re.sub(r"\{[^}]*\}", "", l.split(",,", 1)[1]) for l in caps)   # no stray braces on screen
    assert all(l.endswith(",-1") for l in ass.splitlines() if l.startswith("Style:"))
    assert "לפרק המלא" in ass and "\\p1}m 0 0" in ass                  # end card with dim
