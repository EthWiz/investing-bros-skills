---
name: investing-bros-shorts
description: >-
  Make exactly three branded vertical Shorts from every Investing Bros / אחים
  להשקעות episode, run by the Producer: picks, cuts, render with
  investing-bros-remotion, QA, Codex covers, Drive, Private upload for the
  approval round and links; plus optional 5-10 min mid-form highlights. Use
  for "shorts", "clips", "reels", "רילס", "שורטס", "קליפים", "highlights",
  "mid-form", "מיד-פורם".
---
# Investing Bros shorts

Load `investing-bros-show` first — show facts, deployed asset paths, loudness and recording layout live there.

Load `investing-bros-brand` for visual specifications and request graphic assets from it.
It owns cover art, lower thirds and other visual assets; this skill owns video assembly.
Existing renderer defaults remain legacy implementations until a reviewed migration.
Do not create competing brand rules or silently change approved artwork.

## When to use
After the audio edit (`investing-bros-post-production`) for episode N: make **exactly three shorts per episode** through the complete flow below; mid-form highlights remain optional when Amitai wants them. Every short ends in Drive with its cover and is uploaded **Private** for the approval round (steps 6–7 and Titles and descriptions); going Public waits for the full episode to be live and for the episode owner's publish OK.

**The episode's Producer runs this skill directly** (`investing-bros-show` → Ownership and contact). There is **no separate Shorts bot** (the former "Investing Bro Shorts" / periphery-marketing helper is retired as of 2026-11-05): do **not** `SendToAgent` to another Grok bot for Shorts. The Producer owns Shorts end to end — picks, render, covers, Private upload, Related video, and the approval-round links — and is the only voice to Amitai about them.

