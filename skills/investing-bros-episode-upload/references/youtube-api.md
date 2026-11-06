# YouTube Data API upload (preferred when credentials exist)

On the Grok Bot box, `~/.config/youtube-uploader/` holds `client_secret.json` (Desktop OAuth client, Google Cloud project `investing-bros-uploader`), `token.json` (refresh token, scopes `youtube.upload` + `youtube`) and `venv/` (google-auth-oauthlib, google-api-python-client). If both files exist, upload through the API instead of the Studio browser flow. The credentials never go in the repo, in chat or in logs; the scripts never print them.

## Why
- Resumable, chunked (16 MB) upload with retry and backoff: a dropped connection resumes, it doesn't restart a 2 GB file.
- Frees the box browser (only one browser job runs at a time), so other work keeps going during a long upload.
- Not faster: upload bandwidth is the limit either way.

## Run
```bash
D=~/.config/youtube-uploader; PY=$D/venv/bin/python
S=skills/investing-bros-episode-upload/scripts
$PY $S/yt_upload.py --check-auth          # AUTH_OK channel: <title> (<id>); WRONG_CHANNEL means rerun yt_auth.py
$PY $S/yt_upload.py "$EP/extras/פרק-N-youtube.mp4" --source "$EP/video/פרק-N-וידאו.mp4" \
    --title "$(cat title.txt)" --description-file desc.txt \
    --tags "השקעות,פודקאסט" --thumbnail thumb.jpg [--playlist PLAYLIST_ID] \
    --asset main --record "$EP/extras/uploads/main.json"                  # always Private
$PY $S/yt_upload.py --resume "$EP/extras/uploads/main.json"           # after a failure: finish, never insert again
$PY $S/yt_upload.py --set-thumbnail VIDEO_ID --thumbnail thumb.jpg \
    --asset main --record "$EP/extras/uploads/main.json"            # swap only; does not rewrite the upload record
```
It prints `VIDEO_ID`, `URL` and `RECORD`. The record (`asset`, `version`, `channel`, `video_id`,
`steps`, `steps_done`, `file_sha256`, `source_sha256`, `superseded`) is the episode's proof of what
is uploaded; `investing-bros-producer` reads it. A thumbnail that is set also writes
`extras/uploads/<asset>-thumb.json` (`asset`, `video_id`, `file`, `sha256`, `set_at`) beside that
record. The image sha256 is not a field of the upload record, so a swap does not stale `ok` or
`publish_ok`. `can-public` checks the side record against the approved pick. When `thumbnails.set`
refuses a Short cover, the phone-app acknowledgement is `publish_checklist.py record-thumb`
(`investing-bros-publish`), not a hand-written file and not a waiver. `version` is the sha256 of `--source` (for the full
episode: the master the compressed copy was made from, after `verify_sync.py` showed `SYNC OK`), else
of the uploaded file; the Producer refuses a record whose version isn't the current video's. After a
Studio upload, write the record by hand with `source_sha256` = `shasum -a 256` of that video. The script refuses:
- any channel but אחים להשקעות (checked before every insert);
- a second insert of the same asset version (finish with `--resume`, or pass `--replace` to
  upload it again on purpose; the old ID goes to `superseded` for the cleanup);
- `--privacy public|unlisted` (Public is set in Studio after the publish OK).
A new version of an asset (a fixed file) uploads normally and lists the old ID under
`superseded`. Copy the script from the repo; the credentials stay in `~/.config/youtube-uploader/` (override with `YT_UPLOADER_DIR`).

## Limits
- **Private only.** The app is unaudited, so every API upload is locked Private. That fits the rule anyway: switching to Public/scheduled is done in Studio **only after Amitai's OK**.
- **Quota:** 10,000 units/day; an upload costs 1,600, so about 6 uploads a day (thumbnails/playlist calls cost a little more). Free, no billing account.
- **Reauth every ~7 days** while the OAuth app is in Testing. When refresh fails, the script says so: run `$PY $S/yt_auth.py` (loopback on `localhost:8765`), open the `AUTH_URL` in the box browser, and hand the screen to Amitai to pick the **Investing Bros brand channel** and click Allow. `TOKEN_SAVED` means done.
- Still in Studio: Related video on Shorts, `.srt` captions, visibility change, chapters check.
  The API can't set a Short's Related video. Set it in Studio and verify it by reopening the edit page; a Short
  without it stays Private, and a description link does not count (`investing-bros-publish`).

## Fallback
If the credentials are missing, the token can't be refreshed and Amitai isn't available to reauth, or the quota is used up, use the browser flow in [youtube-studio.md](youtube-studio.md).
