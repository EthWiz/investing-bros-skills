---
name: investing-bros-shorts
description: >-
  Make branded vertical shorts (Reels / YouTube Shorts / TikTok) from an
  Investing Bros / אחים להשקעות episode: pick standalone moments, cut on
  pauses, speaker close-ups, logo + hook headline, burned-in Hebrew captions,
  leveled audio, plus a cover image sized for each short, all uploaded to the
  episode's Drive shorts/ folder. Explainer shorts can get animated cards
  (HyperFrames). Also cuts 5–10 min mid-form highlights for YouTube. Use when
  Amitai asks for "shorts", "clips", "reels", "רילס", "שורטס", "קליפים",
  "hyperframes", "כרטיסים", "גרפיקה מונפשת", "highlights", "mid-form" or
  "מיד-פורם" for episode N.
---
# Investing Bros shorts

Load `investing-bros-show` first — show facts, deployed asset paths, loudness and recording layout live there.

Load `investing-bros-brand` for visual specifications and request graphic assets from it.
It owns cover art, lower thirds and other visual assets; this skill owns video assembly.
Existing renderer defaults remain legacy implementations until a reviewed migration.
Do not create competing brand rules or silently change approved artwork.

## When to use
After the audio edit (`investing-bros-post-production`) for episode N: shorts are made for every episode, mid-form highlights when Amitai wants them. Every short this skill makes ends in Drive with its cover (steps 6–7). Video assets are made only by ליאורה (`investing-bros-show` → Roles).

## Inputs
From the episode's `extras/` folder:
- `segments.json` — the transcript
- the raw master — `.mp4` if the recording has video, otherwise `.m4a`
- the current newspaper logo source (location in `investing-bros-show`) and Heebo
  (`Heebo[wght].ttf` from google/fonts — fallback in `investing-bros-show` →
  references/environment.md)

For audio-only recordings, also the archived square show cover (location in
`investing-bros-show`) for the audiogram background.

Times are on the raw timeline, the same one as `segments.json`. To tell Amitai where a moment is in the published episode, subtract `start` from `edit.json`.

## Steps
1. **Propose moments.** Follow [references/moment-scoring.md](references/moment-scoring.md).
   Riverside's auto-generated shorts, when they are already in Drive, are candidates
   like any other (the box cannot pass Riverside's captcha; don't block on it).
   - Pull ~10 candidates from the transcript, at least 3 from the deep dive.
   - Score each 1–5 on hook, standalone, payoff and friction, then rank them:
     `python3 scripts/score_moments.py segments.json candidates.json --top 5`
     (adds pace, flags filler openers and anything outside 20–45 s).
   - Listen to the top picks, then give Amitai the table it prints (5 picks, at least 2
     from the deep dive). Wait for his picks unless he said to just make them. Nadav
     approves the cut before a rebuild or an upload (`investing-bros-show` → Roles).
   - For each pick, plan the **opening** (the strongest line first, moved to the front if
     it comes later), the **last line** (cut right after the payoff) and the **end card**
     (what the full episode adds on this topic).
   Skip crosstalk and anything that sounds like a buy/sell call out of context. Flag on-air mistakes instead of clipping them.
2. **Find exact cut points.** Whisper segment times are only approximate. For every in/out point, look at the audio energy (20 ms frames) for the pause between words and cut inside it; re-transcribe a 1–3 s window around the point if unsure (whisper drops the last word of a window — give it ~1 s of tail). Never cut mid-word. Inside a clip you may drop a filler stretch, dead air or a phrase you can't make out — **only** if the sentence still says the same thing. Never drop a caveat or disclaimer to make a line punchier.
3. **Graphic assets** (once per episode): request new artwork/specifications from `investing-bros-brand`. The commands below prepare assets for the existing renderer; they do not implement Financial Journal layouts:
   ```bash
   cp <investing-bros-brand>/assets/logo-solid.png logo.png
   python3 scripts/brand.py fonts Heebo[wght].ttf fonts/
   python3 scripts/brand.py frame vertical logo.png frame_vertical.png
   ```
