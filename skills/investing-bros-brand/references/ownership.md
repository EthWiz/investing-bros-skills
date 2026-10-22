# Ownership and asset lifecycle

## Single source of truth
- `investing-bros-show`: names, show facts, episode folders, approval/publication rules.
- `investing-bros-brand`: design rules, source templates, reference examples, prompt
  templates, artwork generation/editing and visual QA for every format.
- `investing-bros-title-description`: episode titles, thumbnail headline options,
  descriptions and chapters. Hand approved copy to brand; do not create visual rules.
- `investing-bros-video`: video edit, audio, captions and compositing; obtain graphic
  assets and visual specifications from brand.
- `investing-bros-segment-video`: segment selection, video production and delivery;
  consume the shared photo-cutout rules from brand without duplicating visual guidance.
- `investing-bros-shorts`: clip selection and vertical-video production; request Shorts
  covers and graphics from brand, then apply approved assets in its render pipeline.
  Shorts covers are made here ([Shorts covers](shorts-covers.md)); there is no separate
  cover skill.

## Handoff
Copy supplies: topic, episode number, approved headline, relevant transcript context.
Brand supplies: artwork, actual format/dimensions, review status and source references.
Video/Shorts supply: required placement, safe regions, duration/transparency needs.
Brand returns the appropriate assets. No task silently redefines the global palette.

## Files and versioning
GitHub holds rules, templates and the reference index. The curated reference images live
in Drive `Brand Resources/references/` (see the asset index); finished per-episode
outputs live in the episode's Drive folders defined by investing-bros-show. Do not
commit reference images or generated variations to Git. Reference images are not production masters.
Record artwork in `extras/artwork-register.json` for the episode (`check_cover.py --register`
reads it), using the example shape in
`assets/templates/artifact-register.example.json`. Reuse an existing register. Record
actual paths/URLs and dimensions, never guesses. Include per-host original sources,
timestamps, identity/side, touch-ups and reuse; record exact component origins for mixed
selections. Mark missing optional data null.
Use versioned draft filenames. Promote a version to the final delivery filename only
once review is explicit; retain the previous version rather than overwriting silently.
Do not treat visual approval as permission to publish or message anyone.

## Status
- draft: generated, not yet reviewed.
- reviewed: visual and text QA completed, ready for user review.
- approved: explicitly accepted by the user; record the approval reference.
- published: deployment confirmed separately under show publishing rules.
- superseded: retained historical version, not the default reference.
Selected working references indexed here define the direction, but do not imply that
final files, dimensions or new formats are approved. Heebo is the approved typeface.

## Promotion and change control
Update the single reference index when a better example is selected. Keep the newest
user-selected tokenization digital-fragment treatment as canonical for that subject.
Propose broad visual changes as a PR with before/after examples. Update consumers by
reference rather than copying palette and layout prose. GitHub becomes canonical once
merged; refresh ChatGPT/Claude/Grokbot installations from the merged version.

## Existing renderers
Video and Shorts renderers keep the screen gold and the deployed wordmark. Change the
shared `brand.py` copies together, render a sample and get it approved before migrating
them. Proposed format specifications are not implemented renderers; say so in handoffs.
