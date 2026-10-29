#!/usr/bin/env python3
"""Check every link in a description, message or notes file before it is posted.

  check_links.py FILE [FILE ...] [--message] [--offline]
  echo "https://youtu.be/ID" | check_links.py -

Never retype a video ID or URL: copy it from tool output (Studio, yt_upload.py, the
API), then run this. YouTube links are resolved through oEmbed
(https://www.youtube.com/oembed?url=...): 200 = public or unlisted, 401/403 = the video
exists but is private (or embedding is off), 400/404 = no such video (a mistyped ID,
episode 9's I-vs-l). Other links get an HTTP HEAD (GET if HEAD is refused). --message
also requires the text to end with the line "sent by Grokbot" (the Telegram approval
message). --offline only parses. Exit 1 if any link is bad.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

SIGNATURE = "sent by Grokbot"
URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")
YT_ID = r"([A-Za-z0-9_-]{11})(?![A-Za-z0-9_-])"
YT_PATTERNS = [
    re.compile(r"(?:www\.|m\.)?youtube\.com/watch\?(?:[^#\s]*&)?v=" + YT_ID),
    re.compile(r"youtu\.be/" + YT_ID),
    re.compile(r"(?:www\.)?youtube\.com/(?:shorts|live|embed)/" + YT_ID),
    re.compile(r"studio\.youtube\.com/video/" + YT_ID),
]
UA = {"User-Agent": "Mozilla/5.0 (investing-bros check_links)"}


def find_links(text: str) -> list[str]:
    out = []
    for u in URL_RE.findall(text):
        u = u.rstrip(".,;:!?״׳")
        if u not in out:
            out.append(u)
    return out


def youtube_id(url: str) -> str | None:
    for p in YT_PATTERNS:
        m = p.search(url)
        if m:
            return m.group(1)
    return None


def looks_like_youtube(url: str) -> bool:
    host = urllib.parse.urlparse(url).netloc.lower()
    return host.endswith("youtube.com") or host.endswith("youtu.be")


def classify_oembed(status: int) -> tuple[bool, str]:
    if status == 200:
        return True, "ok (public or unlisted)"
    if status in (401, 403):
        return True, "exists, private (or embedding off)"
    return False, f"no such video (oEmbed {status}): check the ID was copied, not typed"


def signature_ok(text: str) -> bool:
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    return bool(lines) and lines[-1] == SIGNATURE


def _status(url: str, method: str = "GET") -> int:
    req = urllib.request.Request(url, method=method, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def check(url: str) -> tuple[bool, str]:
    if looks_like_youtube(url) and "/channel/" not in url and "/@" not in url and "/playlist" not in url:
        vid = youtube_id(url)
        if not vid:
            return False, "YouTube link without a valid 11-character video ID"
        q = urllib.parse.urlencode({"url": f"https://www.youtube.com/watch?v={vid}", "format": "json"})
        return classify_oembed(_status(f"https://www.youtube.com/oembed?{q}"))
    st = _status(url, "HEAD")
    if st in (403, 405, 501):
        st = _status(url)
    return (st < 400), f"HTTP {st}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="text files, or - for stdin")
    ap.add_argument("--message", action="store_true", help=f'require the last line "{SIGNATURE}"')
    ap.add_argument("--offline", action="store_true", help="parse only, no network")
    a = ap.parse_args(argv)
    bad = 0
    for f in a.files:
        text = sys.stdin.read() if f == "-" else open(f, encoding="utf-8").read()
        if a.message and not signature_ok(text):
            print(f"{f}: the message must end with the line '{SIGNATURE}'")
            bad += 1
        links = find_links(text)
        if not links:
            print(f"{f}: no links")
        for u in links:
            if a.offline:
                vid = youtube_id(u)
                ok, why = (False, "YouTube link without a valid video ID") if looks_like_youtube(u) and not vid \
                    and not any(s in u for s in ("/channel/", "/@", "/playlist")) else (True, f"id {vid}" if vid else "parsed")
            else:
                try:
                    ok, why = check(u)
                except (urllib.error.URLError, TimeoutError, OSError) as e:
                    ok, why = False, f"unreachable: {e}"
            bad += not ok
            print(f"{'OK ' if ok else 'BAD'}  {u}  {why}")
    print("LINKS OK" if not bad else f"{bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
