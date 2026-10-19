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

## Delivery and typography
Target export sizes in JSON are production intentions. Inspect actual pixel dimensions
and disclose deviations. Never claim a generated 1254px file is a 3000px master. Upscaling
alone does not add detail. Keep reference images separate from final deliverables.
