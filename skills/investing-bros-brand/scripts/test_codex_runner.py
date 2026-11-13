import io
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "codex_runner", Path(__file__).with_name("codex_runner.py")
)
cr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cr)


def test_mac_first_when_reachable_and_logged_in():
    d = cr.decide(mac_status="reachable", mac_login="logged-in")
    assert d.action == "exec" and d.host == "mac" and d.reason == "mac_first"
    assert cr.MAC_MACHINE_ID in "\n".join(d.lines())


def test_unknown_mac_is_still_tried_first():
    d = cr.decide(mac_status="unknown", mac_login="unknown")
    assert d.action == "exec" and d.host == "mac"


def test_unreachable_mac_falls_back_to_box():
    d = cr.decide(mac_status="unreachable", box_login="logged-in")
    assert d.action == "exec" and d.host == "box" and d.reason == "mac_unreachable"
    assert "Fall back automatically" in d.message


def test_mac_non_auth_failure_falls_back_to_box():
    d = cr.decide(
        mac_status="reachable",
        mac_login="logged-in",
        mac_exec="failed",
        box_login="logged-in",
    )
    assert d.action == "exec" and d.host == "box" and d.reason == "mac_failed"


def test_mac_needs_login_stops_without_box_fallback():
    d = cr.decide(
        mac_status="reachable",
        mac_login="needs-login",
        box_login="logged-in",
    )
    assert d.action == cr.NEEDS_LOGIN_BANNER and d.host == "mac"
    assert d.lines()[0] == "NEEDS_LOGIN"
    assert "device-code" in d.message
    assert "auth.json" in d.message
    assert cr.main([
        "decide", "--mac-status", "reachable", "--mac-login", "needs-login",
        "--box-login", "logged-in",
    ]) == cr.EXIT_NEEDS_LOGIN


def test_mac_auth_failed_stops_even_if_box_is_logged_in():
    d = cr.decide(
        mac_status="reachable",
        mac_login="logged-in",
        mac_exec="auth-failed",
        box_login="logged-in",
    )
    assert d.action == cr.NEEDS_LOGIN_BANNER and d.host == "mac"
    assert d.reason == "mac_auth_failed"


def test_box_needs_login_after_mac_unreachable():
    d = cr.decide(mac_status="unreachable", box_login="needs-login")
    assert d.action == cr.NEEDS_LOGIN_BANNER and d.host == "box"
    assert "the box" in d.message


def test_both_non_auth_failures_are_blocked():
    d = cr.decide(
        mac_status="unreachable",
        box_login="logged-in",
        box_exec="failed",
    )
    assert d.action == "blocked" and d.host == "none"
    assert "Pillow" in d.message
    assert cr.main([
        "decide", "--mac-status", "unreachable", "--box-login", "logged-in",
        "--box-exec", "failed",
    ]) == cr.EXIT_BLOCKED


def test_parse_login_status():
    assert cr.parse_login_status("Logged in using ChatGPT\n") == "logged-in"
    assert cr.parse_login_status("Logged in using access token\n") == "logged-in"
    assert cr.parse_login_status("Not logged in\n") == "needs-login"
    assert cr.parse_login_status("ChatGPT account ID not available, please re-run codex login\n") == "needs-login"
    assert cr.parse_login_status("something else") == "unknown"


def test_auth_needed_in_logs():
    assert cr.auth_needed_in("Error: authentication required: please log in")
    assert cr.auth_needed_in("Not logged in")
    assert cr.auth_needed_in("please re-run `codex login`")
    assert not cr.auth_needed_in("OpenAI Codex v0.167.2\nI'm using the imagegen skill")


def test_parse_device_prompt_extracts_url_and_code():
    text = (
        "Follow these steps to sign in with ChatGPT using device code authorization:\n"
        "1. Open this link in your browser and sign in to your account\n"
        "   https://auth.openai.com/codex/device\n"
        "2. Enter this one-time code ABCD-EFGH\n"
        "(expires in 15 minutes)\n"
    )
    parsed = cr.parse_device_prompt(text)
    assert parsed["url"] == "https://auth.openai.com/codex/device"
    assert parsed["code"] == "ABCD-EFGH"


def test_parse_device_prompt_code_on_next_line():
    text = (
        "1. Open this link in your browser and sign in to your account\n"
        "   https://auth.openai.com/codex/device\n"
        "2. Enter this one-time code\n"
        "WXYZ-1234\n"
        "(expires in 15 minutes)\n"
    )
    parsed = cr.parse_device_prompt(text)
    assert parsed["code"] == "WXYZ-1234"


def test_cli_parse_device_and_detect_auth(capsys, monkeypatch):
    prompt = (
        "Follow these steps to sign in with ChatGPT using device code authorization:\n"
        "1. Open this link in your browser and sign in to your account\n"
        "   https://auth.openai.com/codex/device\n"
        "2. Enter this one-time code ABCD-EFGH\n"
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(prompt))
    assert cr.main(["parse-device"]) == cr.EXIT_NEEDS_LOGIN
    out = capsys.readouterr().out
    assert out.startswith("NEEDS_LOGIN")
    assert "url: https://auth.openai.com/codex/device" in out
    assert "code: ABCD-EFGH" in out
    assert "auth.json" in out

    monkeypatch.setattr("sys.stdin", io.StringIO("authentication required: token expired\n"))
    assert cr.main(["detect-auth"]) == cr.EXIT_NEEDS_LOGIN
    monkeypatch.setattr("sys.stdin", io.StringIO("OpenAI Codex v0.167.2\nworkdir ok\n"))
    assert cr.main(["detect-auth"]) == cr.EXIT_OK


def test_cli_parse_status(capsys):
    assert cr.main(["parse-status", "--text", "Logged in using ChatGPT"]) == cr.EXIT_OK
    assert capsys.readouterr().out.strip() == "logged-in"
    assert cr.main(["parse-status", "--text", "Not logged in"]) == cr.EXIT_NEEDS_LOGIN
    assert capsys.readouterr().out.strip() == "needs-login"


def test_decide_output_includes_box_work_root(capsys):
    assert cr.main(["decide", "--mac-status", "unreachable"]) == cr.EXIT_OK
    out = capsys.readouterr().out
    assert "ACTION=exec" in out
    assert "HOST=box" in out
    assert cr.BOX_WORK_ROOT in out
    assert "OPENAI_API_KEY" in out


def test_script_source_never_copies_auth():
    src = Path(__file__).with_name("codex_runner.py").read_text(encoding="utf-8")
    assert "never copies ~/.codex/auth.json" in src.lower() or "Never copy ~/.codex/auth.json" in src
    # Must not contain any instruction or helper to copy the auth file.
    assert "copy ~/.codex/auth.json" not in src.lower().replace("never copy ~/.codex/auth.json", "")
    assert "shutil.copy" not in src
