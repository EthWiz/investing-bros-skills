# Brand history

Why the rules are what they are. Background only: the rules themselves are in the other
files, and a later decision here overrides an earlier one.

## Identity
- Theme 02 ("Financial Journal") was selected from the first round, refined, then
  documented as this skill. Selection never implied approval to publish.
- The main cover was corrected once: use `main-cover.png`, not the earlier version with an
  extra yod in the host credit.
- Established episode headlines: 7 `למה דווקא זהב?`, 6 `וול סטריט עוברת לבלוקצ׳יין`,
  4 `מלחמת העננים`.
- 2026-10-19: the Shorts hook and captions were split into print (torn strips) and screen
  (white captions, gold current word) treatments.
- 2026-10-22: Heebo confirmed as the only typeface. The separate
  `investing-bros-short-covers` skill (legacy type and its own palette) was folded into
  this skill.
- 2026-10-22: reference images moved from the repo to Drive `Brand Resources/references`,
  fetched by file ID.

## Episode and segment covers
- Episode 3: the host-name strip came off episode covers.
- Episode 8: options A/B/C were rejected as too loud and v3a/v3b as too calm. That
  set the "elegant but engaging" taste rule. Episode 8 is also a good portrait source
  (`host-amitai-ep08.png` 00:04.2 and `host-nadav-ep08.png` 00:21.5, from the
  [episode-8 teaser](https://drive.google.com/file/d/1RKKMZRVuoEyMLxGtzhvJU3a1EmZmE0yz/view),
  extracted without facial edits).
- `episode-08-photo-cutouts.png` was the first photo-cutout exploration, superseded by
  the coin and facade selections.
- 2026-10-22: Amitai selected the gold-coin option (also supplied as
  `2451FCCC-0E48-4E80-89D3-40E130D218EA.jpeg`) and an S&P 500 combination: Amitai's
  portrait from the certificate option on the left, Nadav's from the facade option on the
  right, with the facade centerpiece. Do not substitute the earlier facade variant. Bell,
  certificate, vault, monochrome and duotone variants were not selected.
- 2026-10-22: widescreen thumbnails stopped being the square cover centred on a blurred
  stretch; they are composed directly for 16:9. Older covers keep their old export.
- Designed portrait covers in Drive `references/shorts-thumbnails` are not verified camera
  originals; never infer identity from them.

## Shorts covers
- Episode 1, Short 1 (Cybercab, `מי ינצח` / `במרוץ הרובוטקסי?`) was the first approved
  cover; `shorts-title-strips-ep1.png` is its title.
- Covers were made with the Codex CLI on Amitai's Mac from episode 1; the episode-3 Short
  used generated art plus a legacy torn-strip overlay with a host strip and a bottom-left
  logo. New and rebuilt text uses Heebo only.
- 2026-10-21: Amitai removed the host-name strip from Shorts covers and moved the show
  mark bottom-right.

## Renderers
Existing video and Shorts renderers keep the screen gold and the deployed wordmark. Brand
changes don't silently recolour them: change the shared `brand.py` copies together, render
a sample and get it approved first.

## Episode 9 (2026-10-29)
- Amitai set the per-episode face-pick loop ([face picks](face-picks.md)): about ten
  best-effort stills per speaker, he picks the ones he wants and rejects the rest with
  a reason, and each episode's choices are kept as eval labels
  (`evals/face-picks/episodes/ep09.json` is the first). Thumbnails use only real frames
  he picked; no image generation on real faces.
- The same episode's editing and upload lessons (single-pass cuts with measured sync,
  the compressed YouTube copy, verified links, one approval message) live in
  `investing-bros-video` and `investing-bros-episode-upload`.
