---
name: investing-bros-remotion
description: >-
  The animation framework for Investing Bros / אחים להשקעות video: render shorts (hook,
  name tags, word-by-word captions, explainer cards, CTA; no end card) with the show's
  Remotion template over the clean base from investing-bros-shorts. Covers word-timed
  captions, the props format, card modes (inset: most of the frame with the host framed
  around it, full screen, small card), the brand icon set, QA stills, adding icons or
  layouts, and the Remotion licence. Use whenever a short or
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
- For captions: the proofread words of each kept piece (`text.json`), whisper word
  timings for them (`transcribe_clip.py`), `timemap.json` from `make_base.py`, and a
  16 kHz WAV of the same window.
- Static Heebo TTFs (`brand.py fonts`) and the solid logo
  (`investing-bros-brand` → `assets/logo-solid.png`).
- Node 18+ and npm, ffmpeg/ffprobe, a headless Chrome (found automatically; see
  [references/setup.md](references/setup.md)).

## Steps
1. **Plan the cards** (the moments that get animation). Follow
   [references/cards-and-icons.md](references/cards-and-icons.md): one idea per card,
   about one card per 20 s, each step on the word it illustrates, never over the hook
   (first 3 s) or the CTA. Pick the mode: **`inset`** (default: most of the frame, a
   40 px frame of the host video around it), **`full`** (covers the frame for 2–4 s) or
   `card` (the older small card); logo, name tag and captions always stay on top. Card
   text = the hosts' own words; no subtitle that repeats the captions; a value icon
   (`drop`, `rise`, `pie`) shows only a number the host said.
2. **Time the captions word by word:**
   ```bash
   python3 scripts/make_captions.py text.json words.json WORK/timemap.json -o WORK/captions.json \
     --wav window.wav --wav-offset T0
   ```
   `text.json` = `[{"from", "to", "text"}]`, one entry per kept piece (source times, the
   proofread words, keywords in `[brackets]`). Whisper's words are matched to the
   proofread ones even when misspelt, starts that fall in silence move to where the
   speech begins, and the words are grouped into captions of up to two lines (≤ 8 words,
   about 2–3 s each, at least 1.2 s on screen unless joining a neighbour would overflow),
   breaking at sentence ends and real pauses. On screen the whole caption appears at once
   and the word being spoken turns gold: the house format (Amitai, 2026-10-25, after
   comparing one-line pop-in captions and keyword-only colour on episode 8 short 05).
   The older look stays available per short: `caption_style: "build"` with
   `make_captions.py --lines 1` (one line of 1–4 words popping in) and
   `caption_highlight: "keywords"`.
   **Kinetic (on trial, episode 8 short 05 v6):** `caption_style: "punch"` with
   `make_captions.py --style punch`: each phrase grows until it has had its reading time
   (~0.7 s for one word, ~1.1 s for three) and breaks at punctuation or a pause (max 5–6
   words, breaking at a comma when long); the whole phrase pops in at once, one word big and
   sized to fit (the keyword, else a number, else the main content word), the word being
   said on a navy box (gold for keywords and numbers) and the big word bouncing when said;
   captions hold into following pauses; cards lift their content to leave the captions
   room, and captions drop under the CTA strip. v6 also tried 1.15x (`make_base.py
   --speed 1.15`) instead of the house 1.25x.
3. **Make the props** — this also checks the house rules:
   ```bash
   python3 scripts/make_props.py short.json --base WORK/NAME_clean.mp4 --captions WORK/captions.json \
     -o WORK/props.json
   ```
   It refuses unknown icons, emoji, cards over the hook or CTA, overlapping cards,
   steps outside their card, a subtitle repeating the captions, captions over 8 words or
   out of order, and a CTA that stops before the end. Fix the config, not the props.
4. **Look before rendering** — six stills on one sheet (about 30 s):
   ```bash
   python3 scripts/render_short.py --props WORK/props.json --base WORK/NAME_clean.mp4 \
     --fonts WORK/fonts --logo WORK/logo.png --out WORK/NAME.mp4 --stills 1,9.5,12,17,23,27
   ```
   Check `NAME_stills.jpg`: hook strips in the first 3 s, cards inside their box and
   readable, captions right-to-left and building up word by word, logo and name tag on
   top, CTA with its arrow at the end.
   The first run copies the template into `WORK/remotion` and runs `npm ci` once.
5. **Render** — same command without `--stills` (about 3 min for 30 s on 2 cores):
   ```bash
   python3 scripts/render_short.py --props WORK/props.json --base WORK/NAME_clean.mp4 \
     --fonts WORK/fonts --logo WORK/logo.png --out WORK/NAME.mp4
   ```
   It writes `NAME.mp4` and `NAME_layout.json` for `check_short.py`. There is no end
   card: the video ends on the payoff with the CTA, and loops.
6. **QA and hand on** — back to `investing-bros-shorts` step 6: `check_short.py NAME.mp4`
   (reads the layout file), 8-frame strip, Telegram approval, cover, Drive.

To tweak timing or text by eye, run `npm run studio` in `WORK/remotion` (Remotion
Studio, live preview with a timeline) with `public/` staged by step 3; then put the
change back into the config and re-run steps 3–5. A new icon, card mode or layout is
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
