#!/bin/bash
# cold_open.sh SPEECH.mp4 "a-b,c-d,..." OUT.mp4 [MUSIC] [--no-join]
#   times in seconds or HH:MM:SS.mmm.
#   Output: OUT.mp4 = opener re-encoded to the intro spec + intro (-c copy, hard cut).
#   Also writes OUT_opener.mp4. --no-join = opener only.
#
# The music mix is the cold-open music bed in investing-bros-teaser
# (highpass + light afftdn, sidechain duck, fades ~0.8 s / ~1 s,
# loudnorm −14 LUFS / −1 dBTP). This script does not draw the branded panel;
# that is build_teaser.py in investing-bros-teaser.
#
# Env (no machine-specific defaults):
#   INTRO          Amitai's intro mp4. Required for the join, and for the spec unless LIKE is set.
#   LIKE           spec reference when it should not be the intro.
#   MUSIC_START    seconds to skip into the bed (default 0).
#   ARNNDN_MODEL   optional rnnoise model already on the machine. Otherwise afftdn.
#   SKIP_DENOISE   if set, skip speech denoise (the voice turned watery).
. "$(dirname "$0")/lib.sh"
SRC=$1; SEGS=$2; OUT=$3; MUSIC=${4:-}; [[ ${4:-} == --no-join ]] && MUSIC=""
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
REF=${LIKE:-${INTRO:-}}
[[ -n $REF ]] || { echo "set INTRO=path/to/intro.mp4 or LIKE=ref.mp4"; exit 2; }
spec "$REF"
tosec(){ awk -F: '{s=0;for(i=1;i<=NF;i++)s=s*60+$i;print s}' <<<"$1"; }
# 1) cut + concat segments (video+speech), speech chain
F=""; L=""; i=0
IFS=, read -ra R <<<"$SEGS"
for r in "${R[@]}"; do a=$(tosec "${r%-*}"); b=$(tosec "${r#*-}")
  F+="[0:v]trim=$a:$b,setpts=PTS-STARTPTS[v$i];[0:a]atrim=$a:$b,asetpts=PTS-STARTPTS,afade=t=in:d=0.01,areverse,afade=t=in:d=0.02,areverse[a$i];"
  L+="[v$i][a$i]"; i=$((i+1)); done
if [[ -n ${SKIP_DENOISE:-} ]]; then DN="anull"
elif [[ -n ${ARNNDN_MODEL:-} && -f $ARNNDN_MODEL ]]; then DN="arnndn=m=$ARNNDN_MODEL"
else DN="afftdn=nr=10:nf=-30"; fi
F+="${L}concat=n=$i:v=1:a=1[vc][ac];[vc]scale=$W:$H:force_original_aspect_ratio=decrease,pad=$W:$H:-1:-1:color=black,fps=$FPS,setsar=1[v];[ac]highpass=f=80,$DN,aresample=48000,aformat=channel_layouts=stereo[s]"
ffmpeg -v error -y -i "$SRC" -filter_complex "$F" -map '[v]' $ENC_V -an "$T/v.mp4" -map '[s]' -c:a pcm_s24le "$T/speech.wav"
D=$(probe "$T/speech.wav" a:0 duration)
# 2) music: the teaser skill's gate (WAV/FLAC or >=256 kbps, hiss check) + duck + fades
if [[ -n $MUSIC ]]; then
  BR=$(ffprobe -v error -show_entries format=bit_rate -of default=nw=1:nk=1 "$MUSIC" || true); CODEC=$(probe "$MUSIC" a:0 codec_name)
  echo "music: $CODEC ${BR:-unknown}bps"
  if [[ $CODEC != pcm_* && $CODEC != flac ]]; then
    [[ ${BR:-0} =~ ^[0-9]+$ && $BR -ge 256000 ]] || { echo "REJECT: music must be WAV/FLAC or >=256 kbps"; exit 2; }
  fi
  rms_of(){ ffmpeg -hide_banner -i "$1" -af "${2}astats=metadata=1:reset=0,ametadata=print:key=lavfi.astats.Overall.RMS_level" -f null - 2>&1 | awk -F= '/lavfi.astats.Overall.RMS_level/{v=$NF} END{print v}'; }
  FULL=$(rms_of "$MUSIC" ""); HF=$(rms_of "$MUSIC" "highpass=f=8000,")
  echo "hiss check: full RMS ${FULL} dB, above 8 kHz ${HF} dB"
  awk -v a="$FULL" -v b="$HF" 'BEGIN{if(a==""||b=="") exit 1; d=a-b; if(d<0)d=-d; exit (d<10)}' \
    || { echo "REJECT: hiss (band above 8 kHz is within 10 dB of the whole file)"; exit 2; }
  echo "  (listen once: any watermark or voice tag is a reject)"
  ffmpeg -v error -y -i "$T/speech.wav" -ss "${MUSIC_START:-0}" -i "$MUSIC" -filter_complex \
   "[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,atrim=0:$D,asetpts=PTS-STARTPTS,afade=t=in:d=0.8,areverse,afade=t=in:d=1,areverse[bed];[0:a]asplit=2[sc][vox];[bed][sc]sidechaincompress=threshold=0.03:ratio=4:attack=15:release=400[duck];[vox][duck]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[o]" \
   -map '[o]' -c:a pcm_s24le "$T/mix.wav"
else cp "$T/speech.wav" "$T/mix.wav"; fi
# 3) two-pass loudnorm -14 / -1 dBTP (cold-open target), mux opener at intro spec
loudnorm2 "$T/mix.wav" "$T/ln.wav" -14 -1
OP="${OUT%.*}_opener.mp4"
ffmpeg -v error -y -i "$T/v.mp4" -i "$T/ln.wav" -map 0:v -map 1:a -c:v copy $ENC_A -shortest -video_track_timescale "$TS" -movflags +faststart "$OP"
echo "opener: $OP  $(lufs "$OP")"
[[ " $* " == *" --no-join "* ]] && exit 0
# 4) hard cut to intro, concat demuxer -c copy (intro untouched)
[[ -n ${INTRO:-} ]] || { echo "set INTRO=path/to/intro.mp4 (or pass --no-join)"; exit 2; }
"$(dirname "$0")/join.sh" "$OUT" "$OP" "$INTRO"
