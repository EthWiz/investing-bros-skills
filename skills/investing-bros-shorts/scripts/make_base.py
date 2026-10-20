import subprocess, json
SRC="/workspace/podcast/ep3/src_clip3_993s.mp4"
# (audio_start, audio_end, video_start_delay) ; D video starts 0.15s later (Nadav view until 54.54) -> clone-pad
K=[(3.60,14.60,0),(34.30,49.70,0),(49.85,51.60,0),(54.40,65.55,0.15),(66.75,71.20,0),(79.55,81.00,0)]
fc=[];vs=[];as_=[]
for i,(a,b,dl) in enumerate(K):
    d=b-a
    fc.append(f"[0:v]trim=start={a+dl:.3f}:end={b:.3f},setpts=PTS-STARTPTS,crop=405:720:415:0,scale=1080:1920:flags=lanczos,setsar=1"+(f",tpad=start_duration={dl}:start_mode=clone" if dl else "")+f"[v{i}]")
    fc.append(f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={d-0.015:.3f}:d=0.015[a{i}]")
    vs.append(f"[v{i}][a{i}]")
n=len(K)
fc.append("".join(vs)+f"concat=n={n}:v=1:a=1[vc][ac]")
fc.append("[vc]fps=24,eq=contrast=1.05:saturation=1.1[z];[1:v]format=rgba[gr];[z][gr]overlay=0:0[g];[2:v]scale=210:-1[lg];[g][lg]overlay=56:150,format=yuv420p[v]")
fc.append("[ac]highpass=f=80,acompressor=threshold=0.06:ratio=2.5:attack=15:release=250:makeup=1.5,aresample=48000[a]")
subprocess.run(["ffmpeg","-v","error","-y","-i",SRC,"-loop","1","-i","grad.png","-i","logo.png","-filter_complex",";".join(fc),"-map","[v]","-map","[a]",
 "-c:v","libx264","-preset","veryfast","-crf","16","-g","24","-r","24","-c:a","pcm_s24le","-shortest","pre.mov"],check=True)
J=subprocess.run(["ffmpeg","-i","pre.mov","-af","loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json","-f","null","-"],capture_output=True,text=True).stderr
m=json.loads(J[J.rindex("{"):J.rindex("}")+1])
af=f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000"
subprocess.run(["ffmpeg","-v","error","-y","-i","pre.mov","-af",af,"-c:v","copy","-c:a","aac","-b:a","192k","-ar","48000","-movflags","+faststart","ep3_dc_clean.mp4"],check=True)
# timemap
o=0;tm=[]
for a,b,dl in K: tm.append([a,b,o]); o+=b-a
json.dump(tm,open("timemap.json","w")); print("dur",o)
