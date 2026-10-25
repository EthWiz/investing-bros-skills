"""Tests for render_short.py (staging, browser lookup, commands, layout file)."""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from render_short import (FONTS, TEMPLATE, find_browser, layout, render_cmd, stage_assets,  # noqa: E402
                          stage_project, still_cmd)


def test_template_has_what_the_renderer_needs():
    for rel in ("package.json", "package-lock.json", "tsconfig.json", "src/index.ts", "src/Root.tsx",
                "src/Short.tsx", "src/sample-props.json", "public/.gitkeep"):
        assert (TEMPLATE / rel).is_file(), rel
    pkg = json.loads((TEMPLATE / "package.json").read_text())
    versions = {**pkg["dependencies"], **pkg["devDependencies"]}
    assert all(v[0].isdigit() for v in versions.values()), "pin exact versions"
    assert versions["remotion"] == versions["@remotion/cli"]
    assert 'id="Short"' in (TEMPLATE / "src" / "Root.tsx").read_text()


def test_browser_lookup_order(tmp_path):
    shell = tmp_path / "chromium_headless_shell-1243" / "chrome-headless-shell-linux64" / "chrome-headless-shell"
    shell.parent.mkdir(parents=True)
    shell.write_text("")
    pattern = str(tmp_path / "chromium_headless_shell-*" / "chrome-headless-shell-linux64" / "chrome-headless-shell")
    assert find_browser("/x/chrome", {"REMOTION_BROWSER_EXECUTABLE": "/y"}, (pattern,)) == "/x/chrome"
    assert find_browser(None, {"REMOTION_BROWSER_EXECUTABLE": "/y"}, (pattern,)) == "/y"
    assert find_browser(None, {}, (pattern,)) == str(shell)
    assert find_browser(None, {}, (str(tmp_path / "none-*"),)) is None


def test_stage_project_copies_template_and_tracks_install(tmp_path):
    tpl = tmp_path / "tpl"
    (tpl / "src").mkdir(parents=True)
    (tpl / "src" / "index.ts").write_text("x")
    (tpl / "node_modules" / "big").mkdir(parents=True)
    (tpl / "public").mkdir()
    (tpl / "public" / "base.mp4").write_text("old")
    (tpl / "package-lock.json").write_text('{"v": 1}')
    work = tmp_path / "work"
    assert stage_project(work, tpl) is True
    assert (work / "src" / "index.ts").is_file() and not (work / "node_modules" / "big").exists()
    assert not (work / "public" / "base.mp4").exists()
    import hashlib
    (work / "node_modules").mkdir()
    (work / "node_modules" / ".template-lock-sha256").write_text(hashlib.sha256(b'{"v": 1}').hexdigest())
    assert stage_project(work, tpl) is False                       # installed for this lockfile
    (tpl / "package-lock.json").write_text('{"v": 2}')
    assert stage_project(work, tpl) is True                        # lockfile changed -> reinstall


def test_stage_assets_needs_the_static_heebo_weights(tmp_path):
    (tmp_path / "work" / "public").mkdir(parents=True)
    base, logo, fonts = tmp_path / "b.mp4", tmp_path / "l.png", tmp_path / "fonts"
    base.write_text("v")
    logo.write_text("l")
    fonts.mkdir()
    with pytest.raises(SystemExit, match="Heebo-SemiBold"):
        stage_assets(tmp_path / "work", base, fonts, logo)
    for f in FONTS:
        (fonts / f).write_text("f")
    stage_assets(tmp_path / "work", base, fonts, logo)
    pub = tmp_path / "work" / "public"
    assert (pub / "base.mp4").is_file() and (pub / "logo.png").is_file() and (pub / "fonts" / FONTS[2]).is_file()


def test_commands():
    cmd = render_cmd(Path("/o/s.mp4"), Path("/p.json"), "/chrome", 3)
    assert cmd[:6] == ["npx", "remotion", "render", "src/index.ts", "Short", "/o/s.mp4"]
    assert "--props=/p.json" in cmd and "--browser-executable=/chrome" in cmd and "--concurrency=3" in cmd
    assert "--codec=h264" in cmd
    assert not any(c.startswith("--browser-executable") for c in render_cmd(Path("/o.mp4"), Path("/p"), None))
    assert "--frame=228" in still_cmd(Path("/s.png"), Path("/p.json"), 228)


def test_layout_marks_the_silent_end_card_for_check_short():
    lay = layout({"baseDuration": 25.8, "endcardSeconds": 3.0})
    assert lay == {"duration": 28.8, "silent_endcard_seconds": 3.0, "hook_style": "remotion"}
