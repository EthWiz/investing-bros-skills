# Shorts covers (vertical 1080×1920)

The image Reels, Shorts and TikTok show before play and in the profile grid. One cover
per Short; `investing-bros-shorts` asks for it and uses it as `-cover.jpg` and as the
YouTube custom thumbnail.

**Standard since episode 10: the face format.** A real frame of the host who speaks in
the Short, as a photographic cutout, under Amitai's "cut newspaper" title strips.
Episode 10's faceless covers (title over an engraved illustration only) were rejected as
the old format; that style (reference `shorts-title-strips-ep1.png`, Drive
`references/covers`, ID in the [asset index](asset-index.md)) now sets only the strips,
pill and show mark.

**Default since episode 10 (Amitai's pick, 2026-11-05): the one-pass Codex cover with
the real face.** Codex on the Mac renders the whole cover (art, title strips, `פרק N`
pill, show mark) in one pass, with the speaking host's real picked frame passed via
`-i`. `make_cover_title.py` over text-free Codex art is only the fallback when the
one-pass Hebrew is not exact after one targeted regenerate. Feed the prompt on stdin
(`-i` swallows a trailing prompt argument), upscale Codex's ~941×1672 output to
1080×1920 with ffmpeg, and name the result to the gate pattern
`שורט-NN-<נושא>-cover.jpg` ([prompts](prompts.md) → Codex backend).

## Layout (`shorts-vertical`, top to bottom)
- **Background:** navy textured paper.
- **Title:** two torn-paper strips inside the centre 1080×1080 square (y 420–1500), so 1:1
  and 4:5 grid crops keep it. Line 1 on cream, line 2 on mustard, overlapping slightly,
  tilted ±1–2° in opposite directions, rough torn edges with a white paper fringe and a
  soft shadow. Very heavy navy **Heebo Black**, filling the strip, both lines the same
  type size.
- **`פרק N` pill:** white torn-paper pill on the bottom edge of the mustard strip.
- **Host (`host` zone):** the speaking host from a picked frame of this episode (verified
  identity, [face picks](face-picks.md)), natural-color head-and-shoulders cutout over a
  large brand-mustard disc (never green), lower half. His face stays exactly as in the
  frame ([covers](covers.md) → What the face rule means).
- **Topic prop (optional, `hero` zone):** a small gold/cream engraved illustration of the
  topic beside him, subordinate to the face. No brand logos in the art.
- **Show mark bottom-right**, high contrast. No host-name strip, no show mark at the top.

Title = the Short config's shared `cover_title`: one short punchy idea, two lines,
ideally ≤14 characters a line. The cover, opening banner, YouTube title (the lines
joined with one space) and first description line all use it unchanged. No numbers or
claims that aren't in the clip; a necessary Latin name such as `CoreWeave` is allowed.

## Standing option rule (2026-10-22)
Until Amitai says the design is dialed in, every individual Short cover is delivered as
three clearly labeled Codex options A/B/C for him to choose from. This means three
options for each of the episode's three Shorts, not one option per Short.

## How to make it (Codex on Amitai's Mac only)
There is no box fallback: no Pillow compositing of faces, art or strips. Independent Codex renders (A/B/C for this Short, and other Shorts' covers) run as **parallel concurrent sessions** on the Mac, each in its own subfolder; sequential only when one depends on another (prompts → Codex backend). If Codex or the
Mac is unavailable, report the blocker (to the Producer when one runs the episode).

1. **Pick the face.** From the episode's verified face grids, take a picked frame of the
   host who speaks in this Short (a different frame per option where possible). Copy it
   into the Codex workdir.
2. **One-pass cover (the default).** Run [prompts](prompts.md) → Shorts
   cover art with the one-pass replacement and `-i` the host frame and style references
   (prompts → Codex backend). Codex draws the strips, title, pill and show mark.
3. **Verify the Hebrew exactly.** Read every letter at full size and ~200 px wide against
   `cover_title` in `short.json`: same letters, same order, `?` on the left, no
   brackets, no `؟`, no stray text. Then run
   `python3 scripts/check_cover.py COVER.jpg --kind shorts-vertical --config short.json`.
   Any mismatch: one targeted regenerate; if it is still wrong, go to step 4. Upscale a
   kept one-pass cover to the gate name:
   `ffmpeg -i raw.png -vf scale=1080:1920:flags=lanczos -q:v 2 "שורט-NN-<נושא>-cover.jpg"`.
4. **Fallback only (one-pass Hebrew still wrong): text-free Codex face art + Heebo title.** Run the same prompt text-free
   (with the host frame), then typeset the title:
   ```bash
   python3 scripts/make_cover_title.py ART-A.png "option-A/שורט-NN-<נושא>-cover.jpg" \
     --config short.json --pill "פרק N" \
     --font fonts/Heebo-Black.ttf --logo assets/logo-solid.png
   ```
   `--config` reads the same `cover_title` field as the Remotion banner; do not copy the
   lines into separate fields. It refuses a headline with characters that would render as
   tofu (U+061F, brackets, box characters, glyphs missing from the font), crops the art
   to 1080×1920 without stretching, keeps both lines the same size, places the pill and
   logo, and fails if the title would leave the centre square. Make sure the title strips
   don't cover the host's face.
5. **Check all three options** with
   `python3 scripts/check_cover.py "option-X/שורט-NN-<נושא>-cover.jpg" --kind shorts-vertical --config short.json`
   (palette: brand mustard present, no green), then by eye: the face is the right host
   and unaltered, title readable, pill not clipped, logo readable, nothing important
   outside the centre square. Label each option one-pass or typeset. Show the labeled set
   to the episode owner (through the Producer) and wait for their selection.
6. **Promote and check the selected option** with the same `check_cover.py` command,
   appending the output to `extras/cover-check.log`. Then file it next to its Short in
   the episode's Drive `Shorts/` folder (`investing-bros-show` → Drive tree, Shorts
   rule), then hand it to `investing-bros-shorts`.

The legacy video-frame cover (`make_cover.py` in `investing-bros-shorts`) is only for
rebuilding older Shorts.

## Done when
`שורט-NN-<נושא>-cover.jpg` (1080×1920 JPEG) sits next to its Short in `Shorts/` in the
face format, made by Codex on Amitai's Mac, with the exact Hebrew hook, the `פרק N`
pill and the bottom-right show mark, no name strip, and `check_cover.py --config` passes.
Until the design is dialed in, Amitai selected it from three clearly labeled Codex
options.
