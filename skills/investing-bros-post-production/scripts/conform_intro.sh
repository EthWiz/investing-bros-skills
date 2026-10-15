#!/bin/bash
# conform_intro.sh REF.mp4 OUT.mp4 - ONLY if the episode spec differs from the intro (intro is 1280x720/24, episode 1920x1080/24).
# Pure scale/format conform of Amitai's intro (no edits to picture, timing or audio levels). Prefer producing the episode at intro spec.
# Env: INTRO (required) — Amitai's intro mp4. No default path.
. "$(dirname "$0")/lib.sh"
: "${INTRO:?set INTRO=path/to/intro.mp4}"
spec "$1"
ffmpeg -v error -y -i "$INTRO" -vf "scale=$W:$H:flags=lanczos,fps=$FPS,setsar=1" $ENC_V $ENC_A -video_track_timescale "$TS" "$2"; echo "$2"
