---
name: investing-bros-hyperframes
description: >-
  Render an Investing Bros / אחים להשקעות short (or a teaser moment) with
  HyperFrames: ffmpeg cuts the clean host clip, then an HTML/GSAP composition
  adds animated explainer cards (a number counting up, a wrong/right strike,
  a list that builds), the logo and proofread Hebrew captions. Use when
  Amitai asks for "hyperframes", "כרטיסים", "גרפיקה מונפשת", "animated
  graphics" or "a more designed short", and for every Investing Bros short:
  each short requires at least one high-quality, informative animation.
---
# Investing Bros shorts with HyperFrames

Load `investing-bros-show` first (brand, loudness, recording layout). The moment picking, cut points and caption proofreading come from `investing-bros-shorts` — this skill replaces only its render step.

[HyperFrames](https://github.com/heygen-com/hyperframes) (HeyGen, open source) renders video from an HTML page: the DOM declares timing with `data-*` attributes, a paused GSAP timeline drives the motion, and headless Chrome captures it frame by frame. Chrome lays out the text, so Hebrew right-to-left and mixed Hebrew/English come out right without the ASS workarounds.

## When to use
- **Every Investing Bros short requires at least one high-quality, informative HyperFrames animation**, even if Amitai only asks for "shorts". This is a mandatory delivery criterion (Amitai, 2026-10-14).
- The clip **explains** something — a number, a "not X but Y", a before/after, a short list. Cards make it land (episode 6: "SWIFT — ~~מערכת תשלומים~~ / מערכת הודעות", "40$" counting up).
- Amitai asks for HyperFrames or a more designed short.

For a punchline, a story or a reaction clip, keep the animation focused on one meaningful explanation. The plain render can provide the base footage, but it is not a finished short until the required animation has been added and checked.

## Animation quality gate
- Motion must explain something: show the transfer, changing composition, relationship, contrast or spoken number. A decorative entrance or a text card that only repeats the captions is not enough.
- Captions, hook motion, logos, punch-ins, transitions and end cards do not count as the required informative animation.
- Use crisp, coherent graphics in the show palette, deliberate motion and readable Hebrew labels. Check at phone size, not just at full resolution.
- Time the important change to the relevant spoken words; preserve hypotheses and caveats. Do not add made-up figures, percentages, financial claims or predictions.
- Keep eyes, captions and the platform safe zone clear. Inspect frames before, during and after the animation, then check the final export.
- New explanatory scenes belong in the supplied generator with tests and a PR, never in a hand-written one-off HTML composition.

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

## Full-screen overlay (house style, episode 7)
For the house style, the base video comes from `investing-bros-shorts` → `build_fullbleed.py` (full-screen host, word-by-word captions, logo). HyperFrames then adds only 1–2 animated panels in a compact top panel (left 56, top 262, 968×420 scaled to 0.74 so the host's eyes stay clear). Set `"layout": "overlay"` in short.json (no `captions` — they are burned into the input) and use these card types:

| type | shows | keys (times = source) |
|---|---|---|
| `fly` | an asteroid in space: metal sheen, gold veins, then it flies down and lands on Earth with a gold flash | `kicker`, `metal_at`/`metal_label`, `gold_at`/`gold_label`, `fly_at`, `fly_kicker`, `land_label` |
| `supply` | a stack of gold bars, a second stack (×N), an arrow, then a value meter that drops | `kicker`, `factor`, `factor_label`, `more_at`, `value_kicker`, `value_at`, `drop_at`, `drop_to`, `drop_mark`, `drop_label` |
| `money_roles` | coins appear under an abundant-gold hypothesis; a coin transfers between wallets while saving is contrasted | `kicker`, `trade_label`, `save_label`, `abundant_at`, `save_at`, `trade_at`, `conclusion_at`, `conclusion` |
| `coin_dilution` | cheap-metal particles move into a coin and its composition visibly changes; no invented metal percentage | `kicker`, `before_label`, `after_label`, `metal_label`, `mix_at`, `conclusion_at`, `conclusion` |
| `currency_trust` | the spoken cash total appears above a note stack; a connection fills and the central bank lights up as trust is explained | `kicker`, `value`, `amount_at`, `bank_at`, `bank_label_at`, `bank_label`, `trust_at`, `trust_label`, `conclusion_at`, `conclusion` |

The other card types work in the panel too. Worked example: [references/ep7-asteroid-overlay.json](references/ep7-asteroid-overlay.json). Labels are the hosts' words or a faithful label for them. Use the full-screen render (with `-g 24`) as `input-video.mp4`; it already has the logo and end card, so leave `endcard` out.

Worked educational examples: [money roles](references/ep7_money_roles_v2.json), [coin dilution](references/ep7_coin_dilution_v2.json), and [currency trust](references/ep7_currency_trust_v2.json). These use `panel_scale: 0.84`, `panel_left: 20`, `panel_top: 280` for larger illustrations while retaining the 170 px right margin. Inspect the actual host's eyes before using these settings on another recording. The cash amount is a spoken total, not a fictional banknote denomination. Coin colours illustrate a qualitative composition change; do not add an unsupported ratio or percentage.

The episode 7 base footage for these larger scenes uses `build_fullbleed.py` with `video_offset_y: {"L": 160, "R": 0}`. This keeps Nadav's eyes below the panel rather than shifting both hosts upward by the same amount. The framing is part of the animation quality check, not an optional cosmetic pass.

## Hand back
Make the short's cover and upload short + cover + `.srt` exactly as `investing-bros-shorts` steps 6–7 (sized cover, sub-10 MB upload copy, `promo/` naming); keep `short.json` and the project folder in `extras/` so a fix is a text edit plus a re-render. Tell Amitai, per short: where it is in the episode, its length, its cards (one line each), and any words you couldn't verify. Mention he can open `npx hyperframes preview PROJ/public` (Studio) to tweak text or timing himself.

## Never
- Put a number, name or claim on a card that the hosts didn't say.
- Cut, reorder or speed up the footage inside HyperFrames — edits belong in `make_input.py`, where the cuts are at pauses and the sound is levelled.
- Load fonts, scripts or images from a URL in the composition.
- Post anywhere unless Amitai asks in chat for that post, and then only to a destination listed in `investing-bros-show`.
- Hand-write a composition (`index.html`) or card. New layouts and card types go into `build_composition.py` through a PR; follow the working rules in `investing-bros-show`.
