---
name: investing-bros-shorts
description: >-
  Make branded vertical shorts (Reels / YouTube Shorts / TikTok) from an
  Investing Bros / אחים להשקעות episode: pick standalone moments, cut on
  pauses, speaker close-ups, logo + hook headline, burned-in Hebrew captions,
  leveled audio, plus a cover image sized for each short, all uploaded to the
  episode's Drive promo/ folder. Use when Amitai asks for "shorts", "clips",
  "reels", "רילס", "שורטס" or "קליפים" for episode N, and whenever shorts are
  made as part of post-production. Explainer shorts can be rendered with
  animated cards via investing-bros-hyperframes.
---
# Investing Bros shorts

Load `investing-bros-show` first — brand palette, logo, fonts, loudness and the recording layout live there.

## When to use
After post-production for episode N when Amitai asks for shorts — and every time shorts are made as part of a post-production run (`investing-bros-post-production` hands over to this skill). Every short this skill makes ends in Drive with its cover (steps 6–7).

## Inputs
From the episode's `extras/` folder:
- `segments.json` — the transcript
- the raw master — `.mp4` if the recording has video, otherwise `.m4a`
- the show cover (for the logo; location in `investing-bros-show`) and Heebo (`Heebo[wght].ttf` from google/fonts — fallback in `investing-bros-show` → references/environment.md)

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
   python3 scripts/brand.py logo "<show cover>.jpg" logo.png      # cover location in investing-bros-show; check the logo on black
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
6. **Make a cover for each short** — the image Reels / Shorts / TikTok show before play and in the profile grid:
   ```bash
   python3 scripts/make_cover.py --source raw.mp4 --at <source time of a good frame> --side L \
     --headline "סוויפט היא בכלל|[לא מערכת תשלומים]" --episode N \
     --frame frame_vertical.png --fonts fonts/ "שורט-01-סוויפט-cover.jpg"
   ```
   - 1080×1920 JPEG (~100 KB), same look as the short: logo, host close-up, the hook headline, `פרק N` pill.
   - The headline and pill sit inside the centre 1080×1080 square, so Instagram's 4:5 and 1:1 grid crops keep them (TikTok/Shorts show the full 9:16).
   - Headline = the short's hook (same faithful paraphrase as its on-screen headline), 1–3 lines of ≤18 characters.
   - Pick the frame by looking: host facing camera, eyes open, mouth not mid-word, his half of the recording (`--side`). Check the result at thumbnail size (~200 px wide).
7. **Upload to Drive** — the episode folder's `promo/` (find the folder by its `פרק N` prefix as in `investing-bros-show`; create `promo/` inside it if missing). File names follow `investing-bros-show` → Naming:
   - **Cover (`.jpg`) and captions (`.srt`)** — small: the Drive connector's create-file call into the `promo/` folder id (JPEG as base64 with `image/jpeg`; `.srt` as text with `text/plain`, conversion to Google Docs **off**).
   - **Video (`.mp4`)** — too large for the connector. Upload through the browser into `promo/` (signed in as the Drive upload account from `investing-bros-show`). The agent browser's file upload takes ≤10 MB per call, so first make an upload copy: `scripts/fit_size.sh short.mp4 "שורט-01-סוויפט.mp4"` (two-pass, under 9.5 MB; a short that already fits is copied as is). If no browser can reach Drive, give Amitai the exact files, names and folder link to drag in, and say so in the hand-back.
   - Check: list `promo/` and confirm every short has its `.mp4` and `-cover.jpg` (and `.srt`), none empty.

## House style and helper scripts (from episode 7)
The default look is now the **full-screen style**: the speaking host fills the 9:16 frame, captions appear 2–3 words at a time with the spoken word in gold `#F5B71F`, punch-in zooms on new ideas, a hook title for the first ~2.7 s, the logo top-left, and a darkened end card. The split-frame `build_short.py` render stays available.

| Step | Script | Notes |
|---|---|---|
| Get the raw video | `drive.sh get FILE_ID DIR` | rclone remote `show` signed in as the bot account; until that exists, ask Amitai to copy the file into Downloads |
| Snap cuts to pauses | `find_cuts.py WINDOW.wav --offset T0 --at t1 t2…` | flags cuts with no real pause |
| Word timings for the picked windows only | `transcribe_clip.py WINDOW.wav --offset T0 --from a --to b --model small.pt` | never the whole episode; install notes in `investing-bros-show` → references/environment.md |
| Time the proofread captions word by word | `align_words.py short.json words.json -o aligned.json` | `cards` stay the proofread text |
| Centre the face | `face_crop.py raw.mp4 --at t1 t2 t3` | prints `crop_x` for both hosts; confirm on one frame |
| Render the house style | `build_fullbleed.py short.json` then `bash NAME_fb.sh` | also writes `NAME.srt`; `base` + `shots` cut to the other host for reactions; `tags` = name tag; `sources`/`crop` take each host's own high-res Riverside track. Worked example: [references/ep7-asteroid-fullbleed.json](references/ep7-asteroid-fullbleed.json). Its output is also the input for a HyperFrames overlay |
| Check the export | `check_short.py NAME.mp4` | length, −14 LUFS, peak, and a frame strip you must look at |
| Cover in the house style | `make_cover.py --style fullbleed --crop x,y,w,h --logo logo.png …` | same crop as the short |
| Upload to Drive | `drive.sh put FILE PROMO_FOLDER_ID` | |
| Post to Telegram (only when Amitai asks) | `send_telegram.py video short.mp4 --caption … --thumb cover.jpg` | token/chat ID from `telegram.env`; `delete ID` removes the bot's own post |

Add 1–2 animated explainer panels with `investing-bros-hyperframes` only where they show the idea (episode 7: asteroid lands on Earth; supply ×2 → value ½).

## Hand back
Send Amitai the `promo/` folder link and, per short: where it is in the episode, its length, its opening line, a suggested title, its cover's headline, any cuts made inside it, and any words you couldn't verify. If any file still needs his manual upload, list it first.

## Never
- Post anywhere unless Amitai asks in chat for that post, and then only to a destination listed in `investing-bros-show`.
- Put words on screen the hosts didn't say, or captions you haven't proofread.
- Splice pieces so a sentence means something the host didn't mean, or cut a caveat.
- Use an ASS style `Encoding` other than `-1` — any other value forces left-to-right and Hebrew punctuation lands on the wrong side.
- Add music or stock footage unless Amitai supplies it.
- Use a figure you haven't verified as the hook headline or cover headline — keep it in the captions as said, and flag it in the hand-back.
- Hand back a short that isn't in Drive with its cover — or a cover whose headline says more than the clip does.
- Write your own render, caption, download or upload code, or work around a missing feature without saying so — follow the working rules in `investing-bros-show`.
