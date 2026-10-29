#!/usr/bin/env bash
# Make the ~1 GB YouTube upload copy of a finished video master.
#   compress_for_youtube.sh MASTER.mp4 OUT.mp4
# H.264 CRF 23 capped at 3000 kb/s (6000k buffer), AAC 160 kb/s, moov atom first
# (+faststart) so Studio can start processing at once. A 47-minute episode comes out
# around 1 GB. Check it against the master afterwards with investing-bros-video ->
# verify_sync.py MASTER.mp4 OUT.mp4 (no cuts): it must say SYNC OK.
set -euo pipefail
if [[ $# -ne 2 ]]; then
  echo "usage: $0 MASTER.mp4 OUT.mp4" >&2
  exit 2
fi
in=$1 out=$2
[[ -f $in ]] || { echo "no such file: $in" >&2; exit 2; }
[[ $in -ef $out ]] && { echo "OUT must differ from MASTER" >&2; exit 2; }
ffmpeg -v error -stats -nostdin -y -i "$in" -map 0:v:0 -map 0:a:0 \
  -c:v libx264 -preset medium -crf 23 -maxrate 3000k -bufsize 6000k -pix_fmt yuv420p \
  -c:a aac -b:a 160k -ar 48000 -movflags +faststart "$out"
size=$(stat -c %s "$out" 2>/dev/null || stat -f %z "$out")
dur=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$out")
python3 - "$size" "$dur" "$out" <<'PY'
import sys
size, dur, out = int(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
print(f"{out}: {size / 1e9:.2f} GB, {dur / 60:.1f} min, {size * 8 / dur / 1000:.0f} kb/s average")
PY
