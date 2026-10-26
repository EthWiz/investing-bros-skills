#!/usr/bin/env bash
# Download raw files from / upload promo files to the show's Drive with rclone
# (Drive API on www.googleapis.com; no browser, no 10 MB connector limit).
#
#   bash drive.sh get FILE_ID DEST_DIR          # e.g. the raw episode video
#   bash drive.sh put LOCAL_FILE FOLDER_ID      # e.g. a short + its cover into the episode's Shorts/
#
# Needs an rclone remote named "show" signed in as the show's bot account
# (investing-bros-show -> Roles and accounts), config path in $RCLONE_CONFIG.
# One-time setup (Amitai): rclone config create show drive scope=drive  (sign in as the bot).
# Never sign in with Amitai's own account (Advanced Protection blocks it).
#
# rclone is not preinstalled on the box. Install it (no sudo needed):
#   curl -fsSL https://downloads.rclone.org/rclone-current-linux-amd64.zip -o /tmp/rc.zip \
#     && unzip -oq /tmp/rc.zip -d /tmp && install -m755 /tmp/rclone-*-linux-amd64/rclone ~/.local/bin/
# On a Mac: brew install rclone. The one-time sign-in opens a Google page in the browser; Amitai
# signs in there as the bot account (Advanced Protection blocks rclone on his own account).
# If rclone or the "show" remote isn't available, use the Google Drive connector
# instead (DownloadFile / UploadFile with the user's Drive connection), or for
# big files the box browser signed in as the show's bot account (authuser=1).
set -euo pipefail
if ! command -v rclone >/dev/null 2>&1; then
  echo "drive.sh: rclone not installed - install it (see header) or use the Google Drive connector (DownloadFile/UploadFile)" >&2
  exit 3
fi
cmd=${1:?get|put}
case "$cmd" in
  get) rclone backend copyid show: "${2:?FILE_ID}" "${3:?DEST_DIR}/" --progress ;;
  put) rclone copy "${2:?LOCAL_FILE}" "show:" --drive-root-folder-id "${3:?FOLDER_ID}" --progress ;;
  *) echo "usage: drive.sh get FILE_ID DEST | put FILE FOLDER_ID" >&2; exit 2 ;;
esac
