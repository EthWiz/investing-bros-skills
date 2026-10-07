#!/usr/bin/env bash
# Render one promo clip (short or teaser segment) with optional burned-in captions.
#
# Usage:
#   make_clip.sh --source FILE --start S --end E [--format vertical|square]
#                [--captions FILE.ass] [--cover IMAGE] [--fonts-dir DIR] OUT.mp4
#
#   --source   raw recording: video (.mp4/.mov/...) or audio-only (.m4a/.mp3/.wav)
#   --start/--end  seconds (or HH:MM:SS) on the source's (raw) timeline
#   --format   vertical = 1080x1920 (shorts, default), square = 1080x1080 (teaser)
#   --cover    required for audio-only sources: renders an audiogram (cover + waveform)
#   --captions .ass from clip_captions.py (same --format)
#   --fonts-dir  folder with the caption font, if it isn't installed system-wide
#
# Video sources keep the whole frame (both hosts visible) over a blurred fill.
set -euo pipefail

src="" start="" end="" fmt="vertical" subs="" cover="" fontsdir="" out=""
while (( $# )); do
  case "$1" in
    --source) src="$2"; shift 2 ;;
    --start) start="$2"; shift 2 ;;
    --end) end="$2"; shift 2 ;;
    --format) fmt="$2"; shift 2 ;;
    --captions) subs="$2"; shift 2 ;;
    --cover) cover="$2"; shift 2 ;;
    --fonts-dir) fontsdir="$2"; shift 2 ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    -*) echo "error: unknown option $1" >&2; exit 2 ;;
    *) out="$1"; shift ;;
  esac
done
[[ -n "$src" && -n "$start" && -n "$end" && -n "$out" ]] || { sed -n '2,17p' "$0" >&2; exit 2; }
[[ -f "$src" ]] || { echo "error: source not found: $src" >&2; exit 1; }
[[ -z "$subs" || -f "$subs" ]] || { echo "error: captions not found: $subs" >&2; exit 1; }
[[ -e "$out" ]] && { echo "error: $out exists; refusing to overwrite" >&2; exit 1; }

case "$fmt" in
  vertical) W=1080 H=1920 ;;
  square)   W=1080 H=1080 ;;
  *) echo "error: --format must be vertical or square" >&2; exit 2 ;;
esac

has_video=$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_type -of csv=p=0 "$src" | head -n1 || true)
# Cover art embedded in an m4a/mp3 shows up as a video stream; treat those as audio-only.
attached=$(ffprobe -v error -select_streams v:0 -show_entries stream_disposition=attached_pic -of csv=p=0 "$src" | head -n1 || true)
[[ "$attached" == "1" ]] && has_video=""

esc() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e "s/'/\\\\'/g" -e 's/:/\\:/g'; }
sub_filter=""
if [[ -n "$subs" ]]; then
  sub_filter=",subtitles='$(esc "$subs")'"
  [[ -n "$fontsdir" ]] && sub_filter+=":fontsdir='$(esc "$fontsdir")'"
fi

if [[ -n "$has_video" ]]; then
  inputs=(-ss "$start" -to "$end" -i "$src")
  graph="[0:v]scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},boxblur=30:3,eq=brightness=-0.15[bg];"
  graph+="[0:v]scale=${W}:${H}:force_original_aspect_ratio=decrease[fg];"
  graph+="[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,fps=30${sub_filter},format=yuv420p[v]"
  amap="0:a:0"
else
  [[ -n "$cover" ]] || { echo "error: audio-only source needs --cover IMAGE for an audiogram" >&2; exit 1; }
  [[ -f "$cover" ]] || { echo "error: cover not found: $cover" >&2; exit 1; }
  if [[ "$fmt" == vertical ]]; then C=960 CY=220 WY=1220 WH=140; else C=700 CY=40 WY=760 WH=110; fi
  inputs=(-loop 1 -framerate 30 -i "$cover" -ss "$start" -to "$end" -i "$src")
  graph="[0:v]scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},boxblur=40:4,eq=brightness=-0.3[bg];"
  graph+="[0:v]scale=${C}:${C}:force_original_aspect_ratio=increase,crop=${C}:${C}[art];"
  graph+="[1:a:0]showwaves=s=${C}x${WH}:mode=cline:scale=sqrt:colors=white:rate=30,format=rgba[wave];"
  graph+="[bg][art]overlay=(W-w)/2:${CY}[b1];[b1][wave]overlay=(W-w)/2:${WY}:shortest=1,setsar=1${sub_filter},format=yuv420p[v]"
  amap="1:a:0"
fi

ffmpeg -hide_banner -loglevel error -nostdin "${inputs[@]}" \
  -filter_complex "$graph" -map "[v]" -map "$amap" -shortest \
  -c:v libx264 -preset veryfast -crf 20 -r 30 -c:a aac -b:a 160k -ar 48000 -movflags +faststart "$out"
echo "$out: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out") s, ${W}x${H}"
