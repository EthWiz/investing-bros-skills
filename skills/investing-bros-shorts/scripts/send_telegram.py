#!/usr/bin/env python3
"""Post a short, or the episode's approval message (or delete the bot's own post) in the show's Telegram group.

Usage:
    python3 send_telegram.py video short.mp4 --caption "..." [--thumb cover.jpg] [--env telegram.env]
    python3 send_telegram.py text approval.txt [--env telegram.env]
    python3 send_telegram.py delete MESSAGE_ID [--env telegram.env]

Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from the environment or the --env file
(KEY=value lines). Never pass the token on the command line or print it. Each post
needs Amitai's OK in chat (investing-bros-show -> Telegram). Bot uploads max 50 MB.
Prints the message id; keep it (posts.log) so a post can be deleted later.
`text` sends a file as one message (the approval round: every asset in one message,
checked with check_links.py --message first) and refuses text that doesn't end with
the line "sent by Grokbot".
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile


def env(path):
    if path and os.path.exists(path):
        for line in open(path):
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)
    tok, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not tok or not chat:
        sys.exit("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID missing (env or --env file)")
    return tok, chat


SIGNATURE = "sent by Grokbot"


def text_problem(text):
    """Why this approval message can't be sent, or None. Checked before any API call."""
    if not text or not text.strip():
        return "the message is empty"
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    if lines[-1] != SIGNATURE:
        return f'the message must end with the line "{SIGNATURE}"'
    if len(lines) == 1:
        return "the message has nothing but the signature"
    if len(text.strip()) > 4096:
        return "over Telegram's 4096-character message limit: shorten it, keep it one message"
    return None


def call(tok, method, fields):
    args = ["curl", "-sS", "--max-time", "400", "--retry", "2"]
    for k, v in fields:
        upload = k in ("video", "thumbnail") and str(v).startswith("@")
        args += ["-F" if upload else "--form-string", f"{k}={v}"]  # text is never read as a file
    r = subprocess.run(args + [f"https://api.telegram.org/bot{tok}/{method}"], capture_output=True, text=True)
    out = json.loads(r.stdout or "{}")
    if not out.get("ok"):
        sys.exit(f"{method} failed: {out.get('description', r.stderr[:200])}")
    return out["result"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["video", "text", "delete"]); ap.add_argument("target")
    ap.add_argument("--caption", default=""); ap.add_argument("--thumb"); ap.add_argument("--env", default="telegram.env")
    a = ap.parse_args(argv)
    if a.action == "text":  # validate before reading the token or calling the API
        text = open(a.target, encoding="utf-8").read().strip()
        bad = text_problem(text)
        if bad:
            sys.exit(bad)
    tok, chat = env(a.env)
    if a.action == "delete":
        call(tok, "deleteMessage", [("chat_id", chat), ("message_id", a.target)])
        print(f"deleted {a.target}")
        return
    if a.action == "text":
        msg = call(tok, "sendMessage", [("chat_id", chat), ("text", text), ("disable_web_page_preview", "true")])
        with open("posts.log", "a") as f:
            f.write(f"{msg['message_id']}\t{a.target}\n")
        print(f"posted message {msg['message_id']}")
        return
    if os.path.getsize(a.target) > 50 * 1024 * 1024:
        sys.exit("over Telegram's 50 MB bot limit: re-encode a review copy (-crf 21)")
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                            "-of", "json", a.target], capture_output=True, text=True)
    info = json.loads(probe.stdout)
    st, dur = info["streams"][0], round(float(info["format"]["duration"]))
    fields = [("chat_id", chat), ("video", f"@{a.target}"), ("caption", a.caption), ("supports_streaming", "true"),
              ("width", st["width"]), ("height", st["height"]), ("duration", dur)]
    if a.thumb:
        th = os.path.join(tempfile.mkdtemp(), "thumb.jpg")   # Telegram: JPEG <=320 px, <200 KB
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.thumb, "-vf", "scale=-2:320", "-q:v", "4", th], check=True)
        fields.append(("thumbnail", f"@{th}"))
    msg = call(tok, "sendVideo", fields)
    with open("posts.log", "a") as f:
        f.write(f"{msg['message_id']}\t{a.target}\n")
    print(f"posted message {msg['message_id']}")


if __name__ == "__main__":
    main()
