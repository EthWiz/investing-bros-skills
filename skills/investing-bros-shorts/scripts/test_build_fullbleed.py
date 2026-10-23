"""Tests for build_fullbleed.py. Run: python3 -m pytest skills/investing-bros-shorts/scripts"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from build_fullbleed import build_ass, build_command, hook_box_problems  # noqa: E402
from build_short import Timeline, ass_time  # noqa: E402

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


def test_speed_changes_video_audio_and_all_overlay_timings():
    tl = Timeline([p[:3] for p in CFG["pieces"]], 24, speed=1.25)
    cmd = build_command(CFG, tl)
    assert cmd.count("setpts=PTS/1.25") >= 1
    assert "atempo=1.25" in cmd
    assert f'-t {tl.duration:.4f} "ep7_asteroid.mp4"' in cmd
    ass = build_ass(CFG, tl, CHUNKS)
    assert ass_time(tl.duration) in ass


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
    assert cmd.count(" -i ") == 6                                       # 3 videos/audio + gradient + logo + hook strips
    assert "crop=1215:2160:656:0" in cmd and "crop=608:1080:1130:0" in cmd
    assert "enable='between(t,34.000,35.500)'" in cmd                   # 2140.0 - 2106.0


def test_tags_in_gold_box():
    ass = build_ass(dict(CFG, tags=[[2106.05, 2109.5, "נדב רסקין"]]), _tl(), CHUNKS)
    assert any(",Tag," in l and "נדב רסקין" in l for l in ass.splitlines())


def test_hook_is_paper_strips_not_a_caption_by_default():
    cmd = build_command(CFG, _tl())
    ass = build_ass(CFG, _tl(), CHUNKS)
    assert '-loop 1 -framerate 24 -t 2.7 -i "ep7_asteroid_hook.png"' in cmd
    assert "fade=t=out:st=2.50:d=0.2:alpha=1" in cmd and "[s][hk]overlay=0:0:eof_action=pass" in cmd
    assert not any(",Hook," in l for l in ass.splitlines() if l.startswith("Dialogue"))


def test_legacy_hook_style_keeps_the_old_ass_hook():
    cfg = dict(CFG, hook_style="legacy")
    assert "_hook.png" not in build_command(cfg, _tl())
    assert any(",Hook," in l and "\\pos(540,700)" in l for l in build_ass(cfg, _tl(), CHUNKS).splitlines())


def test_caption_y_is_configurable_within_bounds():
    import pytest
    ass = build_ass(dict(CFG, caption_y=1460), _tl(), CHUNKS)
    caps = [l for l in ass.splitlines() if ",Cap," in l]
    assert caps and all("\\pos(540,1460)" in l for l in caps)
    with pytest.raises(ValueError):
        build_ass(dict(CFG, caption_y=1600), _tl(), CHUNKS)      # under the platform UI
    with pytest.raises(ValueError):
        build_ass(dict(CFG, hook_y=1100), _tl(), CHUNKS)         # past the centre band


def test_opening_on_a_later_line_seeks_to_the_earliest_piece():
    pieces = [[2140.0, 2150.0, 0.0], [2106.02, 2120.0, 0.0]]
    cmd = build_command(dict(CFG, pieces=pieces, zooms=[[2141.0, 1.12], [2107.0, 1.0]]), Timeline(pieces, 24))
    assert "-ss 2105.000" in cmd                                     # not 2139.0: the second piece is earlier
    assert "trim=start=35.0000" in cmd and "trim=start=1.0000" in cmd
    assert "zoompan=z='if(gte(it,11.000),1.0,if(gte(it,1.000),1.12,1.0))'" in cmd   # ordered by output time


def test_hook_box_keeps_clear_of_logo_and_captions():
    assert hook_box_problems([816, 1105], 1470) == []                 # centred hook, captions at 1470
    assert any("logo" in p for p in hook_box_problems([300, 590], 1470))
    assert any("captions" in p for p in hook_box_problems([816, 1105], 1150))


def test_endcard_arrow_and_bobbing_callout():
    cfg = dict(CFG, endcard_arrow=True, callouts=[{"at": 2120.0, "text": "הקישור לפרק המלא בתיאור", "dur": 2.2,
                                                   "bottom": 1350, "bob": 7, "size": [794, 186]}])
    ass = build_ass(cfg, _tl(), CHUNKS)
    assert any("\\p1}m 20 0 l 40 0" in l and ",End," in l for l in ass.splitlines())   # drawn arrow, no glyph
    cmd = build_command(cfg, _tl())
    assert '-t 2.200 -i "ep7_asteroid_callout0.png"' in cmd and "setpts=PTS+14.000/TB" in cmd
    assert "y='1164+7*sin(2*PI*2.0*(t-14.000))'" in cmd and "[s1]format=yuv420p[v]" in cmd


def test_cover_endcard_callout_hands_over_and_captions_stay():
    from build_fullbleed import callout_windows, endcard_start
    cfg = dict(CFG, endcard_style="cover", endcard_at=2150.0, endcard_captions=True,
               endcard=["האם טסלה תנצח את המרוץ|של נהיגה אוטונומית?", "פרק 1", "הקישור לפרק המלא בתיאור"],
               callouts=[{"before_endcard": 4.0, "text": "הקישור לפרק המלא בתיאור", "bottom": 1350, "bob": 7,
                          "size": [794, 186]}])
    tl = _tl()
    e0 = endcard_start(cfg, tl)
    assert abs(e0 - tl.map(2150.0)) < 1e-9
    (w0, w1), = callout_windows(cfg, tl)
    assert abs(w0 - (e0 - 4.0)) < 1e-9 and abs(w1 - (e0 + 0.3)) < 1e-9       # crossfades into the card
    ass = build_ass(cfg, tl, CHUNKS)
    assert ",End," not in ass and ",Dim," not in ass                          # no old text end card
    over = build_ass(cfg, tl, CHUNKS, over_card=True)
    caps = [l for l in over.splitlines() if l.startswith("Dialogue")]
    assert caps and all(",Cap," in l for l in caps)
    cmd = build_command(cfg, tl)
    assert '_endcard.png"' in cmd and '_arrow.png"' in cmd and "_fb_over.ass" in cmd
    assert f"setpts=PTS+{e0:.3f}/TB[ec]" in cmd


def test_cover_endcard_png_renders(tmp_path):
    import glob
    import pytest
    from PIL import features
    from brand import endcard_cover
    here = os.path.dirname(os.path.abspath(__file__))
    fonts = glob.glob("/usr/share/fonts/**/Heebo*.ttf", recursive=True)
    logo = os.path.join(here, "..", "..", "investing-bros-brand", "assets", "logo-solid.png")
    if not features.check("raqm") or not fonts:
        pytest.skip("needs Pillow with raqm and Heebo")
    font = fonts[0]
    card = endcard_cover(str(tmp_path / "ec.png"), font, logo, "האם טסלה תנצח את המרוץ|של נהיגה אוטונומית?",
                         "פרק 1", "הקישור לפרק המלא בתיאור")
    assert 150 <= card["box"][0] and card["bottom"] < 1400
