---
name: investing-bros-video
description: >-
  Make the video side of an Investing Bros / אחים להשקעות episode with
  burned-in Hebrew captions: per-host cold-open teasers (15–30 s, 16:9), the
  full video episode (cold opens + intro + episode) with its YouTube
  description, and a 30–60 s promo teaser. Use when Amitai asks for "a
  teaser", "a trailer", "טיזר", "פרומו", "cold open", "פרק מלא", "full
  episode video", "וידאו" or "a teaser with each brother" for episode N.
  Shorts and mid-form are investing-bros-shorts.
---
# Investing Bros video

Load `investing-bros-show` first: brand, logo, fonts, loudness, the intro clip and the recording layout live there. Video assets are made by ליאורה; Nadav approves each cut before a rebuild or upload (show conventions → Roles and accounts).

## When to use
After the audio edit (`investing-bros-post-production`), when the recording has video and Amitai wants the video episode, cold opens or a promo teaser.

## Inputs
From the episode's `extras/`:
- `transcript/segments.json` and `edit.json` (raw timeline; map to edited time with `scripts/edit_map.py edit.json --raw T`)
- the raw master video (`investing-bros-episode-raw-untrimmed.mp4`) and `episode-leveled.wav` (same timeline)
- brand assets from `scripts/brand.py` (logo, fonts, frames) and the intro clip (show conventions → Brand)
- the description file `תיאור-פרק-N.txt` from the episode root, for the YouTube description (step 4)

## Steps

### 1. Pick moments with Nadav and Amitai
Tease, don't resolve: a question raised, a number dropped, a story started; cut before the answer. Wait for the OK unless Amitai said to go ahead.
- **Cold open** (one per host, 15–30 s): 2–5 lines from **one** host. Open on the most surprising line, end on a full sentence: a question or a hook. Reordering whole lines is fine; splicing half-sentences into a new claim is not.
- **Promo teaser** (30–60 s, square): 2–4 moments of 5–15 s, strongest first, covering news, deep dive and an idea.

Cut in the pauses between words, never mid-word (audio energy, or re-transcribe a short window). Proofread every caption against the audio; leave out words you can't verify and report them.

### 2. Render the cold opens (1920×1080)
The host's half of the recording at native size next to a branded panel (logo, episode label, big captions, name); the host stays on his side.
```bash
python3 scripts/brand.py frame panel-left logo.png frame_panel_left.png    # host sits right (Nadav)
python3 scripts/brand.py frame panel-right logo.png frame_panel_right.png  # host sits left (Amitai)
python3 scripts/build_teaser.py teaser_nadav.json   # format in the script; audio_source = episode-leveled.wav
bash teaser_nadav.sh                                # -> seg_*.mp4, aseg_*.wav and the muxed cold open
```
Loudnorm each cold open to −14 LUFS. A music bed, if any, follows [references/music-bed.md](references/music-bed.md); never a noise layer or watermarked music. Keep cold opens on `build_teaser.py`: they must share the episode's x264 settings to join it.

### 3. Assemble the video episode
Order: cold open(s) → the intro, as-is → the episode. Hard cuts.
```bash
scripts/assemble_episode.sh "$EP/פרק-N-וידאו.mp4" \
  --body "$EP/investing-bros-episode-raw-untrimmed.mp4" --body-audio "$EP/episode-leveled.wav" \
  --edit "$EP/edit.json" \
  --before "טיזר 1 - נדב.mp4" --before "טיזר 2 - אמיתי.mp4" --intro "<intro clip>.mp4"
```
`--edit` applies the same start, end and inside cuts as the audio, so the video and the published audio match. Every segment uses the same x264 settings and the body goes in ~8-minute chunks; under a command time limit add `--max-seconds 150` and re-run until it stops printing `resume`. Never join separately encoded pieces with `-c copy`.

Check: video and audio durations match (the script prints both); look at a frame and listen at each join and somewhere late in the episode for sync.

### 4. YouTube description for the video
The video starts with the cold opens + intro, so its chapters are shifted. Copy `תיאור-פרק-N.txt`, add the opening's length to every chapter, add `00:00 טעימה מהפרק` as the first chapter, save as `תיאור-פרק-N-youtube.txt` and check it:
```bash
python3 <investing-bros-title-description>/scripts/check_copy.py --description תיאור-פרק-N-youtube.txt
```

### 5. Promo teaser (when asked)
```bash
python3 scripts/clip_captions.py segments.json START END part-1.ass --format square
scripts/make_clip.sh --source raw.mp4 --start START --end END --format square --captions part-1.ass part-1.mp4
# audio-only: --source raw.m4a --cover show-cover.png
scripts/make_teaser.sh teaser.mp4 part-1.mp4 part-2.mp4 part-3.mp4
```
Vertical (`--format vertical`) only if Amitai asks. An explainer moment can use the HyperFrames render from `investing-bros-shorts`.

### 6. Check and file
Watch each once: captions readable and right-to-left (English words in place), joins clean, no clipped words, nothing out of context that sounds like a buy/sell call. `ebur128`: −14 LUFS for teasers and cold opens, −16 for the episode body.

| Where | What |
|---|---|
| `video/` | `פרק-N-וידאו.mp4`, `תיאור-פרק-N-youtube.txt` |
| `promo/` | Cold opens, promo teaser |
| `extras/` | Teaser JSONs, segment files, the music bed |

Review copies over the transfer caps: compress (show conventions → references/environment.md). Drafts for review go to Telegram only when Amitai asks.

## Done when
- `video/` has the video episode and its checked YouTube description (when a video episode was asked for).
- `promo/` has each cold open and teaser that was asked for.
- Nadav OK'd the cuts.

## Hand back
- Links to `video/` and `promo/`; length of each file
- The moments used (episode time + opening words), any cuts inside a moment, words you couldn't verify
- The join and sync check result

## Never
- Post anywhere unless Amitai asks in chat for that post, and then only to a destination in `investing-bros-show`.
- Put words on screen the hosts didn't say, captions you haven't proofread, or splice lines so a host seems to say something he didn't.
- Cut a caveat to make a line punchier.
- Add music or stock footage Amitai didn't supply, except a cold-open bed mixed per the reference.
- Write your own render, caption, download or upload code, or work around a missing feature without saying so (show conventions → Working rules).
