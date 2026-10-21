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
set -euo pipefail
cmd=${1:?get|put}
case "$cmd" in
  get) rclone backend copyid show: "${2:?FILE_ID}" "${3:?DEST_DIR}/" --progress ;;
  put) rclone copy "${2:?LOCAL_FILE}" "show:" --drive-root-folder-id "${3:?FOLDER_ID}" --progress ;;
  *) echo "usage: drive.sh get FILE_ID DEST | put FILE FOLDER_ID" >&2; exit 2 ;;
esac
