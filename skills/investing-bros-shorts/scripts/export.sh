#!/bin/bash
# export.sh IN.mp4 [OUTDIR]
#  1) share version  <SHARE_MB (default 100): stream-copied if already small, else 2-pass x264 at computed bitrate (aac 128k).
#  2) if IN > PART_MB (default 50): split IN into PART_MB parts + SHA256SUMS. Rejoin: cat NAME.mp4.part* > NAME.mp4 && sha256sum -c
. "$(dirname "$0")/lib.sh"
IN=$1; OD=${2:-$(dirname "$IN")}; mkdir -p "$OD"; N=$(basename "${IN%.*}")
SM=${SHARE_MB:-100}; PM=${PART_MB:-50}; SZ=$(stat -c%s "$IN"); D=$(probe "$IN" v:0 duration)
[[ $D == N/A || -z $D ]] && D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
SH="$OD/${N}_share.mp4"
if (( SZ < SM*1000000 )); then cp "$IN" "$SH"; else
  VB=$(awk -v d="$D" -v m="$SM" 'BEGIN{printf "%d", (m*0.95*8e6/d - 128000 - 20000)/1000}')
  (( VB > 200 )) || { echo "too long for ${SM}MB"; exit 2; }
  P=$(mktemp -u /tmp/x264pass_XXXX)
  ffmpeg -v error -y -i "$IN" -c:v libx264 -preset medium -b:v ${VB}k -pass 1 -passlogfile "$P" -an -f null -
  ffmpeg -v error -y -i "$IN" -c:v libx264 -preset medium -b:v ${VB}k -maxrate $((VB*2))k -bufsize $((VB*4))k -pass 2 -passlogfile "$P" -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart "$SH"
  rm -f "$P"*; fi
echo "share: $SH $(( $(stat -c%s "$SH")/1000000 ))MB"
(( $(stat -c%s "$SH") < SM*1000000 )) || echo "WARNING share file over ${SM}MB"
if (( SZ > PM*1000000 )); then
  split -b ${PM}000000 -d -a 2 "$IN" "$OD/$N.mp4.part"
  (cd "$OD" && sha256sum "$N.mp4.part"* > "${N}_SHA256SUMS"; echo "$(sha256sum < "$(realpath "$IN")" | cut -d' ' -f1)  $N.mp4" >> "${N}_SHA256SUMS")
  echo "parts: $(ls "$OD/$N.mp4.part"* | wc -l) x ${PM}MB + ${N}_SHA256SUMS (rejoin: cat $N.mp4.part* > $N.mp4 && sha256sum -c ${N}_SHA256SUMS)"; fi
