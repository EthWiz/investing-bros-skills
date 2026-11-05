#!/usr/bin/env python3
"""Resumable YouTube Data API uploader for Investing Bros: Private only, show channel only,
and never the same asset twice.

  yt_upload.py --check-auth
  yt_upload.py FILE --title T [--description-file F] [--tags a,b] [--thumbnail IMG] [--playlist ID]
               --asset main|seg01|seg02|short01|short02|short03 --record extras/uploads/ASSET.json
               [--version V] [--replace]
  yt_upload.py --resume extras/uploads/ASSET.json [--thumbnail IMG] [--playlist ID]
  yt_upload.py --set-thumbnail VIDEO_ID --thumbnail IMG

Credentials: ~/.config/youtube-uploader/{client_secret.json,token.json} (never commit/print).

Rules the script enforces:
- Privacy is always private. Going Public happens in Studio, after the episode owner's
  publish OK (investing-bros-publish).
- Before any insert it checks that the token's channel is the show channel (אחים להשקעות,
  investing-bros-show -> Roles and accounts) and refuses otherwise.
- Right after a successful insert it writes the upload record (asset, version, channel,
  video_id, steps, steps_done), before the thumbnail and the playlist. If a later step
  fails, rerun with --resume RECORD: it finishes the remaining steps on the same video
  ID and never inserts again.
- A record already holding this asset version refuses a second insert, unless --replace
  (the old ID moves to `superseded`, for the old-uploads cleanup). A new version of the
  asset (a fixed file) is a normal re-upload; the old ID is recorded as superseded too.
  version defaults to the file's sha256.
"""
import argparse
import hashlib
import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SHOW_CHANNEL_ID = "UCWIlggXQNDFiyJghl6VB6Xw"  # אחים להשקעות; investing-bros-show -> Roles and accounts
DIR = os.environ.get("YT_UPLOADER_DIR", os.path.expanduser("~/.config/youtube-uploader"))
TOKEN = os.path.join(DIR, "token.json")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]
CHUNK = 16 * 1024 * 1024
RETRY_STATUS = {500, 502, 503, 504}
MAX_RETRIES = 10
ASSETS = ["main", "seg01", "seg02", "short01", "short02", "short03"]


class Refused(Exception):
    """A rule of this script says no; nothing was uploaded by the refused step."""


def creds():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    if not os.path.exists(TOKEN):
        sys.exit(f"No token at {TOKEN}; run yt_auth.py (user must click Allow).")
    c = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if not c.valid:
        try:
            c.refresh(Request())
        except Exception as e:
            sys.exit(f"Token refresh failed ({type(e).__name__}); rerun yt_auth.py to reauthorize (7-day expiry in Testing).")
        with open(TOKEN, "w") as f:
            f.write(c.to_json())
        os.chmod(TOKEN, 0o600)
    return c


def client():
    from googleapiclient.discovery import build
    return build("youtube", "v3", credentials=creds(), cache_discovery=False)


def media(path, resumable=False):
    from googleapiclient.http import MediaFileUpload
    return MediaFileUpload(path, chunksize=CHUNK, resumable=True) if resumable else MediaFileUpload(path)


def retry(fn, what, sleep=time.sleep):
    for n in range(MAX_RETRIES):
        try:
            return fn()
        except (OSError, ConnectionError) as e:
            err = type(e).__name__
        except Exception as e:  # googleapiclient HttpError: retry only server errors
            status = getattr(getattr(e, "resp", None), "status", None)
            if status not in RETRY_STATUS:
                raise
            err = f"HTTP {status}"
        s = min(2 ** n + random.random(), 64)
        print(f"{what}: {err}, retry {n+1}/{MAX_RETRIES} in {s:.1f}s", file=sys.stderr)
        sleep(s)
    raise RuntimeError(f"{what}: giving up after {MAX_RETRIES} retries")


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def active_channel(yt) -> str:
    items = yt.channels().list(part="snippet", mine=True).execute().get("items", [])
    return items[0]["id"] if items else ""


def require_show_channel(yt) -> str:
    cid = active_channel(yt)
    if cid != SHOW_CHANNEL_ID:
        raise Refused(f"refused: the token's channel is {cid or 'none'}, not אחים להשקעות ({SHOW_CHANNEL_ID}); "
                      "rerun yt_auth.py and pick the brand channel")
    return cid


