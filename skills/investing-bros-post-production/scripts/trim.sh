#!/usr/bin/env bash
# Cut the raw master to the edited episode and record the cut points.
#
# Usage:
#   trim.sh RAW START END OUT
#     START / END: seconds (e.g. 42.5) or HH:MM:SS(.ms), on the RAW timeline.
#     OUT: .m4a (AAC 192k) or .mp3 (192k).
#
# Also writes edit.json next to OUT: {"raw": ..., "start": s, "end": s, "duration": s}
# Promo clips and chapters use it to map raw time -> edited time (edited = raw - start).
set -euo pipefail
raw="${1:?usage: trim.sh RAW START END OUT}"; start="${2:?START}"; end="${3:?END}"; out="${4:?OUT}"
[[ -f "$raw" ]] || { echo "error: not found: $raw" >&2; exit 1; }
[[ -e "$out" ]] && { echo "error: $out exists; refusing to overwrite" >&2; exit 1; }

to_sec() { awk -F: '{ s = 0; for (i = 1; i <= NF; i++) s = s * 60 + $i; printf "%.3f", s }' <<<"$1"; }
s=$(to_sec "$start"); e=$(to_sec "$end")
awk -v s="$s" -v e="$e" 'BEGIN { exit !(e > s) }' || { echo "error: END must be after START" >&2; exit 1; }

case "${out,,}" in
  *.mp3) codec=(-c:a libmp3lame -b:a 192k) ;;
  *.m4a) codec=(-c:a aac -b:a 192k) ;;
  *) echo "error: OUT must end in .m4a or .mp3" >&2; exit 1 ;;
esac

ffmpeg -hide_banner -loglevel error -nostdin -i "$raw" -ss "$s" -to "$e" -vn "${codec[@]}" "$out"
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out")

python3 - "$raw" "$s" "$e" "$dur" "$(dirname "$out")/edit.json" <<'PY'
import json, os, sys
raw, s, e, d, path = sys.argv[1:]
json.dump({"raw": os.path.basename(raw), "start": float(s), "end": float(e),
           "duration": round(float(d), 3)}, open(path, "w"), indent=2)
print(f"edited: {float(d) / 60:.1f} min; cut points in {path}")
PY
