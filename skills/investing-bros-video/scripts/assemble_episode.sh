#!/usr/bin/env bash
# Build the full VIDEO episode: cold-open clips (teasers) + intro + episode body,
# with the leveled audio, as one 1920x1080 MP4.
#
# Usage:
#   assemble_episode.sh OUT.mp4 --body VIDEO --body-audio LEVELED.wav
#                       [--edit edit.json | --start S --end E]
#                       [--before CLIP.mp4]... [--before-audio CLIP.wav]...
#                       [--intro INTRO.mp4] [--fps RATE] [--force]
#                       [--chunk 460] [--max-seconds N]
#
#   --body        the episode video (raw master or Riverside export), 1920x1080
#   --body-audio  level_audio.sh output for that SAME file (same timeline)
#   --edit        edit.json from trim.sh: start, end and any cuts inside the episode
#                 (same timeline as --body); the body skips every cut
#   --start/--end cut points on that timeline when there is no edit.json (default: whole file)
#   --before      clips that play first, in order (e.g. the teasers); repeatable
#   --before-audio optional 48 kHz PCM sidecars in the same order as --before;
#                  when used, supply one per clip (avoids AAC encoder-delay loss)
#   --intro       the show intro, played after the --before clips
#   --fps         output frame rate (default: the body's native average frame rate)
#   --force       overwrite OUT and rebuild its cached parts
#   --chunk       body is encoded in chunks of this many seconds (default 460)
#   --max-seconds stop after about this long and print "resume"; re-run the same
#                 command to continue. For shells with a per-command time limit.
#
# Every segment is encoded with the same x264 settings (any size is scaled and
# padded to 1920x1080 on black, at the body source's frame rate) and joined with the concat demuxer
# (-c copy), so a 45-minute body never has to be encoded in one go. Finished
# chunks are kept in OUT.parts/ and skipped on re-run. Every audio segment is
# decoded to 48 kHz stereo PCM before concat and checked against its video's
# frame count, so compressed-audio priming cannot accumulate at joins.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

out="${1:?usage: assemble_episode.sh OUT.mp4 --body VIDEO --body-audio WAV [...]}"; shift
body="" baudio="" start="" end="" editjson="" intro="" chunk=460 budget=0 fps="" force=0 replace_existing=0
before=(); before_audio=()
while (( $# )); do
  case "$1" in
    --body) body="$2"; shift 2 ;;
    --body-audio) baudio="$2"; shift 2 ;;
    --start) start="$2"; shift 2 ;;
    --end) end="$2"; shift 2 ;;
    --edit) editjson="$2"; shift 2 ;;
    --before) before+=("$2"); shift 2 ;;
    --before-audio) before_audio+=("$2"); shift 2 ;;
    --intro) intro="$2"; shift 2 ;;
    --fps) fps="$2"; shift 2 ;;
    --force) force=1; shift ;;
    --chunk) chunk="$2"; shift 2 ;;
    --max-seconds) budget="$2"; shift 2 ;;
    *) echo "error: unknown option $1" >&2; exit 2 ;;
  esac
