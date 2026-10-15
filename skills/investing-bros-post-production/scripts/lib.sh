# shared helpers (source me).
# Identical copy in investing-bros-shorts and investing-bros-post-production; edit both together.
set -euo pipefail
# Amitai's intro mp4. Required by cold_open.sh and conform_intro.sh.
# No machine path — pass INTRO= (investing-bros-show → Brand).
INTRO=${INTRO:-}
probe(){ ffprobe -v error -select_streams "$2" -show_entries "stream=$3" -of default=nw=1:nk=1 "$1" | head -1; }
# spec of a reference file -> W H FPS TIMESCALE
spec(){ W=$(probe "$1" v:0 width); H=$(probe "$1" v:0 height); FPS=$(probe "$1" v:0 r_frame_rate)
        TS=$(probe "$1" v:0 time_base | cut -d/ -f2); }
ENC_V="-c:v libx264 -preset veryfast -crf 18 -profile:v high -pix_fmt yuv420p"
ENC_A="-c:a aac -b:a 192k -ar 48000 -ac 2"
# two-pass loudnorm: loudnorm2 in.wav out.wav [I] [TP]
loudnorm2(){ local I=${3:--14} TP=${4:--1} J
  J=$(ffmpeg -hide_banner -i "$1" -af loudnorm=I=$I:TP=$TP:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
  local P; P=$(python3 -c 'import json,sys;m=json.loads(sys.argv[1]);k=["input_i","input_tp","input_lra","input_thresh","target_offset"];n=["measured_I","measured_TP","measured_LRA","measured_thresh","offset"];print(":".join(a+"="+m[b] for a,b in zip(n,k)))' "$J")
  ffmpeg -v error -y -i "$1" -af "loudnorm=I=$I:TP=$TP:LRA=11:$P:linear=true,aresample=48000" -c:a pcm_s24le "$2"; }
lufs(){ ffmpeg -hide_banner -i "$1" -af ebur128=peak=true -f null - 2>&1 | grep -E '^\s+(I|Peak):' | tr -s ' ' | tr '\n' ' '; echo; }
