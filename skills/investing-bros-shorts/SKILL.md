---
name: investing-bros-shorts
description: >-
  Make branded vertical shorts (Reels / YouTube Shorts / TikTok) from an
  Investing Bros / אחים להשקעות episode: pick standalone moments, cut on
  pauses, speaker close-ups, logo + hook headline, burned-in Hebrew captions,
  leveled audio, plus a cover image sized for each short, all uploaded to the
  episode's Drive Shorts/ folder. Explainer shorts can get animated cards
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

Times are on the raw timeline, the same one as `segments.json`. To tell Amitai where a moment is in the published episode, or to link a short to it (`&t=`), map the time with `python3 scripts/edit_map.py edit.json --raw T` (plus the video's opening length on YouTube).

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
3. **Cut fresh from the final episode file.** Always start from the published/final episode master, never from an earlier Short or a burned-in render. Edit the kept pieces with `scripts/make_base.py` (copy it, set `SRC` and the `K` list of `(audio_start, audio_end, video_delay)`): crop to a **static** head-and-shoulders close-up (no zooms, no jump cuts except removing silence), scale to 1080×1920, 24 fps, logo at x 56 y 150 (210 px wide), highpass + gentle compressor, two-pass `loudnorm` to **−14 LUFS**, true peak ≤ −1.5 dB. It writes `<name>_clean.mp4` (no captions/graphics) and `timemap.json`. No music, no SFX, no b-roll.
4. **Captions = exactly what was said.** Transcribe every kept piece word by word (`transcribe_clip.py`, then listen). Captions must match the audio verbatim. If a phrase is unclear after re-transcribing and listening, **cut it out of the edit** (step 3) rather than guess — record what was dropped in `meta.source`. 1–4 words per caption, white heavy Heebo with soft shadow, no box, at y≈1480. Only keywords/numbers go **#F5B71F** (`highlight` list), never every word.
5. **Write the config and render** — one JSON per Short (schema below; full example `references/configs/example-ep3-datacenters.json`), then:
   python3 scripts/v5_gfx.py        # in WORK: edit hook/end-card strings first -> v5_hook.png, v5_cta.png, v5_end.png
   python3 scripts/build_amitai_short.py --config short.json --work WORK --output short.mp4
   `WORK` holds the clean base, `fonts/Heebo-{Black,ExtraBold,SemiBold}.ttf`, `logo.png` (torn-paper logo), `v5_cta.png`, `v5_end.png`. `scripts/end_gfx.py` is the ep3 variant of the end card only.
6. **One QA pass, then Telegram for approval.** Check a strip of 8 frames + `check_short.py`: hook strips 0–3 s, logo on every frame, name tag matches who is speaking, captions RTL and verbatim, panels don't hide captions or logo, CTA + arrow, navy end card with no caption leaking onto it, −14 LUFS / peak < −1 dB. Fix what fails once, then send the Short to Telegram for Nadav/Amitai's approval (`send_telegram.py video short.mp4 --caption …`, destination from `investing-bros-show`). Do not upload or publish before approval.
   Cover: see `investing-bros-short-covers`. **Default (since episode 1, short 01): a dedicated cover per short made with the Codex CLI** on Amitai's Mac, in the `investing-bros-brand` vertical Shorts layout (recipe: `investing-bros-brand` → references/prompts.md, "Codex backend"). Copy the result to the box, resize to 1080×1920 JPEG, check the Hebrew letter by letter at full and thumbnail size, and use it both as `-cover.jpg` and as the YouTube custom thumbnail. `make_cover.py` below is the fallback when Codex is unavailable.
7. **Upload to Drive** — every Short's video and its cover/thumbnail go in the `Shorts/` subfolder of the current episode's Drive folder (`investing-bros-show` → Drive tree, Shorts rule; find the episode folder by its `פרק N` prefix; create `Shorts/` inside it if missing). File names follow `investing-bros-show` → Naming:
   - **Cover (`.jpg`) and captions (`.srt`)** — small: the Drive connector's create-file call into the `Shorts/` folder id (JPEG as base64 with `image/jpeg`; `.srt` as text with `text/plain`, conversion to Google Docs **off**).
   - **Phone-friendly copy first:** re-encode every MP4 you hand over or upload with `-c:v libx264 -profile:v main -pix_fmt yuv420p -movflags +faststart -brand mp42 -c:a aac` (iPhone/WhatsApp/Drive preview all play it).
   - **Video via the box browser, not the connector:** the Drive connector and `UploadFile` label MP4s `application/mp4`, which Drive shows as "unsupported file". Upload videos by dragging them into the `Shorts/` folder in the box browser signed in as the bot Drive account (open Drive links with `?authuser=N` for that account, or the default account hits a verify page).
   - **Video (`.mp4`)** — the newer Drive connector takes a file up to **100 MB** (`investing-bros-show` → references/environment.md); `drive.sh put` uses the Drive API and is not bound by that cap. The browser path is still ≤10 MB per call, so for a browser upload first make an upload copy: `scripts/fit_size.sh short.mp4 "שורט-01-סוויפט.mp4"` (two-pass, under 9.5 MB; a short that already fits is copied as is). If no browser can reach Drive, give Amitai the exact files, names and folder link to drag in, and say so in the hand-back.
   - Check: list `Shorts/` and confirm every short has its `.mp4`, `-cover.jpg`, `.srt` and `youtube-שורט-NN.md`, none empty.

## Approved Shorts format (Amitai's Cybercab Short is the base template)
Reference analysis: [references/style-from-amitai.md](references/style-from-amitai.md). Every template element stays as in Amitai's Short; our additions (explainer panels) are layered on top and never restyle it.

| Element | Spec |
|---|---|
| Hook (0–3 s) | two stacked torn-paper strips, **cream** on top, **mustard/yellow** below, navy Heebo Black ~96 px, top ≈ y 700, on screen from frame 1, 0.3 s fade-out ending at 3.0 s. Text = faithful paraphrase of the clip |
| Logo | torn-paper podcast logo top-left (x 56, y 150, 210 px wide), whole Short |
| Name tag | small gold `#F5B71F` tag, black ExtraBold text, top-right (right edge x 1024, y 150); **switches with the speaker** via `tags` |
| Captions | white heavy Heebo, soft dark shadow, no box, 1–4 words, centred y≈1480, always on (also under panels); keywords only in `#F5B71F`; verbatim |
| Explainer panels | large centred animated navy torn-paper panel, **~1 per 20 s** (45 s → 2), outside hook/CTA/end card. Covering faces is OK; captions and logo stay visible. Drawn vector icons (`VIS` in the script) — **never emoji** (stripped automatically). Panel title/subtitle = **only words spoken in that window**; no invented numbers or claims |
| CTA | "הקישור לפרק המלא בתיאור" on a cream torn strip over the chest + **yellow down arrow**, the last ~3 s of speech |
| End card | hard cut, 3 s silent: navy `#09243B`, big logo, cream pill **פרק X**, episode title in white (2 lines), CTA in yellow + arrow |
| Framing / audio | static close-up, no zoom; no music/SFX; −14 LUFS, peak < −1 dB; 1080×1920, 24 fps |

### Config schema (`build_amitai_short.py`)
All times are **output** seconds (after the edit in `make_base.py`).
```jsonc
{
  "base": "ep3_dc_clean.mp4",                 // clean base in --work (from make_base.py)
  "meta": {"episode": 3, "speaker": "אמיתי רסקין",   // default tag when "tags" is absent
           "title": "…", "source": "episode file + kept/dropped ranges"},
  "hook": {"start": 0.0, "end": 3.0, "top_line": "דאטה סנטרים", "bottom_line": "בחלל?"},
  "tags": [[0.0, 16.49, "אמיתי רסקין"], [16.49, 17.78, "נדב רסקין"]],   // [start, end, name]; switch with speaker
  "hyperframes": [{                            // explainer panels, ~1 per 20 s
    "id": "dc_1", "start": 8.3, "end": 23.5,
    "layout": "steps",                         // or "split_comparison" (last step = camera vs LiDAR split)
    "steps": [{"at": 8.3, "visual": "rack", "title": "להביא לחלל", "subtitle": "רוצה את הדאטה סנטרים"}]
    // optional per step: "pct" (clock), "multiplier" (scale)
  }],
  "cta_overlay": {"start": 40.4, "end": 43.15, "text": "הקישור לפרק המלא בתיאור"},
  "captions": [{"start": 0.0, "end": 1.6, "text": "…verbatim…", "highlight": ["keyword"]}]
}
```
`visual` icons: `car_front, route, brain, robot, house, bars_up, clock, two_cars, scale` (ep1) and `rack, sun_ozone, sun_half, panel_sun, sats` (ep3); unknown visuals fall back to bars/scale. Add new icons as `ic_<name>(d, cx, cy, s, t, a)` and register in `VIS`.
Helpers: `strips.py` (torn strip), `mg.py` (easing), `make_base.py` (edit + loudness), `v5_gfx.py` / `end_gfx.py` (hook, CTA, end card PNGs).

## Legacy renderer and helper scripts (from episode 7)
Kept for helpers (cut snapping, transcription, alignment, checks, Drive, Telegram). Their full-bleed look (zooms 100/112 %, gold active word, logo-only end card) is **superseded** by the approved format above.
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
| Centre the face, place captions + hook | `face_crop.py raw.mp4 --at t1 t2 t3` (side-by-side) or `face_crop.py source.mp4 --at … --crop x,y,w,h` (one-host frame) | prints `crop_x` and, with OpenCV, `caption_y` / `hook_y` suggestions; confirm on one frame — hands in shot pull it off (episode 7: suggested L=64, the face needed ~100) |
| Render the deployed video style | `build_fullbleed.py short.json` then `bash NAME_fb.sh` | also writes `NAME.srt`, `NAME_hook.png` (the paper-strip hook) and `NAME_layout.json`; `caption_y` / `hook_y` / `hook_style` set placement and hook look; pieces may open on a later line; `base` + `shots` cut to the other host for reactions; `tags` = name tag; `sources`/`crop` take each host's own high-res Riverside track. Worked example: [references/ep7-asteroid-fullbleed.json](references/ep7-asteroid-fullbleed.json). Its output is also the input for a HyperFrames overlay |
| Check the export | `check_short.py NAME.mp4 [--layout NAME_layout.json]` | length, −14 LUFS, peak, the first second (no black or faded frame 1, speech within 0.4 s), no dead air at the end, caption/hook inside the bounds, and a frame strip you must look at |
| Legacy video-frame cover (explicit reuse only) | `make_cover.py --style fullbleed --crop x,y,w,h --logo logo.png …` | same crop as the short; new cover artwork comes from `investing-bros-brand` |
| Upload to Drive | `drive.sh put FILE SHORTS_FOLDER_ID` | |
| Send to Telegram for approval (step 6) | `send_telegram.py video short.mp4 --caption … --thumb cover.jpg` | token/chat ID from `telegram.env`; `delete ID` removes the bot's own post |

**Link every short to the full episode** (this is what turns Short views into episode views):
- **Cover end card (`"endcard_style": "cover"`)**: the end card in the cover-art look: navy paper over the video, the torn-paper show logo, a cream `פרק N` pill, the episode title (from `youtube/title.txt` minus the `פרק N - ` prefix, `|` for the 2-line break) in cream, and `הקישור לפרק המלא בתיאור` in mustard with a bobbing mustard arrow under it; `endcard` = `[title, "פרק N", link line]`. Pair it with one callout `{"before_endcard": 4.0, ...}`: the bobbing link callout appears 4 s before the card and crossfades into it (no mid-short callout). When the payoff runs to the last frame, start the card at the payoff's last line (`endcard_at`, source time) and set `"endcard_captions": true` so that line's captions keep burning over the card. The card stays inside y 150–1528 (`check_short.py --layout` fails otherwise).
- **Default since episode 1 (approved v5): `"endcard_style": "cover"` with one `{"before_endcard": 4.0}` callout**, as above. The end card says the link is **in the description** (`הקישור לפרק המלא בתיאור`) — that is where it is on a Short. The older text card (`["בפרק המלא: …", "[אחים להשקעות · פרק N]", …]`, no arrow glyph) stays available with `endcard_style: "text"`; never a generic "לפרק המלא" (the renderers warn).
- **Uploading a Short to YouTube:** prefer the YouTube Data API (`investing-bros-episode-upload` → scripts/yt_upload.py, references/youtube-api.md) when the box has `~/.config/youtube-uploader/` credentials: it uploads Private with the title, description, tags and the `-cover.jpg` as thumbnail, without tying up the browser. Studio in the browser is the fallback. Related video, `.srt` and pinned comment are still set in Studio, and going Public needs Amitai's OK.
- Set the **Related video** in YouTube Studio to the full episode on every Short.
- Hand back a `youtube-שורט-NN.md` next to each short with: the **Related video** to set in YouTube Studio (the full episode — that is the tappable link on the Short), title, description with the episode link at the short's timestamp (`&t=<seconds>`), the pinned-comment text, and the `.srt` to upload. Worked example: [references/youtube-short-example.md](references/youtube-short-example.md).

Add 1–2 animated explainer panels ([references/hyperframes.md](references/hyperframes.md)) only where they show the idea (episode 7: asteroid lands on Earth; supply ×2 → value ½).

### Legacy render steps (full-bleed `build_fullbleed.py` / split-frame `build_short.py`)
Kept as on main for rebuilding older exports; the approved format above replaces them for new Shorts.

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
   - **Framing:** close-up of whoever is talking (their half, 1080 wide); cut to the other host for his lines or a real reaction. Not the whole frame over blur. **Zoom speaker-view recordings** (episode 1: 1280×720, one host full frame, Zoom chooses who is on screen): set `"base": "L"` and `"crop": {"L": [x, 0, 405, 720]}` (9:16 of the full height), and check who is on screen at every piece; drop stretches where Zoom shows the other host while this one talks.
   - **Headline (hook):** a faithful paraphrase of what is said in the clip — never a claim the hosts didn't make, never investment promises. **As short as possible while still landing:** one idea, ideally ≤ 6 words, two lines; drop secondary details (they belong in the clip, not the hook). Bad: `למה לסייברקאב אין הגה ורק שני מקומות?` Good: `["למה לסייברקאב", "אין הגה?"]`. The YouTube title uses the same short hook (Hebrew only, see Titles and descriptions).
   - **The hook must not look like a caption.** `build_fullbleed.py` draws it by default (`"hook_style": "strips"`) as Financial Journal torn-paper strips: line 1 on cream `#F5EBD5`, line 2 on mustard `#D8A52E`, navy `#09243B` Heebo Black, a soft paper shadow (spec in `investing-bros-brand` → layouts). Captions stay white with the current word gold. `"hook_style": "legacy"` (white/gold ASS hook) is only for rebuilding old exports.
   - **Captions:** proofread against the audio, max two lines, ~24 characters a line, key terms in `[…]` (that markup currently renders as legacy gold `#F5B71F`). Words you can't make out: leave them out of the caption (don't guess) and list them in the hand-back. An English phrase inside a Hebrew caption is one token joined with a no-break space (`מ-day one`), or libass shows its words in reverse.
   - **Placement — put captions and hook where they make most sense**, inside the bounds (centre y on the 1920-px frame, constants in `brand.py`). **Brief hook → centre of the frame**: the paper-strip hook is on screen only ~2.7 s, so it sits horizontally centred around `hook_y` **960** (allowed 300–1000); it may cover the face briefly, but it keeps at least `HOOK_GAP` (40 px) clear below the logo's bottom edge (y 277) and above the caption line. Captions `caption_y` **1100–1470** (clear of the bottom ~400 px of platform UI; default 1290) go just under the chin. `face_crop.py … [--crop x,y,w,h]` suggests both from the face box (OpenCV): captions under the chin, the hook in the centre unless it would run into those captions; it warns when a close-up is too big for the captions to clear. Confirm on a frame. `build_fullbleed.py` refuses a hook block that breaks the gaps, and `check_short.py` fails a render whose `NAME_layout.json` is outside the bounds or the gaps. A close-up whose chin sits below ~1410 can't be fully cleared: use `caption_y` 1470, turn punch-in zooms off (they push the face down), and say so in the hand-back.
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
   - **Default (since episode 1, short 01): a dedicated cover per short made with the Codex CLI** on Amitai's Mac, in the `investing-bros-brand` vertical Shorts layout (recipe: `investing-bros-brand` → references/prompts.md, "Codex backend"). Copy the result to the box, resize to 1080×1920 JPEG, check the Hebrew letter by letter at full and thumbnail size, and use it both as `-cover.jpg` and as the YouTube custom thumbnail. `make_cover.py` below is the fallback when Codex is unavailable.
   - 1080×1920 JPEG (~100 KB), same look as the short: logo, host close-up, the hook headline, `פרק N` pill.
   - The headline and pill sit inside the centre 1080×1080 square, so Instagram's 4:5 and 1:1 grid crops keep them (TikTok/Shorts show the full 9:16).
   - Headline = the short's hook (same faithful paraphrase as its on-screen headline), 1–3 lines of ≤18 characters.
   - Pick the frame by looking: host facing camera, eyes open, mouth not mid-word, his half of the recording (`--side`). Check the result at thumbnail size (~200 px wide).

