---
name: investing-bros-shorts
description: >-
  Make branded vertical shorts (Reels / YouTube Shorts / TikTok) from an
  Investing Bros / אחים להשקעות episode: pick standalone moments that hook in
  the first second, cut on pauses, speaker close-ups, logo + hook headline,
  burned-in Hebrew captions, leveled audio, a cover image built to be clicked,
  and an end card plus platform links that send viewers to the full episode,
  all uploaded to the episode's Drive promo/ folder. Also cut optional 5–10 min
  mid-form YouTube segments from the episode. Use when Amitai asks for
  "shorts", "clips", "reels", "רילס", "שורטס", "קליפים", "mid-form" or
  "מיד-פורם" for episode N, and whenever shorts are made as part of
  post-production. Explainer shorts can be rendered with animated cards via
  investing-bros-hyperframes.
---
# Investing Bros shorts

Load `investing-bros-show` first — brand palette, logo, fonts, loudness and the recording layout live there.

A short has three jobs, in this order: **stop the scroll** (the first second), **hold to the payoff** (one idea, no dead air, something changes on screen every few seconds), and **send the viewer to the full episode** (badge, end card, platform link). The cover is a fourth, separate job: it wins the click where the short does not autoplay (profile grids, the YouTube channel page and home page).

## When to use
After post-production for episode N when Amitai asks for shorts — and every time shorts are made as part of a post-production run (`investing-bros-post-production` hands over to this skill). Every short this skill makes ends in Drive with its cover (steps 6–7). Also for an optional mid-form segment (below). Video assets are made only by ליאורה (`investing-bros-show` → Roles).

## Inputs
From the episode's `extras/` folder:
- `segments.json` — the transcript
- the raw master — `.mp4` if the recording has video, otherwise `.m4a`
- the show cover (for the logo; location in `investing-bros-show`) and Heebo (`Heebo[wght].ttf` from google/fonts — fallback in `investing-bros-show` → references/environment.md)

For audio-only recordings, also the show cover (location in `investing-bros-show`).

Times are on the raw timeline, the same one as `segments.json`. To tell Amitai where a moment is in the published episode, subtract `start` from `edit.json`.

