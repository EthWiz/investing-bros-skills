"""Tests for make_input.py and build_composition.py. Run: python3 -m pytest skills/investing-bros-hyperframes/scripts"""
import json
import os
import re
import sys

import pytest

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
from build_composition import Timeline, build, close_gaps, text  # noqa: E402
from make_input import build_command, out_time, pieces_of  # noqa: E402

EXAMPLE = json.load(open(os.path.join(HERE, "..", "references", "example-swift.json"), encoding="utf-8"))


def test_timeline_maps_through_cuts():
    tl = Timeline([[100, 110], [120, 125]], 24)
    assert tl.duration == pytest.approx(15)
    assert tl.map(120) == pytest.approx(10)
    with pytest.raises(ValueError):
        tl.map(115)


def test_text_escapes_isolates_english_and_highlights():
    assert text("a<b") == "<bdi>a</bdi>&lt;<bdi>b</bdi>"
    out = text("ל־use cases [הפיננסיים]|שורה")
    assert "<bdi>use cases</bdi>" in out and '<span class="em">הפיננסיים</span>' in out and "<br/>" in out


def test_close_gaps():
    assert close_gaps([(0, 1.0, "a"), (1.2, 2, "b")])[0][1] == 1.2


def test_example_builds_a_valid_composition():
    index, files, sb, words = build(EXAMPLE)
    assert sb["composition"]["durationSeconds"] == pytest.approx(47.0833, abs=0.01)
    assert set(files) == {"c1", "c2", "c3", "c4", "c5", "end"}
    hosts = re.findall(r'<div class="card-host clip" id="card-[^"]+" data-card-id="([^"]+)"', index)
    assert hosts == ["c1", "c2", "c3", "c4", "c5", "end"]          # every card host has clip class + id
    assert "window.__timelines['talking-head-recut']=tl" in index
    assert "https://" not in index and "http://" not in index.replace("http://www.w3.org/2000/svg", "")  # nothing fetched
    for cid, h in files.items():                                    # card CSS is scoped
        for rule in re.findall(r"^([^{\n]+)\{", h.split("<style>")[1].split("</style>")[0], re.M):
            assert rule.startswith(f'.card[data-card-id="{cid}"]')
    assert len(re.findall(r'class="cap clip"', index)) == len(EXAMPLE["captions"])
    assert words and all(w["end"] >= w["start"] for w in words)


def test_overlapping_cards_are_rejected():
    cfg = dict(EXAMPLE, cards=[dict(EXAMPLE["cards"][0], end=852.0), EXAMPLE["cards"][1]])
    with pytest.raises(ValueError):
        build(cfg)


def test_input_command_switches_host_and_uses_levelled_audio():
    cfg = {"name": "t", "fps": 24, "source": "raw.mp4", "audio_source": "lev.wav",
           "pieces": [[1, 12], [15, 30]], "shots": [[1, 12, "L"], [15, 30, "R"]]}
    cmd = build_command(cfg)
    assert "between(t,11.000,26.000)" in cmd
    assert "scale=1080:1216" in cmd and "-g 24" in cmd
    assert '-i "lev.wav"' in cmd and "volume=2dB" in cmd and "loudnorm" not in cmd
    p = pieces_of(cfg)
    assert out_time(p, 15) == pytest.approx(11)


def test_input_command_without_levelled_audio_applies_gain():
    cfg = {"name": "t", "fps": 24, "source": "raw.mp4", "pieces": [[1, 12, 16.5]]}
    cmd = build_command(cfg)
    assert "volume=16.5dB" in cmd and "loudnorm=I=-14" in cmd


@pytest.mark.parametrize("audio_source", ["lev.wav", None])
def test_input_command_forces_stereo_output(audio_source):
    # mono sources (Riverside AAC) used to fail at aresample -> output; both audio paths must set a layout
    cfg = {"name": "t", "fps": 24, "source": "raw.mp4", "pieces": [[1, 12]], "shots": [[1, 12, "L"]]}
    if audio_source:
        cfg["audio_source"] = audio_source
    af = build_command(cfg).split("-filter_complex")[1]
    assert "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a]" in af


def test_overlay_layout_with_fly_and_supply_cards():
    cfg = json.load(open(os.path.join(HERE, "..", "references", "ep7-asteroid-overlay.json"), encoding="utf-8"))
    index, files, sb, _ = build(cfg)
    assert set(files) == {"c1", "c2"}
    assert 'height:1920px' in index and 'id="logo"' not in index         # full-screen input already has the logo
    assert "top:262px" in index and "scale:0.74" in index                 # compact top panel, eyes clear
    assert "#c1-ast" in index and "strokeDashoffset" in index and "#c2-f" in index
    assert "http://www.w3.org/2000/svg" in index                          # only the SVG namespace, nothing fetched
    assert "https://" not in index
    assert sb["videoTrack"]["bounds"]["height"] == 1920