## Titles and descriptions (YouTube)
- **Title: Hebrew only.** The short Hebrew hook (same brevity rule as the on-screen hook), optionally one emoji. **No English words, no `#shorts` or any other hashtag in the title, no pipe `|`.** YouTube already files a ≤3-minute vertical video as a Short. English company names go in the description and hashtags, not the title. Example: `למה לסייברקאב אין הגה? 🚕`. ✗ `למה לסייברקאב אין הגה? 🚕 Tesla Cybercab #shorts`, ✗ `למה לסייברקאב אין הגה? | פרק 1`.
- **Description, in this order** (matches the episode order in PR #20: intro, disclaimer, then links, before chapters/hashtags):
  1. a 1–2 sentence hook, then a question that invites comments; a `גילוי נאות` line when a host disclosed a holding on air (confirm with Amitai it's still true);
  2. `אין כאן המלצת השקעה. רק שיחה.`;
  3. blank line, `🎧 לפרק המלא ביוטיוב: <episode link>?t=<seconds>` and `האזינו בספוטיפיי: <Spotify episode link>`;
  4. blank line, a subscribe line, then hashtags (Hebrew and English allowed here).
- **Publish** (only after Amitai's explicit OK, and Nadav's approval of the cut unless Amitai waives it): upload the phone-friendly MP4, set the custom cover, the Related video, the `.srt`, then update `youtube-שורט-NN.md` with the status and the Shorts URL.

## Mid-form highlights
Optional 5–10 min YouTube videos, each **one continuous standalone stretch** of the episode on one engaging subject (episode 7: "למה זהב?" 11:57–19:11, about 7 min). Not a montage. Elsewhere these are called highlights or clips.
- Full standalone segments (deep dive every episode, investment ideas, interviews, explainers) are segment videos via `investing-bros-segment-video`, not mid-form. Mid-form is for other stretches, e.g. an investment idea. Pick 1–3 with Amitai.
- Start and end on sentence boundaries (`find_cuts.py`). Leave out any part that is being re-recorded.
- **Title** with a few English keywords. **Description:** hook, link to the full episode, the disclaimer. Run `check_copy.py` from `investing-bros-title-description` on the description (`--description`).
- File as `mid-form/מיד-פורם-NN-<נושא>.mp4` with its title and description in `מיד-פורם-NN-<נושא>.txt`. Share a review copy compressed under 100 MB (transfer caps in `investing-bros-show` → references/environment.md). Nadav approves it before upload.

## Done when
- `Shorts/` has every short Nadav approved (episode 7 shipped 5), each with `.mp4`, `-cover.jpg`, `.srt` and `youtube-שורט-NN.md`, none empty.
- `mid-form/` has each highlight that was asked for, with its `.txt`.
- `check_short.py` passed on every short.

## Hand back
Send Amitai the `Shorts/` folder link and, per short: where it is in the episode, its scores, its length (and why, if over 45 s), its opening line, a suggested title, its cover's headline, any cuts made inside it, and any words you couldn't verify. If any file still needs his manual upload, list it first.

## Never
- Post anywhere public unless Amitai asks in chat for that post (the Telegram approval send in step 6 is the exception), and only to a destination listed in `investing-bros-show`.
- Put words on screen the hosts didn't say, or captions you haven't proofread.
- Splice pieces so a sentence means something the host didn't mean, or cut a caveat.
- Use an ASS style `Encoding` other than `-1` — any other value forces left-to-right and Hebrew punctuation lands on the wrong side.
- Add music, SFX or stock footage.
- Put emoji or invented numbers on a panel, or guess an unclear phrase in a caption — cut it instead.
- Reuse a burned-in Short as the source — cut fresh from the final episode file.
- Use a figure you haven't verified as the hook headline or cover headline — keep it in the captions as said, and flag it in the hand-back.
- Hand back a short that isn't in Drive with its cover — or a cover whose headline says more than the clip does.
- Write your own render, caption, download or upload code, or work around a missing feature without saying so — follow the working rules in `investing-bros-show`.
