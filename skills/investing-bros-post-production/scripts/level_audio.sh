#!/usr/bin/env bash
# Even out the two hosts and normalise the episode to podcast loudness.
#
# Usage:
#   level_audio.sh IN OUT.wav [--target -16]
#
# IN can be the raw master (.m4a/.mp3/.wav) or a video file (its first audio
# stream is used). OUT is 48 kHz stereo 16-bit WAV on the SAME timeline as IN
# (no trimming, no delay), so transcripts, cut points and video stay in sync.
#
# Chain: highpass 70 Hz -> light FFT denoise -> dynaudnorm (2.2 s window, up
# to +26 dB, so a quiet host is lifted to the loud one) -> gentle 2:1
# compression -> one fixed gain to the target -> true-peak limiter at -1.5 dBFS.
# The gain is measured first (two passes) instead of loudnorm's dynamic mode,
# which pumps when the input's peaks are high.
#
# Episode 6: one host sat ~16 dB below the other; after this they measured
# within ~2 dB and the whole episode at -16.0 LUFS, LRA 3.8.
set -euo pipefail
in="${1:?usage: level_audio.sh IN OUT.wav [--target -16]}"; out="${2:?OUT.wav}"; shift 2
target=-16
[[ "${1:-}" == "--target" ]] && target="${2:?}"
[[ -f "$in" ]] || { echo "error: not found: $in" >&2; exit 1; }
[[ -e "$out" ]] && { echo "error: $out exists; refusing to overwrite" >&2; exit 1; }

pre="$(mktemp -t level-XXXXXX).wav"
trap 'rm -f "$pre"' EXIT
ffmpeg -hide_banner -loglevel error -nostdin -y -i "$in" -vn -map 0:a:0 \
  -af "highpass=f=70,afftdn=nr=6:nf=-50,dynaudnorm=f=200:g=11:p=0.9:m=20,acompressor=threshold=0.1:ratio=2:attack=20:release=250,aresample=48000" \
  -ac 1 -c:a pcm_s24le "$pre"

measured=$(ffmpeg -hide_banner -nostdin -i "$pre" -af ebur128 -f null - 2>&1 | awk '/Integrated loudness:/{f=1} f && /I:/{print $2; exit}')
[[ -n "$measured" ]] || { echo "error: could not measure loudness" >&2; exit 1; }
gain=$(awk -v t="$target" -v m="$measured" 'BEGIN { printf "%.2f", t - m }')

ffmpeg -hide_banner -loglevel error -nostdin -i "$pre" \
  -af "volume=${gain}dB,alimiter=limit=0.84:attack=5:release=60:level=disabled,aformat=channel_layouts=stereo" \
  -ar 48000 -c:a pcm_s16le "$out"

ffmpeg -hide_banner -nostdin -i "$out" -af ebur128=peak=true -f null - 2>&1 \
  | awk '/Summary:/{f=1} f && /I:|LRA:|Peak:/{printf "%s ", $0} END{print ""}' | tr -s ' '
echo "$out: gain ${gain} dB after dynaudnorm (pre-gain loudness ${measured} LUFS)"
