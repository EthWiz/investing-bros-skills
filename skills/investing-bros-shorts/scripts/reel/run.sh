#!/bin/bash
set -e
cd "$(dirname "$0")"
python3 -c "import render" >/dev/null   # writes captions_chunks.json + mg_schedule.json
python3 audio.py
J=$(ffmpeg -v info -i mix_pre.wav -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
python3 - "$J" << 'PY'
import json,sys,subprocess
m=json.loads(sys.argv[1])
af=f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
subprocess.run(["ffmpeg","-v","error","-y","-i","mix_pre.wav","-af",af,"-ar","48000","-c:a","pcm_s24le","mix.wav"],check=True)
PY
python3 render.py | tail -1
