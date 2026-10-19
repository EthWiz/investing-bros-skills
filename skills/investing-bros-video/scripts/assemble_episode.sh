#!/usr/bin/env bash
# Build the full VIDEO episode: cold-open clips (teasers) + intro + episode body,
# with the leveled audio, as one 1920x1080 MP4.
#
# Usage:
#   assemble_episode.sh OUT.mp4 --body VIDEO --body-audio LEVELED.wav
#                       [--edit edit.json | --start S --end E] [--before CLIP.mp4]... [--intro INTRO.mp4]
#                       [--chunk 460] [--max-seconds N]
#
#   --body        the episode video (raw master or Riverside export), 1920x1080
#   --body-audio  level_audio.sh output for that SAME file (same timeline)
#   --edit        edit.json from trim.sh: start, end and any cuts inside the episode
#                 (same timeline as --body); the body skips every cut
#   --start/--end cut points on that timeline when there is no edit.json (default: whole file)
#   --before      clips that play first, in order (e.g. the teasers); repeatable
#   --intro       the show intro, played after the --before clips
#   --chunk       body is encoded in chunks of this many seconds (default 460)
#   --max-seconds stop after about this long and print "resume"; re-run the same
#                 command to continue. For shells with a per-command time limit.
#
# Every segment is encoded with the same x264 settings (any size is scaled and
# padded to 1920x1080 on black, 24 fps) and joined with the concat demuxer
# (-c copy), so a 45-minute body never has to be encoded in one go. Finished
# chunks are kept in OUT.parts/ and skipped on re-run. Audio is assembled as
# one WAV where every segment is trimmed/padded to its video's exact length,
# so sync cannot drift at the joins.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
X264=(-c:v libx264 -preset veryfast -crf 19 -profile:v high -level 4.0 -pix_fmt yuv420p -g 48 -video_track_timescale 24000 -r 24)
VF="scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fps=24,format=yuv420p"

out="${1:?usage: assemble_episode.sh OUT.mp4 --body VIDEO --body-audio WAV [...]}"; shift
body="" baudio="" start="" end="" editjson="" intro="" chunk=460 budget=0; before=()
while (( $# )); do
  case "$1" in
    --body) body="$2"; shift 2 ;;
    --body-audio) baudio="$2"; shift 2 ;;
    --start) start="$2"; shift 2 ;;
    --end) end="$2"; shift 2 ;;
    --edit) editjson="$2"; shift 2 ;;
    --before) before+=("$2"); shift 2 ;;
    --intro) intro="$2"; shift 2 ;;
    --chunk) chunk="$2"; shift 2 ;;
    --max-seconds) budget="$2"; shift 2 ;;
    *) echo "error: unknown option $1" >&2; exit 2 ;;
  esac
done
[[ -f "$body" && -f "$baudio" ]] || { echo "error: --body and --body-audio are required" >&2; exit 2; }
[[ -e "$out" ]] && { echo "error: $out exists; refusing to overwrite" >&2; exit 1; }
# Kept body ranges on the body's timeline, one "a b" per line.
ranges=()
if [[ -n "$editjson" ]]; then
  [[ -z "$start$end" ]] || { echo "error: use --edit or --start/--end, not both" >&2; exit 2; }
  kept=$(python3 "$here/edit_map.py" "$editjson" --keep)
  while IFS= read -r l; do [[ -n "$l" ]] && ranges+=("$l"); done <<<"$kept"
else
  [[ -z "$start" ]] && start=0
  [[ -z "$end" ]] && end=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$body")
  ranges=("$start $end")
fi
work="${out%.*}.parts"; mkdir -p "$work"
t0=$(date +%s)
over_budget() { (( budget > 0 && $(date +%s) - t0 > budget )); }
frames() { ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 "$1"; }
dur_of_frames() { awk -v f="$1" 'BEGIN { printf "%.6f", f / 24 }'; }