def load_record(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def save_record(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def insert(yt, a, sleep=time.sleep) -> str:
    body = {"snippet": {"title": a.title, "description": a.description or "",
                        "tags": [t.strip() for t in (a.tags or "").split(",") if t.strip()],
                        "categoryId": a.category},
            "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}}
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media(a.file, resumable=True))
    resp = None
    while resp is None:
        status, resp = retry(req.next_chunk, "upload chunk", sleep)
        if status:
            print(f"uploaded {int(status.progress()*100)}%", file=sys.stderr)
    return resp["id"]


def finish(yt, rec: dict, path: Path, sleep=time.sleep) -> None:
    """The steps after the insert, each recorded as soon as it is done."""
    vid = rec["video_id"]
    for step in rec["steps"]:
        if step["name"] in rec["steps_done"]:
            continue
        if step["name"] == "thumbnail":
            retry(lambda: yt.thumbnails().set(videoId=vid, media_body=media(step["file"])).execute(), "thumbnail", sleep)
            print("THUMBNAIL_SET")
        elif step["name"] == "playlist":
            retry(lambda: yt.playlistItems().insert(part="snippet", body={"snippet": {"playlistId": step["id"],
                  "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute(), "playlist", sleep)
            print("PLAYLIST_ADDED", step["id"])
        rec["steps_done"].append(step["name"])
        save_record(path, rec)


def planned_steps(a) -> list:
    steps = []
    if a.thumbnail:
        steps.append({"name": "thumbnail", "file": a.thumbnail})
    if a.playlist:
        steps.append({"name": "playlist", "id": a.playlist})
    return steps


def upload(yt, a, sleep=time.sleep) -> dict:
    path = Path(a.record)
    source_sha = sha256_file(a.source) if getattr(a, "source", None) else None
    version = a.version or source_sha or sha256_file(a.file)
    old = load_record(path)
    superseded = list(old.get("superseded", [])) if old else []
    if old and old.get("video_id"):
        if old.get("asset") != a.asset:
            raise Refused(f"refused: {path} is the record of {old.get('asset')}, not {a.asset}")
        if old.get("version") == version and not a.replace:
            missing = [s["name"] for s in old.get("steps", []) if s["name"] not in old.get("steps_done", [])]
            hint = f"finish it with --resume {path}" if missing else "it is complete"
            raise Refused(f"refused: {a.asset} version {version[:12]} is already uploaded as {old['video_id']} "
                          f"({hint}); a second copy needs --replace")
        superseded.append({"video_id": old["video_id"], "version": old.get("version"), "at": now()})
    channel = require_show_channel(yt)
    vid = insert(yt, a, sleep)
    rec = {"asset": a.asset, "version": version, "channel": channel, "video_id": vid, "privacy": "private",
           "file": os.path.basename(a.file), "file_sha256": sha256_file(a.file),
           **({"source": os.path.basename(a.source), "source_sha256": source_sha} if source_sha else {}),
           "title": a.title,
           "created_at": now(), "steps": planned_steps(a), "steps_done": ["insert"], "superseded": superseded}
    save_record(path, rec)
    print(f"VIDEO_ID {vid}\nURL https://youtu.be/{vid}\nRECORD {path}")
    if superseded:
        print("SUPERSEDED " + " ".join(s["video_id"] for s in superseded) + " (delete once the new upload is verified)")
    finish(yt, rec, path, sleep)
    return rec


def resume(yt, a, sleep=time.sleep) -> dict:
    path = Path(a.resume)
    rec = load_record(path)
    if not rec or not rec.get("video_id"):
        raise Refused(f"refused: {path} has no uploaded video to resume; nothing was inserted")
    names = {s["name"] for s in rec["steps"]}
    for s in planned_steps(a):  # steps added on the command line (e.g. a thumbnail that wasn't ready)
        if s["name"] not in names:
            rec["steps"].append(s)
    save_record(path, rec)
    print(f"VIDEO_ID {rec['video_id']} (resumed; no new insert)")
    finish(yt, rec, path, sleep)
    return rec


def parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("file", nargs="?", help="video file")
    p.add_argument("--title"); p.add_argument("--description", default="")
    p.add_argument("--description-file", help="read description from file")
    p.add_argument("--tags", default="", help="comma-separated")
    p.add_argument("--category", default="22")
    p.add_argument("--thumbnail", help="image to set via thumbnails.set")
    p.add_argument("--playlist", help="playlist id to add the video to")
    p.add_argument("--privacy", default="private", choices=["private"],
                   help="always private; Public is set in Studio after the publish OK")
    p.add_argument("--asset", choices=ASSETS, help="which deliverable this is (the pipeline track)")
    p.add_argument("--record", help="upload record to write, e.g. extras/uploads/main.json")
    p.add_argument("--source", help="the file this upload was made from (the full video master the compressed "
                   "copy came from, checked with verify_sync.py); its sha256 is the asset version")
    p.add_argument("--version", help="asset version (default: the --source sha256, else the file's)")
    p.add_argument("--replace", action="store_true", help="upload this version again; the old ID becomes superseded")
    p.add_argument("--resume", metavar="RECORD", help="finish thumbnail/playlist on the recorded video; never inserts")
    p.add_argument("--set-thumbnail", metavar="VIDEO_ID", help="only set --thumbnail on an existing video")
    p.add_argument("--check-auth", action="store_true", help="refresh token and print channel; no upload")
    return p


def main(argv=None, yt=None, sleep=time.sleep) -> int:
    p = parser()
    a = p.parse_args(argv)
    if not (a.check_auth or a.set_thumbnail or a.resume):
        if not a.file or not a.title:
            p.error("file and --title required")
        if not a.asset or not a.record:
            p.error("--asset and --record are required for an upload (the record prevents a second copy)")
    if a.set_thumbnail and not a.thumbnail:
        p.error("--set-thumbnail needs --thumbnail")
    if a.description_file:
        a.description = Path(a.description_file).read_text(encoding="utf-8")
    yt = yt or client()
    try:
        if a.check_auth:
            r = yt.channels().list(part="snippet", mine=True).execute()
            for i in r.get("items", []):
                mark = "AUTH_OK" if i["id"] == SHOW_CHANNEL_ID else "WRONG_CHANNEL"
                print(f"{mark} channel: {i['snippet']['title']} ({i['id']})")
            return 0
        if a.set_thumbnail:
            retry(lambda: yt.thumbnails().set(videoId=a.set_thumbnail, media_body=media(a.thumbnail)).execute(),
                  "thumbnail", sleep)
            print("THUMBNAIL_SET", a.set_thumbnail)
            return 0
        if a.resume:
            resume(yt, a, sleep)
        else:
            upload(yt, a, sleep)
    except Refused as e:
        print(e, file=sys.stderr)
        return 1
    except Exception as e:
        rec = a.resume or a.record
        print(f"FAILED: {type(e).__name__}: {e}", file=sys.stderr)
        if rec and (load_record(Path(rec)) or {}).get("video_id"):
            print(f"the video is uploaded; finish with: yt_upload.py --resume {rec}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
