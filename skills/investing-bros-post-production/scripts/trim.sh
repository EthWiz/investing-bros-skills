#!/usr/bin/env bash
# Cut the raw master to the edited episode and record the cut points.
#
# Usage:
#   trim.sh RAW START END OUT [--cut A-B]...
#     START / END: seconds (e.g. 42.5) or HH:MM:SS(.ms), on the RAW timeline.
#     --cut A-B:   also remove raw A..B inside the episode (a long silence, a false
#                  start). Repeatable. Cut inside a pause; each join gets a 10 ms fade.
#     OUT: .m4a (AAC 192k) or .mp3 (192k).
#
# Also writes edit.json next to OUT:
#   {"raw": ..., "start": s, "end": s, "cuts": [[a, b], ...], "duration": s}
# Chapters, shorts and the video map raw -> edited time with edit_map.py
# (with no cuts that is simply edited = raw - start).
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
raw="${1:?usage: trim.sh RAW START END OUT [--cut A-B]...}"; start="${2:?START}"; end="${3:?END}"; out="${4:?OUT}"
shift 4
cuts=()
while (( $# )); do
  case "$1" in
    --cut) cuts+=(--cut "${2:?--cut needs A-B}"); shift 2 ;;
    *) echo "error: unknown option $1" >&2; exit 2 ;;
  esac
done
[[ -f "$raw" ]] || { echo "error: not found: $raw" >&2; exit 1; }
[[ -e "$out" ]] && { echo "error: $out exists; refusing to overwrite" >&2; exit 1; }

case "${out,,}" in
  *.mp3) codec=(-c:a libmp3lame -b:a 192k) ;;
  *.m4a) codec=(-c:a aac -b:a 192k) ;;
  *) echo "error: OUT must end in .m4a or .mp3" >&2; exit 1 ;;
esac

# Kept raw ranges ("a b" per line); edit_map.py validates START/END and every cut.
ranges=$(python3 "$here/edit_map.py" --check "$start" "$end" ${cuts[@]+"${cuts[@]}"})
lines=(); while IFS= read -r l; do [[ -n "$l" ]] && lines+=("$l"); done <<<"$ranges"

if (( ${#lines[@]} == 1 )); then
  read -r s e <<<"${lines[0]}"
  ffmpeg -hide_banner -loglevel error -nostdin -i "$raw" -ss "$s" -to "$e" -vn "${codec[@]}" "$out"
else
  fc=""; labels=""; i=0
  for l in "${lines[@]}"; do
    read -r a b <<<"$l"
    d=$(awk -v a="$a" -v b="$b" 'BEGIN { printf "%.3f", b - a - 0.01 }')
    fc+="[0:a]atrim=start=$a:end=$b,asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st=$d:d=0.01[k$i];"
    labels+="[k$i]"; i=$((i + 1))
  done
  fc+="${labels}concat=n=$i:v=0:a=1[a]"
  ffmpeg -hide_banner -loglevel error -nostdin -i "$raw" -filter_complex "$fc" -map "[a]" "${codec[@]}" "$out"
fi
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out")

python3 - "$raw" "$dur" "$(dirname "$out")/edit.json" "${lines[@]}" <<'PY'
import json, os, sys
raw, d, path, *lines = sys.argv[1:]
r = [[float(x) for x in l.split()] for l in lines]
cuts = [[r[i][1], r[i + 1][0]] for i in range(len(r) - 1)]
json.dump({"raw": os.path.basename(raw), "start": r[0][0], "end": r[-1][1], "cuts": cuts,
           "duration": round(float(d), 3)}, open(path, "w"), indent=2)
removed = sum(b - a for a, b in cuts)
print(f"edited: {float(d) / 60:.1f} min ({len(cuts)} cut(s) inside, {removed:.1f} s removed); cut points in {path}")
PY
