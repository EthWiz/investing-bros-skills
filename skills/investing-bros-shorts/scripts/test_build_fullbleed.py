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


def test_reaction_cut_and_high_res_tracks():
    cfg = dict(CFG, base="R", shots=[[2140.0, 2141.5, "L"]], sources={"L": "amitai.mp4", "R": "nadav.mp4"},
               crop={"L": [656, 0, 1215, 2160]}, audio_source="raw.mp4", pieces=[[2106.02, 2154.45, 0.0]])
    cmd = build_command(cfg, _tl())
    assert cmd.count(" -i ") == 5                                       # 3 videos/audio + gradient + logo
    assert "crop=1215:2160:656:0" in cmd and "crop=608:1080:1130:0" in cmd
    assert "enable='between(t,34.000,35.500)'" in cmd                   # 2140.0 - 2106.0


def test_tags_in_gold_box():
    ass = build_ass(dict(CFG, tags=[[2106.05, 2109.5, "נדב רסקין"]]), _tl(), CHUNKS)
    assert any(",Tag," in l and "נדב רסקין" in l for l in ass.splitlines())


def test_without_endcard_keeps_final_spoken_caption():
    cfg = dict(CFG)
    cfg.pop("endcard")
    ass = build_ass(cfg, _tl(), CHUNKS)
    assert any(",Cap," in line and "לעתיד." in line for line in ass.splitlines())
    assert ",Dim," not in ass and ",End," not in ass


def test_safe_caption_and_face_framing_can_be_configured():
    cfg = dict(CFG, caption_x=480, caption_y=1430, hook_y=360, video_offset_y=160)
    ass = build_ass(cfg, _tl(), CHUNKS)
    assert "\\pos(480,1430)" in ass and "\\pos(540,360)" in ass
    cmd = build_command(cfg, _tl())
    assert "pad=1080:2080:0:0:color=black,crop=1080:1920:0:160[framed]" in cmd
    assert "[framed][gr]overlay=0:0" in cmd


def test_excessive_framing_offset_is_rejected():
    import pytest
    with pytest.raises(ValueError, match="video_offset_y"):
        build_command(dict(CFG, video_offset_y=1920), _tl())


def test_host_specific_offset_leaves_each_face_in_its_safe_position():
    cfg = dict(CFG, base="R", shots=[[2140,2141.5,"L"]], video_offset_y={"L":160,"R":0})
    cmd = build_command(cfg, _tl())
    assert "[VL_offset]pad=1080:2080:0:0:color=black,crop=1080:1920:0:160[VL]" in cmd
    assert "[VR]pad=" not in cmd and "[z]pad=" not in cmd
    assert "[VR][VL]overlay=" in cmd
