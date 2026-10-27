"""Tests for preflight.py (what each lesson stage needs; required vs optional; no real machine assumed)."""
import os
import subprocess
import sys
from collections import namedtuple
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from preflight import (FONTS, check_disk, check_fonts, check_modules, check_node, check_rclone,  # noqa: E402
                       check_template, check_tool, main)


def runner(stdout="", code=0):
    return lambda cmd, **kw: subprocess.CompletedProcess(cmd, code, stdout=stdout, stderr="")


def test_a_missing_tool_fails_with_how_to_fix_it():
    r = check_tool("ffmpeg", fix="brew install ffmpeg", which=lambda n: None)
    assert (r["ok"], r["required"], r["fix"]) == (False, True, "brew install ffmpeg")
    r = check_tool("ffmpeg", which=lambda n: "/bin/ffmpeg", run=runner("ffmpeg version 7.1\nmore"))
    assert r["ok"] and r["detail"] == "ffmpeg version 7.1" and r["fix"] == ""


def test_node_must_be_18_or_newer():
    which = lambda n: f"/bin/{n}"
    assert check_node(which, runner("v22.3.0"))["ok"]
    assert not check_node(which, runner("v16.20.0"))["ok"]
    assert not check_node(lambda n: None, runner())["ok"]


def test_python_modules_are_checked_in_the_running_interpreter():
    r = check_modules(("numpy", "PIL"), find=lambda n: None if n == "numpy" else object())
    assert not r["ok"] and "missing numpy" in r["detail"] and sys.executable in r["detail"]


def test_fonts_and_template(tmp_path):
    assert not check_fonts(None)["ok"]
    for f in FONTS[:2]:
        (tmp_path / f).write_bytes(b"ttf")
    r = check_fonts(str(tmp_path))
    assert not r["ok"] and "Heebo-Black.ttf" in r["detail"]
    assert not check_template(tmp_path)["ok"]
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "package-lock.json").write_text("{}")
    assert check_template(tmp_path)["ok"]
    work = tmp_path / "work"
    (work / "node_modules" / "remotion").mkdir(parents=True)
    assert "installed in" in check_template(tmp_path / "nowhere", work)["detail"]


def test_no_upload_route_is_reported_but_optional():
    r = check_rclone(lambda n: None)
    assert (r["ok"], r["required"]) == (False, False) and "stage files locally" in r["detail"]
    r = check_rclone(lambda n: "/bin/rclone", runner("other:\nshow:\n"))
    assert r["ok"]


def test_disk():
    usage = namedtuple("usage", "total used free")
    assert check_disk(Path("."), 3.0, lambda p: usage(0, 0, 10e9))["ok"]
    assert not check_disk(Path("."), 3.0, lambda p: usage(0, 0, 1e9))["ok"]


def test_deliver_never_fails_on_its_optional_route(monkeypatch, capsys):
    import preflight
    monkeypatch.setattr(preflight.shutil, "which", lambda n: None)
    assert main(["--stage", "deliver"]) == 0
    assert "opt " in capsys.readouterr().out
    assert main(["--stage", "base"]) == 1                              # ffmpeg is required for the base