done
[[ -f "$body" && -f "$baudio" ]] || { echo "error: --body and --body-audio are required" >&2; exit 2; }
if (( ${#before_audio[@]} && ${#before_audio[@]} != ${#before[@]} )); then
  echo "error: give one --before-audio for every --before, or none" >&2
  exit 2
fi
for f in "${before_audio[@]}"; do [[ -f "$f" ]] || { echo "error: not found: $f" >&2; exit 1; }; done
if [[ -e "$out" && "$force" -ne 1 ]]; then
  echo "error: $out exists; pass --force to overwrite it" >&2
  exit 1
fi
if [[ -e "$out" && "$force" -eq 1 ]]; then
  replace_existing=1
  rm -f "$out"
fi
[[ -n "$fps" ]] || fps=$(ffprobe -v error -select_streams v:0 -show_entries stream=avg_frame_rate \
  -of default=noprint_wrappers=1:nokey=1 "$body")
fps_decimal=$(python3 - "$fps" <<'PY'
import sys
from fractions import Fraction
print(f"{float(Fraction(sys.argv[1])):.9f}")
PY
)
gop=$(python3 -c 'import sys; print(max(1, round(float(sys.argv[1]) * 2)))' "$fps_decimal")
X264=(-c:v libx264 -preset veryfast -crf 19 -profile:v high -level 4.0 -pix_fmt yuv420p -g "$gop" -video_track_timescale 90000 -r "$fps")
VF="scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fps=$fps,format=yuv420p"
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
work="${out%.*}.parts"
(( replace_existing )) && rm -rf "$work"
mkdir -p "$work"
t0=$(date +%s)
over_budget() { (( budget > 0 && $(date +%s) - t0 > budget )); }
frames() { ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 "$1"; }
dur_of_frames() { awk -v f="$1" -v rate="$fps_decimal" 'BEGIN { printf "%.9f", f / rate }'; }
fps_matches() {
  local actual
  actual=$(ffprobe -v error -select_streams v:0 -show_entries stream=avg_frame_rate \
    -of default=noprint_wrappers=1:nokey=1 "$1")
  python3 - "$actual" "$fps" <<'PY'
import sys
from fractions import Fraction

raise SystemExit(0 if abs(float(Fraction(sys.argv[1])) - float(Fraction(sys.argv[2]))) < 0.001 else 1)
PY
}
pcm_samples() {
  ffprobe -v error -select_streams a:0 -show_entries stream=duration_ts \
    -of default=noprint_wrappers=1:nokey=1 "$1"
}
check_pcm_frames() {
  python3 - "$1" "$2" "$fps_decimal" <<'PY'
import sys

samples, frames = map(float, sys.argv[1:3])
fps = float(sys.argv[3])
expected = round(frames * 48000 / fps)
if abs(samples - expected) > 1:
    raise SystemExit(
        f"error: PCM segment has {samples:.0f} samples; expected {expected} "
        f"for {frames:.0f} frames at {fps:g} fps"
    )
PY
}
audio_duration() {
  local d
  d=$(ffprobe -v error -select_streams a:0 -show_entries stream=duration -of default=noprint_wrappers=1:nokey=1 "$1")
  [[ -n "$d" && "$d" != "N/A" ]] || d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$1")
  printf '%s' "$d"
}
check_sync() {
  python3 - "$1" "$2" "$3" <<'PY'
import sys

video, audio, tolerance = map(float, sys.argv[1:])
drift = abs(video - audio)
print(f"sync: video {video:.3f}s, audio {audio:.3f}s, drift {drift:.3f}s")
if drift > tolerance:
    raise SystemExit(
        f"error: audio/video clock mismatch ({drift:.3f}s > {tolerance:.3f}s); "
        "rebuild extracted audio with make_pts_audio.sh"
    )
PY
}

# A WAV made by plain `ffmpeg -i VIDEO out.wav` can collapse packet timestamp
# gaps. Catch it before rendering a whole episode with permanently early audio.
sync_tolerance=$(python3 -c 'import sys; print(max(0.05, 1 / float(sys.argv[1]) + 0.005))' "$fps_decimal")
check_sync "$(audio_duration "$body")" "$(audio_duration "$baudio")" "$sync_tolerance"

# 1. Short clips (before + intro): video-only segment + exact-length audio.
clip_seg() {  # $1=video input $2=name $3=optional PCM audio input
  local v="$work/$2.mp4" a="$work/$2.wav"
  if [[ -f "$v" ]] && ! fps_matches "$v"; then
    if (( force )); then
      rm -f "$v"
    else
      echo "error: cached $v has a different frame rate; rerun with --force" >&2
      exit 1
    fi
  fi
  if [[ ! -f "$v" ]]; then
    ffmpeg -v error -nostdin -y -i "$1" -map 0:v:0 -an -vf "$VF" "${X264[@]}" "$work/tmp.mp4" && mv "$work/tmp.mp4" "$v"
  fi
  local d; d=$(dur_of_frames "$(frames "$v")")
  ffmpeg -v error -nostdin -y -i "${3:-$1}" -map 0:a:0 \
    -af "aresample=48000:async=1:min_hard_comp=0.01:first_pts=0,aformat=channel_layouts=stereo,apad,atrim=duration=$d" \
    -c:a pcm_s16le "$a"
  check_pcm_frames "$(pcm_samples "$a")" "$(frames "$v")"
}
list=(); i=0
for c in "${before[@]}"; do
  pcm=""
  (( ${#before_audio[@]} )) && pcm="${before_audio[$i]}"
  clip_seg "$c" "before$i" "$pcm"
  list+=("before$i")
  i=$((i + 1))
done
if [[ -n "$intro" ]]; then
  clip_seg "$intro" intro
  # bring the intro's music to the episode's level (-16 LUFS) so it doesn't jump out
  ffmpeg -v error -nostdin -y -i "$work/intro.wav" -af loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000 -c:a pcm_s16le "$work/intro_n.wav"
  d=$(dur_of_frames "$(frames "$work/intro.mp4")")
  ffmpeg -v error -nostdin -y -i "$work/intro_n.wav" -af "apad,atrim=duration=$d" -c:a pcm_s16le "$work/intro.wav"
  check_pcm_frames "$(pcm_samples "$work/intro.wav")" "$(frames "$work/intro.mp4")"
  list+=(intro)
fi

# 2-3. Body: each kept range in chunks (resumable), then its audio trimmed to
# that range's frame count (keeps sync across cuts). Without cuts there is one range.
body_wavs=()
for ((r = 0; r < ${#ranges[@]}; r++)); do
  read -r rs re <<<"${ranges[$r]}"
  # single range keeps the old part names so existing caches still resume
  if (( ${#ranges[@]} == 1 )); then pfx="body"; wav="body"; else pfx="body${r}_"; wav="body_r$r"; fi
  total=$(awk -v s="$rs" -v e="$re" 'BEGIN { printf "%.6f", e - s }')
  n=$(awk -v t="$total" -v c="$chunk" 'BEGIN { printf "%d", (t + c - 0.000001) / c }')
  for ((k = 0; k < n; k++)); do
    f="$work/$pfx$k.mp4"; list+=("$pfx$k")
    if [[ -f "$f" ]] && ! fps_matches "$f"; then
      if (( force )); then
        rm -f "$f"
      else
        echo "error: cached $f has a different frame rate; rerun with --force" >&2
        exit 1
      fi
    fi
    [[ -f "$f" ]] && continue
    if over_budget; then echo "resume: range $((r + 1))/${#ranges[@]}, $k of $n body chunks done — run the same command again"; exit 3; fi
    ss=$(awk -v s="$rs" -v k="$k" -v c="$chunk" 'BEGIN { printf "%.6f", s + k * c }')
    len=$(awk -v t="$total" -v k="$k" -v c="$chunk" 'BEGIN { l = t - k * c; if (l > c) l = c; printf "%.6f", l }')
    ffmpeg -v error -nostdin -y -ss "$ss" -t "$len" -i "$body" -map 0:v:0 -an -vf "$VF" "${X264[@]}" "$work/tmp.mp4"
    mv "$work/tmp.mp4" "$f"
    echo "body chunk $((k + 1))/$n of range $((r + 1))/${#ranges[@]} done ($(frames "$f") frames)"
  done
  bf=0; for ((k = 0; k < n; k++)); do bf=$((bf + $(frames "$work/$pfx$k.mp4"))); done
  bd=$(dur_of_frames "$bf")
  ffmpeg -v error -nostdin -y -ss "$rs" -i "$baudio" \
    -af "aresample=48000:async=1:min_hard_comp=0.01:first_pts=0,aformat=channel_layouts=stereo,apad,atrim=duration=$bd" \
    -c:a pcm_s16le "$work/$wav.wav"
  check_pcm_frames "$(pcm_samples "$work/$wav.wav")" "$bf"
  body_wavs+=("$wav")
done

# 4. Join video (copy) and audio, mux.
: > "$work/video.txt"; : > "$work/audio.txt"
for s in "${list[@]}"; do echo "file '$s.mp4'" >> "$work/video.txt"; done
for s in "${list[@]}"; do [[ "$s" == body* ]] || echo "file '$s.wav'" >> "$work/audio.txt"; done
for s in "${body_wavs[@]}"; do echo "file '$s.wav'" >> "$work/audio.txt"; done
ffmpeg -v error -nostdin -y -f concat -safe 0 -i "$work/video.txt" -c copy "$work/video.mp4"
ffmpeg -v error -nostdin -y -f concat -safe 0 -i "$work/audio.txt" -c:a pcm_s16le "$work/audio.wav"
expected_samples=0
for s in "${list[@]}"; do
  if [[ "$s" == body* ]]; then continue; fi
  expected_samples=$((expected_samples + $(pcm_samples "$work/$s.wav")))
done
for s in "${body_wavs[@]}"; do expected_samples=$((expected_samples + $(pcm_samples "$work/$s.wav"))); done
actual_samples=$(pcm_samples "$work/audio.wav")
[[ "$actual_samples" -eq "$expected_samples" ]] || {
  echo "error: PCM concat has $actual_samples samples; expected $expected_samples" >&2
  exit 1
}
ffmpeg -v error -nostdin -y -i "$work/video.mp4" -i "$work/audio.wav" \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$out"

vd=$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$out")
ad=$(ffprobe -v error -select_streams a:0 -show_entries stream=duration -of csv=p=0 "$out")
check_sync "$vd" "$ad" "$sync_tolerance"
echo "$out: video ${vd}s, audio ${ad}s, ${fps} fps. PCM concat: ${actual_samples} samples. Parts kept in $work/ — delete once reviewed."