## Steps
1. **Propose moments.** Start from Riverside's auto-generated shorts. Riverside makes clips automatically; prefer picking good ready-made ones and adding motion captions over cutting from scratch. Give Amitai 3–6 candidates as a table: start–end, **first words** (what plays in second 0), **payoff line**, score (below), cover headline idea, the **open loop** for the end card (what the episode says next that this clip doesn't), a title. Episode 7 shipped 5 — aim for that. Wait for his picks unless he said to just make them. Nadav approves the cut before a rebuild or an upload (`investing-bros-show` → Roles).

   Score each candidate 0–2 on five things and lead with the highest (8+ of 10 is a strong short):

   | | 0 | 2 |
   |---|---|---|
   | **Hook** | warms up ("אז…", "חווים את זה היום") | the first sentence is a claim, a number, a story or a question a stranger wants answered |
   | **One idea** | needs the episode to make sense | one idea, standalone, clean end line |
   | **Payoff** | trails off | lands a surprise, a reframe or a punchline before the end |
   | **Energy** | flat read, long pauses | a host reacts, laughs or pushes back; quick delivery |
   | **Open loop** | the clip says it all | the episode goes further (the next question, the other host's view), so the end card has something true to promise |

   Viewers decide in the first 1–2 seconds whether to swipe (YouTube Studio → Analytics → Shorts → *Viewed vs swiped away*). Length: the shortest cut that still lands the payoff, usually 25–45 s, never over 60. Strong episode-6 shapes: a surprising fact ("SWIFT is a messaging system, not a payments system"), a story → concept ("pizza for 10,000 BTC → why stablecoins exist"), a host's question answered by the other ("So what? Liquidity"). Skip crosstalk and anything that sounds like a buy/sell call out of context. Flag on-air mistakes instead of clipping them.
2. **Find exact cut points.** Start on the hook word itself: no breath, no "אז", no setup sentence the hook doesn't need. Whisper segment times are only approximate. For every in/out point, look at the audio energy (20 ms frames) for the pause between words and cut inside it; re-transcribe a 1–3 s window around the point if unsure (whisper drops the last word of a window — give it ~1 s of tail). Never cut mid-word. Inside a clip you may drop a filler stretch, dead air or a phrase you can't make out — **only** if the sentence still says the same thing. Never drop a caveat or disclaimer to make a line punchier.

   **Payoff-first** (optional): if the strongest line comes late, the short may open with it and then play the setup — list that piece first in `pieces` (`build_fullbleed.py` plays pieces in list order). Only when it is one whole sentence that means the same on its own, it is not played twice, and Nadav approves the cut.
3. **Brand assets** (once per episode):
   ```bash
   python3 scripts/brand.py logo "<show cover>.jpg" logo.png      # cover location in investing-bros-show; check the logo on black
   python3 scripts/brand.py fonts Heebo[wght].ttf fonts/
   python3 scripts/brand.py frame vertical logo.png frame_vertical.png
   ```
   Without github.com: `npm pack @fontsource-variable/heebo`, then `brand.py fonts heebo-hebrew-wght-normal.woff2 heebo-latin-wght-normal.woff2 fonts/` (merges the subsets).
4. **Edit list → render.** One JSON per short: kept pieces, which host is on screen, the hook, punch-in zooms, the badge, the end card, a name tag and the caption cards. The house style is the full-screen render (`build_fullbleed.py`, see House style below); the split-frame `build_short.py` stays available:
   ```bash
   python3 scripts/build_fullbleed.py short1.json   # writes short1_fb.ass / .sh / .srt; errors on dashes, warns on pacing
   bash short1_fb.sh                                # run where the source, logo.png and fonts/ are
   ```
   - **Framing:** close-up of whoever is talking; cut to the other host for his lines or a real reaction. Not the whole frame over blur.
   - **Hook** (first ~2.7 s, `hook`): a faithful paraphrase of what is said in the clip (e.g. "סוויפט היא בכלל לא מערכת תשלומים"), 3–7 words, never a claim the hosts didn't make, never investment promises. It reads from frame 0 (no fade-in), because that frame is what the feed and the YouTube frame picker show. Use the same words as the cover headline.
   - **Badge** (`badge`, e.g. `מתוך פרק 7`): a small pill under the logo from the end of the hook to the end card, so a viewer who leaves early still knows there is a full episode.
   - **Pacing:** something changes on screen at least every ~5 s: a punch-in (zooms alternate 100% / 112%), a reaction shot, a jump cut. The build warns about any still stretch over 6 s.
   - **Captions:** proofread against the audio, max two lines, ~24 characters a line, key terms in `[…]` (gold `#F5B71F`, the house accent). Sit above the bottom 400 px and left of the right 170 px (platform UI). Words you can't make out: leave them out of the caption (don't guess) and list them in the hand-back. The last line stays captioned under the end card.
   - **End card** (last ~2.8 s, `endcard`): see *Point every short at the full episode* below.
   - **Audio:** if one host is quieter, give his pieces a gain (`[start, end, +dB]`) so both measure within ~2 dB; the render normalises to −14 LUFS.

   For a quick whole-frame clip or an audio-only audiogram, `scripts/clip_captions.py` + `scripts/make_clip.sh` still work.

   **Explainer moment? Render it with HyperFrames instead.** When the clip explains something a card can show — a number, "not X but Y", a list, a before/after — use `investing-bros-hyperframes` for this step: the same pieces, shots and captions, plus animated cards (count-up, strike-through, building list) in the band under the video. It looks more produced and gets Hebrew/English text right natively, at ~6× the render time. Punchlines and stories stay on the plain render.
