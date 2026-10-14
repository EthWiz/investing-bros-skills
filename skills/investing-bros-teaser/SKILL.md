---
name: investing-bros-teaser
description: >-
  Make teasers for an Investing Bros / אחים להשקעות episode with burned-in
  Hebrew captions: a 30–60 second promo teaser from a few of the best
  moments, or per-host cold-open teasers (one per brother, 15–30 s, 16:9) that
  open the full video episode. Use when Amitai asks for "a teaser", "a
  trailer", "טיזר", "פרומו", "cold open" or "a teaser with each brother" for
  episode N.
---
# Investing Bros teaser

Load `investing-bros-show` first — brand palette, logo, fonts, loudness and the recording layout live there.

## When to use
After post-production for episode N, when Amitai asks for a teaser. Video assets are made only by ליאורה (`investing-bros-show` → Roles). Two kinds:
- **Promo teaser** (default): 30–60 s, square, moments from across the episode.
- **Per-host cold open**: one teaser per host, only that host speaking, 16:9 — they play before the intro in the full video episode (`investing-bros-post-production`, video episode step).

## Inputs
From the episode's `extras/` folder:
- `segments.json` — the transcript
- the raw master — `.mp4` if the recording has video, otherwise `.m4a`
- for cold opens: the leveled episode audio (`episode-leveled.wav` from post-production) and the brand assets (`scripts/brand.py`: logo, fonts, frame)

For audio-only recordings, also the show cover (location in `investing-bros-show`).

Times are on the raw timeline, the same one as `segments.json`. To tell Amitai where a moment is in the published episode, subtract `start` from `edit.json`.

## Steps
1. **Pick moments with Amitai.** Tease, don't resolve: a question raised, a number dropped, a story started — cut before the answer. Wait for his OK unless he said to go ahead.
   - Promo teaser: 2–4 moments, 5–15 s each, strongest first, covering news, deep dive and an idea.
   - Cold open: 2–5 lines from **one** host (15–30 s; episode 7's open was ~22 s): open on the most surprising line, end on a full sentence — a question or a hook ("…אז יש לי מניה בכיס?", "השאלה הגדולה היא: So what?"). Each line must stand on its own — reordering lines is fine, splicing half-sentences into a new claim is not. Music, if any, is the ducked bed in **Cold-open music bed** below — not a noise layer. Hard cut into Amitai's intro, which plays as-is (`investing-bros-show` → Brand).
2. **Exact cut points**: cut in the pauses between words (audio energy, or re-transcribe a short window), never mid-word. Proofread every caption against the audio — whisper gets names, numbers and English terms wrong; leave out words you can't verify and report them.
3. **Render.**
   - Promo teaser (1080×1080):
     ```bash
     python3 scripts/clip_captions.py segments.json START END part-1.ass --format square
     scripts/make_clip.sh --source raw.mp4 --start START --end END --format square --captions part-1.ass part-1.mp4
     # audio-only: --source raw.m4a --cover show-cover.png
     scripts/make_teaser.sh teaser.mp4 part-1.mp4 part-2.mp4 part-3.mp4
     ```
     Make a vertical version (`--format vertical` for every part) only if Amitai asks.
   - Cold open (1920×1080): the host's half of the recording at native size next to a branded panel (logo, episode label, big captions, name); the host stays on his side of the recording.
     ```bash
     python3 scripts/brand.py frame panel-left logo.png frame_panel_left.png    # host sits right (Nadav)
     python3 scripts/brand.py frame panel-right logo.png frame_panel_right.png  # host sits left (Amitai)
     python3 scripts/build_teaser.py teaser_nadav.json   # format in the script; audio_source = episode-leveled.wav
     bash teaser_nadav.sh   # -> seg_*.mp4 (video for the episode join), aseg_*.wav, and the muxed teaser
     ```
     Taking the audio from the leveled episode track keeps the edit in sync with the episode. Then loudnorm the cold open to −14 LUFS (episode 7; the social-clip target in `investing-bros-show`). The episode body stays at −16; the join is a hard cut.
   - Animated graphics (optional): when a teaser moment is an explainer — a number, "not X but Y" — and Amitai wants it more designed, render that moment (or a vertical teaser) with `investing-bros-hyperframes` and its cards. Keep the per-host cold opens on `build_teaser.py`: they must match the episode's x264 settings to join it without re-encoding, which a HyperFrames export doesn't.
4. **Watch it once**: captions readable and right-to-left (English words in place), joins clean, no clipped words, nothing out of context that sounds like a buy/sell call. Check loudness (`ebur128`): −14 LUFS for a promo teaser and for a cold open. Nadav approves the cut before a rebuild or an upload.

## Cold-open music bed
A bed is real music ducked under the voice. Episode 7's track sounded like static — do not ship that. `build_teaser.py` does not add music: mix the wav below, then set `audio_source` to it so the script does not loudnorm the cold open back to −16.

**Track.** Licensed or royalty-free, WAV or ≥256 kbps. Never generated audio, a low-bitrate file, or a watermarked preview (AudioJungle and the like). Listen once. Then reject hiss — the band above 8 kHz on a static bed is almost as loud as the whole file:
```bash
ffmpeg -i bed.wav -af astats=metadata=1:reset=0,ametadata=print:key=lavfi.astats.Overall.RMS_level -f null -
ffmpeg -i bed.wav -af highpass=f=8000,astats=metadata=1:reset=0,ametadata=print:key=lavfi.astats.Overall.RMS_level -f null -
```
If those two RMS numbers are within 10 dB, it is hiss. Stop.

**Mix.** Denoise speech first: `highpass=f=80`, then light `afftdn=nr=10:nf=-30` (if the voice turns watery, drop the denoise). `arnndn` only when a model is already on the machine. Duck with `sidechaincompress`: music is the main input, speech is the sidechain (`threshold=0.03:ratio=4:attack=15:release=400` — fast in, slow enough that it does not pump between words). Under speech the bed sits about −18 to −24 dB below the dialogue; it may rise in a pause. No sidechain: `volume` on the bed until that same gap is true. Fade the bed in ~0.8 s and out ~1 s. Loudnorm the **mix** last, to −14 LUFS integrated, true peak −1 dBTP.

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

**Checklist.** No hiss, no watermark. Speech intelligible. Music never competes (about −18 to −24 dB under the dialogue). Bed fades in and out. `ebur128`: about −14 LUFS, true peak ≤ −1 dBTP. Hard cut into the intro.

## Hand back
Upload to the episode's `promo/` folder. Send Amitai the link with each teaser's length, the moments used (episode time + opening words), any cuts inside a moment, and any words you couldn't verify.

## Never
- Post anywhere unless Amitai asks in chat for that post, and then only to a destination listed in `investing-bros-show`.
- Put words on screen the hosts didn't say, or captions you haven't proofread.
- Splice lines so a host seems to say something he didn't, or cut a caveat to make a line punchier.
- Add music or stock footage unless Amitai supplies it, except a cold-open bed mixed as in **Cold-open music bed**. Never generated noise, a low-bitrate file, or watermarked music.
- Write your own render, caption, download or upload code, or work around a missing feature without saying so — follow the working rules in `investing-bros-show`.
