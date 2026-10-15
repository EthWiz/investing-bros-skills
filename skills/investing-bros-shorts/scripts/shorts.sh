#!/bin/bash
# shorts.sh CONFIG [OUTDIR]  - one vertical 1080x1920 Short per config line.
# CONFIG lines (# = comment):  SOURCE | START | END | TITLE (\n = line break) | OUTNAME.mp4 [| facetrack]
#   START/END in s or HH:MM:SS.mmm. 6th field "facetrack" = two-shot source -> active-speaker crop (facetrack_split.py).
# Optional per-clip files next to CONFIG:  OUTNAME.fix.json  {"heard":"correct"} ASR fixes
#                                         OUTNAME.mgs.json  [[kind, anchor_word, offset_s, dur_s]] motion-graphic cues
# Pipeline: cut clip only (input seek) -> 9:16 crop @25fps + logo end card -> ivrit-ai whisper word timings
#   -> silence trims, alternating 100/112% zoom, Heebo Black captions (gold active word, PIL+raqm), title box, 2-pass loudnorm -14/-1.
# Env: ENDCARD (required, logo end-card mp4), HEEBO_FONT (Heebo-Variable.ttf), YUNET (yunet.onnx), MODELS_DIR,
#      LIMIT_FRAMES=N (test render), KEEP_WORK=1 (keep temp dir)
# The Heebo font, yunet.onnx and the end-card video are not in the repo.
# Defaults: HEEBO_FONT=<skill>/fonts/Heebo-Variable.ttf, YUNET and MODELS_DIR under <skill>/models/.
. "$(dirname "$0")/lib.sh"
RD=$(cd "$(dirname "$0")" && pwd); CFG=$(realpath "$1"); CD=$(dirname "$CFG"); OD=$(realpath -m "${2:-$CD}"); mkdir -p "$OD"
REEL=${REEL:-$RD/reel}; : "${ENDCARD:?set ENDCARD=path/to/endcard.mp4}"; ENDCARD=$(realpath "$ENDCARD")
export HEEBO_FONT=$(realpath -m "${HEEBO_FONT:-$RD/../fonts/Heebo-Variable.ttf}"); export MODELS_DIR=$(realpath -m "${MODELS_DIR:-$RD/../models}")
YUNET=$(realpath -m "${YUNET:-$RD/../models/yunet.onnx}")
python3 -c 'from PIL import features; assert features.check("raqm"), "Pillow needs raqm"'
tosec(){ awk -F: '{s=0;for(i=1;i<=NF;i++)s=s*60+$i;printf "%.3f\n",s}' <<<"$1"; }
trim(){ sed 's/^ *//;s/ *$//' <<<"$1"; }
grep -v '^\s*#' "$CFG" | grep -v '^\s*$' | while IFS='|' read -r S A B TI ON FT; do
  S=$(cd "$CD" && realpath "$(trim "$S")"); A=$(tosec "$(trim "$A")"); B=$(tosec "$(trim "$B")"); TI=$(trim "$TI"); ON=$(trim "$ON"); FT=$(trim "${FT:-}")
  WD=$(mktemp -d "${TMPDIR:-/tmp}/short_XXXX"); cp "$REEL"/{plan,render,captions,mg,audio,asr_clip}.py "$REEL/run.sh" "$WD/"
  for x in fix mgs; do [[ -f "$CD/${ON%.mp4}.$x.json" ]] && cp "$CD/${ON%.mp4}.$x.json" "$WD/$x.json"; done
  python3 "$RD/make_title.py" "$TI" "$WD/title.png" >/dev/null; D=$(awk -v a=$A -v b=$B 'BEGIN{printf "%.3f",b-a}')
  # cut ONLY this clip from the big source (fast input seek, lossless-ish intermediate)
  ffmpeg -v error -y -ss "$A" -t "$D" -i "$S" -c:v libx264 -preset veryfast -crf 12 -c:a pcm_s16le "$WD/clip.mov"
  if [[ $FT == facetrack ]]; then python3 "$RD/facetrack_split.py" "$WD/clip.mov" "$WD/clip9.mov" --yunet "$YUNET"; IN="$WD/clip9.mov"; CROP="null"
  else IN="$WD/clip.mov"; CROP="crop=ih*9/16:ih"; fi
  ffmpeg -v error -y -i "$IN" -i "$ENDCARD" -filter_complex \
   "[0:v]$CROP,scale=1080:1920:flags=lanczos,fps=25,setsar=1[c];[1:v]scale=1080:1920,fps=25,setsar=1[e];[0:a]aresample=48000,aformat=channel_layouts=stereo[a0];anullsrc=r=48000:cl=stereo,atrim=0:$(probe "$ENDCARD" v:0 duration)[a1];[c][a0][e][a1]concat=n=2:v=1:a=1[v][a]" \
   -map '[v]' -map '[a]' -c:v libx264 -preset veryfast -crf 14 -pix_fmt yuv420p -c:a pcm_s16le "$WD/src.mov"
  SE=$(probe "$WD/src.mov" v:0 duration)
  ffmpeg -v error -y -i "$WD/src.mov" -vn -ac 1 -ar 48000 -c:a pcm_s16le "$WD/src48k.wav"
  ffmpeg -v error -y -i "$WD/src.mov" -vn -ac 1 -ar 16000 -c:a pcm_s16le "$WD/src16k.wav"
  python3 "$RD/patch_reel.py" "$WD" src.mov "$D" "$SE" "$OD/$ON" >/dev/null
  (cd "$WD" && python3 asr_clip.py > asr.log 2>&1)
  if [[ -n ${LIMIT_FRAMES:-} ]]; then sed -i "s#python3 render.py | tail -1#python3 render.py $LIMIT_FRAMES | tail -1#" "$WD/run.sh"; fi
  rm -f "$OD/$ON"; bash "$WD/run.sh" </dev/null; [[ -s "$OD/$ON" ]] || { echo "FAILED $ON (work: $WD)"; exit 4; }; echo "short: $OD/$ON  $(lufs "$OD/$ON")"
  [[ -n ${KEEP_WORK:-} ]] && echo "work: $WD" || rm -rf "$WD"
done
