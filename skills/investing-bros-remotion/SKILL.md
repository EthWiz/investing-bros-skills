---
name: investing-bros-remotion
description: >-
  The animation framework for Investing Bros / אחים להשקעות video: render shorts (hook,
  name tags, word-by-word captions, explainer cards, CTA; no end card) with the show's
  Remotion template over the clean base from investing-bros-shorts. Covers word-timed
  captions, the props format, card modes (inset: most of the frame with the host framed
  around it, full screen, small card), the brand icon set, QA stills, adding icons or
  layouts, and the Remotion licence. Also renders the crypto course's 16:9 lesson videos
  (the Lesson composition). Use whenever a short, clip or crypto-course lesson gets
  animation, or when Amitai asks for "Remotion", "animation", "אנימציה",
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
  1.15x (house speed), −14 LUFS, logo and gradient burned in, no captions.
- The short's config JSON (`investing-bros-shorts` → Config schema; times are
  **output** seconds). Its shared `cover_title` drives both the cover and opening
  banner; do not add a separate hook title. Explainer cards go in `cards` (format below).
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
   speech begins, and the words are grouped into the **house kinetic captions**
   (Amitai, 2026-10-26, episode 8 short 05 v6.1, after the reference
   [youtube.com/shorts/nD0smg5J6Fo](https://www.youtube.com/shorts/nD0smg5J6Fo)):
   - each phrase grows until it has had its **reading time** (0.45 s + 0.045 s per
     character: ~0.7 s for one word, ~1.1 s for three), then breaks at punctuation, a
     pause or 3 words; never more than 5–6 words (a long one breaks at its last comma);
     a leftover that still can't be read joins a neighbour; captions hold into pauses;
   - the **whole phrase pops in at once**; one word per phrase is **big and sized to fit**
     (the keyword, else a number, else the main content word; Hebrew function words
     never), at 78–135 px (72–98 px under the CTA); the rest are ~64 px with balanced
     padding and normal word spacing;
   - the **word being spoken sits on a navy box** (gold box with navy text for keywords
     and numbers) that moves word by word, and the big word bounces when it is said;
   - mixed Hebrew/Latin/numbers are bidi-isolated (`S&P 500`, `ב-S&P` and figures stay
     in reading order), and a multi-token Latin name plus its number stays in one phrase;
   - over a card the card's content lifts to leave the captions the lower third; under
     the CTA strip the captions drop lower and smaller.
   Older looks stay available per short: `caption_style: "line"` with
   `make_captions.py --style lines --lines 2` (two calm lines, gold spoken word) and
   `caption_style: "build"` with `--style lines --lines 1` (one line popping in), plus
   `caption_highlight: "keywords"`.
3. **Make the props** — this also checks the house rules:
   ```bash
   python3 scripts/make_props.py short.json --base WORK/NAME_clean.mp4 --captions WORK/captions.json \
     -o WORK/props.json
   ```
   It refuses a render over the hard 45 s cap, unknown icons, emoji, cards over the opening banner or CTA, overlapping cards,
   steps outside their card, a subtitle repeating the captions, captions over 6 words or
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
6. **QA and hand on** — back to `investing-bros-shorts` step 6:
   `check_short.py NAME.mp4 --config short.json --youtube-notes youtube-שורט-NN.md`
   (reads the layout file), 8-frame strip, Telegram approval, cover, Drive.

To tweak timing or text by eye, run `npm run studio` in `WORK/remotion` (Remotion
Studio, live preview with a timeline) with `public/` staged by step 3; then put the
change back into the config and re-run steps 3–5. A new icon, card mode or layout is
a template change in this repo (with a test), never a one-off edit in `WORK/remotion`.

## Lesson videos (crypto course, 16:9)
The template's second composition, `Lesson` (1920×1080, 30 fps, `src/lesson/`), plays a lesson's joined takes with captions, strips, an agenda and progress marker, and the lesson's own scenes. The cut and the lesson's config belong to `investing-bros-crypto-course` (its video reference has the workflow and layout); this skill owns the composition and three scripts:
- `scripts/make_lesson_props.py lesson-N/lesson-N-video.json --words-dir WORDS -o props.json [--srt captions.srt] [--takes-dir DIR]` (the config lives in the lesson's own folder, or is the Drive manifest): captions from the proofread words on Whisper's timings (two calm lines, sentences kept whole), every graphic's time from its anchor phrase, each scene's words and times from its segment's `content`, and the layout. It refuses anything that breaks the house rules (graphics in the first 30 s, unknown scenes or the wrong mode, a scene missing what `scenes.json` says it needs or timed outside its segment, segments out of order, phrases that aren't said, punch-ins over 1.25x, no script Doc revision or a snapshot changed after parsing, a scene variant that isn't allowed or has its events out of order, words stamped to another take).
- `scripts/render_lesson.py --props … --base … --fonts … --logo … --out lesson.mp4 [--stills 25,38,… | --transitions]`: the same staging as `render_short.py`, plus the scenes' images into `public/assets/`. `--stills` gives a contact sheet (with `--vertical`, of the 9:16 `LessonScenes` composition: the scenes marked `vertical` alone on navy, to check them before a Short uses them); `--transitions` a clip around every cut and layout change, with sound, since stills can't show timing. Run the full render in the background; afterwards it measures the sound against the base and shifts it back (Remotion's AAC keeps the encoder priming, about 43 ms late), without re-encoding. Every render leaves `lesson.mp4.render.json` beside the video; after a change to the config, `--patch` renders only the stretches whose props changed (widened to the old export's keyframes, about 8 s apart) and stream-copies the rest, keeping the sound: a new chart or caption fix in a minute or two instead of the whole lesson. It refuses, and asks for a full render, when the base, an image or anything lesson-wide changed, or the template changed without `--range START-END` (only you know where a template change shows); `lesson_patch.py` has the rules and its checks.
- `scripts/check_lesson.py lesson.mp4 --props props.json --base base.mp4 --fonts FONTS`: fails on the wrong format or length, loudness outside -16..-12 LUFS or a true peak above -1 dBTP, sound more than a frame off the base at any cut, 1.5 s of dead air across a cut, and captions out of order, overlapping, off their words, under 0.7 s, or over two lines in their layout. Run it before anyone sees a render. With `--record DIR --config … [--takes-dir …]` it then writes the export record (what produced the video, its hash and this report), only when everything passes and never over an older one.
- `scripts/phone_copy.py lesson.mp4 -o lesson-N-phone-720p.mp4 [--mb 30]`: the 720p review copy for a phone, two-pass to fit the size, and it fails if the copy has no audible sound. Use an ASCII name: a Hebrew one played silent in a phone preview.

A scene is a component listed by name in `src/lesson/scenes.ts` and declared in `src/lesson/scenes.json` (its mode, the anchors and content keys it reads, its images); the two must name the same scenes. It gets `{at, start, end, content, assets}`, and every word it shows comes from `content`, never from the component. Reusable scenes sit in `src/lesson/` (`terms`: a heading and terms that appear one by one; `double-spend`: one coin, a sender and two recipients, as `scenario: "copy"` (the coin is copied and both get it, then an X) or `scenario: "ledger"` (the bank's ledger splits into everyone's copy and the second payment is refused), in 16:9 and 9:16; `growth-bars`: how much each asset grew, as bars on one linear scale, each rising on its name and showing the multiple Amitai says (`said`), in 16:9 and 9:16; `price-drop`: a fall from a peak on a price chart with no prices on the axes, the line dropping to `(100 - percent)%` of the peak's height with an arrow and a bracket, in 16:9 and 9:16; `conflict`: two computers hear two payments of one coin in a different order, their ledgers part (≠), then the question and a short chain as the way out; `mining`: a simplified mining setup, rigs racing on the puzzle, the winner's piece sealing the page, the others checking it and each getting a copy, the second payment refused; `chain`: linked pages with fingerprints, an old page erased, its print changing and the link breaking, then the network's copies agreeing and growing; `private-key`: the key opens a safe on the coins, is lost, the safe locks and the helpdesk gets an X; all four in 16:9 and 9:16, their drawings shared in `blocks.tsx`), a lesson's own in `src/lesson/lesson<N>/`. A scene with variants declares them in `scenes.json` (`variants`: the content key, the allowed values, each one's extra content and the order its events must come in), and the props script checks them. Anchors and content a take may not say go under `optional` (the Satoshi panel's month and closing question): the scene shows them only when the config gives them, so no stand-in is needed. The face point the punch-ins and the bubble centre on is the config's `face` (default 840, 450), set by `make_lesson_base.py frame` in `investing-bros-crypto-course`. A `bubble` scene draws the whole frame behind Amitai's circle; a `side` scene draws inside `SidePanel`. Shared pieces (strips, panel, entrance springs) are in `src/lesson/kit.tsx` and `panels.tsx`.

## Done when
- `NAME.mp4` and `NAME_layout.json` exist for each short, rendered from this template
  with props that passed `make_props.py`, and `check_short.py` passes on the video.
- The short continues through `investing-bros-shorts` (Telegram approval, cover, then
  `Shorts/` in the episode's Drive folder: playable `.m4v` (`video/x-m4v`), `-cover.jpg`, `.srt`,
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
