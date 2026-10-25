---
name: investing-bros-remotion
description: >-
  The animation framework for Investing Bros / אחים להשקעות video: render shorts (hook,
  name tags, captions, explainer cards, CTA, end card) with the show's Remotion template
  over the clean base from investing-bros-shorts. Covers the props format, card modes
  (inset with the host framed around it, full screen, small card), the brand icon set,
  QA stills, adding icons or layouts, and the Remotion licence. Use whenever a short or
  clip gets animation, or when Amitai asks for "Remotion", "animation", "אנימציה",
  "כרטיס מונפש", "גרפיקה מונפשת", "explainer card", "full screen card" or "מסך מלא".
---
# Investing Bros animation (Remotion)

Load `investing-bros-show` first. Visual rules come from `investing-bros-brand`;
the short's cut, captions and approvals come from `investing-bros-shorts`. This skill
owns how things move on screen, not what the short says or how it looks in a still.

**Remotion is the show's animation framework** (decided by Amitai 2026-10-25, after
comparing it with HyperFrames and the Python renderer on episode 8 short 05). New
animated work goes through this template. `build_amitai_short.py` and HyperFrames
stay only for rebuilding older exports.

## When to use
Step 5 (render) of every short in `investing-bros-shorts`, and any other vertical clip
that needs animated graphics. The cut, the clean base and the proofread captions are
done before this skill starts.

## Inputs
- The clean base video from `make_base.py` (`investing-bros-shorts` step 3): cut,
  1.25x, −14 LUFS, logo and gradient burned in, no captions.
- The short's config JSON (`investing-bros-shorts` → Config schema; times are
  **output** seconds). Explainer cards go in `cards` (format below).
- Static Heebo TTFs (`brand.py fonts`) and the solid logo
  (`investing-bros-brand` → `assets/logo-solid.png`).
- Node 18+ and npm, ffmpeg/ffprobe, a headless Chrome (found automatically; see
  [references/setup.md](references/setup.md)).

## Steps
1. **Plan the cards** (the moments that get animation). Follow
   [references/cards-and-icons.md](references/cards-and-icons.md): one idea per card,
   about one card per 20 s, each step on the word it illustrates, never over the hook
   (first 3 s) or the CTA. Pick the mode: **`inset`** (default: a large card with the
   host visible around it), **`full`** (covers the frame for 2–4 s; logo, name tag and
   captions stay on top) or `card` (the older small card). Card text = the hosts'
   own words; a value icon (`drop`, `rise`, `pie`) shows only a number the host said.
2. **Make the props** — this also checks the house rules:
   ```bash
   python3 scripts/make_props.py short.json --base WORK/NAME_clean.mp4 -o WORK/props.json
   ```
   It refuses unknown icons, emoji, cards over the hook or CTA, overlapping cards,
   steps outside their card, captions over 4 words or out of order. Fix the config,
   not the props.
3. **Look before rendering** — six stills on one sheet (about 30 s):
   ```bash
   python3 scripts/render_short.py --props WORK/props.json --base WORK/NAME_clean.mp4 \
     --fonts WORK/fonts --logo WORK/logo.png --out WORK/NAME.mp4 --stills 1,9.5,12,17,23,27
   ```
   Check `NAME_stills.jpg`: hook strips in the first 3 s, cards inside their box and
   readable, captions right-to-left below the card, logo and name tag visible, end card.
   The first run copies the template into `WORK/remotion` and runs `npm ci` once.
4. **Render** — same command without `--stills` (about 3 min for 30 s on 2 cores):
   ```bash
   python3 scripts/render_short.py --props WORK/props.json --base WORK/NAME_clean.mp4 \
     --fonts WORK/fonts --logo WORK/logo.png --out WORK/NAME.mp4
   ```
   It writes `NAME.mp4` and `NAME_layout.json` (marks the 3 s silent end card).
5. **QA and hand on** — back to `investing-bros-shorts` step 6: `check_short.py NAME.mp4`
   (reads the layout file), 8-frame strip, Telegram approval, cover, Drive.

To tweak timing or text by eye, run `npm run studio` in `WORK/remotion` (Remotion
Studio, live preview with a timeline) with `public/` staged by step 3; then put the
change back into the config and re-run steps 2–4. A new icon, card mode or layout is
a template change in this repo (with a test), never a one-off edit in `WORK/remotion`.

## Done when
- `NAME.mp4` and `NAME_layout.json` exist for each short, rendered from this template
  with props that passed `make_props.py`, and `check_short.py` passes on the video.
- The short continues through `investing-bros-shorts` (Telegram approval, cover, then
  `Shorts/` in the episode's Drive folder: `.mp4`, `-cover.jpg`, `.srt`,
  `youtube-שורט-NN.md`).

## Hand back
Per short: the cards (time, mode, icon, words), the stills sheet, render time, and any
card text you weren't sure the hosts said. Template changes go in a PR with a test.

## Never
- Put words, numbers or claims on a card the hosts didn't say; a value icon shows only
  a spoken number.
- Edit `WORK/remotion` by hand to ship a short; change the template here instead.
- Cut, reorder or change speed in Remotion; that stays in `make_base.py`.
- Load fonts, scripts or images from a URL inside the composition; everything is
  staged into `public/`.
- Add music, SFX, stock footage or emoji.
- Unpin or bump Remotion versions without rendering the sample and running the tests.
- Add a person to the team without checking the Remotion licence
  (`investing-bros-show` → Animation).
