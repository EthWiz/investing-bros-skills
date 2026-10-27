# Setup and troubleshooting

Part of `investing-bros-remotion`.

## What runs where
- `template/` is a Remotion 4 project pinned to exact versions (`package-lock.json`).
  `render_short.py` copies it into the work folder and runs `npm ci` once per lockfile.
  `node_modules/` is never committed.
- Remotion renders by loading the composition in headless Chrome and screenshotting each
  frame, then encoding with its bundled ffmpeg. The base video is read frame-exact by
  `OffthreadVideo`, so it needs no special keyframes.

## Chrome
`render_short.py` picks, in order: `--browser`, `$REMOTION_BROWSER_EXECUTABLE`, a
Playwright headless shell (cloud box:
`/opt/pw-browsers/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell`;
Mac: `~/Library/Caches/ms-playwright/…`). With none of these, Remotion downloads its own,
which fails on networks that block Google's storage host.

## Timing (episode 8 short 05, 29 s, cloud box, 2 cores)
- `--stills` sheet: ~30 s. Full render: ~3 min. The first run adds ~30 s for `npm ci`.
- On Amitai's Mac (4 cores, 4 GB, 3-minute command limit) run the render in steps that
  finish in time, or render in the cloud box and move the MP4 (show → environment).

## Timing (crypto course lesson 1 draft, 3:16 at 1080p, Amitai's Mac via Claude Code, 10 cores)
- `render_lesson.py --stills` with 11 stills: about 1 minute after the first `npm ci`. Full render at `--concurrency 8`: 8.5 minutes. Run it in the background.

## Problems seen
| Symptom | Fix |
|---|---|
| Hebrew in a fallback font | the static Heebo TTFs weren't staged; pass `--fonts` with the three `brand.py fonts` files |
| `Could not find a browser` / download blocked | pass `--browser` or set `REMOTION_BROWSER_EXECUTABLE` |
| `check_short.py` warns about silence at the end | there is no end card, so the clean base must end right after the payoff; recut in `make_base.py` |
| Captions run ahead of or behind the voice | rebuild them with `make_captions.py --wav`; check the proofread `text.json` matches what is said in each kept piece |
| A lesson's side panel leaves a strip of video at the bottom edge | the torn-edge clip stops short of the frame: the panel overshoots it (`top: -14`, `height: 1108` in `SidePanel`) |
| Words of a card title in the wrong order | the title box must stay `direction: rtl` with a plain flex row (not `row-reverse`) |
