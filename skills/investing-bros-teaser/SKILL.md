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
After post-production for episode N, when Amitai asks for a teaser. Two kinds:
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
   - Cold open: 2–5 lines from **one** host (15–30 s): open on the most surprising line, end on a question or a hook ("…אז יש לי מניה בכיס?", "השאלה הגדולה היא: So what?"). Each line must stand on its own — reordering lines is fine, splicing half-sentences into a new claim is not.
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
     Taking the audio from the leveled episode track keeps teaser and episode at the same loudness.
   - Animated graphics (optional): when a teaser moment is an explainer — a number, "not X but Y" — and Amitai wants it more designed, render that moment (or a vertical teaser) with `investing-bros-hyperframes` and its cards. Keep the per-host cold opens on `build_teaser.py`: they must match the episode's x264 settings to join it without re-encoding, which a HyperFrames export doesn't.
4. **Watch it once**: captions readable and right-to-left (English words in place), joins clean, no clipped words, nothing out of context that sounds like a buy/sell call. Check loudness (`ebur128`): −14 LUFS for a promo teaser, −16 for a cold open.

## Hand back
Upload to the episode's `promo/` folder. Send Amitai the link with each teaser's length, the moments used (episode time + opening words), any cuts inside a moment, and any words you couldn't verify.

## Never
- Post anywhere unless Amitai asks in chat for that post, and then only to a destination listed in `investing-bros-show`.
- Put words on screen the hosts didn't say, or captions you haven't proofread.
- Splice lines so a host seems to say something he didn't, or cut a caveat to make a line punchier.
- Add music or stock footage unless Amitai supplies it.
- Write your own render, caption, download or upload code, or work around a missing feature without saying so — follow the working rules in `investing-bros-show`.
