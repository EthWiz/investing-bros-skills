---
name: investing-bros-shorts
description: >-
  Make exactly three branded vertical shorts (Reels / YouTube Shorts / TikTok)
  from every Investing Bros / אחים להשקעות episode: pick standalone moments,
  render and QA them, make each cover through the Codex workflow, get Telegram
  approval, file all four assets per short in Drive, then upload after the full
  episode is live and set its links. Rendering and animated explainer cards go
  through investing-bros-remotion. Also cuts 5–10 min mid-form highlights for YouTube. Use when
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
After the audio edit (`investing-bros-post-production`) for episode N: make **exactly three shorts per episode** through the complete flow below; mid-form highlights remain optional when Amitai wants them. Every short ends in Drive with its cover and is uploaded only after the full episode is live (steps 6–7 and Titles and descriptions). Video assets are made only by ליאורה (`investing-bros-show` → Roles).

## Inputs
From the episode's `extras/` folder:
- `segments.json` — the transcript
- the raw master — `.mp4` if the recording has video, otherwise `.m4a` (timeline and audio)
- **each host's own Riverside video track** for the picture, never the side-by-side
  export: Riverside recording share link → Tracks → <host> → download → **Aligned video**
  (`investing-bros-show` → Recording layout). No tracks yet: ask Amitai for the
  recording's share link; don't fall back to cropping the side-by-side
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
   - Listen to the top picks, then give Amitai the table it prints (5 candidates, at least 2
     from the deep dive). The production batch is **exactly 3**: wait for his three picks
     unless he said to just make them, in which case take the top three. Nadav approves
     each cut before a rebuild or an upload (`investing-bros-show` → Roles).
   - For each pick, plan the **opening** (the strongest line first, moved to the front if
     it comes later), the **last line** (cut right after the payoff; the short ends there and loops) and the **CTA**
     (what the full episode adds on this topic).
   - Plan a short two-line **cover title** at the same time. It is the one shared title
     used by the cover, opening banner, YouTube title and first description line. It may
     contain a necessary Latin company/index name; do not add figures or claims absent
     from the clip.
   Skip crosstalk and anything that sounds like a buy/sell call out of context. Flag on-air mistakes instead of clipping them.
