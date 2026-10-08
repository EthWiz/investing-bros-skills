---
name: investing-bros-hyperframes
description: >-
  Render an Investing Bros / אחים להשקעות short (or a teaser moment) with
  HyperFrames: ffmpeg cuts the clean host clip, then an HTML/GSAP composition
  adds animated explainer cards (a number counting up, a wrong/right strike,
  a list that builds), the logo and proofread Hebrew captions. Use when
  Amitai asks for "hyperframes", "כרטיסים", "גרפיקה מונפשת", "animated
  graphics" or "a more designed short", or when a short explains a concept
  that cards can show.
---
# Investing Bros shorts with HyperFrames

Load `investing-bros-show` first (brand, loudness, recording layout). The moment picking, cut points and caption proofreading come from `investing-bros-shorts` — this skill replaces only its render step.

[HyperFrames](https://github.com/heygen-com/hyperframes) (HeyGen, open source) renders video from an HTML page: the DOM declares timing with `data-*` attributes, a paused GSAP timeline drives the motion, and headless Chrome captures it frame by frame. Chrome lays out the text, so Hebrew right-to-left and mixed Hebrew/English come out right without the ASS workarounds.

## When to use
- The clip **explains** something — a number, a "not X but Y", a before/after, a short list. Cards make it land (episode 6: "SWIFT — ~~מערכת תשלומים~~ / מערכת הודעות", "40$" counting up).
- Amitai asks for HyperFrames or a more designed short.

For a punchline, a story or a quick reaction clip, the plain `investing-bros-shorts` render is enough and ~6× faster to render.

## Inputs
- The short's edit list from `investing-bros-shorts` step 1–2: kept `pieces` (cut at pauses), `shots` (L/R host), proofread `captions`.
- The source recording (side-by-side, 1920×1080) and the levelled episode audio (`episode-leveled.wav` from post-production) — or the raw audio plus per-piece gains.
- Brand assets from `investing-bros-shorts` → `brand.py`: `logo.png` (wordmark) and the static Heebo TTFs.
- Node 18+, ffmpeg/ffprobe, and the HyperFrames CLI (`npx hyperframes`, from npm).

## Steps
1. **Write `short.json`** — one file drives both scripts; format in `scripts/build_composition.py`, full worked example in [references/example-swift.json](references/example-swift.json). Add `cards` (2–6 per short, one at a time, never overlapping):
   | type | shows | good for |
   |---|---|---|
   | `route` | A ——→ B with a filling bar | a transfer, a move, a journey |
   | `stat` | a number counting up + label + optional quote | a figure the host says |
   | `strike` | title, a crossed-out wrong label, then the right one | "it's not X, it's Y" |
   | `statement` | kicker, a chip, then a big two-line claim | the clip's thesis |
   | `list` | rows that slide in (on / off) + a conclusion line | contrasts, "everything except…" |
   Every `*_at` is the moment the word is **spoken** (source time). Card text is either the host's words or a faithful label for them — no numbers, names or claims he didn't say. Leave gaps where nothing needs a card; captions carry those stretches.
2. **Cut the clean clip** (ffmpeg — HyperFrames plays its input untouched, so all editing happens here):
   ```bash
   python3 scripts/make_input.py short.json      # -> NAME_input.sh
   bash NAME_input.sh                             # -> NAME_input.mp4, 1080x1216, keyframe every second, ~-14 LUFS
   ```
3. **Stage the project**:
   ```bash
   mkdir -p PROJ/public/fonts PROJ/public/vendor
   cp NAME_input.mp4 PROJ/public/input-video.mp4 && cp logo.png PROJ/public/logo.png
   python3 -c "from fontTools.ttLib import TTFont as F
   for w in ('SemiBold','ExtraBold','Black'):
       f=F(f'fonts/Heebo-{w}.ttf'); f.flavor='woff2'; f.save(f'PROJ/public/fonts/Heebo-{w}.woff2')"
   npm i --no-save gsap@3 && cp node_modules/gsap/dist/gsap.min.js PROJ/public/vendor/
   python3 scripts/build_composition.py short.json --project PROJ
   ```
   The composition must not load anything from the network at render time — fonts, GSAP, logo and video are all local files.
4. **Check before rendering**:
   ```bash
   npx hyperframes doctor                          # needs ffmpeg + Chrome Headless Shell
   npx hyperframes lint PROJ/public                # 0 errors (Studio-layout warnings are fine)
   npx hyperframes snapshot PROJ/public --at 3,10,20,30,40,46   # -> public/snapshots/contact-sheet.jpg
   ```
   Look at the contact sheet: captions right-to-left and readable, every card fully inside its band, no empty card waiting for its first line, the right host on screen, logo legible.
   If `doctor` can't get Chrome (blocked download), point it at an existing headless shell: `export PRODUCER_HEADLESS_SHELL_PATH=/path/to/chrome-headless-shell` (Playwright installs one under `$PLAYWRIGHT_BROWSERS_PATH/chromium_headless_shell-*/chrome-linux/headless_shell`).
5. **Render**:
   ```bash
   cd PROJ && PRODUCER_BROWSER_GPU_MODE=hardware npx hyperframes render public --skill=talking-head-recut -o output.mp4 --fps 24
   ```
   Drop `PRODUCER_BROWSER_GPU_MODE=hardware` on machines without a GPU. Episode 6 (47 s, 2 cores, software GL): ~3 minutes. Shells with a time limit: start it in the background and poll its log.
6. **Check the export**: duration = the clip's; `ffmpeg -i output.mp4 -af ebur128=peak=true -f null -` → about −14 LUFS, peak ≤ −1 dB; frames at each card's key moment; listen to every cut.

## Hand back
Upload `output.mp4` (and the captions as `.srt` from `investing-bros-shorts` if wanted) to the episode's `promo/` folder; keep `short.json` and the project folder in `extras/` so a fix is a text edit plus a re-render. Tell Amitai, per short: where it is in the episode, its length, its cards (one line each), and any words you couldn't verify. Mention he can open `npx hyperframes preview PROJ/public` (Studio) to tweak text or timing himself.

## Never
- Put a number, name or claim on a card that the hosts didn't say.
- Cut, reorder or speed up the footage inside HyperFrames — edits belong in `make_input.py`, where the cuts are at pauses and the sound is levelled.
- Load fonts, scripts or images from a URL in the composition.
- Post anywhere — Amitai posts.
