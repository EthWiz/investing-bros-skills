"""Tests for the show intro builder and its music score."""
import json
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import build_intro as bi  # noqa: E402
import compose_intro_music as cm  # noqa: E402

CFG = {"fps": 24, "duration": 8.0, "line": "עשור של השקעות"}
HOSTS = [
    {"name": "אמיתי רסקין", "file": "hosts/host-0.png", "w": 420, "h": 700,
     "name_file": "hosts/name-0.png", "name_w": 300, "name_h": 90},
    {"name": "נדב רסקין", "file": "hosts/host-1.png", "w": 400, "h": 700,
     "name_file": "hosts/name-1.png", "name_w": 260, "name_h": 90},
]


def test_html_is_rtl_full_hd_and_names_the_composition():
    page = bi.build_html(CFG, HOSTS, logo_h=458)
    assert 'data-width="1920" data-height="1080"' in page
    assert 'data-duration="8.0000"' in page and 'data-fps="24"' in page
    assert '<div id="line" dir="rtl">' in page and "עשור של השקעות" in page
    assert "window.__timelines['intro']=tl" in page
    # no network loads at render time
    assert not re.search(r"(src|href|url)\(?=?['\"]?https?://", page)


def test_first_host_is_on_the_right_and_enters_first():
    page = bi.build_html(CFG, HOSTS, logo_h=458)
    left_r = int(re.search(r'id="host-r"[^>]*left:(\d+)px', page).group(1))
    left_l = int(re.search(r'id="host-l"[^>]*left:(\d+)px', page).group(1))
    assert left_r > 960 > left_l
    assert 'alt="אמיתי רסקין"' in page.split('id="name-r"')[1].split(">")[0]
    js = bi.timeline_js(CFG, HOSTS)
    assert "tl.fromTo('#host-r'" in js and f"}},{bi.T['host'][0]});" in js


def test_wordmark_lands_on_the_music_hits():
    js = bi.timeline_js(CFG, HOSTS)
    assert f"ease:'power3.out'}},{cm.LOGO_1});" in js
    assert f"duration:0.2,ease:'power2.out'}},{cm.LOGO_2});" in js
    assert bi.T["logo"] == cm.LOGO_1 and bi.T["logo_full"] == cm.LOGO_2


def test_times_snap_to_frames():
    assert bi.q(0.3, 24) == pytest.approx(7 / 24, abs=1e-4)
    assert bi.q(3.0, 24) == 3.0


def test_host_cutout_rejects_an_opaque_frame(tmp_path):
    from PIL import Image
    frame = tmp_path / "frame.png"
    Image.new("RGBA", (200, 300), (120, 100, 90, 255)).save(frame)
    with pytest.raises(ValueError, match="no transparency"):
        bi.host_cutout(str(frame), str(tmp_path / "out.png"))


def test_host_cutout_trims_and_scales(tmp_path):
    from PIL import Image, ImageDraw
    src = tmp_path / "cut.png"
    im = Image.new("RGBA", (400, 600), (0, 0, 0, 0))
    ImageDraw.Draw(im).rectangle((100, 100, 299, 499), fill=(200, 150, 120, 255))
    im.save(src)
    w, h = bi.host_cutout(str(src), str(tmp_path / "out.png"), height=700)
    assert (w, h) == (350, 700)


def test_score_hits_and_length():
    stems = cm.score()
    piano = stems["piano"]["events"]
    starts = {round(e[0], 3) for e in piano if len(e[2]) >= 6}
    assert {cm.LOGO_1, cm.LOGO_2} <= starts
    for st in stems.values():
        for start, dur, keys, vel in st["events"]:
            assert 0 <= start and start + dur <= cm.LENGTH
            assert all(0 <= k <= 127 for k in keys) and 1 <= vel <= 127


def test_example_config_is_valid():
    path = os.path.join(os.path.dirname(__file__), "..", "references", "intro.example.json")
    cfg = json.load(open(path, encoding="utf-8"))
    assert cfg["duration"] == cm.LENGTH and cfg["fps"] == 24
    assert [h["name"] for h in cfg["hosts"]] == ["אמיתי רסקין", "נדב רסקין"]
    assert "—" not in cfg["line"] and "–" not in cfg["line"]
