"""Tests for render_lesson.py and the template's Lesson composition."""
import json
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from render_lesson import FPS, clip_cmd, render_cmd, shift_audio_cmd, stage_scene_assets, still_cmd, transition_times  # noqa: E402
from render_short import TEMPLATE  # noqa: E402


def test_template_has_the_lesson_composition():
    root = (TEMPLATE / "src" / "Root.tsx").read_text()
    assert 'id="Lesson"' in root and "width={1920}" in root and "height={1080}" in root
    assert re.search(r"LESSON_FPS = (\d+)", root).group(1) == str(FPS)
    for rel in ("Lesson.tsx", "types.ts", "scenes.ts", "overlays.tsx", "panels.tsx", "kit.tsx"):
        assert (TEMPLATE / "src" / "lesson" / rel).is_file(), rel


def test_every_scene_in_the_registry_has_its_file():
    scenes = (TEMPLATE / "src" / "lesson" / "scenes.ts").read_text()
    mods = re.findall(r"from '\./((?:lesson\d+/)?\w+)'", scenes)
    assert "Terms" in mods                              # the reusable scene sits in lesson/
    for mod in mods:
        if mod != "types":
            assert (TEMPLATE / "src" / "lesson" / f"{mod}.tsx").is_file(), mod


def test_the_registry_and_the_scene_manifest_name_the_same_scenes():
    scenes = (TEMPLATE / "src" / "lesson" / "scenes.ts").read_text()
    block = scenes[scenes.index("SCENES"):]
    registered = set(re.findall(r"^\s*'?([\w-]+)'?:\s*\w+,", block, re.M))
    manifest = json.loads((TEMPLATE / "src" / "lesson" / "scenes.json").read_text(encoding="utf-8"))
    declared = {k for k in manifest if not k.startswith("_")}
    assert registered == declared
    for name, spec in manifest.items():
        if not name.startswith("_"):
            assert spec["mode"] in ("side", "bubble") and {"anchors", "content"} <= set(spec), name


def test_lesson_fonts_are_the_static_heebo_weights():
    lesson = (TEMPLATE / "src" / "lesson" / "Lesson.tsx").read_text()
    assert "fontFaces()" in lesson                      # the same staged TTFs as the Shorts
    for f in (TEMPLATE / "src" / "lesson").rglob("*.tsx"):
        assert "http" not in f.read_text(), f"{f.name}: nothing loads from a URL"


def test_commands_render_the_lesson_composition():
    r = render_cmd(Path("/o/l.mp4"), Path("/p.json"), "/chrome", 6)
    assert r[:5] == ["npx", "remotion", "render", "src/index.ts", "Lesson"]
    assert "--concurrency=6" in r and "--browser-executable=/chrome" in r and "--props=/p.json" in r
    s = still_cmd(Path("/o/s.png"), Path("/p.json"), 90 * FPS)
    assert "Lesson" in s and f"--frame={90 * FPS}" in s


PROPS = {"duration": 60.0,
         "beats": [{"start": 0.0, "end": 20.0}, {"start": 20.0, "end": 45.0}, {"start": 45.0, "end": 60.0}],
         "segments": [{"start": 0.0, "end": 8.0, "mode": "full", "zoom": 1.1},
                      {"start": 8.0, "end": 20.0, "mode": "full"},
                      {"start": 20.0, "end": 30.0, "mode": "full"},     # a take cut, no layout change
                      {"start": 30.0, "end": 52.5, "mode": "side", "scene": "terms"},
                      {"start": 52.5, "end": 60.0, "mode": "full"}]}


def test_transitions_are_every_cut_and_every_layout_change():
    assert transition_times(PROPS) == [8.0, 20.0, 30.0, 45.0, 52.5]
    c = clip_cmd(Path("/o/c.mp4"), Path("/p.json"), 570, 645)
    assert "--frames=570-645" in c and "Lesson" in c