4. **Edit list → render.** One JSON per short (format in `scripts/build_short.py`): kept pieces in play order, which host is on screen per stretch (L/R halves of the side-by-side recording), the fixed hook headline, the end card, a name tag, and the caption cards. Both renderers warn on length, a missing hook and a generic end card; fix those before rendering.
   ```bash
   python3 scripts/build_short.py short1.json     # writes short1.ass / .srt / .sh, warns on length and long lines
   bash short1.sh                                 # run where raw.mp4, frame_vertical.png and fonts/ are
   ```
   - **The first second:** frame 1 is the host mid-sentence with the hook on screen. No fade-in, no logo intro, no breath before the first word. The hook is an open question the short answers at the end.
   - **Framing:** close-up of whoever is talking (their half, 1080 wide); cut to the other host for his lines or a real reaction. Not the whole frame over blur.
   - **Headline:** a faithful paraphrase of what is said in the clip (e.g. "סוויפט היא בכלל לא מערכת תשלומים") — never a claim the hosts didn't make, never investment promises.
   - **Captions:** proofread against the audio, max two lines, ~24 characters a line, key terms in `[…]` (that markup currently renders as legacy gold `#F5B71F`). Sit above the bottom 400 px and left of the right 170 px (platform UI). Words you can't make out: leave them out of the caption (don't guess) and list them in the hand-back.
   - **Audio:** if one host is quieter, give his pieces a gain (`[start, end, +dB]`) so both measure within ~2 dB; the render normalises to −14 LUFS.
   For a quick whole-frame clip or an audio-only audiogram, `scripts/clip_captions.py` + `scripts/make_clip.sh` still work.

   **Explainer moment? Render it with HyperFrames instead.** When the clip explains something a card can show — a number, "not X but Y", a list, a before/after — follow [references/hyperframes.md](references/hyperframes.md) for this step: the same pieces, shots and captions, plus animated cards (count-up, strike-through, building list) in the band under the video. It looks more produced and gets Hebrew/English text right natively, at ~6× the render time. Punchlines and stories stay on the plain render.
5. **Check the export.** For each short:
   - a strip of 6–8 frames across the clip: captions right-to-left (punctuation at the left end, English words in place), not over faces, inside the safe zone; the right host on screen
   - `ffmpeg -i short.mp4 -af ebur128=peak=true -f null -` → about −14 LUFS, peak below −1 dB; per-host levels close
   - duration 20–45 s (up to 60 s with a reason in the hand-back); listen to every cut — no clipped words, no clicks
6. **Make a cover for each short** — the image Reels / Shorts / TikTok show before play and in the profile grid:
   Request Financial Journal cover artwork from `investing-bros-brand`, supplying the hook, episode number and source frame if relevant. The command and layout notes below describe the legacy video-frame cover only; use them when retaining that deployed style. They are not an alternative brand system.
   ```bash
   python3 scripts/make_cover.py --source raw.mp4 --at <source time of a good frame> --side L \
     --headline "סוויפט היא בכלל|[לא מערכת תשלומים]" --episode N \
     --frame frame_vertical.png --fonts fonts/ "שורט-01-סוויפט-cover.jpg"
   ```
   - 1080×1920 JPEG (~100 KB), same look as the short: logo, host close-up, the hook headline, `פרק N` pill.
   - The headline and pill sit inside the centre 1080×1080 square, so Instagram's 4:5 and 1:1 grid crops keep them (TikTok/Shorts show the full 9:16).
   - Headline = the short's hook (same faithful paraphrase as its on-screen headline), 1–3 lines of ≤18 characters.
   - Pick the frame by looking: host facing camera, eyes open, mouth not mid-word, his half of the recording (`--side`). Check the result at thumbnail size (~200 px wide).