5. **Check the export.** For each short, `python3 scripts/check_short.py short.mp4`, then look:
   - `short_hook.jpg` (the frame at 0.5 s): hook fully on screen and readable, the host's face clear. This is the scroll-stopper.
   - `short_strip.jpg`, 8 frames across the clip: captions right-to-left (punctuation at the left end, English words in place), not over faces, inside the safe zone; the right host on screen; the badge and the end card in place.
   - the printout: about −14 LUFS, peak below −1 dB, no **dead air** (any pause of 0.6 s or more is flagged; cut it in `pieces`); duration ≤ 60 s. Per-host levels close.
   - listen to every cut — no clipped words, no clicks.
6. **Make a cover for each short** (see *Covers that get clicked* below):
   ```bash
   python3 scripts/cover_frames.py raw.mp4 --from 2106 --to 2154 --crop 176,0,608,1080 frames.jpg   # pick --at by looking
   python3 scripts/make_cover.py --style fullbleed --source raw.mp4 --at 2121.0 --crop 176,0,608,1080 --logo logo.png \
     --headline "סוויפט היא בכלל|[[לא מערכת תשלומים]]" --episode N --fonts fonts/ --preview "שורט-01-סוויפט-cover.jpg"
   ```
   1080×1920 JPEG (~100 KB) in the short's look: logo, host close-up, the headline, `פרק N` pill. Look at `…-cover_preview.png` (feed size, the 3:4 and 1:1 grid crops, a 120-px thumbnail): the boxed line must read in the 120-px one. `--style split --side L --frame frame_vertical.png` makes the split-frame look.
7. **Upload to Drive** — the episode folder's `promo/` (find the folder by its `פרק N` prefix as in `investing-bros-show`; create `promo/` inside it if missing). File names follow `investing-bros-show` → Naming:
   - **Cover (`.jpg`) and captions (`.srt`)** — small: the Drive connector's create-file call into the `promo/` folder id (JPEG as base64 with `image/jpeg`; `.srt` as text with `text/plain`, conversion to Google Docs **off**).
   - **Platform copy (`youtube-שורט-NN.md`)** — as text, next to the short (see *Point every short at the full episode*).
   - **Video (`.mp4`)** — the newer Drive connector takes a file up to **100 MB** (`investing-bros-show` → references/environment.md); `drive.sh put` uses the Drive API and is not bound by that cap. The browser path is still ≤10 MB per call, so for a browser upload first make an upload copy: `scripts/fit_size.sh short.mp4 "שורט-01-סוויפט.mp4"` (two-pass, under 9.5 MB; a short that already fits is copied as is). If no browser can reach Drive, give Amitai the exact files, names and folder link to drag in, and say so in the hand-back.
   - Check: list `promo/` and confirm every short has its `.mp4`, `-cover.jpg`, `.srt` and `.md`, none empty.

## Covers that get clicked
Where the cover is seen, and what that means (checked October 2026):

| Platform | Where the cover shows | How it is set |
|---|---|---|
| YouTube Shorts | Home page and the channel's Home / Shorts tabs, **not** the Shorts feed (there the video autoplays from frame 0) | Custom upload only for YouTube Partner Program channels, on desktop. Otherwise pick a frame in the YouTube app: pick the hook frame (~0.5 s), which carries the same headline |
| Instagram Reels | Profile grid, cropped to **3:4** (1080×1440) since January 2025; the full 9:16 elsewhere | Upload the 1080×1920 cover before posting; it can't be changed after |
| TikTok | Profile grid (about 3:4) | Upload or pick a cover when posting |

So the hook frame and the cover say the same thing, and the headline and pill stay inside the centre 1080×1080 (every grid crop keeps it; `make_cover.py` enforces it). What makes a viewer click:
- **One face, one emotion.** Pick the frame with `cover_frames.py`: a clear expression that fits the hook (surprise, a smile, a raised eyebrow, a pointing hand), eyes open, mouth not mid-word, sharp, no hand over the face. The script adds a little contrast and sharpening for small sizes.
- **3–6 words, one focal line.** The headline is the short's hook, said shorter. Put the words that carry the curiosity in one `[[…]]` line (navy on a gold box); the rest white. The script refuses more than 3 lines or 18 characters a line, and warns over 6 words.
- **Open a question, don't answer it.** "למה סין קונה זהב?" beats "סין קונה זהב כי…". Still a faithful paraphrase: never a number you haven't verified, never a promise the clip doesn't keep.
- **Complement the title, don't repeat it.** The platform shows the title next to or under the cover; together they should say more than either alone.
- **Check it tiny.** If the boxed line isn't readable in the 120-px tile of the preview, cut words.

