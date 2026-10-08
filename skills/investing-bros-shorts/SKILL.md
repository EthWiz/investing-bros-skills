---
name: investing-bros-shorts
description: >-
  Make branded vertical shorts (Reels / YouTube Shorts / TikTok) from an
  Investing Bros / אחים להשקעות episode: pick standalone moments, cut on
  pauses, speaker close-ups, logo + hook headline, burned-in Hebrew captions,
  leveled audio. Use when Amitai asks for "shorts", "clips", "reels", "רילס",
  "שורטס" or "קליפים" for episode N. Explainer shorts can be rendered with
  animated cards via investing-bros-hyperframes.
---
# Investing Bros shorts

Load `investing-bros-show` first — brand palette, logo, fonts, loudness and the recording layout live there.

## When to use
After post-production for episode N, when Amitai asks for shorts.

## Inputs
From the episode's `extras/` folder:
- `segments.json` — the transcript
- the raw master — `.mp4` if the recording has video, otherwise `.m4a`
- the dark show cover (for the logo) and Heebo (`Heebo[wght].ttf` from google/fonts)

For audio-only recordings, also the show cover (location in `investing-bros-show`).

Times are on the raw timeline, the same one as `segments.json`. To tell Amitai where a moment is in the published episode, subtract `start` from `edit.json`.

## Steps
1. **Propose moments.** Give Amitai 3–6 candidates as a table: start–end, opening line, why it works, a title. Wait for his picks unless he said to just make them. A good short:
   - hooks in the first 3 seconds (a claim, a number, a story, a question — not "אז…", not "חווים את זה היום")
   - makes sense with no episode context, and is **one idea** with a clean end line
   - lands at 30–60 seconds
   Skip crosstalk and anything that sounds like a buy/sell call out of context. Flag on-air mistakes instead of clipping them. Strong episode-6 shapes: a surprising fact ("SWIFT is a messaging system, not a payments system"), a story → concept ("pizza for 10,000 BTC → why stablecoins exist"), a host's question answered by the other ("So what? — liquidity").
2. **Find exact cut points.** Whisper segment times are only approximate. For every in/out point, look at the audio energy (20 ms frames) for the pause between words and cut inside it; re-transcribe a 1–3 s window around the point if unsure (whisper drops the last word of a window — give it ~1 s of tail). Never cut mid-word. Inside a clip you may drop a filler stretch, dead air or a phrase you can't make out — **only** if the sentence still says the same thing. Never drop a caveat or disclaimer to make a line punchier.
3. **Brand assets** (once per episode):
   ```bash
   python3 scripts/brand.py logo "<dark cover>.jpg" logo.png      # check it on black
   python3 scripts/brand.py fonts Heebo[wght].ttf fonts/
   python3 scripts/brand.py frame vertical logo.png frame_vertical.png
   ```
4. **Edit list → render.** One JSON per short (format in `scripts/build_short.py`): kept pieces, which host is on screen per stretch (L/R halves of the side-by-side recording), the fixed hook headline, the end card, a name tag, and the caption cards.
   ```bash
   python3 scripts/build_short.py short1.json     # writes short1.ass / .srt / .sh, warns on length and long lines
   bash short1.sh                                 # run where raw.mp4, frame_vertical.png and fonts/ are
   ```
   - **Framing:** close-up of whoever is talking (their half, 1080 wide); cut to the other host for his lines or a real reaction. Not the whole frame over blur.
   - **Headline:** a faithful paraphrase of what is said in the clip (e.g. "סוויפט היא בכלל לא מערכת תשלומים") — never a claim the hosts didn't make, never investment promises.
   - **Captions:** proofread against the audio, max two lines, ~24 characters a line, key terms in `[emerald]`. Sit above the bottom 400 px and left of the right 170 px (platform UI). Words you can't make out: leave them out of the caption (don't guess) and list them in the hand-back.
   - **Audio:** if one host is quieter, give his pieces a gain (`[start, end, +dB]`) so both measure within ~2 dB; the render normalises to −14 LUFS.
   For a quick whole-frame clip or an audio-only audiogram, `scripts/clip_captions.py` + `scripts/make_clip.sh` still work.

   **Explainer moment? Render it with HyperFrames instead.** When the clip explains something a card can show — a number, "not X but Y", a list, a before/after — use `investing-bros-hyperframes` for this step: the same pieces, shots and captions, plus animated cards (count-up, strike-through, building list) in the band under the video. It looks more produced and gets Hebrew/English text right natively, at ~6× the render time. Punchlines and stories stay on the plain render.
5. **Check the export.** For each short:
   - a strip of 6–8 frames across the clip: captions right-to-left (punctuation at the left end, English words in place), not over faces, inside the safe zone; the right host on screen
   - `ffmpeg -i short.mp4 -af ebur128=peak=true -f null -` → about −14 LUFS, peak below −1 dB; per-host levels close
   - duration 30–60 s; listen to every cut — no clipped words, no clicks

## Hand back
Upload the shorts (and their `.srt`) to the episode's `promo/` folder. Send Amitai the folder link and, per short: where it is in the episode, its length, its opening line, a suggested title, any cuts made inside it, and any words you couldn't verify.

## Never
- Post anywhere — Amitai posts.
- Put words on screen the hosts didn't say, or captions you haven't proofread.
- Splice pieces so a sentence means something the host didn't mean, or cut a caveat.
- Use an ASS style `Encoding` other than `-1` — any other value forces left-to-right and Hebrew punctuation lands on the wrong side.
- Add music or stock footage unless Amitai supplies it.
