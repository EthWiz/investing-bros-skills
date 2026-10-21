# Layout templates

Use `assets/templates/layouts.json` as normalized compositional templates. Bounds are
[x, y, width, height] from the TOP LEFT, in fractions of the full canvas. Zones are
planning guides, not masks to crop existing art. Recompose for each aspect ratio.

## Square show cover
Show masthead dominates upper region, two-chair illustration below, host strip at foot.
Keep the name legible at 160px. Background/texture may bleed, important text may not.

## Square episode cover
Two torn headline strips at the top (cream, then mustard), a small cream `פרק N` tab
under them, then ONE big, impactful subject illustration filling most of the lower
area (rough mustard backing disc allowed). The compact two-strip show mark
(`אחים` cream / `להשקעות` mustard) sits in the BOTTOM-RIGHT corner. No host credit
strip and no folded-newspaper prop under the subject (Amitai, 2026-10-20, episode 3).
Allow longer titles to occupy the title zone with two or three lines. Shorten only
with user authorization; never silently rewrite supplied copy. Covers made before
episode 3 (masthead top, newspaper base, host strip) are the older structure; reuse
their palette, strips and engraving, not that layout. Reference:
`episode-3/promo/cover-פרק-3-v3.png` once approved.

A company name may appear in its own wordmark style (e.g. SPACEX with the X swoosh)
in the headline strip ONLY when Amitai asks for it; otherwise no brand logos.

## Widescreen YouTube thumbnail (approved, episode 1 and 3)
Do not recompose a wide layout. Make the square episode cover first, then centre it
at 720×720 on a blurred, darkened stretch of itself (as `episode-1/promo/youtube-thumbnail-פרק-1.jpg`):
```bash
ffmpeg -i cover-פרק-N.png -filter_complex \
  "[0]scale=1280:1280,crop=1280:720,boxblur=30:3,eq=brightness=-0.25[bg];[0]scale=720:720:flags=lanczos[fg];[bg][fg]overlay=280:0" \
  -q:v 2 promo/thumbnail-פרק-N.jpg
```
A headline-right / illustration-left wide composition (the old proposed adaptation)
was rejected for episode 3 as not the regular cover structure.

## Vertical Shorts covers (two required styles)
For every new Short, produce both the existing illustrated cover and the real-frame
speaker cover. Read [Shorts cover specifications](shorts-covers.md) for both layouts,
source-frame selection, host alternation and QA. Preserve an existing series' chosen
illustrated layout; its new photographic partner uses the actual video background,
top-left logo, two torn headline strips and a centred torn episode tab below them.
Use `shorts-real-frame` in the JSON for photographic composition guides. The old
`shorts-vertical` entry describes the earlier illustrated adaptation only.

## Discussion card (proposed adaptation)
Small masthead, one short question and a restrained subject detail. A discussion
question needs no quotation marks or attribution. Only use quotes from a supplied
transcript with verified speaker and wording.

## Lower third (proposed adaptation)
Navy-and-cream torn-paper name strip with a small mustard show strip. Use one exact
host name. Provide a transparent version if requested; no portrait or invented video
frame. Generate paper texture with imagegen, then use appropriate existing text/layout
tools for deterministic type when available. This package is not a rendering script.

## Full-frame episode teaser (approved production layout)
This is the default 16:9 cold open. Keep the active speaker full-frame at about 1.2×,
with no side panel or split screen. Put the solid torn-paper logo at top-left, the
gold `פרק N` and white episode name at top-right, and word-by-word captions over a
soft feathered blurred lower-third band. The current word is gold; the others are
white. Use Heebo Black for the title block and Heebo ExtraBold for captions.

Do not add a speaker name, underline, hairline or hard caption box. Dip to black
between moments. Exact production coordinates, type sizes and colors are in
`assets/templates/layouts.json`; `investing-bros-video` owns the renderer and its
portable per-episode config.

## Delivery and typography
Target export sizes in JSON are production intentions. Inspect actual pixel dimensions
and disclose deviations. Never claim a generated 1254px file is a 3000px master. Upscaling
alone does not add detail. Keep reference images separate from final deliverables.

## Shorts video hook (approved production layout)
The first 2.7 s of every full-bleed Short: the hook as two torn-paper strips, cream line 1
above mustard line 2, navy Heebo Black at about 108 px (line 2 ~10% larger), a soft navy
paper shadow, fading out over 0.2 s. **Brief hook → centre of the frame:** centred
horizontally with its block centred around y 960 on 1920 (allowed 300–1000), at least
40 px clear below the logo's bottom edge (y 277) and above the caption line. Covering the
face for those 2.7 s is accepted. Captions sit at centre y 1100–1470, just under the chin.
`investing-bros-shorts` renders it (`brand.hook_strips`, `build_fullbleed.py`); the
exact constants are in `brand.py` (`HOOK_STRIPS`, `HOOK_Y_BOUNDS`, `CAPTION_Y_BOUNDS`).

