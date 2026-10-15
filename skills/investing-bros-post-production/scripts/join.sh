#!/bin/bash
# join.sh OUT.mp4 A.mp4 B.mp4 ...   concat demuxer, -c copy; refuses mismatched codec/res/fps/audio
. "$(dirname "$0")/lib.sh"
OUT=$1; shift; L=$(mktemp); trap 'rm -f "$L"' EXIT
key(){ echo "$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate -of csv=p=0 "$1") $(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels -of csv=p=0 "$1")"; }
K0=$(key "$1")
for f in "$@"; do k=$(key "$f"); [[ $k == "$K0" ]] || { echo "MISMATCH $f: [$k] vs [$K0]"; exit 3; }; echo "file '$(realpath "$f")'" >> "$L"; done
ffmpeg -v error -y -f concat -safe 0 -i "$L" -map 0:v:0 -map 0:a:0 -c copy -movflags +faststart "$OUT"
echo "joined: $OUT ($(probe "$OUT" v:0 duration)s)"
