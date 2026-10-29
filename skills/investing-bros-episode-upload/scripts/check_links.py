#!/usr/bin/env python3
"""Check every link in a description, message or notes file before it is posted.

  check_links.py FILE [FILE ...] [--message] [--offline]
  echo "https://youtu.be/ID" | check_links.py -

Never retype a video ID or URL: copy it from tool output (Studio, yt_upload.py, the
API), then run this. YouTube links are resolved through oEmbed
(https://www.youtube.com/oembed?url=...): 200 = public or unlisted, 401/403 = the video
exists but is private (or embedding is off), 400/404 = no such video (a mistyped ID,
episode 9's I-vs-l). URLs are parsed with urllib.parse: YouTube is recognised by exact
host name only (youtube.com, www./m./music./studio.youtube.com, youtu.be), the id comes
only from the path or the `v` query, and a look-alike host (e.g. youtube.com.evil.io)
is BAD. Hosts outside the show's list are flagged in the output. Other links get an
HTTP HEAD (GET if HEAD is refused). --message
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
YT_ID_RE = re.compile(r"[A-Za-z0-9_-]{11}")
# Exact host names (no suffix matching: "youtube.com.evil.io" is not YouTube).
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com",
                 "studio.youtube.com", "youtu.be", "www.youtu.be"}
KNOWN_HOSTS = YOUTUBE_HOSTS | {
    "drive.google.com", "docs.google.com", "open.spotify.com", "creators.spotify.com",
    "podcasts.apple.com", "feeds.redcircle.com", "app.redcircle.com", "t.me",
    "www.instagram.com", "instagram.com", "www.tiktok.com", "tiktok.com", "x.com", "twitter.com",
    "github.com"}
LOOKALIKE = ("youtube", "youtu.be", "google", "spotify", "redcircle", "apple")
YT_PAGES = ("/channel/", "/c/", "/user/", "/@", "/playlist", "/feed/")  # not videos
UA = {"User-Agent": "Mozilla/5.0 (investing-bros check_links)"}


def find_links(text: str) -> list[str]:
    out = []
    for u in URL_RE.findall(text):
        u = u.rstrip(".,;:!?״׳")
        if u not in out:
            out.append(u)
    return out


def host_of(url: str) -> str:
    return (urllib.parse.urlsplit(url).hostname or "").lower().rstrip(".")


def is_youtube(url: str) -> bool:
    return host_of(url) in YOUTUBE_HOSTS


def is_lookalike(url: str) -> bool:
    """A host that names a service we link to but isn't its real host name."""
    h = host_of(url)
    return h not in KNOWN_HOSTS and any(w in h for w in LOOKALIKE)


def is_youtube_video(url: str) -> bool:
    if not is_youtube(url):
        return False
    path = urllib.parse.urlsplit(url).path
    return not (path in ("", "/") or any(path.startswith(p) for p in YT_PAGES))


def youtube_id(url: str) -> str | None:
    """The 11-character video id, from the path or the `v` query only (never a regex
    over the whole URL), or None."""
    if not is_youtube(url):
        return None
    parts = urllib.parse.urlsplit(url)
    host, segs = host_of(url), [p for p in parts.path.split("/") if p]
    cand = None
    if host in ("youtu.be", "www.youtu.be"):
        cand = segs[0] if len(segs) == 1 else None
    elif segs[:1] == ["watch"] and len(segs) == 1:
        vs = urllib.parse.parse_qs(parts.query).get("v", [])
        cand = vs[0] if len(vs) == 1 else None
    elif len(segs) >= 2 and segs[0] in ("shorts", "live", "embed", "video"):
        if segs[0] != "video" or host == "studio.youtube.com":
            cand = segs[1]
    return cand if cand and YT_ID_RE.fullmatch(cand) else None


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


def parse_check(url: str) -> tuple[bool | None, str]:
    """Offline verdict: (False, why) for a bad link, (None, note) when the network decides."""
    if urllib.parse.urlsplit(url).scheme not in ("http", "https") or not host_of(url):
        return False, "not a web link"
    if is_lookalike(url):
        return False, f"look-alike host {host_of(url)!r}: not a real YouTube/Google/Spotify host"
    if is_youtube_video(url):
        vid = youtube_id(url)
        if not vid:
            return False, "YouTube link without a valid 11-character video ID"
        return None, f"id {vid}"
    if host_of(url) not in KNOWN_HOSTS:
        return None, f"host {host_of(url)} is not on the show's list: check it is the intended site"
    return None, "parsed"


def check(url: str) -> tuple[bool, str]:
    ok, why = parse_check(url)
    if ok is False:
        return ok, why
    if is_youtube_video(url):
        vid = youtube_id(url)
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
                ok, why = parse_check(u)
                ok = ok is not False
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
