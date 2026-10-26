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

## Shorts opening banner (approved production layout, `shorts-video-hook`)
The first 3 s of every new Remotion Short: the config's exact shared `cover_title` as
two torn-paper strips matching the cover, cream line 1 over mustard line 2, navy Heebo
Black at about 96 px, with a soft navy paper shadow and a 0.3 s fade ending at 3.0 s.
The block starts around y 700. Covering the face briefly is accepted. Never substitute
a longer, number-heavy hook. The same field supplies the cover, YouTube title and first
description line. Legacy full-bleed rebuilds keep their deployed coordinates.

**Banner vs captions:** never the same treatment. The banner is print (the strips
above); current kinetic captions use a moving navy active-word box (gold for a keyword
or number), one 78–135 px emphasis word and ~64 px secondary words. Mixed
Hebrew/Latin/numbers use bidi isolation. Titles are one idea, ideally six words or
fewer, in two lines.

## Discussion card (proposed adaptation, `discussion-square`)
Small masthead, one short question and a restrained subject detail. A discussion question
needs no quotation marks or attribution. Quote only from a supplied transcript with a
verified speaker and wording.

## Lower third (proposed adaptation, `lower-third`)
Navy-and-cream torn-paper name strip with a small mustard show strip. One exact host
name. Transparent version on request; no portrait or invented video frame. Generate the
paper texture, then set the name in Heebo with a deterministic tool.

## Full-episode outro callout
The canonical clip and its Drive ID live in `investing-bros-show`. YouTube's previous-
episode and Subscribe elements sit over its final 20 seconds. An on-video callout is
optional; when a build includes one, set `פרקים קודמים` in Heebo only, using the
navy/cream/mustard paper language, and keep it clear of the clickable end-screen
elements. Standalone segment videos do not use this outro.

## Motion and sound direction
Paper slides, gentle settling and restrained cuts; type readable on the final hold.
Subtle paper sounds and a warm understated instrumental sting. This skill contains no
licensed music, soundtrack or video template; don't claim those exist.

Proposed adaptations are specifications, not implemented renderers: label them as
proposed until reviewed, and preview in the target platform before locking placement.
