#!/usr/bin/env bash
# Join rendered clips (all the same --format from make_clip.sh) into one teaser,
# with a short fade at each join and at both ends.
#
# Usage:
#   make_teaser.sh OUT.mp4 CLIP1.mp4 CLIP2.mp4 [...]
set -euo pipefail
out="${1:?usage: make_teaser.sh OUT.mp4 CLIP1.mp4 CLIP2.mp4 [...]}"; shift
(( $# >= 1 )) || { echo "error: give at least one clip" >&2; exit 2; }
[[ -e "$out" ]] && { echo "error: $out exists; refusing to overwrite" >&2; exit 1; }

F=0.25   # fade length in seconds
size=""
inputs=(); graph=""; i=0
for c in "$@"; do
  [[ -f "$c" ]] || { echo "error: not found: $c" >&2; exit 1; }
  s=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$c")
  [[ -z "$size" ]] && size="$s"
  [[ "$s" == "$size" ]] || { echo "error: $c is $s but the first clip is $size; render all clips with the same --format" >&2; exit 1; }
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$c")
  fo=$(awk -v d="$d" -v f="$F" 'BEGIN { printf "%.3f", d - f }')
  inputs+=(-i "$c")
  graph+="[$i:v]fade=t=in:st=0:d=$F,fade=t=out:st=$fo:d=$F,setsar=1[v$i];"
  graph+="[$i:a]afade=t=in:st=0:d=$F,afade=t=out:st=$fo:d=$F[a$i];"
  i=$((i + 1))
done
for ((j = 0; j < i; j++)); do graph+="[v$j][a$j]"; done
graph+="concat=n=$i:v=1:a=1[v][a]"

ffmpeg -hide_banner -loglevel error -nostdin "${inputs[@]}" -filter_complex "$graph" \
  -map "[v]" -map "[a]" -c:v libx264 -preset veryfast -crf 20 -c:a aac -b:a 160k -movflags +faststart "$out"
echo "$out: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out") s, $size"
