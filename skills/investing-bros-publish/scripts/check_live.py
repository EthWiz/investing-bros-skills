#!/usr/bin/env python3
"""Check from outside (no login, no token) that an Investing Bros item is really live.

  check_live.py redcircle --episode N [--title TITLE_OR_FILE]
  check_live.py youtube ID [ID ...] --expect public|unlisted|private

redcircle: reads the show's public RSS feed and finds the item whose itunes:episode
is N. Prints its title and duration. With --title, the feed title must equal that
title once direction marks are stripped (the same rule as check_titles_match.py).

youtube: for each video ID (copied from Studio, never retyped):
  public   = oEmbed 200 AND the ID is in the אחים להשקעות channel RSS feed
  unlisted = oEmbed 200 and NOT in the channel feed
  private  = oEmbed 401/403
oEmbed 400/404 means no such video (a mistyped ID). The channel feed lists only the
newest ~15 uploads, which always covers the episode being published.
A just-published video (especially a Short) can return oEmbed 200 but stay out of
the channel feed for about 1–3 minutes, so check_live reports it as unlisted. When
--expect public, the check retries the feed for about three minutes (six waits of
30 s; override with --retries / --wait) before failing. Episode 12's first Short
passed on retry after that lag.

This is the outside check only. The Studio checks (Related video on Shorts, cards,
end screens, subtitles) are done by reopening the Studio page; see the SKILL.md.
Exit 0 when every check passes, 1 otherwise.
"""
from __future__ import annotations

import argparse
import time
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

CHANNEL_ID = "UCWIlggXQNDFiyJghl6VB6Xw"  # אחים להשקעות
CHANNEL_FEED = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
REDCIRCLE_FEED = "https://feeds.redcircle.com/c798e000-7934-4f82-a0e3-59b78f0894c6"
OEMBED = "https://www.youtube.com/oembed?format=json&url="
ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
MARKS = "\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
ITUNES = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"
UA = {"User-Agent": "Mozilla/5.0 (investing-bros check_live)"}


def http_get(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, ""


def normalize(title: str) -> str:
    return " ".join(title.translate({ord(c): None for c in MARKS}).split())


def _read(arg: str) -> str:
    p = Path(arg)
    try:
        if p.is_file():
            return p.read_text(encoding="utf-8").strip()
    except OSError:
        pass
    return arg


def feed_item(xml_text: str, episode: int) -> dict | None:
    root = ET.fromstring(xml_text)
    for item in root.iter("item"):
        if (item.findtext(f"{ITUNES}episode") or "").strip() == str(episode):
            return {"title": item.findtext("title") or "",
                    "duration": item.findtext(f"{ITUNES}duration") or "",
                    "season": item.findtext(f"{ITUNES}season") or "",
                    "type": item.findtext(f"{ITUNES}episodeType") or ""}
    return None


def check_redcircle(episode: int, title: str | None, get=http_get) -> list[str]:
    status, body = get(REDCIRCLE_FEED)
    if status != 200:
        return [f"FAIL RedCircle feed returned HTTP {status}"]
    item = feed_item(body, episode)
    if item is None:
        return [f"FAIL RedCircle feed has no item with itunes:episode {episode} (not published, or the episode number is missing)"]
    out = [f"ok   RedCircle episode {episode}: {normalize(item['title'])} "
           f"(duration {item['duration']}, season {item['season'] or '-'}, type {item['type'] or '-'})"]
    if title is not None and normalize(item["title"]) != normalize(title):
        out.append(f"FAIL RedCircle title differs:\n  feed:     {normalize(item['title'])}\n  expected: {normalize(title)}")
    return out


def channel_ids(xml_text: str) -> set[str]:
    return set(re.findall(r"<yt:videoId>([A-Za-z0-9_-]{11})</yt:videoId>", xml_text))


def youtube_state(oembed_status: int, in_feed: bool) -> str:
    if oembed_status == 200:
        return "public" if in_feed else "unlisted"
    if oembed_status in (401, 403):
        return "private"
    if oembed_status in (400, 404):
        return "missing"
    return f"unknown (HTTP {oembed_status})"


def check_youtube(ids: list[str], expect: str, get=http_get,
                  retries: int = 0, wait: float = 30.0, sleep=time.sleep) -> list[str]:
    out = []
    bad = [i for i in ids if not ID_RE.match(i)]
    for i in bad:
        out.append(f"FAIL {i!r} is not an 11-character video ID; copy it from Studio")
    ids = [i for i in ids if ID_RE.match(i)]
    attempts = retries if expect == "public" and retries > 0 else 0
    last = []
    for attempt in range(attempts + 1):
        status, feed = get(CHANNEL_FEED)
        if status != 200:
            return out + [f"FAIL channel feed returned HTTP {status}"]
        listed = channel_ids(feed)
        last = []
        lagging = []
        for vid in ids:
            url = OEMBED + urllib.parse.quote(f"https://www.youtube.com/watch?v={vid}", safe="")
            code, _ = get(url)
            state = youtube_state(code, vid in listed)
            mark = "ok  " if state == expect else "FAIL"
            last.append(f"{mark} {vid}: {state} (expected {expect}; oEmbed {code}, "
                        f"{'in' if vid in listed else 'not in'} channel feed)")
            if expect == "public" and code == 200 and vid not in listed:
                lagging.append(vid)
        if not lagging or attempt == attempts:
            break
        print(f"waiting {wait:g}s for channel feed ({', '.join(lagging)} not listed yet; "
              f"attempt {attempt + 1}/{attempts})", file=sys.stderr)
        sleep(wait)
    return out + last


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    rc = sub.add_parser("redcircle")
    rc.add_argument("--episode", type=int, required=True)
    rc.add_argument("--title", help="expected title, or a file holding it")
    yt = sub.add_parser("youtube")
    yt.add_argument("ids", nargs="+")
    yt.add_argument("--expect", choices=["public", "unlisted", "private"], required=True)
    yt.add_argument("--retries", type=int, default=6,
                    help="when expecting public, retry a 200 oEmbed not yet in the channel feed")
    yt.add_argument("--wait", type=float, default=30,
                    help="seconds between channel-feed retries (default 30; six retries ≈ 3 min)")
    a = ap.parse_args(argv)
    if a.cmd == "redcircle":
        lines = check_redcircle(a.episode, _read(a.title) if a.title else None)
    else:
        lines = check_youtube(a.ids, a.expect, retries=a.retries, wait=a.wait)
    print("\n".join(lines))
    return 1 if any(l.startswith("FAIL") for l in lines) else 0


if __name__ == "__main__":
    sys.exit(main())