## Inputs
From the episode's `extras/` folder:
- `segments.json` — the transcript
- the raw master — `.mp4` if the recording has video, otherwise `.m4a` (timeline and audio)
- **each host's own Riverside video track** for the picture — the **canonical camera
  track as-is**, never the combined / side-by-side Riverside export, and never a zoomed
  or re-cropped half of that export: Riverside recording share link → Tracks → <host> →
  download → **Aligned video** (`investing-bros-show` → Recording layout). **If either
  host's Aligned video track is missing: stop.** Ask the episode owner for the recording's share
  link (or to download each host's Aligned video from Tracks). Do **not** fall
  back to cropping, zooming or upscaling the side-by-side / combined recording, and do
  **not** pass `--allow-side-by-side` without the episode owner's explicit OK in chat.
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
   - Listen to the top picks, then give the Producer (for the episode owner) the table it prints (5 candidates, at least 2
     from the deep dive). The production batch is **exactly 3**: wait for the owner's three picks
     unless they said to just make them, in which case take the top three. The episode owner
     approves each cut in the approval round (`investing-bros-show` → Episode owner).
   - For each pick, plan the **opening** (the strongest line first, moved to the front if
     it comes later), the **last line** (cut right after the payoff; the short ends there and loops) and the **CTA**
     (what the full episode adds on this topic).
   - Plan a short two-line **cover title** at the same time. It is the one shared title
     used by the cover, opening banner, YouTube title and first description line. It may
     contain a necessary Latin company/index name; do not add figures or claims absent
     from the clip.
   Skip crosstalk and anything that sounds like a buy/sell call out of context. Flag on-air mistakes instead of clipping them.
2. **Find exact cut points.** Whisper segment times are only approximate. For every in/out point, look at the audio energy (20 ms frames) for the pause between words and cut inside it; re-transcribe a 1–3 s window around the point if unsure (whisper drops the last word of a window — give it ~1 s of tail). Never cut mid-word. Inside a clip you may drop a filler stretch, dead air or a phrase you can't make out — **only** if the sentence still says the same thing. Never drop a caveat or disclaimer to make a line punchier.
3. **Cut fresh from the final episode file.** Always start from the published/final episode master, never from an earlier Short or a burned-in render. Edit the kept pieces with `scripts/make_base.py`: copy it, set `SRC` (the master: timeline and audio), `TRACKS` (each host's Aligned video track) and the `K` list of `(audio_start, audio_end, video_delay, crop, track)` with the speaking host's track and a centred 9:16 crop in that track's pixels, then run `python3 make_base.py --output <name>_clean.mp4` (house speed 1.15x). It crops to a **static** head-and-shoulders close-up (no zooms, no jump cuts except removing silence), scales to 1080×1920 at 24 fps, places the logo at x 56 y 150 (210 px wide), and applies highpass + gentle compressor + two-pass `loudnorm` to **−14 LUFS**, true peak ≤ −1.5 dB. It writes the named clean MP4 (no captions/graphics) and `timemap.json`. No music, no SFX, no b-roll. It syncs each track to the master from the audio and prints the offset, and it refuses a side-by-side picture (episode 8: cropping one half came out tight, soft and off-centre). **Never pass `--allow-side-by-side` without the episode owner's explicit OK in chat**; when they OK it, list that OK in the hand-back. Prefer stopping for the missing canonical tracks over forcing a side-by-side crop.
   **House playback speed is 1.15x** (Amitai, 2026-10-26, on episode 8 short 05 v6: 1.25x was too fast to read the captions; 1.25x had replaced 1.5x on 2026-10-23). The scripts default to `--speed 1.15` (`make_base.py`, `build_short.py`, `make_clip.sh` vertical, `make_captions.py`; a test keeps them equal); pass `--speed 1.0` only to disable it. They speed video with `setpts` and audio with `atempo`, which preserves natural voice pitch. Source cut points stay on the raw timeline; `timemap.json` and every caption/overlay time are on the shortened output timeline.
4. **Captions = exactly what was said, timed word by word.** Transcribe every kept piece word by word (`transcribe_clip.py`, then listen). Captions must match the audio verbatim. The proofread text comes from the Riverside transcript in the episode folder (the whisper `segments.json` is only for timing; its Hebrew is unreliable). Build the captions with `investing-bros-remotion` → `make_captions.py` (proofread words + whisper word timings + `timemap.json` + the window WAV). If a phrase is unclear after re-transcribing and listening, **cut it out of the edit** (step 3) rather than guess — record what was dropped in `meta.source`. Format: see Captions in the table below.
5. **Write the config and render with Remotion** — one JSON per Short (schema below), then follow `investing-bros-remotion` (the show's animation framework, decided 2026-10-25): `make_props.py` checks the config and writes the props, `render_short.py --stills` gives a QA sheet, `render_short.py` renders `NAME.mp4` + `NAME_layout.json` over the clean base. Explainer cards are its `cards` (modes `inset` default, `full`, `card`). `v5_gfx.py` + `build_amitai_short.py` are legacy: only for rebuilding older exports.
6. **One QA pass, then Telegram for approval.** Run `check_short.py NAME.mp4 --config short.json --youtube-notes youtube-שורט-NN.md > "$EP/extras/check-short-NN.log"` (the Producer's `shortNN render` evidence) and inspect its 8-frame strip on the **final speed-adjusted render**. The check enforces the shared title in YouTube metadata and the 15–45 s duration; inspect that the opening banner exactly matches `cover_title`, logo is on every frame, name tag matches the speaker, mixed Hebrew/Latin/numbers read in the right order, captions are verbatim, panels hide neither captions nor logo, and the CTA + arrow runs to the last frame (no end card). Audio is −14 LUFS / peak < −1 dB. **45.0 s is a hard cap**: at 1.15x, cut tighter until the check passes; there is no longer an over-length exception. Duration is always checked after speed-up, never against source ranges. Fix what fails once, then the Short goes for the episode owner's approval together with the episode's other assets, in one Telegram message (`investing-bros-episode-upload` → approval round; `send_telegram.py text`), not one post per Short. Send the Short's video file itself only when the episode owner asks (`send_telegram.py video short.mp4 --caption … --thumb cover.jpg`, destination from `investing-bros-show`). A vertical Short needs `width=1080`, `height=1920`, `supports_streaming=true` and a vertical `thumbnail` in `sendVideo`, or Telegram shows it landscape; the script sends the first three (from ffprobe) and the thumbnail only with `--thumb`, so never skip it or call the Bot API by hand. The Private upload is what goes in the approval round; never set a Short Public before the approval and the publish OK.
   Cover: every one of the three standing deliverables gets a dedicated cover from
   `investing-bros-brand` → `references/shorts-covers.md`. **The face format is the
   current standard** (Amitai, episode 10: covers without the hosts' faces were the old
   format): a real frame of the host who speaks in the Short, picked from the verified
   face grids and passed to Codex as an `-i` input, kept photographic. **Default (Amitai's
   pick, episode 10): the one-pass Codex cover** — Codex on Amitai's Mac draws art, Hebrew
   title, pill and logo in one pass with the real face frame via `-i`, prompt fed on stdin
   (`-i` swallows a trailing prompt argument); upscale its ~941×1672 PNG to 1080×1920 with
   ffmpeg (lanczos) straight to `שורט-NN-<נושא>-cover.jpg`. Only if the one-pass Hebrew
   still does not match `cover_title` after one regenerate, fall back to text-free art
   typeset with `make_cover_title.py --config short.json` (same `cover_title` as the
   opening banner, so they cannot drift). Until Amitai says the design is dialed in, brand delivers three
   clearly labeled options A/B/C per Short and the episode owner picks one. Check the pick with
   `check_cover.py --kind shorts-vertical --config short.json` and use it both as
   `-cover.jpg` and as the YouTube custom thumbnail. No Pillow compositing on the box: if
   Codex is unavailable, report the blocker to the Producer; a legacy `make_cover.py`
   rebuild does not complete the current standing batch.
7. **Upload to Drive** — every Short's video and its cover/thumbnail go in the `Shorts/` subfolder of the current episode's Drive folder (`investing-bros-show` → Drive tree, Shorts rule; find the episode folder by its `פרק N` prefix; create `Shorts/` inside it if missing). File names follow `investing-bros-show` → Naming:
   - **Cover (`.jpg`) and captions (`.srt`)** — small: the Drive connector's create-file call into the `Shorts/` folder id (JPEG as base64 with `image/jpeg`; `.srt` as text with `text/plain`, conversion to Google Docs **off**).
   - **Phone-friendly copy first:** re-encode every MP4 you hand over or upload with `-c:v libx264 -profile:v main -pix_fmt yuv420p -movflags +faststart -brand mp42 -c:a aac` (iPhone/WhatsApp/Drive preview all play it).
   - **Drive video filename is `.m4v`:** keep the local render as MP4 if convenient, but rename/re-encode the upload copy to `שורט-NN-<נושא>.m4v`. The `.m4v` extension makes Drive type it as `video/x-m4v`, which its player can play; a `.mp4` upload is typed `application/mp4` and is not playable there.
   - **Video (`.m4v`)** — the newer Drive connector takes a file up to **100 MB** (`investing-bros-show` → references/environment.md); `drive.sh put` uses the Drive API and is not bound by that cap. For the ≤10 MB browser path, make the upload copy with `scripts/fit_size.sh short.mp4 "שורט-01-סוויפט.m4v"` (two-pass, under 9.5 MB; a short that already fits is copied as is), then upload it into `Shorts/`. Confirm its Drive MIME type is `video/x-m4v`; never file a Short as `.mp4` / `application/mp4`. If no browser can reach Drive, give the episode owner the exact files, names and folder link to drag in, and say so in the hand-back.
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
Legacy renderers, looks, end cards and helpers for rebuilding older exports: [references/legacy-renderers.md](references/legacy-renderers.md).

## Helper scripts

| Step | Script | Notes |
|---|---|---|
| Get the raw video | `drive.sh get FILE_ID DIR` | rclone remote `show` signed in as the bot account; until that exists, ask Amitai to copy the file into Downloads |
| Snap cuts to pauses | `find_cuts.py WINDOW.wav --offset T0 --at t1 t2…` | flags cuts with no real pause |
| Word timings for the picked windows only | `transcribe_clip.py WINDOW.wav --offset T0 --from a --to b --model small.pt` | never the whole episode; install notes in `investing-bros-show` → references/environment.md |
| Time the proofread captions word by word | `align_words.py short.json words.json -o aligned.json` | `cards` stay the proofread text |
| Centre the face, place captions + hook | `face_crop.py raw.mp4 --at t1 t2 t3` (side-by-side) or `face_crop.py source.mp4 --at … --crop x,y,w,h` (one-host frame) | prints `crop_x` and, with OpenCV, `caption_y` / `hook_y` suggestions; confirm on one frame — hands in shot pull it off (episode 7: suggested L=64, the face needed ~100) |
| Check the export | `check_short.py NAME.mp4 --config short.json --youtube-notes youtube-שורט-NN.md [--layout NAME_layout.json]` | hard 45 s cap, shared cover/banner/YouTube title, −14 LUFS, peak, the first second, no dead air at the end, layout bounds, and a frame strip you must look at |
| Upload to Drive | `drive.sh put FILE SHORTS_FOLDER_ID` | |
| Send to Telegram for approval (step 6) | `send_telegram.py text approval.txt` (the one approval message); `send_telegram.py video short.mp4 --caption … --thumb cover.jpg` when Amitai asks for the file | token/chat ID from `telegram.env`; `delete ID` removes the bot's own post |

## Links to the full episode and the YouTube upload
This is what turns Short views into episode views:
- **End cards are legacy only.** New Shorts have no end card (the format table above; Amitai, 2026-10-25). The legacy cover end card ([references/legacy-renderers.md](references/legacy-renderers.md)) and the older text card (`endcard_style: "text"`) stay in the legacy renderers only for rebuilding older exports; never a generic "לפרק המלא" (the renderers warn).
- **Uploading a Short to YouTube:** prefer the YouTube Data API (`investing-bros-episode-upload` → scripts/yt_upload.py, references/youtube-api.md) when the box has `~/.config/youtube-uploader/` credentials: it uploads **Private by default** with the title, description, tags and the `-cover.jpg` as thumbnail, without tying up the browser. Studio in the browser is the fallback. **Related video** (to the full episode) and `.srt` are still set in Studio (no pinned comment), and going Public needs the episode owner's OK.
- **Review uploads are Private by default** (Amitai, 2026-11-05): upload each Short **Private** once its cover is approved so its link can go in the single Telegram approval-round message with the rest of the episode's assets. Keep the description's full-episode `?t=` and Spotify links pointed at the Private (or later Public) episode URL. Going **Public** still waits until the full episode is live and the episode owner OKs publish (`investing-bros-publish`). Audience: **No, it's not made for kids**.
- **Before any Studio action on a Short** (Related video, `.srt`): open `https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw/videos/short`, confirm in the avatar menu that **אחים להשקעות** is active (not the personal Grok Bot channel), and click into the Short from that list. A direct edit link loads as Grok Bot. Non-waivable; check again on every edit page.
- **No pinned comment** (Amitai, 2026-11-01): the full-episode link lives in the description and the Related video.
- Set the **Related video** in YouTube Studio to the full episode on every Short. **Empty Related video picker: check the active channel first.** "No matching results" for the episode URL, ID and title is not a permissions problem. It means Studio is acting as Grok Bot. Go back to `https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw/videos/short`, confirm אחים להשקעות in the avatar menu, click into the Short and try again. Only if the picker is still empty with אחים להשקעות active: keep the Short Private and ask Amitai or Nadav to set Related video from the owner/brand account. Name the Short (title + ID) and the full episode to pick (title + `https://youtu.be/<EPISODE_ID>`), with the path Studio → אחים להשקעות → Content → Shorts → the Short. Then reopen it yourself (from the list, with אחים להשקעות active) and check the field before ticking.  **Related video is a hard rule:** set it to the full episode in Studio (Shorts → Details → Related video), then reopen the edit page and confirm the field shows the episode. A link in the description does NOT count. If it can't be set (e.g. "No matching results"), the Short stays Private and the failure is reported; never publish a Short with only a description link. The publish gate is `investing-bros-publish`.
- **No custom cover set → the Short stays Private.** Nothing goes Public without the episode owner's approval and publish OK.
- Hand back a `youtube-שורט-NN.md` next to each short with: the **Related video** to set in YouTube Studio (the full episode — that is the tappable link on the Short), title, description with the episode link at the short's timestamp (`&t=<seconds>`), and the `.srt` to upload. Worked example: [references/youtube-short-example.md](references/youtube-short-example.md).

## Titles and descriptions (YouTube)
- **Title = cover title exactly.** Join `cover_title.top_line` and `bottom_line` with one space; do not append an emoji, episode label, English translation, `#shorts`, another hashtag or `|`. A necessary Latin name such as `CoreWeave` or `S&P 500` stays exactly as approved on the cover.
- **Description, in this order** (matches the episode order in PR #20: intro, disclaimer, then links, before chapters/hashtags):
  1. first line = the cover title exactly; after it, a concise hook/question grounded in what the hosts actually said;
     include a disclosure or holdings statement **only if it was stated in the episode**, and preserve its meaning. Never add a disclosure, holding, number or claim from assumptions or outside research;
  2. `אין כאן המלצת השקעה. רק שיחה.`;
  3. blank line, `🎧 לפרק המלא ביוטיוב: <episode link>?t=<seconds>` and `האזינו בספוטיפיי: <Spotify episode link>`;
  4. blank line, a subscribe line, then hashtags (Hebrew and English allowed here).
- **Publish** (only after the episode owner's publish OK and their approval of the cut): the phone-friendly MP4 is already up as **Private** with its custom cover for the approval round; before Public, confirm **Related video** is the full episode (verified by reopening the edit page; if it can't be set, the Short stays Private) and `.srt` is attached. Once the Short is Public, update `youtube-שורט-NN.md` with the status and Shorts URL. Covers always follow `investing-bros-brand` → `references/shorts-covers.md` (face format).

## Mid-form highlights
Optional 5–10 min YouTube videos, each **one continuous standalone stretch** of the episode on one engaging subject (episode 7: "למה זהב?" 11:57–19:11, about 7 min). Not a montage. Elsewhere these are called highlights or clips.
- Segment videos (~7 min, max 10, one sub-question; exactly two per episode, with the required deep dive as segment 01) go through `investing-bros-segment-video`, not mid-form. Mid-form is for other stretches. Pick 1–3 mid-form highlights with the episode owner.
- Start and end on sentence boundaries (`find_cuts.py`). Leave out any part that is being re-recorded.
- **Title** with a few English keywords. **Description:** hook, link to the full episode, the disclaimer. Run `check_copy.py` from `investing-bros-title-description` on the description (`--description`).
- File as `mid-form/מיד-פורם-NN-<נושא>.mp4` with its title and description in `מיד-פורם-NN-<נושא>.txt`. Share a review copy compressed under 100 MB (transfer caps in `investing-bros-show` → references/environment.md). The episode owner approves it before upload.

## Done when
- `Shorts/` has **exactly three** shorts, each with a non-empty playable `.m4v` (`video/x-m4v`), the episode owner's selected
  Codex-made face-format `-cover.jpg` from three labeled options (passed `check_cover.py`), `.srt` and
  `youtube-שורט-NN.md`.
- All three were selected through the picks flow, rendered and passed `check_short.py`, sent to Telegram with their covers and approved.
- All three were uploaded **Private** for the approval round (and only go Public after the full episode is live and the episode owner OKs publish). Each has its custom cover (brand face-format), `.srt`, full-episode timestamp link and Spotify episode link in the description, **Related video** set to the full episode and verified by reopening the edit page (not just a description link), and its URL/status recorded in `youtube-שורט-NN.md`.
- `mid-form/` has each highlight that was asked for, with its `.txt`.

## Hand back
As the Producer (this is not a separate Shorts-bot hand-back): keep the `Shorts/` folder link and, for shorts 01–03: where each is in the episode, its scores, final length, shared cover/banner/YouTube title, Telegram approval-round inclusion, Drive `.m4v` and YouTube URLs (Private review IDs), episode links, any cuts made inside it, and any words you couldn't verify. If any file still needs a host's manual upload, list it first. List any superseded Private upload you deleted (title, video ID). Batch anything that needs the episode owner into the one review message (`investing-bros-episode-upload` → approval round).

## Never
- Make a Short Public without its custom cover set, or without the episode owner's approval.
- Make a Short Public whose Related video isn't the full episode, verified by reopening its edit page. A link in the description does not count.
- Post anywhere public unless asked in chat for that post (the pipeline's Telegram messages are the exception), and only to a destination listed in `investing-bros-show`.
- Put words on screen the hosts didn't say, or captions you haven't proofread.
- Splice pieces so a sentence means something the host didn't mean, or cut a caveat.
- Crop, zoom or upscale a Short's picture from the combined / side-by-side Riverside export; use each host's **canonical camera track as-is**. Never pass `--allow-side-by-side` without the episode owner's OK.
- Keep going when a host's Aligned video track is missing — stop and ask the episode owner for the Riverside share link (or the tracks) instead.
- Hand Shorts off to a separate Grok bot (`SendToAgent`, "Investing Bro Shorts", periphery-marketing helper). The Producer runs this skill directly.
- Use an ASS style `Encoding` other than `-1` — any other value forces left-to-right and Hebrew punctuation lands on the wrong side.
- Add music, SFX or stock footage.
- Put emoji or invented numbers on a panel, or guess an unclear phrase in a caption — cut it instead.
- Reuse a burned-in Short as the source — cut fresh from the final episode file.
- Use a figure you haven't verified as the hook headline or cover headline — keep it in the captions as said, and flag it in the hand-back.
- Hand back a short that isn't in Drive with its cover — or a cover whose headline says more than the clip does.
- Ping the episode owner with status updates instead of one batched review; contact them only for reviews and approvals (`investing-bros-show` → Ownership and contact).
- Make a new Short cover in the old faceless format, or composite one with Pillow on the box.
- Write your own render, caption, download or upload code, or work around a missing feature without saying so — follow the working rules in `investing-bros-show`.