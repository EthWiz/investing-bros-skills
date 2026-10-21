#!/usr/bin/env python3
"""Resumable YouTube Data API uploader for Investing Bros.
Credentials: ~/.config/youtube-uploader/{client_secret.json,token.json} (never commit/print).
Uploads default to private (unaudited app forces private anyway)."""
import argparse, os, random, sys, time
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

DIR = os.environ.get("YT_UPLOADER_DIR", os.path.expanduser("~/.config/youtube-uploader"))
TOKEN = os.path.join(DIR, "token.json")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]
CHUNK = 16 * 1024 * 1024
RETRY_STATUS = {500, 502, 503, 504}
MAX_RETRIES = 10

def creds():
    if not os.path.exists(TOKEN):
        sys.exit(f"No token at {TOKEN}; run auth.py (user must click Allow).")
    c = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if not c.valid:
        try:
            c.refresh(Request())
        except Exception as e:
            sys.exit(f"Token refresh failed ({type(e).__name__}); rerun auth.py to reauthorize (7-day expiry in Testing).")
        with open(TOKEN, "w") as f: f.write(c.to_json())
        os.chmod(TOKEN, 0o600)
    return c

def retry(fn, what):
    for n in range(MAX_RETRIES):
        try:
            return fn()
        except HttpError as e:
            if e.resp.status not in RETRY_STATUS: raise
            err = f"HTTP {e.resp.status}"
        except (OSError, ConnectionError) as e:
            err = type(e).__name__
        s = min(2 ** n + random.random(), 64)
        print(f"{what}: {err}, retry {n+1}/{MAX_RETRIES} in {s:.1f}s", file=sys.stderr); time.sleep(s)
    sys.exit(f"{what}: giving up after {MAX_RETRIES} retries")

def upload(yt, a):
    body = {"snippet": {"title": a.title, "description": a.description or "",
                        "tags": [t.strip() for t in (a.tags or "").split(",") if t.strip()],
                        "categoryId": a.category},
            "status": {"privacyStatus": a.privacy, "selfDeclaredMadeForKids": False}}
    media = MediaFileUpload(a.file, chunksize=CHUNK, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = retry(req.next_chunk, "upload chunk")
        if status: print(f"uploaded {int(status.progress()*100)}%", file=sys.stderr)
    return resp["id"]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("file", nargs="?", help="video file")
    p.add_argument("--title"); p.add_argument("--description", default="")
    p.add_argument("--description-file", help="read description from file")
    p.add_argument("--tags", default="", help="comma-separated")
    p.add_argument("--category", default="22")
    p.add_argument("--thumbnail", help="image to set via thumbnails.set")
    p.add_argument("--playlist", help="playlist id to add the video to")
    p.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    p.add_argument("--set-thumbnail", metavar="VIDEO_ID", help="only set --thumbnail on an existing video")
    p.add_argument("--check-auth", action="store_true", help="refresh token and print channel title; no upload")
    a = p.parse_args()
    yt = build("youtube", "v3", credentials=creds(), cache_discovery=False)
    if a.check_auth:
        r = yt.channels().list(part="snippet", mine=True).execute()
        for i in r.get("items", []): print(f"AUTH_OK channel: {i['snippet']['title']} ({i['id']})")
        return
    if a.set_thumbnail:
        if not a.thumbnail: p.error("--set-thumbnail needs --thumbnail")
        retry(lambda: yt.thumbnails().set(videoId=a.set_thumbnail, media_body=MediaFileUpload(a.thumbnail)).execute(), "thumbnail")
        print("THUMBNAIL_SET", a.set_thumbnail); return
    if not a.file or not a.title: p.error("file and --title required")
    if a.description_file: a.description = open(a.description_file).read()
    vid = upload(yt, a)
    print(f"VIDEO_ID {vid}\nURL https://youtu.be/{vid}")
    if a.thumbnail:
        retry(lambda: yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(a.thumbnail)).execute(), "thumbnail")
        print("THUMBNAIL_SET")
    if a.playlist:
        retry(lambda: yt.playlistItems().insert(part="snippet", body={"snippet": {"playlistId": a.playlist,
              "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute(), "playlist")
        print("PLAYLIST_ADDED", a.playlist)

if __name__ == "__main__":
    main()
