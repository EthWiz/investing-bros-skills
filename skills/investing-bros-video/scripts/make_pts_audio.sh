#!/usr/bin/env bash
# Extract audio without collapsing timestamp gaps in AAC or other packetized input.
# Usage: make_pts_audio.sh INPUT_MEDIA OUTPUT.wav
set -euo pipefail

in="${1:?usage: make_pts_audio.sh INPUT_MEDIA OUTPUT.wav}"
out="${2:?usage: make_pts_audio.sh INPUT_MEDIA OUTPUT.wav}"
[[ -f "$in" ]] || { echo "error: not found: $in" >&2; exit 1; }
[[ -e "$out" ]] && { echo "error: $out exists; refusing to overwrite" >&2; exit 1; }

ffmpeg -v error -nostdin -y -i "$in" -map 0:a:0 -vn \
  -af "aresample=async=1:min_hard_comp=0.01:first_pts=0,aformat=channel_layouts=stereo" \
  -ar 48000 -c:a pcm_s16le "$out"

source_duration=$(ffprobe -v error -select_streams a:0 -show_entries stream=duration \
  -of default=noprint_wrappers=1:nokey=1 "$in")
[[ -n "$source_duration" && "$source_duration" != "N/A" ]] || \
  source_duration=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
wav_duration=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out")

python3 - "$source_duration" "$wav_duration" <<'PY'
import sys

source, wav = map(float, sys.argv[1:])
drift = abs(source - wav)
print(f"source audio {source:.3f}s, WAV {wav:.3f}s, drift {drift:.3f}s")
if drift > 0.05:
    raise SystemExit("error: extracted audio does not match the source PTS timeline")
PY