2. **Find exact cut points.** Whisper segment times are only approximate. For every in/out point, look at the audio energy (20 ms frames) for the pause between words and cut inside it; re-transcribe a 1–3 s window around the point if unsure (whisper drops the last word of a window — give it ~1 s of tail). Never cut mid-word. Inside a clip you may drop a filler stretch, dead air or a phrase you can't make out — **only** if the sentence still says the same thing. Never drop a caveat or disclaimer to make a line punchier.
3. **Cut fresh from the final episode file.** Always start from the published/final episode master, never from an earlier Short or a burned-in render. Edit the kept pieces with `scripts/make_base.py`: copy it, set `SRC` (the master: timeline and audio), `TRACKS` (each host's Aligned video track) and the `K` list of `(audio_start, audio_end, video_delay, crop, track)` with the speaking host's track and a centred 9:16 crop in that track's pixels, then run `python3 make_base.py --output <name>_clean.mp4` (house speed 1.15x). It crops to a **static** head-and-shoulders close-up (no zooms, no jump cuts except removing silence), scales to 1080×1920 at 24 fps, places the logo at x 56 y 150 (210 px wide), and applies highpass + gentle compressor + two-pass `loudnorm` to **−14 LUFS**, true peak ≤ −1.5 dB. It writes the named clean MP4 (no captions/graphics) and `timemap.json`. No music, no SFX, no b-roll. It syncs each track to the master from the audio and prints the offset, and it refuses a side-by-side picture (episode 8: cropping one half came out tight, soft and off-centre); `--allow-side-by-side` only with Amitai's OK, listed in the hand-back.
   **House playback speed is 1.15x** (Amitai, 2026-10-26, on episode 8 short 05 v6: 1.25x was too fast to read the captions; 1.25x had replaced 1.5x on 2026-10-23). The scripts default to `--speed 1.15` (`make_base.py`, `build_short.py`, `make_clip.sh` vertical, `make_captions.py`; a test keeps them equal); pass `--speed 1.0` only to disable it. They speed video with `setpts` and audio with `atempo`, which preserves natural voice pitch. Source cut points stay on the raw timeline; `timemap.json` and every caption/overlay time are on the shortened output timeline.
4. **Captions = exactly what was said, timed word by word.** Transcribe every kept piece word by word (`transcribe_clip.py`, then listen). Captions must match the audio verbatim. The proofread text comes from the Riverside transcript in the episode folder (the whisper `segments.json` is only for timing; its Hebrew is unreliable). Build the captions with `investing-bros-remotion` → `make_captions.py` (proofread words + whisper word timings + `timemap.json` + the window WAV). If a phrase is unclear after re-transcribing and listening, **cut it out of the edit** (step 3) rather than guess — record what was dropped in `meta.source`. Format: see Captions in the table below.
5. **Write the config and render with Remotion** — one JSON per Short (schema below), then follow `investing-bros-remotion` (the show's animation framework, decided 2026-10-25): `make_props.py` checks the config and writes the props, `render_short.py --stills` gives a QA sheet, `render_short.py` renders `NAME.mp4` + `NAME_layout.json` over the clean base. Explainer cards are its `cards` (modes `inset` default, `full`, `card`). `v5_gfx.py` + `build_amitai_short.py` are legacy: only for rebuilding older exports.
6. **One QA pass, then Telegram for approval.** Run `check_short.py NAME.mp4 --config short.json --youtube-notes youtube-שורט-NN.md` and inspect its 8-frame strip on the **final speed-adjusted render**. The check enforces the shared title in YouTube metadata and the 15–45 s duration; inspect that the opening banner exactly matches `cover_title`, logo is on every frame, name tag matches the speaker, mixed Hebrew/Latin/numbers read in the right order, captions are verbatim, panels hide neither captions nor logo, and the CTA + arrow runs to the last frame (no end card). Audio is −14 LUFS / peak < −1 dB. **45.0 s is a hard cap**: at 1.15x, cut tighter until the check passes; there is no longer an over-length exception. Duration is always checked after speed-up, never against source ranges. Fix what fails once, then send the Short to Telegram for Nadav/Amitai's approval (`send_telegram.py video short.mp4 --caption … --thumb cover.jpg`, destination from `investing-bros-show`). A vertical Short needs `width=1080`, `height=1920`, `supports_streaming=true` and a vertical `thumbnail` in `sendVideo`, or Telegram shows it landscape; the script sends the first three (from ffprobe) and the thumbnail only with `--thumb`, so never skip it or call the Bot API by hand. Do not upload or publish before approval.
   Cover: every one of the three standing deliverables gets a dedicated cover from
   `investing-bros-brand` (Shorts covers). Pass the Short config to
   `make_cover_title.py --config`: both it and Remotion read the same `cover_title`
   field, so the cover and opening banner cannot drift. Until Amitai says the design is dialed in,
   brand delivers three clearly labeled Codex options A/B/C for each individual Short;
   Amitai picks one. Set the exact approved title in Heebo with `make_cover_title.py`,
   check the selected option with `check_cover.py`, and use it both as `-cover.jpg` and
   as the YouTube custom thumbnail. If Codex is unavailable, report the blocker; a
   legacy `make_cover.py` rebuild does not complete the current standing batch.
7. **Upload to Drive** — every Short's video and its cover/thumbnail go in the `Shorts/` subfolder of the current episode's Drive folder (`investing-bros-show` → Drive tree, Shorts rule; find the episode folder by its `פרק N` prefix; create `Shorts/` inside it if missing). File names follow `investing-bros-show` → Naming:
   - **Cover (`.jpg`) and captions (`.srt`)** — small: the Drive connector's create-file call into the `Shorts/` folder id (JPEG as base64 with `image/jpeg`; `.srt` as text with `text/plain`, conversion to Google Docs **off**).
   - **Phone-friendly copy first:** re-encode every MP4 you hand over or upload with `-c:v libx264 -profile:v main -pix_fmt yuv420p -movflags +faststart -brand mp42 -c:a aac` (iPhone/WhatsApp/Drive preview all play it).
   - **Drive video filename is `.m4v`:** keep the local render as MP4 if convenient, but rename/re-encode the upload copy to `שורט-NN-<נושא>.m4v`. The `.m4v` extension makes Drive type it as `video/x-m4v`, which its player can play; a `.mp4` upload is typed `application/mp4` and is not playable there.
   - **Video (`.m4v`)** — the newer Drive connector takes a file up to **100 MB** (`investing-bros-show` → references/environment.md); `drive.sh put` uses the Drive API and is not bound by that cap. For the ≤10 MB browser path, make the upload copy with `scripts/fit_size.sh short.mp4 "שורט-01-סוויפט.m4v"` (two-pass, under 9.5 MB; a short that already fits is copied as is), then upload it into `Shorts/`. Confirm its Drive MIME type is `video/x-m4v`; never file a Short as `.mp4` / `application/mp4`. If no browser can reach Drive, give Amitai the exact files, names and folder link to drag in, and say so in the hand-back.
   - Check: list `Shorts/` and confirm all three shorts have their `.m4v`, `-cover.jpg`, `.srt` and `youtube-שורט-NN.md`, none empty.

## Approved Shorts format (Amitai's Cybercab Short is the base template)
Reference analysis: [references/style-from-amitai.md](references/style-from-amitai.md). Every template element stays as in Amitai's Short; our additions (explainer panels) are layered on top and never restyle it.

| Element | Spec |
|---|---|
| Opening banner (0–3 s) | the exact shared `cover_title`: two stacked torn-paper strips in the cover style, **cream** on top and **mustard/yellow** below, navy Heebo Black ~96 px, top ≈ y 700, on screen from frame 1, 0.3 s fade-out ending at 3.0 s. Keep it short and punchy; never replace it with a long, number-heavy hook |
| Logo | torn-paper podcast logo top-left (x 56, y 150, 210 px wide), whole Short |
| Name tag | small gold `#F5B71F` tag, black ExtraBold text, top-right (right edge x 1024, y 150); **switches with the speaker** via `tags` |
| Captions | **house kinetic captions since 2026-10-26 (episode 8 short 05, Amitai; reference [youtube.com/shorts/nD0smg5J6Fo](https://www.youtube.com/shorts/nD0smg5J6Fo)):** short phrases that each stay up for their **reading time** (~0.7 s one word, ~1.1 s three; up to 5–6 words when speech is fast), the whole phrase popping in at once; **one big word per phrase** (keyword, else number, else main content word), now 25% smaller than PR #54 at **78–135 px** (**72–98 px** under the CTA), with scaled 3/20/9 px box padding, ~14 px radius and 4/5 px gaps; secondary words ~**64 px**, padding about 2/8/7 px, so big and small stay balanced. The **word being spoken is on a navy box** (gold box, navy text for keywords and numbers) that moves word by word; centred y≈1330 (drops lower under the CTA); always on, also over cards (which lift their content); verbatim. Mixed Hebrew/Latin/numbers must use bidi isolation so `S&P 500`, `ב-S&P` and figures keep their order, and `make_captions.py` keeps multi-token Latin names in one phrase. Built with default `--style punch` and rendered by default (`caption_style: "punch"`) |
| Explainer cards | animated navy torn-paper cards from `investing-bros-remotion` (`inset` by default: most of the frame, a thin frame of the host video around it), **~1 per 20 s** (45 s → 2), outside hook and CTA; captions, logo and name tag stay on top. Brand vector icons — **never emoji** (refused by `make_props.py`). Card title = **only words spoken in that window**; no subtitle that repeats the captions; a value icon only shows a number the host said |
| CTA | "הקישור לפרק המלא בתיאור" on a cream torn strip over the chest + **yellow down arrow**, the last ~3 s of speech |
| End card | **none** (Amitai, 2026-10-25: Shorts best practice). The short ends on the payoff and loops; the CTA strip and its bobbing arrow pointing down to the description stay to the last frame |
| Framing / audio | static close-up, no zoom; 1.15x video + pitch-preserving audio by default; no music/SFX; −14 LUFS, peak < −1 dB; 1080×1920, 24 fps |

### Config schema (read by `investing-bros-remotion` → `make_props.py`)
All times are **output** seconds (after the edit and `--speed` adjustment in `make_base.py`).
```jsonc
{
  "base": "ep3_dc_clean.mp4",                 // clean base in --work (from make_base.py)
  "meta": {"episode": 3, "speaker": "אמיתי רסקין",   // default tag when "tags" is absent
           "source": "episode file + kept/dropped ranges"},
  "cover_title": {"top_line": "CoreWeave", "bottom_line": "בסכנה?"}, // also banner + YouTube title/description line 1
  "tags": [[0.0, 16.49, "אמיתי רסקין"], [16.49, 17.78, "נדב רסקין"]],   // [start, end, name]; switch with speaker
  "cards": [{                                  // explainer cards, ~1 per 20 s (format: investing-bros-remotion)
    "id": "drop", "mode": "inset", "start": 8.99, "end": 14.18,
    "steps": [{"at": 8.99, "visual": "house", "title": "לא קמים בבוקר", "subtitle": "נכנסים לפורטפוליו שלהם"},
              {"at": 10.95, "visual": "drop", "value": 30, "title": "צניחה של 30%", "subtitle": "בבית שלהם"}]
  }],
  "cta_overlay": {"start": 40.4, "end": 43.15, "text": "הקישור לפרק המלא בתיאור"},
  "captions": [{"start": 0.0, "end": 1.6, "text": "…verbatim…", "highlight": ["keyword"]}]
}
```
Icons and card modes: `investing-bros-remotion` → references/cards-and-icons.md. Older configs with `hyperframes` still convert. Captions come from `make_captions.py` (passed to `make_props.py --captions`); `cta_overlay` runs to the end of the video.
Legacy helpers (older exports only): `build_amitai_short.py` (its own icons in `VIS`), `strips.py`, `mg.py`, `v5_gfx.py` / `end_gfx.py`, example `references/configs/example-ep3-datacenters.json`.

## Legacy renderer and helper scripts (from episode 7)
Kept for helpers (cut snapping, transcription, alignment, checks, Drive, Telegram). Their full-bleed look (zooms 100/112 %, gold active word, logo-only end card) is **superseded** by the approved format above.
The deployed **full-screen renderer** puts the speaking host in the 9:16 frame, captions 2–3 words at a time with the spoken word in legacy gold `#F5B71F`, punch-in zooms on new ideas, a hook title for the first ~2.7 s, the logo top-left, and a darkened end card. The split-frame `build_short.py` render stays available. These are implementation notes; `investing-bros-brand` owns new visual specifications, and migration requires a reviewed sample.

Episode 7 (video producer), on top of that look:
- **Historical episode 7 batch: 5 shorts**, **1080×1920**. This is a legacy record, not the current count; new episodes always deliver exactly 3. Fast cuts, no silences. Zooms alternate **100% / 112%**. Logo end card.
- A complex idea can use a motion animation ([references/hyperframes.md](references/hyperframes.md)). Its existing navy/gold/white implementation remains until a reviewed brand migration.
- Captions are Heebo Black, active word in gold `#F5B71F`. The scripts render Hebrew with libass (Encoding −1). libass can reverse RTL word order; the video producer worked around that with PIL + raqm. If a script's captions come out in the wrong order, stop and propose a script change — don't ship a one-off renderer (working rules in `investing-bros-show`).

| Step | Script | Notes |
|---|---|---|
| Get the raw video | `drive.sh get FILE_ID DIR` | rclone remote `show` signed in as the bot account; until that exists, ask Amitai to copy the file into Downloads |
| Snap cuts to pauses | `find_cuts.py WINDOW.wav --offset T0 --at t1 t2…` | flags cuts with no real pause |
| Word timings for the picked windows only | `transcribe_clip.py WINDOW.wav --offset T0 --from a --to b --model small.pt` | never the whole episode; install notes in `investing-bros-show` → references/environment.md |
| Time the proofread captions word by word | `align_words.py short.json words.json -o aligned.json` | `cards` stay the proofread text |
| Centre the face, place captions + hook | `face_crop.py raw.mp4 --at t1 t2 t3` (side-by-side) or `face_crop.py source.mp4 --at … --crop x,y,w,h` (one-host frame) | prints `crop_x` and, with OpenCV, `caption_y` / `hook_y` suggestions; confirm on one frame — hands in shot pull it off (episode 7: suggested L=64, the face needed ~100) |
| Render the deployed video style | `build_fullbleed.py short.json` then `bash NAME_fb.sh` | `--speed` defaults to the house 1.15 and `1.0` disables it; also writes speed-synced `NAME.srt`, `NAME_hook.png` (the paper-strip hook) and `NAME_layout.json`; `caption_y` / `hook_y` / `hook_style` set placement and hook look; pieces may open on a later line; `base` + `shots` cut to the other host for reactions; `tags` = name tag; `sources`/`crop` take each host's own high-res Riverside track. Worked example: [references/ep7-asteroid-fullbleed.json](references/ep7-asteroid-fullbleed.json). Its output is also the input for a HyperFrames overlay |
| Check the export | `check_short.py NAME.mp4 --config short.json --youtube-notes youtube-שורט-NN.md [--layout NAME_layout.json]` | hard 45 s cap, shared cover/banner/YouTube title, −14 LUFS, peak, the first second, no dead air at the end, layout bounds, and a frame strip you must look at |
| Legacy video-frame cover (explicit reuse only) | `make_cover.py --style fullbleed --crop x,y,w,h --logo logo.png …` | same crop as the short; new cover artwork comes from `investing-bros-brand` |
| Upload to Drive | `drive.sh put FILE SHORTS_FOLDER_ID` | |
| Send to Telegram for approval (step 6) | `send_telegram.py video short.mp4 --caption … --thumb cover.jpg` | token/chat ID from `telegram.env`; `delete ID` removes the bot's own post |

**Link every short to the full episode** (this is what turns Short views into episode views):
- **Cover end card (`"endcard_style": "cover"`)**: the end card in the cover-art look: navy paper over the video, the torn-paper show logo, a cream `פרק N` pill, the episode title (from `youtube/title.txt` minus the `פרק N - ` prefix, `|` for the 2-line break) in cream, and `הקישור לפרק המלא בתיאור` in mustard with a bobbing mustard arrow under it; `endcard` = `[title, "פרק N", link line]`. Pair it with one callout `{"before_endcard": 4.0, ...}`: the bobbing link callout appears 4 s before the card and crossfades into it (no mid-short callout). When the payoff runs to the last frame, start the card at the payoff's last line (`endcard_at`, source time) and set `"endcard_captions": true` so that line's captions keep burning over the card. The card stays inside y 150–1528 (`check_short.py --layout` fails otherwise).
- **Default since episode 1 (approved v5): `"endcard_style": "cover"` with one `{"before_endcard": 4.0}` callout**, as above. The end card says the link is **in the description** (`הקישור לפרק המלא בתיאור`) — that is where it is on a Short. The older text card (`["בפרק המלא: …", "[אחים להשקעות · פרק N]", …]`, no arrow glyph) stays available with `endcard_style: "text"`; never a generic "לפרק המלא" (the renderers warn).
- **Uploading a Short to YouTube:** prefer the YouTube Data API (`investing-bros-episode-upload` → scripts/yt_upload.py, references/youtube-api.md) when the box has `~/.config/youtube-uploader/` credentials: it uploads Private with the title, description, tags and the `-cover.jpg` as thumbnail, without tying up the browser. Studio in the browser is the fallback. Related video, `.srt` and pinned comment are still set in Studio, and going Public needs Amitai's OK.
- **Upload an episode's Shorts only after the full episode is live on YouTube**, so each description carries the real episode link at the Short's moment (`?t=<start seconds>`) and the episode's Spotify link, copied from the full episode's YouTube description (missing there → ask Nadav). Audience: **No, it's not made for kids**.
- Set the **Related video** in YouTube Studio to the full episode on every Short.
- **No custom cover set → the Short stays Private.** Nothing goes Public without Nadav's approval (and Amitai's OK).
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
   python3 scripts/build_short.py short1.json  # house speed 1.15; writes speed-synced .ass / .srt / .sh
   bash short1.sh                                 # run where raw.mp4, frame_vertical.png and fonts/ are
   ```
   - **The first second:** frame 1 is the host mid-sentence with the hook on screen. No fade-in, no logo intro, no breath before the first word. The hook is an open question the short answers at the end.
   - **Framing:** close-up of whoever is talking (their half, 1080 wide); cut to the other host for his lines or a real reaction. Not the whole frame over blur. **Zoom speaker-view recordings** (episode 1: 1280×720, one host full frame, Zoom chooses who is on screen): set `"base": "L"` and `"crop": {"L": [x, 0, 405, 720]}` (9:16 of the full height), and check who is on screen at every piece; drop stretches where Zoom shows the other host while this one talks.
   - **Headline (legacy config key `hook`; new work uses `cover_title`):** a faithful paraphrase of what is said in the clip — never a claim the hosts didn't make, never investment promises. **As short as possible while still landing:** one idea, ideally ≤ 6 words, two lines; drop secondary details. The cover, opening banner, YouTube title and first description line all use that one title.
   - **The hook must not look like a caption.** `build_fullbleed.py` draws it by default (`"hook_style": "strips"`) as Financial Journal torn-paper strips: line 1 on cream `#F5EBD5`, line 2 on mustard `#D8A52E`, navy `#09243B` Heebo Black, a soft paper shadow (spec in `investing-bros-brand` → layouts). Captions stay white with the current word gold. `"hook_style": "legacy"` (white/gold ASS hook) is only for rebuilding old exports.
   - **Captions:** proofread against the audio, max two lines, ~24 characters a line, key terms in `[…]` (that markup currently renders as legacy gold `#F5B71F`). Words you can't make out: leave them out of the caption (don't guess) and list them in the hand-back. An English phrase inside a Hebrew caption is one token joined with a no-break space (`מ-day one`), or libass shows its words in reverse.
   - **Placement — put captions and hook where they make most sense**, inside the bounds (centre y on the 1920-px frame, constants in `brand.py`). **Brief hook → centre of the frame**: the paper-strip hook is on screen only ~2.7 s, so it sits horizontally centred around `hook_y` **960** (allowed 300–1000); it may cover the face briefly, but it keeps at least `HOOK_GAP` (40 px) clear below the logo's bottom edge (y 277) and above the caption line. Captions `caption_y` **1100–1470** (clear of the bottom ~400 px of platform UI; default 1290) go just under the chin. `face_crop.py … [--crop x,y,w,h]` suggests both from the face box (OpenCV): captions under the chin, the hook in the centre unless it would run into those captions; it warns when a close-up is too big for the captions to clear. Confirm on a frame. `build_fullbleed.py` refuses a hook block that breaks the gaps, and `check_short.py` fails a render whose `NAME_layout.json` is outside the bounds or the gaps. A close-up whose chin sits below ~1410 can't be fully cleared: use `caption_y` 1470, turn punch-in zooms off (they push the face down), and say so in the hand-back.
   - **Audio:** if one host is quieter, give his pieces a gain (`[start, end, +dB]`) so both measure within ~2 dB; the render normalises to −14 LUFS.
   For a quick whole-frame clip or an audio-only audiogram, `scripts/clip_captions.py` + `scripts/make_clip.sh` still work. Vertical output defaults to the house `--speed 1.15`; square promo output stays at 1.0x unless explicitly overridden.

   **Explainer moment? Render it with HyperFrames instead.** When the clip explains something a card can show — a number, "not X but Y", a list, a before/after — follow [references/hyperframes.md](references/hyperframes.md) for this step: the same pieces, shots and captions, plus animated cards (count-up, strike-through, building list) in the band under the video. It looks more produced and gets Hebrew/English text right natively, at ~6× the render time. Punchlines and stories stay on the plain render.
5. **Check the export.** For each short:
   - a strip of 6–8 frames across the clip: captions right-to-left (punctuation at the left end, English words in place), not over faces, inside the safe zone; the right host on screen
   - `ffmpeg -i short.mp4 -af ebur128=peak=true -f null -` → about −14 LUFS, peak below −1 dB; per-host levels close
   - duration **after playback speed is applied**: 20–45 s; 45.0 s is a hard maximum, with no exception. Listen to every cut — no clipped words, no clicks
6. **Make a cover for each short** — the image Reels / Shorts / TikTok show before play and in the profile grid. It comes from `investing-bros-brand` (Shorts covers): give it the hook, the episode number and the Short's file name, and use the result both as `-cover.jpg` and as the YouTube custom thumbnail. Layout, font and checks live there only.
   Until Amitai says the design is dialed in, brand returns three clearly labeled Codex
   options A/B/C for each individual Short; show all three and use only Amitai's pick.
   Rebuilding an older Short in the legacy video-frame style is the only use of `make_cover.py`:
   ```bash
   python3 scripts/make_cover.py --source raw.mp4 --at <source time of a good frame> --side L \
     --headline "סוויפט היא בכלל|[לא מערכת תשלומים]" --episode N \
     --frame frame_vertical.png --fonts fonts/ "שורט-01-סוויפט-cover.jpg"
   ```
   The current standing batch needs all three covers from that brand flow (Codex art, Heebo title); a legacy `make_cover.py` rebuild does not complete a new episode's standing batch.

## Titles and descriptions (YouTube)
- **Title = cover title exactly.** Join `cover_title.top_line` and `bottom_line` with one space; do not append an emoji, episode label, English translation, `#shorts`, another hashtag or `|`. A necessary Latin name such as `CoreWeave` or `S&P 500` stays exactly as approved on the cover.
- **Description, in this order** (matches the episode order in PR #20: intro, disclaimer, then links, before chapters/hashtags):
  1. first line = the cover title exactly; after it, a concise hook/question grounded in what the hosts actually said;
     include a disclosure or holdings statement **only if it was stated in the episode**, and preserve its meaning. Never add a disclosure, holding, number or claim from assumptions or outside research;
  2. `אין כאן המלצת השקעה. רק שיחה.`;
  3. blank line, `🎧 לפרק המלא ביוטיוב: <episode link>?t=<seconds>` and `האזינו בספוטיפיי: <Spotify episode link>`;
  4. blank line, a subscribe line, then hashtags (Hebrew and English allowed here).
- **Publish** (only after Amitai's explicit OK, and Nadav's approval of the cut unless Amitai waives it): after the full episode is live, upload the phone-friendly MP4, set the custom cover, Related video and `.srt`; once the Short is Public, post and pin the full-episode comment from `youtube-שורט-NN.md`, then update that file with the status and Shorts URL.

## Mid-form highlights
Optional 5–10 min YouTube videos, each **one continuous standalone stretch** of the episode on one engaging subject (episode 7: "למה זהב?" 11:57–19:11, about 7 min). Not a montage. Elsewhere these are called highlights or clips.
- Segment videos (~7 min, max 10, one sub-question; exactly two per episode, with the required deep dive as segment 01) go through `investing-bros-segment-video`, not mid-form. Mid-form is for other stretches. Pick 1–3 mid-form highlights with Amitai.
- Start and end on sentence boundaries (`find_cuts.py`). Leave out any part that is being re-recorded.
- **Title** with a few English keywords. **Description:** hook, link to the full episode, the disclaimer. Run `check_copy.py` from `investing-bros-title-description` on the description (`--description`).
- File as `mid-form/מיד-פורם-NN-<נושא>.mp4` with its title and description in `מיד-פורם-NN-<נושא>.txt`. Share a review copy compressed under 100 MB (transfer caps in `investing-bros-show` → references/environment.md). Nadav approves it before upload.

## Done when
- `Shorts/` has **exactly three** shorts, each with a non-empty playable `.m4v` (`video/x-m4v`), Amitai's selected
  Codex-made `-cover.jpg` from three labeled options, `.srt` and
  `youtube-שורט-NN.md`.
- All three were selected through the picks flow, rendered and passed `check_short.py`, sent to Telegram with their covers and approved.
- All three were uploaded only after the full episode went live. Each has its custom cover, `.srt`, full-episode timestamp link and Spotify episode link in the description, Related video set to the full episode, its full-episode comment pinned once Public, and its URL/status recorded in `youtube-שורט-NN.md`.
- `mid-form/` has each highlight that was asked for, with its `.txt`.

## Hand back
Send Amitai the `Shorts/` folder link and, for shorts 01–03: where each is in the episode, its scores, final length, shared cover/banner/YouTube title, Telegram approval, Drive `.m4v` and YouTube URLs, episode links, any cuts made inside it, and any words you couldn't verify. If any file still needs his manual upload, list it first.

## Never
- Make a Short Public without its custom cover set, or without Nadav's approval.
- Post anywhere public unless Amitai asks in chat for that post (the Telegram approval send in step 6 is the exception), and only to a destination listed in `investing-bros-show`.
- Put words on screen the hosts didn't say, or captions you haven't proofread.
- Splice pieces so a sentence means something the host didn't mean, or cut a caveat.
- Crop a Short's picture from the side-by-side export; use each host's own Riverside track.
- Use an ASS style `Encoding` other than `-1` — any other value forces left-to-right and Hebrew punctuation lands on the wrong side.
- Add music, SFX or stock footage.
- Put emoji or invented numbers on a panel, or guess an unclear phrase in a caption — cut it instead.
- Reuse a burned-in Short as the source — cut fresh from the final episode file.
- Use a figure you haven't verified as the hook headline or cover headline — keep it in the captions as said, and flag it in the hand-back.
- Hand back a short that isn't in Drive with its cover — or a cover whose headline says more than the clip does.
- Write your own render, caption, download or upload code, or work around a missing feature without saying so — follow the working rules in `investing-bros-show`.
