---
name: investing-bros-teaser
description: >-
  Make a 30–60 second teaser (trailer) for an Investing Bros / אחים להשקעות
  episode from a few of its best moments, with burned-in Hebrew captions. Use
  when Amitai asks for "a teaser", "a trailer", "טיזר" or "פרומו" for episode N.
---
# Investing Bros teaser

Load `investing-bros-show` first.

## When to use
After post-production for episode N, when Amitai asks for a teaser.

## Inputs
From the episode's `extras/` folder:
- `segments.json` — the transcript
- the raw master — `.mp4` if the recording has video, otherwise `.m4a`

For audio-only recordings, also the show cover (location in `investing-bros-show`).

Times are on the raw timeline, the same one as `segments.json`. To tell Amitai where a moment is in the published episode, subtract `start` from `edit.json`.

## Steps
1. **Pick 2–4 moments with Amitai**, 5–15 seconds each, strongest first. Tease, don't resolve: a question raised, a number dropped, a disagreement starting — cut before the answer. Try to cover the episode's range: news, deep dive, an investment idea. Wait for his OK.
2. **Captions** for each moment (square format):
   ```bash
   python3 scripts/clip_captions.py segments.json START END part-1.ass --format square
   ```
   Proofread the text against the audio — whisper gets names and numbers wrong.
3. **Render each moment** (1080×1080), then join them with short fades:
   ```bash
   scripts/make_clip.sh --source raw.mp4 --start START --end END --format square --captions part-1.ass part-1.mp4
   # audio-only: --source raw.m4a --cover show-cover.png
   scripts/make_teaser.sh teaser.mp4 part-1.mp4 part-2.mp4 part-3.mp4
   ```
   Total length should land at 30–60 seconds. Make a vertical version (`--format vertical` for every part) only if Amitai asks.
4. **Watch it once**: captions readable and right-to-left, joins clean, nothing out of context that sounds like a buy/sell call.

## Hand back
Upload `teaser.mp4` to the episode's `promo/` folder. Send Amitai the link with its length and the moments used.

## Never
- Post anywhere — Amitai posts.
- Put words on screen the hosts didn't say, or captions you haven't proofread.
- Add music or stock footage unless Amitai supplies it.