# 1. Short clips (before + intro): video-only segment + exact-length audio.
clip_seg() {  # $1=input $2=name
  local v="$work/$2.mp4" a="$work/$2.wav"
  if [[ ! -f "$v" ]]; then
    ffmpeg -v error -nostdin -y -i "$1" -map 0:v:0 -an -vf "$VF" "${X264[@]}" "$work/tmp.mp4" && mv "$work/tmp.mp4" "$v"
  fi
  local d; d=$(dur_of_frames "$(frames "$v")")
  ffmpeg -v error -nostdin -y -i "$1" -map 0:a:0 -af "aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration=$d" -c:a pcm_s16le "$a"
}
list=(); alist=(); i=0
for c in "${before[@]}"; do clip_seg "$c" "before$i"; list+=("before$i"); i=$((i + 1)); done
if [[ -n "$intro" ]]; then
  clip_seg "$intro" intro
  # bring the intro's music to the episode's level (-16 LUFS) so it doesn't jump out
  ffmpeg -v error -nostdin -y -i "$work/intro.wav" -af loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000 -c:a pcm_s16le "$work/intro_n.wav"
  d=$(dur_of_frames "$(frames "$work/intro.mp4")")
  ffmpeg -v error -nostdin -y -i "$work/intro_n.wav" -af "apad,atrim=duration=$d" -c:a pcm_s16le "$work/intro.wav"
  list+=(intro)
fi

# 2. Body in chunks (resumable), range by range so every cut is skipped.
body_wavs=()
for ((r = 0; r < ${#ranges[@]}; r++)); do
  read -r rs re <<<"${ranges[$r]}"
  total=$(awk -v s="$rs" -v e="$re" 'BEGIN { printf "%.6f", e - s }')
  n=$(awk -v t="$total" -v c="$chunk" 'BEGIN { printf "%d", (t + c - 0.000001) / c }')
  for ((k = 0; k < n; k++)); do
    f="$work/body${r}_$k.mp4"; list+=("body${r}_$k")
    [[ -f "$f" ]] && continue
    if over_budget; then echo "resume: range $((r + 1))/${#ranges[@]}, $k of $n chunks done — run the same command again"; exit 3; fi
    ss=$(awk -v s="$rs" -v k="$k" -v c="$chunk" 'BEGIN { printf "%.6f", s + k * c }')
    len=$(awk -v t="$total" -v k="$k" -v c="$chunk" 'BEGIN { l = t - k * c; if (l > c) l = c; printf "%.6f", l }')
    ffmpeg -v error -nostdin -y -ss "$ss" -t "$len" -i "$body" -map 0:v:0 -an -vf "$VF" "${X264[@]}" "$work/tmp.mp4"
    mv "$work/tmp.mp4" "$f"
    echo "body range $((r + 1))/${#ranges[@]}, chunk $((k + 1))/$n done ($(frames "$f") frames)"
  done

  # 3. This range's audio, trimmed to its video's frame count (keeps sync across cuts).
  bf=0; for ((k = 0; k < n; k++)); do bf=$((bf + $(frames "$work/body${r}_$k.mp4"))); done
  bd=$(dur_of_frames "$bf")
  ffmpeg -v error -nostdin -y -ss "$rs" -i "$baudio" -af "aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration=$bd" -c:a pcm_s16le "$work/body_r$r.wav"
  body_wavs+=("body_r$r")
done

# 4. Join video (copy) and audio, mux.
: > "$work/video.txt"; : > "$work/audio.txt"
for s in "${list[@]}"; do echo "file '$s.mp4'" >> "$work/video.txt"; done
for s in "${list[@]}"; do [[ "$s" == body* ]] || echo "file '$s.wav'" >> "$work/audio.txt"; done
for s in "${body_wavs[@]}"; do echo "file '$s.wav'" >> "$work/audio.txt"; done
ffmpeg -v error -nostdin -y -f concat -safe 0 -i "$work/video.txt" -c copy "$work/video.mp4"
ffmpeg -v error -nostdin -y -f concat -safe 0 -i "$work/audio.txt" -c:a pcm_s16le "$work/audio.wav"
ffmpeg -v error -nostdin -i "$work/video.mp4" -i "$work/audio.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$out"

vd=$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$out")
ad=$(ffprobe -v error -select_streams a:0 -show_entries stream=duration -of csv=p=0 "$out")
echo "$out: video ${vd}s, audio ${ad}s (should match within ~0.05 s). Parts kept in $work/ — delete once reviewed."
