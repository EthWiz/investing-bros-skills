# Shorts covers (vertical 1080×1920)

The image Reels, Shorts and TikTok show before play and in the profile grid. One cover
per Short; `investing-bros-shorts` asks for it and uses it as `-cover.jpg` and as the
YouTube custom thumbnail. Approved style: Amitai's "cut newspaper" title over an
engraved topic illustration. Reference: `shorts-title-strips-ep1.png` (Drive
`references/covers`, ID in the [asset index](asset-index.md)).

## Layout (`shorts-vertical`, top to bottom)
- **Background:** navy textured paper.
- **Title:** two torn-paper strips inside the centre 1080×1080 square (y 420–1500), so 1:1
  and 4:5 grid crops keep it. Line 1 on cream, line 2 on mustard, overlapping slightly,
  tilted ±1–2° in opposite directions, rough torn edges with a white paper fringe and a
  soft shadow. Very heavy navy **Heebo Black**, filling the strip, both lines the same
  type size.
- **`פרק N` pill:** white torn-paper pill on the bottom edge of the mustard strip.
- **Illustration:** one gold/cream engraved (line-hatched) illustration of the Short's
  topic over a large mustard disc, centre and lower half. No brand logos in the art.
- **Show mark bottom-right**, high contrast. No host-name strip, no show mark at the top.

Title = the Short's hook, the same faithful paraphrase as its on-screen hook: one idea,
two lines, ideally ≤14 characters a line. No numbers that aren't in the clip.

## How to make it
1. **Generate the art text-free with Codex on Amitai's Mac** (prompt: [prompts](prompts.md)
   → Shorts cover art, run through prompts → Codex backend): vertical 9:16, navy textured
   paper, engraved illustration of the topic over a mustard disc, empty top half for the
   title, empty bottom-right corner, no text, letters or logos. The three standing Shorts
   of an episode need Codex art (`investing-bros-shorts`); if Codex is unavailable, report
   the blocker instead of switching generator. Image models misspell Hebrew; never keep
   generated text.
2. **Typeset the title with Heebo:**
   ```bash
   python3 scripts/make_cover_title.py ART.png "שורט-NN-<נושא>-cover.jpg" \
     --line1 "מי ינצח" --line2 "במרוץ הרובוטקסי?" --pill "פרק 1" \
     --font fonts/Heebo-Black.ttf --logo assets/logo-solid.png
   ```
   It crops the art to 1080×1920 without stretching, keeps both lines the same size, puts
   the pill and the logo in place, and fails if the title would leave the centre square.
3. **Check:** `python3 scripts/check_cover.py "שורט-NN-<נושא>-cover.jpg" --kind shorts-vertical`,
   then look at it full size and at ~200 px wide: title readable, `?` on the left, pill not
   clipped, logo readable, nothing important outside the centre square.
4. **File it** next to its Short in the episode's Drive `Shorts/` folder
   (`investing-bros-show` → Drive tree, Shorts rule), then hand it to `investing-bros-shorts`.

A whole cover generated in one pass by Codex ([prompts](prompts.md) → one-pass cover) is
acceptable when every Hebrew letter checks out at full and thumbnail size; otherwise redo
the text with step 2. The legacy video-frame cover (`make_cover.py`
in `investing-bros-shorts`) is only for rebuilding older Shorts.

## Done when
`שורט-NN-<נושא>-cover.jpg` (1080×1920 JPEG) sits next to its Short in `Shorts/` with the
exact Hebrew hook, the `פרק N` pill and the bottom-right show mark, no name strip, and
`check_cover.py` passes.
