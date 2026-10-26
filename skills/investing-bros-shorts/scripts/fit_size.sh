#!/usr/bin/env bash
# Re-encode a finished short so it fits an upload limit (default 9.5 MB), two-pass x264.
#
# Usage:
#   fit_size.sh IN.mp4 OUT.m4v [MAX_MB]
#
# Why: Claude in Chrome's file upload (the agent's way into Drive's web UI) takes at most
# 10 MB per call, and the Drive connector can't carry video at all. A 45 s 1080x1920 short
# at ~1.5 Mb/s still looks clean — the platforms re-encode to about that anyway.
# If IN already fits, it is copied unchanged. Audio stays AAC 128k.
set -euo pipefail
in="${1:?usage: fit_size.sh IN.mp4 OUT.m4v [MAX_MB]}"; out="${2:?OUT.m4v}"; max="${3:-9.5}"
[[ -f "$in" ]] || { echo "error: not found: $in" >&2; exit 1; }
[[ "$out" == *.m4v ]] || { echo "error: Drive Shorts must use a .m4v filename so Drive assigns video/x-m4v" >&2; exit 1; }
[[ -e "$out" ]] && { echo "error: $out exists; refusing to overwrite" >&2; exit 1; }
size=$(stat -c %s "$in" 2>/dev/null || stat -f %z "$in")
if awk -v s="$size" -v m="$max" 'BEGIN { exit !(s <= m * 1000000) }'; then
  cp "$in" "$out"; echo "$out: already under ${max} MB, copied"; exit 0
fi
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
vk=$(awk -v m="$max" -v d="$dur" 'BEGIN { printf "%d", m * 8000 / d - 128 - 40 }')
(( vk > 300 )) || { echo "error: ${max} MB is too small for ${dur}s" >&2; exit 1; }
log="$(mktemp -t fitsize-XXXXXX)"
trap 'rm -f "$log"*' EXIT
ffmpeg -v error -nostdin -y -i "$in" -c:v libx264 -preset slow -b:v "${vk}k" -pass 1 -passlogfile "$log" -an -f null /dev/null
ffmpeg -v error -nostdin -i "$in" -c:v libx264 -preset slow -b:v "${vk}k" -maxrate "$((vk * 2))k" -bufsize "$((vk * 2))k" \
  -pass 2 -passlogfile "$log" -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart "$out"
echo "$out: $(awk -v s="$(stat -c %s "$out" 2>/dev/null || stat -f %z "$out")" 'BEGIN { printf "%.1f", s / 1000000 }') MB (video ${vk} kb/s)"
