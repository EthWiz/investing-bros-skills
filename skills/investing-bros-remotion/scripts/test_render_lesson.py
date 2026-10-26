"""Tests for render_lesson.py and the template's Lesson composition."""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from render_lesson import FPS, render_cmd, still_cmd  # noqa: E402
from render_short import TEMPLATE  # noqa: E402


def test_template_has_the_lesson_composition():
    root = (TEMPLATE / "src" / "Root.tsx").read_text()
    assert 'id="Lesson"' in root and "width={1920}" in root and "height={1080}" in root
    assert re.search(r"LESSON_FPS = (\d+)", root).group(1) == str(FPS)
    for rel in ("Lesson.tsx", "types.ts", "scenes.ts", "overlays.tsx", "panels.tsx", "kit.tsx"):
        assert (TEMPLATE / "src" / "lesson" / rel).is_file(), rel


def test_every_scene_in_the_registry_has_its_file():
    scenes = (TEMPLATE / "src" / "lesson" / "scenes.ts").read_text()
    for mod in re.findall(r"from '\./(lesson\d+/\w+)'", scenes):
        assert (TEMPLATE / "src" / "lesson" / f"{mod}.tsx").is_file(), mod


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
