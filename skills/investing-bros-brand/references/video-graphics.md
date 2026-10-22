# Video graphics, cards and lower thirds

Layouts for graphics that appear inside videos. `investing-bros-video` and
`investing-bros-shorts` own the renderers; exact coordinates, sizes and colours are in
`assets/templates/layouts.json` and the constants in their `brand.py`.

## Full-frame episode teaser (approved production layout, `teaser-fullframe`)
The default 16:9 cold open. The active speaker full-frame at about 1.2×, no side panel or
split screen. Solid torn-paper logo top-left; gold `פרק N` and white episode name
top-right; word-by-word captions over a soft feathered blurred lower-third band, current
word gold, others white. Heebo Black for the title block, Heebo ExtraBold for captions.
No speaker name, underline, hairline or hard caption box. Dip to black between moments.

## Shorts video hook (approved production layout, `shorts-video-hook`)
The first 2.7 s of every full-bleed Short: the hook as two torn-paper strips, cream line 1
over mustard line 2, navy Heebo Black at about 108 px (line 2 ~10% larger), a soft navy
paper shadow, fading out over 0.2 s. Centred horizontally, block centred around y 960 on
1920 (allowed 300–1000), at least 40 px clear below the logo (bottom y 277) and above the
captions. Covering the face for those 2.7 s is accepted. Captions sit at centre y
1100–1470, just under the chin. Rendered by `investing-bros-shorts`
(`brand.hook_strips`, `build_fullbleed.py`; constants `HOOK_STRIPS`, `HOOK_Y_BOUNDS`,
`CAPTION_Y_BOUNDS`).

**Hook vs captions:** never the same treatment. The hook is print (the strips above);
captions stay the screen style: white Heebo with the current word in `#F5B71F`. Hooks
are as short as possible: one idea, ideally six words or fewer, two lines
(`למה לסייברקאב` / `אין הגה?`). The Short's cover uses the same two-strip title.

## Discussion card (proposed adaptation, `discussion-square`)
Small masthead, one short question and a restrained subject detail. A discussion question
needs no quotation marks or attribution. Quote only from a supplied transcript with a
verified speaker and wording.

## Lower third (proposed adaptation, `lower-third`)
Navy-and-cream torn-paper name strip with a small mustard show strip. One exact host
name. Transparent version on request; no portrait or invented video frame. Generate the
paper texture, then set the name in Heebo with a deterministic tool.

## Motion and sound direction
Paper slides, gentle settling and restrained cuts; type readable on the final hold.
Subtle paper sounds and a warm understated instrumental sting. This skill contains no
licensed music, soundtrack or video template; don't claim those exist.

Proposed adaptations are specifications, not implemented renderers: label them as
proposed until reviewed, and preview in the target platform before locking placement.