def test_audio_shift_moves_only_the_sound_without_re_encoding():
    cmd = shift_audio_cmd(Path("in.mp4"), Path("out.mp4"), 0.043)
    assert cmd[cmd.index("-itsoffset") + 1] == "-0.043000"          # 43 ms late -> pulled earlier
    assert cmd.index("-itsoffset") < cmd.index("-i", cmd.index("-itsoffset"))
    assert ["-map", "0:v:0", "-map", "1:a:0", "-c", "copy"] == cmd[cmd.index("-map"):cmd.index("-map") + 6]


def test_scene_assets_are_staged_under_public(tmp_path):
    src = tmp_path / "page.png"
    src.write_bytes(b"png")
    stage_scene_assets(tmp_path / "work", {"assets": {"whitepaper": "assets/whitepaper.png"},
                                           "assetSources": {"whitepaper": str(src)}})
    assert (tmp_path / "work" / "public" / "assets" / "whitepaper.png").read_bytes() == b"png"
    stage_scene_assets(tmp_path / "work", {})                        # a lesson with no images


def test_vertical_scenes_have_a_9_by_16_composition():
    root = (TEMPLATE / "src" / "Root.tsx").read_text()
    block = root[root.index('id="LessonScenes"'):]
    assert "width={1080}" in block and "height={1920}" in block and "LESSON_FPS" in block
    manifest = json.loads((TEMPLATE / "src" / "lesson" / "scenes.json").read_text(encoding="utf-8"))
    vertical = [k for k, v in manifest.items() if not k.startswith("_") and v.get("vertical")]
    assert vertical == ["double-spend", "growth-bars", "price-drop", "mining", "chain", "conflict", "private-key"]
    files = {"double-spend": "DoubleSpend", "growth-bars": "GrowthBars", "price-drop": "PriceDrop", "mining": "Mining", "chain": "Chain",
             "conflict": "Conflict", "private-key": "PrivateKey"}
    for name in vertical:                                            # it lays itself out from the frame size
        src = (TEMPLATE / "src" / "lesson" / f"{files[name]}.tsx").read_text()
        assert "useVideoConfig" in src and "TALL" in src, name
    s = still_cmd(Path("/o/v.png"), Path("/p.json"), 300, composition="LessonScenes")
    assert s[:5] == ["npx", "remotion", "still", "src/index.ts", "LessonScenes"]


@pytest.mark.parametrize("scene", ["DoubleSpend", "GrowthBars", "PriceDrop", "Mining", "Chain", "Conflict", "PrivateKey", "blocks"])
def test_reusable_scenes_take_every_word_from_content(scene):
    src = (TEMPLATE / "src" / "lesson" / f"{scene}.tsx").read_text()
    hebrew = [line for line in src.splitlines() if re.search(r"[֐-׿]", line) and not line.strip().startswith("//")]
    assert hebrew == []                                              # no Hebrew text baked into the component


def test_double_spend_has_its_two_scenarios():
    manifest = json.loads((TEMPLATE / "src" / "lesson" / "scenes.json").read_text(encoding="utf-8"))
    assert set(manifest["double-spend"]["variants"]["options"]) == {"copy", "ledger"}


def test_caption_punctuation_stays_outside_the_word_isolate():
    # "פי 3.5." garbled: inside <bdi dir="auto"> a number runs left to right, so its period went to the wrong side
    kit = (TEMPLATE / "src" / "lesson" / "kit.tsx").read_text()
    pattern = re.search(r"w\.match\(/(.+)/s\)", kit).group(1)
    for word, core, trail in [("3.5.", "3.5", "."), ("2019,", "2019", ","), ("קיים?", "קיים", "?"), ("S&P", "S&P", "")]:
        m = re.match(pattern, word, re.S)
        assert (m.group(1), m.group(2)) == (core, trail), word
    lesson = (TEMPLATE / "src" / "lesson" / "Lesson.tsx").read_text()
    assert "splitTrail(wd.w)" in lesson and "<bdi dir=\"auto\">{core}</bdi>{trail}" in lesson
