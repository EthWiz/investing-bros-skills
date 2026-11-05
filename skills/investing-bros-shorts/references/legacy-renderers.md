# Legacy Shorts renderers (older exports only)

Moved from the skill's SKILL.md (no rule changed). New Shorts use the approved format and
`investing-bros-remotion`; these renderers and looks are only for rebuilding older exports.

Legacy helpers (older exports only): `build_amitai_short.py` (its own icons in `VIS`), `strips.py`, `mg.py`, `v5_gfx.py` / `end_gfx.py`, example `references/configs/example-ep3-datacenters.json`.

## Legacy look (from episode 7)
Kept for helpers (cut snapping, transcription, alignment, checks, Drive, Telegram). Their full-bleed look (zooms 100/112 %, gold active word, logo-only end card) is **superseded** by the approved format above.
The deployed **full-screen renderer** puts the speaking host in the 9:16 frame, captions 2–3 words at a time with the spoken word in legacy gold `#F5B71F`, punch-in zooms on new ideas, a hook title for the first ~2.7 s, the logo top-left, and a darkened end card. The split-frame `build_short.py` render stays available. These are implementation notes; `investing-bros-brand` owns new visual specifications, and migration requires a reviewed sample.

Episode 7 (video producer), on top of that look:
- **Historical episode 7 batch: 5 shorts**, **1080×1920**. This is a legacy record, not the current count; new episodes always deliver exactly 3. Fast cuts, no silences. Zooms alternate **100% / 112%**. Logo end card.
- A complex idea can use a motion animation ([references/hyperframes.md](hyperframes.md)). Its existing navy/gold/white implementation remains until a reviewed brand migration.
- Captions are Heebo Black, active word in gold `#F5B71F`. The scripts render Hebrew with libass (Encoding −1). libass can reverse RTL word order; the video producer worked around that with PIL + raqm. If a script's captions come out in the wrong order, stop and propose a script change — don't ship a one-off renderer (working rules in `investing-bros-show`).

## Legacy render and cover scripts

| Step | Script | Notes |
|---|---|---|
| Render the deployed video style | `build_fullbleed.py short.json` then `bash NAME_fb.sh` | `--speed` defaults to the house 1.15 and `1.0` disables it; also writes speed-synced `NAME.srt`, `NAME_hook.png` (the paper-strip hook) and `NAME_layout.json`; `caption_y` / `hook_y` / `hook_style` set placement and hook look; pieces may open on a later line; `base` + `shots` cut to the other host for reactions; `tags` = name tag; `sources`/`crop` take each host's own high-res Riverside track. Worked example: [references/ep7-asteroid-fullbleed.json](ep7-asteroid-fullbleed.json). Its output is also the input for a HyperFrames overlay |
| Legacy video-frame cover (explicit reuse only) | `make_cover.py --style fullbleed --crop x,y,w,h --logo logo.png …` | same crop as the short; new cover artwork comes from `investing-bros-brand` |

## Legacy end card

- **Legacy cover end card (`"endcard_style": "cover"`, older exports only)**: the end card in the cover-art look: navy paper over the video, the torn-paper show logo, a cream `פרק N` pill, the episode title (from `youtube/title.txt` minus the `פרק N - ` prefix, `|` for the 2-line break) in cream, and `הקישור לפרק המלא בתיאור` in mustard with a bobbing mustard arrow under it; `endcard` = `[title, "פרק N", link line]`. Pair it with one callout `{"before_endcard": 4.0, ...}`: the bobbing link callout appears 4 s before the card and crossfades into it (no mid-short callout). When the payoff runs to the last frame, start the card at the payoff's last line (`endcard_at`, source time) and set `"endcard_captions": true` so that line's captions keep burning over the card. The card stays inside y 150–1528 (`check_short.py --layout` fails otherwise).

## Explainer panels (HyperFrames)

Add 1–2 animated explainer panels ([references/hyperframes.md](hyperframes.md)) only where they show the idea (episode 7: asteroid lands on Earth; supply ×2 → value ½).

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

   **Explainer moment? Render it with HyperFrames instead.** When the clip explains something a card can show — a number, "not X but Y", a list, a before/after — follow [references/hyperframes.md](hyperframes.md) for this step: the same pieces, shots and captions, plus animated cards (count-up, strike-through, building list) in the band under the video. It looks more produced and gets Hebrew/English text right natively, at ~6× the render time. Punchlines and stories stay on the plain render.
5. **Check the export.** For each short:
   - a strip of 6–8 frames across the clip: captions right-to-left (punctuation at the left end, English words in place), not over faces, inside the safe zone; the right host on screen
   - `ffmpeg -i short.mp4 -af ebur128=peak=true -f null -` → about −14 LUFS, peak below −1 dB; per-host levels close
   - duration **after playback speed is applied**: 20–45 s; 45.0 s is a hard maximum, with no exception. Listen to every cut — no clipped words, no clicks
6. **Make a cover for each short** — the image Reels / Shorts / TikTok show before play and in the profile grid. It comes from `investing-bros-brand` (Shorts covers, face format: a real frame of the speaking host): give it the hook, the episode number, the speaking host, the Short's file name and its verified face picks, and use the result both as `-cover.jpg` and as the YouTube custom thumbnail. Layout, font and checks live there only.
   Until Amitai says the design is dialed in, brand returns three clearly labeled Codex
   options A/B/C for each individual Short; show all three and use only the episode owner's pick.
   Rebuilding an older Short in the legacy video-frame style is the only use of `make_cover.py`:
   ```bash
   python3 scripts/make_cover.py --source raw.mp4 --at <source time of a good frame> --side L \
     --headline "סוויפט היא בכלל|[לא מערכת תשלומים]" --episode N \
     --frame frame_vertical.png --fonts fonts/ "שורט-01-סוויפט-cover.jpg"
   ```
   The current standing batch needs all three covers from that brand flow (Codex on Amitai's Mac, face format, exact Hebrew); a legacy `make_cover.py` rebuild does not complete a new episode's standing batch.