7. **Upload to Drive** — the episode folder's `shorts/` (find the folder by its `פרק N` prefix as in `investing-bros-show`; create `shorts/` inside it if missing). File names follow `investing-bros-show` → Naming:
   - **Cover (`.jpg`) and captions (`.srt`)** — small: the Drive connector's create-file call into the `shorts/` folder id (JPEG as base64 with `image/jpeg`; `.srt` as text with `text/plain`, conversion to Google Docs **off**).
   - **Video (`.mp4`)** — the newer Drive connector takes a file up to **100 MB** (`investing-bros-show` → references/environment.md); `drive.sh put` uses the Drive API and is not bound by that cap. The browser path is still ≤10 MB per call, so for a browser upload first make an upload copy: `scripts/fit_size.sh short.mp4 "שורט-01-סוויפט.mp4"` (two-pass, under 9.5 MB; a short that already fits is copied as is). If no browser can reach Drive, give Amitai the exact files, names and folder link to drag in, and say so in the hand-back.
   - Check: list `shorts/` and confirm every short has its `.mp4`, `-cover.jpg`, `.srt` and `youtube-שורט-NN.md`, none empty.

## Existing renderer and helper scripts (from episode 7)
The deployed **full-screen renderer** puts the speaking host in the 9:16 frame, captions 2–3 words at a time with the spoken word in legacy gold `#F5B71F`, punch-in zooms on new ideas, a hook title for the first ~2.7 s, the logo top-left, and a darkened end card. The split-frame `build_short.py` render stays available. These are implementation notes; `investing-bros-brand` owns new visual specifications, and migration requires a reviewed sample.

Episode 7 (video producer), on top of that look:
- **5 shorts** per episode, **1080×1920**. Fast cuts, no silences. Zooms alternate **100% / 112%**. Logo end card.
- A complex idea can use a motion animation ([references/hyperframes.md](references/hyperframes.md)). Its existing navy/gold/white implementation remains until a reviewed brand migration.
- Captions are Heebo Black, active word in gold `#F5B71F`. The scripts render Hebrew with libass (Encoding −1). libass can reverse RTL word order; the video producer worked around that with PIL + raqm. If a script's captions come out in the wrong order, stop and propose a script change — don't ship a one-off renderer (working rules in `investing-bros-show`).

| Step | Script | Notes |
|---|---|---|
| Get the raw video | `drive.sh get FILE_ID DIR` | rclone remote `show` signed in as the bot account; until that exists, ask Amitai to copy the file into Downloads |
| Snap cuts to pauses | `find_cuts.py WINDOW.wav --offset T0 --at t1 t2…` | flags cuts with no real pause |
| Word timings for the picked windows only | `transcribe_clip.py WINDOW.wav --offset T0 --from a --to b --model small.pt` | never the whole episode; install notes in `investing-bros-show` → references/environment.md |
| Time the proofread captions word by word | `align_words.py short.json words.json -o aligned.json` | `cards` stay the proofread text |
| Centre the face | `face_crop.py raw.mp4 --at t1 t2 t3` | prints `crop_x` for both hosts; confirm on one frame — hands in shot pull it off (episode 7: suggested L=64, the face needed ~100) |
| Render the deployed video style | `build_fullbleed.py short.json` then `bash NAME_fb.sh` | also writes `NAME.srt`; `base` + `shots` cut to the other host for reactions; `tags` = name tag; `sources`/`crop` take each host's own high-res Riverside track. Worked example: [references/ep7-asteroid-fullbleed.json](references/ep7-asteroid-fullbleed.json). Its output is also the input for a HyperFrames overlay |
| Check the export | `check_short.py NAME.mp4` | length, −14 LUFS, peak, and a frame strip you must look at |
| Legacy video-frame cover (explicit reuse only) | `make_cover.py --style fullbleed --crop x,y,w,h --logo logo.png …` | same crop as the short; new cover artwork comes from `investing-bros-brand` |
| Upload to Drive | `drive.sh put FILE SHORTS_FOLDER_ID` | |
| Post to Telegram (only when Amitai asks) | `send_telegram.py video short.mp4 --caption … --thumb cover.jpg` | token/chat ID from `telegram.env`; `delete ID` removes the bot's own post |

