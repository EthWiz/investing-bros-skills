# Cold-open music bed

Used by `investing-bros-video` step 2 when a cold open gets music.

A bed is real music ducked under the voice. Episode 7's track sounded like static — do not ship that. `build_teaser.py` does not add music: mix the wav below, then set `audio_source` to it so the script does not loudnorm the cold open back to −16.

## Track
Licensed or royalty-free, WAV or ≥256 kbps. Never generated audio, a low-bitrate file, or a watermarked preview (AudioJungle and the like). Listen once. Then reject hiss — the band above 8 kHz on a static bed is almost as loud as the whole file:
```bash
ffmpeg -i bed.wav -af astats=metadata=1:reset=0,ametadata=print:key=lavfi.astats.Overall.RMS_level -f null -
ffmpeg -i bed.wav -af highpass=f=8000,astats=metadata=1:reset=0,ametadata=print:key=lavfi.astats.Overall.RMS_level -f null -
```
If those two RMS numbers are within 10 dB, it is hiss. Stop.

## Mix
Denoise speech first: `highpass=f=80`, then light `afftdn=nr=10:nf=-30` (if the voice turns watery, drop the denoise). `arnndn` only when a model is already on the machine. Duck with `sidechaincompress`: music is the main input, speech is the sidechain (`threshold=0.03:ratio=4:attack=15:release=400` — fast in, slow enough that it does not pump between words). Under speech the bed sits about −18 to −24 dB below the dialogue; it may rise in a pause. No sidechain: `volume` on the bed until that same gap is true. Fade the bed in ~0.8 s and out ~1 s. Loudnorm the **mix** last, to −14 LUFS integrated, true peak −1 dBTP.

```bash
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 speech.wav)
ffmpeg -y -i speech.wav -i bed.wav -filter_complex "\
[0:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,highpass=f=80,afftdn=nr=10:nf=-30,asplit=2[sc][vox];\
[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,atrim=duration=${DUR},asetpts=PTS-STARTPTS,afade=t=in:d=0.8,areverse,afade=t=in:d=1,areverse[bed];\
[bed][sc]sidechaincompress=threshold=0.03:ratio=4:attack=15:release=400[duck];\
[vox][duck]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,loudnorm=I=-14:TP=-1:LRA=11[a]" \
-map "[a]" -c:a pcm_s16le cold-open-mix.wav
```
`speech.wav` is the cold-open dialogue, already leveled. If the bed still competes or has vanished, change only its level and run this once more.

## Checklist
No hiss, no watermark. Speech intelligible. Music never competes (about −18 to −24 dB under the dialogue). Bed fades in and out. `ebur128`: about −14 LUFS, true peak ≤ −1 dBTP. Hard cut into the intro.
