# Layout templates

Use `assets/templates/layouts.json` as normalized compositional templates. Bounds are
[x, y, width, height] from the TOP LEFT, in fractions of the full canvas. Zones are
planning guides, not masks to crop existing art. Recompose for each aspect ratio.

## Square show cover
Show masthead dominates upper region, two-chair illustration below, host strip at foot.
Keep the name legible at 160px. Background/texture may bleed, important text may not.

## Square episode cover
Top compact two-line show masthead, two torn headline strips, small number tab, one
central illustration and bottom host strip. Allow longer titles to occupy the title
zone with two or three lines. Shorten only with user authorization; never silently
rewrite supplied copy. Match selected reference proportions before chasing coordinates.

## Widescreen thumbnail (proposed adaptation)
Keep a compact show mark at top, large torn-paper headline on the RIGHT, illustration
on the LEFT and small number/host credit along the bottom. Make the headline/subject
read at small size. Never squeeze the entire square cover into a wide frame. Keep
critical copy away from the bottom-right playback overlay area. This is a design
convention, not a guarantee of platform UI behavior.

## Vertical Shorts cover (proposed adaptation)
Compact show mark above a short question, large central topic illustration and number.
Keep essential elements in the central area with generous top/bottom clearance.
Use real video frames only if supplied or sourced with authorization. Do not invent
host faces. Preview in the target platform before locking placement.

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