**Link every short to the full episode** (this is what turns Short views into episode views):
- End card: name what the full episode adds on this topic and point up to the link, e.g. `["בפרק המלא: למה דווקא זהב?", "[אחים להשקעות · פרק N]", "הקישור לפרק כאן למעלה"]`. Not a generic "לפרק המלא" (the renderers warn). No arrow glyphs (Heebo has none).
- Hand back a `youtube-שורט-NN.md` next to each short with: the **Related video** to set in YouTube Studio (the full episode — that is the tappable link on the Short), title, description with the episode link at the short's timestamp (`&t=<seconds>`), the pinned-comment text, and the `.srt` to upload. Worked example: [references/youtube-short-example.md](references/youtube-short-example.md).

Add 1–2 animated explainer panels ([references/hyperframes.md](references/hyperframes.md)) only where they show the idea (episode 7: asteroid lands on Earth; supply ×2 → value ½).

## Titles and descriptions (YouTube)
- **Title:** Hebrew hook + emoji + a short English keyword phrase + `#shorts`. Example: `למה סין קונה הרבה זהב? 🇨🇳 Why China Is Buying Gold #shorts`.
- **Description:** a 1–2 sentence hook; a question that invites comments; `🎧 לפרק המלא: <link>`; a subscribe line; `אין כאן המלצת השקעה. רק שיחה.`; hashtags mixing Hebrew and English.

## Mid-form highlights
Optional 5–10 min YouTube videos, each **one continuous standalone stretch** of the episode on one engaging subject (episode 7: "למה זהב?" 11:57–19:11, about 7 min). Not a montage. Elsewhere these are called highlights or clips.
- Pick 1–3 with Amitai: a deep-dive argument or an investment idea that stands without the rest of the episode.
- Start and end on sentence boundaries (`find_cuts.py`). Leave out any part that is being re-recorded.
- **Title** with a few English keywords. **Description:** hook, link to the full episode, the disclaimer. Run `check_copy.py` from `investing-bros-title-description` on the description (`--description`).
- File as `mid-form/מיד-פורם-NN-<נושא>.mp4` with its title and description in `מיד-פורם-NN-<נושא>.txt`. Share a review copy compressed under 100 MB (transfer caps in `investing-bros-show` → references/environment.md). Nadav approves it before upload.

## Done when
- `shorts/` has every short Nadav approved (episode 7 shipped 5), each with `.mp4`, `-cover.jpg`, `.srt` and `youtube-שורט-NN.md`, none empty.
- `mid-form/` has each highlight that was asked for, with its `.txt`.
- `check_short.py` passed on every short.

## Hand back
Send Amitai the `shorts/` folder link and, per short: where it is in the episode, its scores, its length (and why, if over 45 s), its opening line, a suggested title, its cover's headline, any cuts made inside it, and any words you couldn't verify. If any file still needs his manual upload, list it first.

## Never
- Post anywhere unless Amitai asks in chat for that post, and then only to a destination listed in `investing-bros-show`.
- Put words on screen the hosts didn't say, or captions you haven't proofread.
- Splice pieces so a sentence means something the host didn't mean, or cut a caveat.
- Use an ASS style `Encoding` other than `-1` — any other value forces left-to-right and Hebrew punctuation lands on the wrong side.
- Add music or stock footage unless Amitai supplies it.
- Use a figure you haven't verified as the hook headline or cover headline — keep it in the captions as said, and flag it in the hand-back.
- Hand back a short that isn't in Drive with its cover — or a cover whose headline says more than the clip does.
- Write your own render, caption, download or upload code, or work around a missing feature without saying so — follow the working rules in `investing-bros-show`.
