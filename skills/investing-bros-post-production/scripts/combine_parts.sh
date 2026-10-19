#!/usr/bin/env bash
# Combine recording parts (audio or video) into one raw master, in the order given.
#
# Usage:
#   combine_parts.sh [--video OUT_VIDEO.mp4] OUT_AUDIO.m4a PART1 [PART2 ...]
#
# - Audio is always produced (AAC 192k, 48 kHz) from every part's first audio stream.
# - With --video, the parts' video is also joined (scaled/padded to 1920x1080, 30 fps)
#   so promo clips can use it later. All parts must then contain video.
# - Refuses to overwrite an existing output (the raw master must never be overwritten).
set -euo pipefail

video_out=""
if [[ "${1:-}" == "--video" ]]; then
  video_out="${2:?--video needs an output path}"
  shift 2
fi
out="${1:?usage: combine_parts.sh [--video OUT.mp4] OUT.m4a PART1 [PART2 ...]}"
shift
(( $# >= 1 )) || { echo "error: no input parts given" >&2; exit 2; }

for f in "$out" ${video_out:+"$video_out"}; do
  [[ -e "$f" ]] && { echo "error: $f already exists; refusing to overwrite" >&2; exit 1; }
done
for p in "$@"; do
  [[ -f "$p" ]] || { echo "error: part not found: $p" >&2; exit 1; }
done

inputs=(); filt=""; n=$#; i=0
for p in "$@"; do
  inputs+=(-i "$p")
  filt+="[$i:a:0]aresample=48000:async=1:min_hard_comp=0.01:first_pts=0,aformat=channel_layouts=stereo[a$i];"
  i=$((i + 1))
done
for ((i = 0; i < n; i++)); do filt+="[a$i]"; done
filt+="concat=n=$n:v=0:a=1[a]"

ffmpeg -hide_banner -loglevel error -nostdin "${inputs[@]}" \
  -filter_complex "$filt" -map "[a]" -c:a aac -b:a 192k "$out"
echo "audio: $out ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out") s)"

if [[ -n "$video_out" ]]; then
  vf=""
  for ((i = 0; i < n; i++)); do
    vf+="[$i:v:0]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v$i];"
    vf+="[$i:a:0]aresample=48000:async=1:min_hard_comp=0.01:first_pts=0,aformat=channel_layouts=stereo[a$i];"
  done
  for ((i = 0; i < n; i++)); do vf+="[v$i][a$i]"; done
  vf+="concat=n=$n:v=1:a=1[v][a]"
  ffmpeg -hide_banner -loglevel error -nostdin "${inputs[@]}" \
    -filter_complex "$vf" -map "[v]" -map "[a]" \
    -c:v libx264 -preset veryfast -crf 20 -c:a aac -b:a 192k "$video_out"
  echo "video: $video_out"
fi
