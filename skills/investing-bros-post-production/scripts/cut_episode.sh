#!/bin/bash
# cut_episode.sh SOURCE.mp4 EDL.txt OUT.mp4 [COLD_OPEN.mp4]
#  EDL: lines "HH:MM:SS.mmm -> HH:MM:SS.mmm" (ep7 final/edl.txt KEEPS format) or "start end" in seconds; '#' comments ok.
#  If every keep starts on a keyframe -> stream copy; else ONE fast single-pass encode (veryfast crf18) of all keeps.
#  Then [COLD_OPEN (already contains intro, from cold_open.sh)] + body joined by concat demuxer -c copy.
#  Body is encoded to the source's own res/fps; COLD_OPEN must match it (run cold_open.sh with LIKE=SOURCE).
. "$(dirname "$0")/lib.sh"
SRC=$1; EDL=$2; OUT=$3; CO=${4:-}; T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
tosec(){ awk -F: '{s=0;for(i=1;i<=NF;i++)s=s*60+$i;printf "%.3f\n",s}' <<<"$1"; }
mapfile -t K < <(grep -v '^\s*#' "$EDL" | grep -oE '[0-9:.]+ *(->| ) *[0-9:.]+' | awk '{print $1, $NF}')
[[ ${#K[@]} -gt 0 ]] || { echo "no keeps in EDL"; exit 1; }
spec "$SRC"; FR=$(awk -F/ -v f="$FPS" 'BEGIN{split(f,a,"/");print a[2]/a[1]}')
KF=$(ffprobe -v error -select_streams v:0 -skip_frame nokey -show_entries frame=pts_time -of csv=p=0 "$SRC")
IN=(); copy=1; F=""; L=""; i=0
for k in "${K[@]}"; do a=$(tosec "${k% *}"); b=$(tosec "${k#* }")
  awk -v a="$a" -v fr="$FR" '{d=$1-a;if(d<0)d=-d;if(d<fr)f=1}END{exit !f}' <<<"$KF" || copy=0
  IN+=(-ss "$a" -to "$b" -i "$SRC"); L+="[$i:v][$i:a]"; i=$((i+1)); done
BODY=$T/body.mp4
if [[ $copy == 1 ]]; then echo "all keeps on keyframes -> stream copy"; j=0
  for k in "${K[@]}"; do a=$(tosec "${k% *}"); b=$(tosec "${k#* }")
    ffmpeg -v error -y -ss "$a" -to "$b" -i "$SRC" -c copy -avoid_negative_ts make_zero "$T/p$j.mp4"; echo "file '$T/p$j.mp4'" >> "$T/l.txt"; j=$((j+1)); done
  ffmpeg -v error -y -f concat -safe 0 -i "$T/l.txt" -c copy "$BODY"
else echo "keeps not keyframe-aligned -> single fast encode of $i ranges"
  ffmpeg -v error -y "${IN[@]}" -filter_complex "${L}concat=n=$i:v=1:a=1[v][a]" -map '[v]' -map '[a]' $ENC_V -r "$FPS" $ENC_A -video_track_timescale "$TS" "$BODY"; fi
if [[ -n $CO ]]; then "$(dirname "$0")/join.sh" "$OUT" "$CO" "$BODY"; else mv "$BODY" "$OUT"; echo "body: $OUT"; fi
