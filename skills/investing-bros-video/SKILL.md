---
name: investing-bros-video
description: >-
  Make the video side of an Investing Bros / אחים להשקעות episode with
  burned-in Hebrew captions: a combined full-frame cold-open teaser (30–60 s,
  16:9), the
  full video episode (cold opens + intro + episode) with its YouTube
  description, and a 30–60 s promo teaser. Use when Amitai asks for "a
  teaser", "a trailer", "טיזר", "פרומו", "cold open", "פרק מלא", "full
  episode video", "וידאו" or "a teaser with each brother" for episode N.
  Shorts and mid-form are investing-bros-shorts.
---
# Investing Bros video

Load `investing-bros-show` first: show facts, deployed assets, loudness, the intro clip and recording layout live there. Video assets are made by ליאורה; Nadav approves each cut before a rebuild or upload (show conventions → Roles and accounts).

Load `investing-bros-brand` for visual specifications and request graphic assets from it.
It owns cover art, lower thirds and other visual assets; this skill owns video assembly.
The approved full-frame teaser layout is implemented here; do not create competing
brand rules or silently change approved artwork.

## When to use
After the audio edit (`investing-bros-post-production`), when the recording has video and Amitai wants the video episode, cold opens or a promo teaser.

## Inputs
From the episode's `extras/`:
- `transcript/segments.json` and `edit.json` (raw timeline; `edited = raw − start`)
- the raw master video (`investing-bros-episode-raw-untrimmed.mp4`) and `episode-leveled.wav` (same timeline)
- approved graphic assets from `investing-bros-brand`; the current newspaper logo
  and Heebo variable font are converted by `scripts/brand.py`; intro clip from show conventions → Brand
- the description file `תיאור-פרק-N.txt` from the episode root, for the YouTube description (step 4)

For a back-catalogue re-upload with no raw recording, transcript or `edit.json`, use
the published RedCircle/Drive audio as the edited timeline (`start = 0`), transcribe
it with `investing-bros-post-production`, and measure its start inside the existing
video in step 4. Do not invent raw-time mappings that no longer exist.

## Steps

### 1. Pick moments with Nadav and Amitai
Tease, don't resolve: a question raised, a number dropped, a story started; cut before the answer. Wait for the OK unless Amitai said to go ahead.
- **Cold open teaser** (one combined 30–60 s video): 3–5 short moments per host,
  Amitai first and then Nadav. Open on the most surprising line, end each moment on
  a full sentence: a question or a hook. Reordering whole lines is fine; splicing
  half-sentences into a new claim is not.
- **Promo teaser** (30–60 s, square): 2–4 moments of 5–15 s, strongest first, covering news, deep dive and an idea.

Cut in the pauses between words, never mid-word (audio energy, or re-transcribe a short window). Proofread every caption against the audio; leave out words you can't verify and report them.

### 2. Render the cold opens (1920×1080)
The default is the approved full-frame speaker layout: about 1.2× face crop, solid
logo top-left, gold `פרק N` plus white episode name top-right, and word-by-word
Heebo ExtraBold captions over a soft feathered blur band. The current word is gold.
There is no side panel, split screen, speaker name, underline or hard caption box;
moments dip to black.

Copy [the config template](references/teaser-fullframe.example.json) to the episode's
`extras/`, replace its relative paths, crops, title, moments and proofread caption
states, then run:
```bash
# Normal episode: use episode-leveled.wav in the JSON; level_audio.sh preserves PTS.
# Already-mastered back catalogue with no leveled WAV:
<investing-bros-video>/scripts/make_pts_audio.sh \
  "$EP/extras/investing-bros-episode-raw-untrimmed.mp4" "$EP/extras/source-audio-pts.wav"
cp <investing-bros-brand>/assets/logo-solid.png "$EP/extras/logo_solid.png"
python3 <investing-bros-video>/scripts/brand.py fonts Heebo[wght].ttf "$EP/extras/fonts/"
python3 <investing-bros-video>/scripts/build_fullframe_teaser.py "$EP/extras/teaser.json"
```
Use the source's native frame rate (auto-detected if `fps` is omitted). Choose one crop
per host after checking the first frame; the template's 1280×720 values are examples,
not defaults for every recording. `make_pts_audio.sh` preserves packet timestamp gaps,
and the renderer rejects audio whose clock differs from the source.

The renderer applies two-pass loudness normalization to −14 LUFS / −1.5 dBTP.
A music bed, if any, follows [references/music-bed.md](references/music-bed.md);
never a noise layer or watermarked music. `build_teaser.py` and panel frames remain
only for reproducing an old export; they are not the default.

The checked-in solid logo is the approved asset. `brand.py logo` can rebuild it from
the current newspaper source when that source changes, but a regenerated logo needs
visual review on bright and dark frames before replacing the approved asset.

### 3. Assemble the video episode
Order: cold open(s) → the intro, as-is → the episode. Hard cuts.
```bash
scripts/assemble_episode.sh "$EP/video/פרק-N-וידאו.mp4" \
  --body "$EP/extras/investing-bros-episode-raw-untrimmed.mp4" \
  --body-audio "$EP/extras/episode-leveled.wav" \
  --start START --end END \
  --before "$EP/promo/טיזר-פרק-N.mp4" \
  --before-audio "$EP/extras/teaser-assembly-audio.wav" \
  --intro "<Investing-bros-intro.mp4>"
```
`START`/`END` come from `edit.json`. Every segment uses the same x264 settings and the body goes in ~8-minute chunks; under a command time limit add `--max-seconds 150` and re-run until it stops printing `resume`. Never join separately encoded pieces with `-c copy`.

The output keeps the body's native frame rate; use `--fps RATE` only for a deliberate
conversion. `--force` replaces an existing output and rebuilds its cached parts.
The teaser renderer's `assembly_audio` is a normalized PCM
sidecar; pass it with `--before-audio` so AAC encoder delay cannot move the next
segment's speech. The script decodes every other part to PCM too, verifies each
segment's sample count, rejects a body-audio file whose duration does not match the
body's audio PTS clock, and rejects final A/V drift. Look at a frame and listen at
each join and somewhere late in the episode for sync.

### 4. YouTube description for the video
The video starts with the teaser + intro, so its chapters are shifted. Use
`find_offset_and_shift.py` from `investing-bros-title-description`; it can either
cross-correlate the body audio against the video or take a verified `--offset`:
```bash
python3 <investing-bros-title-description>/scripts/find_offset_and_shift.py \
  פרק-N-וידאו.mp4 הקלטה-ערוכה-פרק-N.m4a תיאור-פרק-N.txt תיאור-פרק-N-youtube.txt
python3 <investing-bros-title-description>/scripts/check_copy.py \
  --description תיאור-פרק-N-youtube.txt --youtube --allow-missing-spotify
```
Do not add `--spotify` to this check: the YouTube-only teaser chapter may be under
30 seconds. A match score below 0.5 means the video body is a different edit; stop
and re-time from that video's transcript. If the clean per-episode Spotify URL is
already known, insert its required line after the disclaimer and remove
`--allow-missing-spotify`; otherwise the upload skill obtains and adds it later
without blocking the private upload.

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