## Point every short at the full episode
The point of a short is a new listener for the episode. Three layers, all on every short:
1. **Badge** (`badge`): `מתוך פרק N`, on screen from the end of the hook to the end card.
2. **End card** (`endcard`, last ~2.8 s, the last line stays captioned above it), 2–3 lines of ≤24 characters:
   - line 1, the **open loop**: a question the episode really answers after this clip (from the transcript, never invented), e.g. `למה מדינות קונות זהב?`
   - line 2, where: `[בפרק N המלא]`
   - line 3, how to find it on any platform: `חפשו: אחים להשקעות`

   One ask only: the full episode. "Follow for more" competes with it, so leave it out. No arrows (Heebo has none) and no "link above/below" on screen: the link sits in a different place on every platform.
3. **Platform links**, written by you into `youtube-שורט-NN.md` next to each short (worked example: [references/youtube-short-example.md](references/youtube-short-example.md)):
   - **YouTube:** the **Related video** in YouTube Studio (the Short → Details) = the full episode. It shows as a tappable link under the channel handle. Plus the description with the episode link at the short's timestamp (`&t=<seconds>`), and a pinned comment with the same link.
   - **Instagram:** caption with the open-loop question and "הקישור לפרק המלא בביו"; check that the profile's bio link points at the show.
   - **TikTok:** same caption; the bio link if the account has one.

## House style and helper scripts (from episode 7)
The default look is the **full-screen style**: the speaking host fills the 9:16 frame, captions appear 2–3 words at a time with the spoken word in gold `#F5B71F`, punch-in zooms on new ideas, a hook title for the first ~2.7 s, the logo top-left with the `מתוך פרק N` badge under it, and a darkened end card. The split-frame `build_short.py` render stays available.

Episode 7 (video producer), on top of that look:
- **5 shorts** per episode, **1080×1920**. Fast cuts, no silences. Zooms alternate **100% / 112%**. Logo end card.
- A complex idea gets a navy-blue motion animation (`investing-bros-hyperframes`) — still the navy / gold / white palette, no loud colours (show conventions → Tone).
- Captions are Heebo Black, active word in gold `#F5B71F`. The scripts render Hebrew with libass (Encoding −1). libass can reverse RTL word order; the video producer worked around that with PIL + raqm. If a script's captions come out in the wrong order, stop and propose a script change — don't ship a one-off renderer (working rules in `investing-bros-show`).

