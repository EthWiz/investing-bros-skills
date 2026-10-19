# Reusable image-generation prompts

Replace every placeholder before running. Treat each asset as a separate generation.
Read the available imagegen skill and inspect local references before referencing them.

## Base style block
Create a finished {FORMAT} artwork for Hebrew podcast אחים להשקעות in the selected
Financial Journal identity. Use the attached selected artwork as style reference.
Deep navy textured paper #09243B, warm cream #F5EBD5, printed mustard #D8A52E.
Rough torn-paper headline strips, subtle paper shadows, bold contemporary Hebrew
sans-serif, cream-and-navy engraved/halftone cutouts, controlled mustard accents.
One central subject, at most one supporting concept, generous navy breathing room.
No glossy cinematic scene, metallic text, neon palette, market charts or crowded
unrelated clippings. All Hebrew text exact and right-to-left. Preserve host credit
'עם אמתי ונדב רסקין'. אמתי has four letters א מ ת י; do not add another י.

## Main cover
{BASE_STYLE}
Large two-strip masthead: 'אחים' on cream, 'להשקעות' on mustard. Below: two inward-facing
midcentury chairs, one round table, two coffees and one folded newspaper, all as
engraved cutouts. One rough mustard backing disc. Exact host strip at bottom.
Follow assets/references/main-cover.png. No portraits, extra title or episode number.

## Episode cover
{BASE_STYLE}
Follow the {LAYOUT_ID} compositional specification. Compact show masthead at top.
Headline exact '{HEADLINE_LINE_1}' on cream and '{HEADLINE_LINE_2}' on mustard.
Number label exact 'פרק {EPISODE_NUMBER}'. Main visual: {HERO_AND_MEANING}.
Supporting detail, if useful: {SUPPORTING_DETAIL_OR_NONE}.
Host strip at bottom. Keep text/number hierarchy like episode-07-gold.png.
Do not reuse its gold ingot unless this episode is about gold.

## Tokenization digital treatment
Keep the intact left part of the certificate physical cream engraved paper. Transform
the right-hand detached pieces progressively into navy digital tiles with fine
mustard grids and recognizable certificate linework. Add a few square pixels and
short right-angle links. Subtle warm edge light is allowed only here. No cyan neon
or global holographic background. Use episode-06-tokenization-digital.png.

## Localized edit
Edit this EXACT selected image. Change ONLY {REQUESTED_CHANGE_AND_REGION}. Preserve
{INVARIANTS}, all other composition and text. Correct credit if explicitly requested
or known wrong: 'עם אמתי ונדב רסקין'. Do not redesign unrelated elements. Maintain
original aspect ratio and transparency unless the user asks otherwise.

## Other formats
{BASE_STYLE}
Create {SHORTS_COVER_OR_DISCUSSION_CARD_OR_LOWER_THIRD} using its normalized layout.
Exact text: {COPY}. Adapt illustration placement to this aspect ratio. Label this a
proposed format adaptation until reviewed. Do not merely stretch a square image.

## Example requests
- "Create episode 8 about electricity infrastructure" -> ask for the exact headline
  if absent, or offer clearly labeled options; illustrate one relevant object.
- "Make the tokenized pieces digital" -> use the exact selected image and digital
  treatment above; preserve every unrelated component.
- "Create a gold Short cover" -> use the gold reference and vertical layout, preserve
  supplied wording/episode number, recompose and check safe areas.
