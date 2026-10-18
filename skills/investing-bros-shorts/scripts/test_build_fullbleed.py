"""Tests for build_fullbleed.py. Run: python3 -m pytest skills/investing-bros-shorts/scripts"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from build_fullbleed import (build_ass, build_command, check_pieces, check_text, endcard_warnings,  # noqa: E402
                             pacing_warnings)
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
    assert "בפרק 7 המלא" in ass and "\\p1}m 0 0" in ass                # end card with dim


def test_reaction_cut_and_high_res_tracks():
    cfg = dict(CFG, base="R", shots=[[2140.0, 2141.5, "L"]], sources={"L": "amitai.mp4", "R": "nadav.mp4"},
               crop={"L": [656, 0, 1215, 2160]}, audio_source="raw.mp4", pieces=[[2106.02, 2154.45, 0.0]])
    cmd = build_command(cfg, _tl())
    assert cmd.count(" -i ") == 5                                       # 3 videos/audio + gradient + logo
    assert cmd.count(" -ss ") == 3                                      # in source order: one window per file
    assert "crop=1215:2160:656:0" in cmd and "crop=608:1080:1130:0" in cmd
    assert "enable='between(t,34.000,35.500)'" in cmd                   # 2140.0 - 2106.0


def test_tags_in_gold_box():
    ass = build_ass(dict(CFG, tags=[[2106.05, 2109.5, "נדב רסקין"]]), _tl(), CHUNKS)
    assert any(",Tag," in l and "נדב רסקין" in l for l in ass.splitlines())


def test_episode_badge_runs_from_hook_end_to_end_card():
    ass = build_ass(CFG, _tl(), CHUNKS)
    badge = [l for l in ass.splitlines() if ",Badge," in l]
    assert len(badge) == 1 and "מתוך פרק 7" in badge[0]
    assert badge[0].startswith("Dialogue: 4,0:00:02.70,0:00:45.")      # 2.7 s -> 48.4 - 2.8 s


def test_last_line_stays_captioned_above_the_end_card():
    ass = build_ass(CFG, _tl(), CHUNKS)
    caps = [l for l in ass.splitlines() if ",Cap," in l]
    assert all(l.startswith("Dialogue: 7,") for l in caps)                 # above the dim (5) and end text (6)
    assert any(l.split(",")[2] > "0:00:46.00" for l in caps)               # still captioning inside the last 2.8 s
    off = build_ass(dict(CFG, endcard_captions=False), _tl(), CHUNKS)
    assert not any(",Cap," in l and l.split(",")[1] > "0:00:45.70" for l in off.splitlines())


def test_hook_is_readable_on_frame_zero():
    hook = next(l for l in build_ass(CFG, _tl(), CHUNKS).splitlines() if ",Hook," in l)
    assert "\\fscx88" in hook and "\\fad(0," in hook                     # no fade-in, only a small pop


def test_dashes_on_screen_are_errors():
    assert check_text(CFG, CHUNKS) == []
    bad = dict(CFG, endcard=["לפרק המלא \u2014 כאן", "[פרק 7]"])
    assert len(check_text(bad, CHUNKS)) == 1
    assert check_text(dict(CFG, hook=["א \u2013 ב"]), CHUNKS)


def test_payoff_first_pieces_play_in_list_order():
    cfg = dict(CFG, pieces=[[2137.3, 2140.5, 0.0], [2106.02, 2137.3, 0.0]], zooms=[[2110.0, 1.1], [2138.0, 1.12]])
    tl = Timeline([p[:3] for p in cfg["pieces"]], 24)
    cmd = build_command(cfg, tl)
    # the payoff piece gets its own seek: one window for both would buffer 30 s of decoded frames (OOM)
    assert cmd.index("-ss 2136.292") < cmd.index("-ss 2105.000")
    assert "[v0_0]trim=start=1.0000:end=4.2083" in cmd                     # plays first, from its own input
    assert "[v1_0]trim=start=1.0000:end=32.2917" in cmd
    z = cmd.split("zoompan=z='")[1].split("'")[0]
    assert z.startswith("if(gte(it,7.208),1.1,")                           # 2110.0 plays at 3.2 + 4.0 s: outermost
    assert check_pieces(tl) == []
    assert check_pieces(Timeline([[10, 20], [15, 25]], 24))                # overlapping source time


def test_pacing_and_end_card_warnings():
    w = pacing_warnings(CFG, _tl())
    assert len(w) == 1 and "19.6-30.1" in w[0]                             # ep7: 10.5 s with no visual change
    assert endcard_warnings(CFG) == []
    assert endcard_warnings(dict(CFG, endcard=["רק שורה אחת"]))
    assert endcard_warnings(dict(CFG, endcard=["שורה ארוכה מדי בשביל כרטיס הסיום הזה", "[פרק 7]"]))
