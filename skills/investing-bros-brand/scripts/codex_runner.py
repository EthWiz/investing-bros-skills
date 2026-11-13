#!/usr/bin/env python3
"""Pick and run Codex for Investing Bros covers (investing-bros-brand).

Mac first, box CLI fallback, stop when a login is needed. The agent gathers
reachability with ListMachines and `codex login status` on each reachable host,
then calls `decide`. This script never copies ~/.codex/auth.json and never
prints tokens.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Amitai's Mac (investing-bros-show → environment). Device shell: Shell with this machineId.
MAC_MACHINE_ID = "566a74b2-614d-458f-be63-660743243124"
MAC_CODEX_BIN = "~/.nvm/versions/node/v22.23.1/bin/codex"
BOX_WORK_ROOT = "/workspace/investing-bros"
MAC_WORK_ROOT = "/Users/amitairuskin/Pictures/investing-bros"

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NEEDS_LOGIN = 2
EXIT_BLOCKED = 3

MAC_STATUSES = ("reachable", "unreachable", "unknown")
LOGIN_STATUSES = ("logged-in", "needs-login", "unknown")
EXEC_STATUSES = ("ok", "failed", "auth-failed", "not-tried")

# `codex login status` and `codex login --device-auth` wording (codex-cli 0.167.2).
LOGGED_IN_RE = re.compile(
    r"^Logged in using\b|^Successfully logged in\.?\s*$", re.I | re.M
)
NOT_LOGGED_IN_RE = re.compile(
    r"^Not logged in\s*$|is not logged in|please re-run `?codex login`?|"
    r"ChatGPT auth not available",
    re.I | re.M,
)
AUTH_NEEDED_RE = re.compile(
    r"authentication required|not logged in|please re-run `?codex login`?|"
    r"ChatGPT auth not available|chatgpt authentication required|"
    r"codex account authentication required",
    re.I,
)
DEVICE_URL_RE = re.compile(r"https://(?:auth\.openai\.com|chatgpt\.com)/[^\s]+")
DEVICE_CODE_RE = re.compile(
    r"Enter this one-time code\s+([A-Z0-9]{4,8}(?:-[A-Z0-9]{4,8})?)",
    re.I,
)
# Fallback when the code is on the next line of a formatted prompt.
DEVICE_CODE_LINE_RE = re.compile(r"\b([A-Z0-9]{4}(?:-[A-Z0-9]{4}){1,2})\b")

NEEDS_LOGIN_BANNER = "NEEDS_LOGIN"
NO_AUTH_COPY = (
    "Never copy ~/.codex/auth.json between machines. Never print tokens. "
    "Do not skip or work around the login. Do not use an API key."
)


class Decision:
    def __init__(self, action: str, host: str, reason: str, message: str):
        self.action = action  # exec | NEEDS_LOGIN | blocked
        self.host = host  # mac | box | none
        self.reason = reason
        self.message = message

    def lines(self) -> list[str]:
        out = [
            f"ACTION={self.action}",
            f"HOST={self.host}",
            f"REASON={self.reason}",
        ]
        if self.host == "mac":
            out.append(f"MACHINE_ID={MAC_MACHINE_ID}")
            out.append(f"CODEX_BIN={MAC_CODEX_BIN}")
            out.append(f"WORK_ROOT={MAC_WORK_ROOT}")
        elif self.host == "box":
            out.append("MACHINE_ID=")
            out.append("CODEX_BIN=codex")
            out.append(f"WORK_ROOT={BOX_WORK_ROOT}")
        out.append(self.message)
        if self.action == NEEDS_LOGIN_BANNER:
            out.insert(0, NEEDS_LOGIN_BANNER)
        return out


def parse_login_status(text: str) -> str:
    """Map `codex login status` output to logged-in | needs-login | unknown."""
    if LOGGED_IN_RE.search(text) and not NOT_LOGGED_IN_RE.search(text):
        return "logged-in"
    if NOT_LOGGED_IN_RE.search(text):
        return "needs-login"
    return "unknown"


def auth_needed_in(text: str) -> bool:
    """True when Codex output says a login or re-auth is required."""
    if NOT_LOGGED_IN_RE.search(text):
        return True
    return bool(AUTH_NEEDED_RE.search(text))


def parse_device_prompt(text: str) -> dict[str, str]:
    """Pull the device-code URL and one-time code out of `codex login --device-auth` output."""
    urls = DEVICE_URL_RE.findall(text)
    url = ""
    for candidate in urls:
        # Prefer the device page, not revoke/client metadata URLs.
        if "/codex/device" in candidate or "/oauth/codex" in candidate and "client.json" not in candidate:
            url = candidate.rstrip(".,)")
            break
    if not url and urls:
        url = urls[0].rstrip(".,)")
    code = ""
    m = DEVICE_CODE_RE.search(text)
    if m:
        code = m.group(1).upper()
    elif "one-time code" in text.lower():
        # Code often sits on its own line after the instruction.
        after = text.lower().split("one-time code", 1)[1]
        m2 = DEVICE_CODE_LINE_RE.search(after)
        if m2:
            code = m2.group(1).upper()
    return {"url": url, "code": code}


def format_needs_login(host: str, url: str = "", code: str = "") -> str:
    who = "Amitai's Mac" if host == "mac" else "the box"
    lines = [
        NEEDS_LOGIN_BANNER,
        f"Codex on {who} needs ChatGPT device-code login.",
        "Run `codex login --device-auth` on that host, show Amitai the URL and "
        "one-time code, and wait for him to complete it.",
        NO_AUTH_COPY,
    ]
    if url:
        lines.append(f"url: {url}")
    if code:
        lines.append(f"code: {code}")
    return "\n".join(lines)


def decide(
    mac_status: str = "unknown",
    mac_login: str = "unknown",
    mac_exec: str = "not-tried",
    box_login: str = "unknown",
    box_exec: str = "not-tried",
) -> Decision:
    """Choose Mac, the box, a login stop, or a hard block.

    Fallback to the box is only for an unreachable Mac or a non-auth Codex
    failure there. A needed login is never skipped or worked around.
    """
    if mac_status not in MAC_STATUSES:
        raise ValueError(f"mac_status must be one of {MAC_STATUSES}")
    if mac_login not in LOGIN_STATUSES or box_login not in LOGIN_STATUSES:
        raise ValueError(f"login status must be one of {LOGIN_STATUSES}")
    if mac_exec not in EXEC_STATUSES or box_exec not in EXEC_STATUSES:
        raise ValueError(f"exec status must be one of {EXEC_STATUSES}")

    mac_ok = mac_status in ("reachable", "unknown") and mac_exec == "not-tried"
    mac_failed_non_auth = mac_status == "unreachable" or mac_exec == "failed"

    # Login needed on a host we are trying (or just tried) always stops the run.
    if mac_status in ("reachable", "unknown") and mac_exec == "not-tried" and mac_login == "needs-login":
        return Decision(
            NEEDS_LOGIN_BANNER,
            "mac",
            "mac_needs_login",
            format_needs_login("mac"),
        )
    if mac_exec == "auth-failed":
        return Decision(
            NEEDS_LOGIN_BANNER,
            "mac",
            "mac_auth_failed",
            format_needs_login("mac"),
        )

    if mac_ok:
        return Decision(
            "exec",
            "mac",
            "mac_first",
            "Run Codex on Amitai's Mac first (Shell with MACHINE_ID; parallel "
            "sessions in per-option subfolders; prompt on stdin; env -u "
            "OPENAI_API_KEY). " + NO_AUTH_COPY,
        )

    # Mac is out of the way: unreachable or a non-auth failure. Try the box.
    if not mac_failed_non_auth and not mac_ok:
        # Defensive: unexpected combination.
        mac_failed_non_auth = True

    if box_exec == "auth-failed" or (box_exec == "not-tried" and box_login == "needs-login"):
        return Decision(
            NEEDS_LOGIN_BANNER,
            "box",
            "box_needs_login" if box_login == "needs-login" else "box_auth_failed",
            format_needs_login("box"),
        )
    if box_exec == "failed":
        return Decision(
            "blocked",
            "none",
            "both_failed",
            "Codex failed on Amitai's Mac and on the box (not a login prompt). "
            "Stop and report the error. Do not switch generators and do not "
            "composite covers with Pillow. " + NO_AUTH_COPY,
        )
    return Decision(
        "exec",
        "box",
        "mac_unreachable" if mac_status == "unreachable" else "mac_failed",
        "Mac is unreachable or Codex there failed for a non-auth reason. "
        "Fall back automatically to Codex CLI on the box (parallel sessions "
        f"under {BOX_WORK_ROOT}/episode-<N>/art/; prompt on stdin; env -u "
        "OPENAI_API_KEY). " + NO_AUTH_COPY,
    )


def find_codex_bin(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    env = os.environ.get("CODEX_BIN")
    if env:
        return env
    # When this script itself is running on the Mac, prefer the known nvm path.
    mac_path = Path(os.path.expanduser(MAC_CODEX_BIN))
    if sys.platform == "darwin" and mac_path.exists():
        return str(mac_path)
    found = shutil.which("codex")
    if found:
        return found
    local = Path.home() / ".local/bin/codex"
    if local.exists():
        return str(local)
    raise FileNotFoundError(
        "codex binary not found. On the box install with npm i -g @openai/codex; "
        f"on the Mac use {MAC_CODEX_BIN}."
    )


def _scrub_cmd_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("OPENAI_API_KEY", None)
    return env


def run_login_status(bin_path: str) -> tuple[int, str]:
    proc = subprocess.run(
        [bin_path, "login", "status"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=_scrub_cmd_env(),
        check=False,
    )
    return proc.returncode, proc.stdout or ""


def run_exec(bin_path: str, args: list[str], cwd: str | None = None) -> int:
    """Run `codex exec` with the prompt on stdin and OPENAI_API_KEY unset."""
    cmd = [bin_path, "exec", *args]
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        env=_scrub_cmd_env(),
        check=False,
    )
    return proc.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Mac-first Codex runner with a box CLI fallback. Stops on login."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_dec = sub.add_parser("decide", help="Choose Mac, box, NEEDS_LOGIN, or blocked")
    p_dec.add_argument("--mac-status", choices=MAC_STATUSES, default="unknown")
    p_dec.add_argument("--mac-login", choices=LOGIN_STATUSES, default="unknown")
    p_dec.add_argument("--mac-exec", choices=EXEC_STATUSES, default="not-tried")
    p_dec.add_argument("--box-login", choices=LOGIN_STATUSES, default="unknown")
    p_dec.add_argument("--box-exec", choices=EXEC_STATUSES, default="not-tried")

    sub.add_parser("login-status", help="Run `codex login status` on this host")
    p_ps = sub.add_parser("parse-status", help="Parse `codex login status` text from stdin")
    p_ps.add_argument("--text", default=None, help="Status text (default: stdin)")

    sub.add_parser(
        "parse-device",
        help="Parse a device-auth prompt from stdin; print NEEDS_LOGIN, url and code",
    )
    sub.add_parser(
        "detect-auth",
        help="Exit 2 if stdin (a Codex log) says a login is required",
    )
    sub.add_parser("which", help="Print the local Codex binary path")

    p_ex = sub.add_parser(
        "exec",
        help="Run `codex exec` here with env -u OPENAI_API_KEY; prompt on stdin",
    )
    p_ex.add_argument("--bin", default=None, help="Codex binary (default: auto)")
    p_ex.add_argument("--cwd", default=None)
    p_ex.add_argument("exec_args", nargs=argparse.REMAINDER)

    args = parser.parse_args(argv)

    if args.cmd == "decide":
        decision = decide(
            mac_status=args.mac_status,
            mac_login=args.mac_login,
            mac_exec=args.mac_exec,
            box_login=args.box_login,
            box_exec=args.box_exec,
        )
        sys.stdout.write("\n".join(decision.lines()) + "\n")
        if decision.action == NEEDS_LOGIN_BANNER:
            return EXIT_NEEDS_LOGIN
        if decision.action == "blocked":
            return EXIT_BLOCKED
        return EXIT_OK

    if args.cmd == "which":
        try:
            print(find_codex_bin())
            return EXIT_OK
        except FileNotFoundError as exc:
            print(exc, file=sys.stderr)
            return EXIT_ERROR

    if args.cmd == "parse-status":
        text = args.text if args.text is not None else sys.stdin.read()
        status = parse_login_status(text)
        print(status)
        return EXIT_NEEDS_LOGIN if status == "needs-login" else EXIT_OK

    if args.cmd == "parse-device":
        text = sys.stdin.read()
        parsed = parse_device_prompt(text)
        sys.stdout.write(
            format_needs_login("box" if "linux" in sys.platform else "mac",
                               parsed.get("url", ""), parsed.get("code", ""))
            + "\n"
        )
        if parsed.get("url") or parsed.get("code") or auth_needed_in(text) or "device code" in text.lower():
            return EXIT_NEEDS_LOGIN
        return EXIT_ERROR

    if args.cmd == "detect-auth":
        text = sys.stdin.read()
        if auth_needed_in(text):
            sys.stdout.write(format_needs_login("box" if sys.platform.startswith("linux") else "mac") + "\n")
            return EXIT_NEEDS_LOGIN
        return EXIT_OK

    if args.cmd == "login-status":
        try:
            bin_path = find_codex_bin()
        except FileNotFoundError as exc:
            print(exc, file=sys.stderr)
            return EXIT_ERROR
        code, text = run_login_status(bin_path)
        status = parse_login_status(text)
        # Print only the classification, never the raw file or tokens.
        print(status)
        if status == "needs-login" or auth_needed_in(text):
            sys.stdout.write(format_needs_login("box" if sys.platform.startswith("linux") else "mac") + "\n")
            return EXIT_NEEDS_LOGIN
        if status == "logged-in":
            return EXIT_OK
        if code != 0:
            print("codex login status failed; treat as unknown and inspect the error.", file=sys.stderr)
            return EXIT_ERROR
        return EXIT_OK

    if args.cmd == "exec":
        try:
            bin_path = find_codex_bin(args.bin)
        except FileNotFoundError as exc:
            print(exc, file=sys.stderr)
            return EXIT_ERROR
        exec_args = list(args.exec_args)
        if exec_args and exec_args[0] == "--":
            exec_args = exec_args[1:]
        return run_exec(bin_path, exec_args, cwd=args.cwd)

    return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