| Step | Script | Notes |
|---|---|---|
| Get the raw video | `drive.sh get FILE_ID DIR` | rclone remote `show` signed in as the bot account; until that exists, ask Amitai to copy the file into Downloads |
| Snap cuts to pauses | `find_cuts.py WINDOW.wav --offset T0 --at t1 t2…` | flags cuts with no real pause |
| Word timings for the picked windows only | `transcribe_clip.py WINDOW.wav --offset T0 --from a --to b --model small.pt` | never the whole episode; install notes in `investing-bros-show` → references/environment.md |
| Time the proofread captions word by word | `align_words.py short.json words.json -o aligned.json` | `cards` stay the proofread text |
| Centre the face | `face_crop.py raw.mp4 --at t1 t2 t3` | prints `crop_x` for both hosts; confirm on one frame — hands in shot pull it off (episode 7: suggested L=64, the face needed ~100) |
| Render the house style | `build_fullbleed.py short.json` then `bash NAME_fb.sh` | also writes `NAME.srt`; `base` + `shots` cut to the other host for reactions; `tags` = name tag; `badge`; `endcard`; `sources`/`crop` take each host's own high-res Riverside track; pieces play in list order (payoff-first). Errors on a dash on screen; warns on a still stretch over 6 s and a long end-card line. Worked example: [references/ep7-asteroid-fullbleed.json](references/ep7-asteroid-fullbleed.json). Its output is also the input for a HyperFrames overlay |
| Check the export | `check_short.py NAME.mp4` | length, −14 LUFS, peak, dead air, plus the hook frame and a frame strip you must look at |
| Pick the cover frame | `cover_frames.py raw.mp4 --from a --to b --crop x,y,w,h frames.jpg` | sheet of 12 candidates labelled with source time; `--font fonts/Heebo-SemiBold.ttf` if ffmpeg has no default font |
| Cover in the house style | `make_cover.py --style fullbleed --crop x,y,w,h --logo logo.png --preview …` | same crop as the short; `[[…]]` = boxed focal line |
| Upload to Drive | `drive.sh put FILE PROMO_FOLDER_ID` | |
| Post to Telegram (only when Amitai asks) | `send_telegram.py video short.mp4 --caption … --thumb cover.jpg` | token/chat ID from `telegram.env`; `delete ID` removes the bot's own post |

Add 1–2 animated explainer panels with `investing-bros-hyperframes` only where they show the idea (episode 7: asteroid lands on Earth; supply ×2 → value ½).

## Titles and descriptions (YouTube)
- **Title:** Hebrew hook + emoji + a short English keyword phrase + `#shorts`. Example: `למה סין קונה הרבה זהב? 🇨🇳 Why China Is Buying Gold #shorts`. It complements the cover headline rather than repeating it word for word.
- **Description:** a 1–2 sentence hook; a question that invites comments; `🎧 לפרק המלא: <link>`; a subscribe line; `אין כאן המלצת השקעה. רק שיחה.`; hashtags mixing Hebrew and English.
- No em or en dash in any of it (`investing-bros-show` → Hebrew); use a comma, a colon or `|`.

## Mid-form segments
Optional 5–10 min YouTube segments: **one continuous standalone stretch** cut from the episode (episode 7: "למה זהב?" 11:57–19:11, about 7 min). Not a montage.
- Start and end on sentence boundaries (`find_cuts.py`). Leave out any part that is being re-recorded.
- **Title** with a few English keywords. **Description:** hook, link to the full episode, the disclaimer above.
- Share a review copy compressed under 100 MB (transfer caps in `investing-bros-show` → references/environment.md). Nadav approves it before upload.

## Hand back
Send Amitai the `promo/` folder link and, per short: where it is in the episode, its length, its score, its opening line, a suggested title, its cover's headline, its end-card open loop, any cuts made inside it (and whether it opens payoff-first), any build or check warnings you accepted and why, and any words you couldn't verify. If any file still needs his manual upload, list it first. Remind him of the per-platform link steps in each `youtube-שורט-NN.md` (Related video, pinned comment, bio link).

## Never
- Post anywhere unless Amitai asks in chat for that post, and then only to a destination listed in `investing-bros-show`.
- Put words on screen the hosts didn't say, or captions you haven't proofread.
- Splice pieces so a sentence means something the host didn't mean, or cut a caveat. A payoff-first open moves a whole sentence, never half of one.
- Promise on the end card something the episode doesn't contain.
- Use an ASS style `Encoding` other than `-1` — any other value forces left-to-right and Hebrew punctuation lands on the wrong side.
- Put an em or en dash on screen, in a cover or in platform copy.
- Add music or stock footage unless Amitai supplies it.
- Use a figure you haven't verified as the hook headline or cover headline — keep it in the captions as said, and flag it in the hand-back.
- Hand back a short that isn't in Drive with its cover — or a cover whose headline says more than the clip does.
- Write your own render, caption, download or upload code, or work around a missing feature without saying so — follow the working rules in `investing-bros-show`.
