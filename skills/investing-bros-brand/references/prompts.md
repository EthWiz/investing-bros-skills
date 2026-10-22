# Reusable image-generation prompts

Replace every placeholder before running. Treat each asset as a separate generation.
Read the available imagegen skill. Download each reference from Drive by the ID in the
[asset index](asset-index.md) and inspect it before attaching it.

## Base style block
Create a finished {FORMAT} artwork for Hebrew podcast אחים להשקעות in the selected
Financial Journal identity. Use the attached selected artwork as style reference.
Deep navy textured paper #09243B, warm cream #F5EBD5, printed mustard #D8A52E.
Rough torn-paper headline strips, subtle paper shadows, bold contemporary Hebrew
sans-serif, cream-and-navy engraved/halftone cutouts, controlled mustard accents.
One central subject, at most one supporting concept, generous navy breathing room.
No glossy cinematic scene, metallic text, neon palette, market charts or crowded
unrelated clippings. All Hebrew text exact and right-to-left. Where a format carries
the host credit, it is exactly 'עם אמיתי ונדב רסקין'. אמיתי has five letters א מ י ת י;
do not drop the middle י.

## Main cover
{BASE_STYLE}
Large two-strip masthead: 'אחים' on cream, 'להשקעות' on mustard. Below: two inward-facing
midcentury chairs, one round table, two coffees and one folded newspaper, all as
engraved cutouts. One rough mustard backing disc. Exact host strip at bottom.
Follow main-cover.png (Drive reference, see the asset index). No portraits, extra title or episode number.

## Photo-cutout thumbnail: segments and main episodes
Read [covers](covers.md) and inspect both selected references.
Use this complete prompt, not the illustration-oriented base style block above.

Create option {OPTION_LABEL} of three clearly labeled A/B/C options for one finished
16:9 {SEGMENT_OR_MAIN_EPISODE} thumbnail for אחים להשקעות.
The option label belongs in the output filename and review presentation, not in the art.
Input 1: {AMITAI_ORIGINAL_SOURCE}, Amitai portrait frame from episode {EPISODE_NUMBER},
LEFT.
Input 2: {NADAV_ORIGINAL_SOURCE}, Nadav portrait frame from episode {EPISODE_NUMBER},
RIGHT.
Input 3: {SELECTED_COIN_OR_FACADE_REFERENCE}, layout and brand reference only.
Both portraits must come from this same episode's recording; they may come from any
point in the episode and, for a segment, need not come from the segment itself. Never
substitute a photo or frame from another episode.
Use exactly one of each distinct brother. Preserve their separate facial structure,
age, hairlines, beard and eye shape. Use the fresh source frames rather than recycling
reference-cover faces. Remove room backgrounds and video overlays. Natural-color,
photographic head-and-shoulder cutouts, clean edges and comparable face scale.
Light touch-ups only: {ALLOWED_TOUCHUPS_OR_NONE}. Keep pores and natural expressions;
no facial reshaping, duplicated faces, exaggerated emotion, strong filters or plastic skin.
Deep navy textured paper #09243B, cream #F5EBD5 and mustard #D8A52E graphic palette.
Center exact '{HEADLINE_LINE_1}' on cream torn paper and exact '{HEADLINE_LINE_2}'
on mustard torn paper, heavy navy Hebrew lettering. Correct RTL Hebrew and LTR ticker.
Keep faces and headline dominant, with navy breathing room and a restrained mustard disc.
Below the headline between shoulders, one polished photographic centerpiece:
{TOPIC_IMAGE_AND_MEANING}. Realistic material detail, soft light and restrained shadow;
no cheap clip art, cartoon rays, fake financial data or unrelated decorations.
{NUMBER_RULE}
Compact bottom-right show mark: 'אחים' on cream above 'להשקעות' on mustard, clear
of chin and duration badge. No host names, blurred padding, neon or metallic headline.
Target {WIDTH}×{HEIGHT}; inspect actual output dimensions and faces afterward.

Fill NUMBER_RULE with 'No episode number or badge' for segments. For a main episode,
use a small supplied 'פרק {EPISODE_NUMBER}' tab below the title, clear of the centerpiece.
Use the topic + short question for segment copy; use approved episode copy for episodes.
Run the prompt separately for A, B and C through the Codex backend, with meaningfully
different portraits and centerpieces while keeping the fixed visual system.
For localized mixed selections, use the edit prompt below and list exact source/side
for each selected portrait and centerpiece. Do not invent another pose during that edit.

## Main episode square cover
Use the same sources and exact copy as the thumbnail prompt. Change the format to 1:1
and recompose per [covers](covers.md): headline strips at top,
number below, both portraits lower, one subordinate topic image if it fits, mustard disc
and bottom-right show mark. Preserve both faces and every letter; do not crop or
squeeze the wide image. Target 3000×3000; disclose the actual output size.

## Tokenization digital treatment
Keep the intact left part of the certificate physical cream engraved paper. Transform
the right-hand detached pieces progressively into navy digital tiles with fine
mustard grids and recognizable certificate linework. Add a few square pixels and
short right-angle links. Subtle warm edge light is allowed only here. No cyan neon
or global holographic background. Use episode-06-tokenization-digital.png.

## Localized edit
Edit this EXACT selected image. Change ONLY {REQUESTED_CHANGE_AND_REGION}. Preserve
{INVARIANTS}, all other composition and text. Correct credit if explicitly requested
or known wrong: 'עם אמיתי ונדב רסקין'. Do not redesign unrelated elements. Maintain
original aspect ratio and transparency unless the user asks otherwise.

## Shorts cover art (text-free)
Rules and the typesetting step: [Shorts covers](shorts-covers.md). Attach this episode's
approved cover and episode-07-gold.png as style references, named in the prompt. This
prompt is complete on its own; don't add the base style block, which asks for text.

Create vertical 9:16 Shorts cover artwork for Hebrew podcast אחים להשקעות, saved as
{OUTPUT_NAME}, option {OPTION_LABEL} of three clearly labeled A/B/C options for this
Short. The option label belongs in the output filename and review presentation, not in
the art. NO text, letters, numbers, strips, labels or logos anywhere: the title is
typeset afterwards. Match the illustration style of the attached {EPISODE_COVER_FILE} and
episode-07-gold.png (Financial Journal identity). Deep navy textured paper #09243B with
subtle grain. Centre and lower half: {HERO_AND_MEANING}, one gold and cream #F5EBD5
engraved, line-hatched illustration over a large rough printed-mustard #D8A52E disc.
Leave the top half above the disc empty navy for a two-line title and keep the
bottom-right corner empty for the show mark. One subject, generous breathing room; no
glossy cinematic scene, metallic shine, neon, charts or clutter.

For a one-pass cover (Codex, when Hebrew comes out right), replace the NO-text sentence with:
title line 1 exact '{HEADLINE_LINE_1}' on a cream torn strip and line 2 exact
'{HEADLINE_LINE_2}' on a mustard torn strip, heavy navy sans-serif, inside the centre
square of the frame; a small white torn pill exact 'פרק {EPISODE_NUMBER}' on the bottom
edge of the mustard strip; compact show mark bottom-right ('אחים' on cream above
'להשקעות' on mustard). No host names. All Hebrew exact and right-to-left.

## Other formats
{BASE_STYLE}
Create {DISCUSSION_CARD_OR_LOWER_THIRD} using its layout in [video graphics](video-graphics.md).
Exact text: {COPY}. Adapt illustration placement to this aspect ratio. Label this a
proposed format adaptation until reviewed. Do not merely stretch a square image.

## Codex backend (Grokbot on Amitai's Mac)
Until Amitai says the design is dialed in, every main-episode, segment and individual
Short cover is generated as three labeled options A/B/C through Codex on Amitai's Mac
(machine 566a74b2-614d-458f-be63-660743243124) with the device shell (Shell with that
machineId). If that backend is unavailable, report the blocker; do not switch generators.
For non-cover artwork, Grokbot may use its own image tool with the same prompt when the
Mac is unavailable. Codex uses Amitai's ChatGPT plan, never an API key.
1. Before a run, refresh the Mac's `~/.agents/skills` copies from this repo's `main`
   (Codex reads them), only after Amitai approves that exact command.
2. Workdir `/Users/amitairuskin/Pictures/investing-bros/episode-<N>/short-<NN>/`,
   `episode-<N>/cover/` for main-episode artwork, or
   `episode-<N>/segment-<NN>/` for segment artwork. Put the relevant references there
   (for main episodes and segments: the selected photo-cutout reference plus original
   host frames from episode N; for illustrated Shorts: the episode and gold style
   references) and the filled prompt as `prompt-{a|b|c}.txt`. CopyToBox/CopyFromBox need
   absolute `/Users/amitairuskin/...` paths; `~` is not expanded.
3. For Shorts, start the prompt with `Use $imagegen to create`, then the Shorts cover art
   template above, and add: "Output will be upscaled to 1080x1920 afterwards;
   do not resize. Write your final image_gen prompt to <name>-prompt.txt and copy the
   final PNG into this folder. After saving, check there is no stray text (or, for a
   one-pass cover, every Hebrew word exactly as above); if wrong, regenerate or edit once.
   Report the final file name and pixel size (sips)." Typeset the title on the box with
   `make_cover_title.py`, which also brings the art to 1080×1920.
4. Run, allowing about 5 minutes (Shell `block_until_ms` ≥ 600000):
   ```bash
   cd <workdir> && env -u OPENAI_API_KEY ~/.nvm/versions/node/v22.23.1/bin/codex exec \
     --skip-git-repo-check -i ref-episode-<N>-cover.png -i ref-episode-07-gold.png \
     -- "$(cat prompt-a.txt)" < /dev/null > codex-a.log 2>&1
   ```
   Repeat with the B and C prompt and log names. Replace the example Shorts reference
   arguments with the matching style reference and both same-episode host frames for a
   photo-cutout cover.
   `env -u OPENAI_API_KEY` keeps billing on the ChatGPT plan. `--skip-git-repo-check`
   is needed outside a trusted folder. `-i` takes several values, so `--` must come
   before the prompt or Codex fails with "a value is required for '--image'".
   Never print or copy `~/.codex/auth.json`. Verified with codex-cli 0.163.0.
5. Built-in `$imagegen` is gpt-image-2 (per OpenAI docs) with no model, quality or
   size control: it picks the size (square 1254×1254, 9:16 941×1672). Copy the PNG to
   the box. Text-free Shorts art goes straight into `make_cover_title.py`. A one-pass
   Shorts cover is upscaled there
   (`ffmpeg -i in.png -vf scale=1080:1920:flags=lanczos out.jpg`); check the centre 1:1
   crop (`-vf crop=1080:1080:0:420`) still shows the title. Then run `check_cover.py`
   and the quality checks.
For main episodes and segments, use the photo-cutout prompts and their source image
arguments, skip the Shorts steps, and inspect the real dimensions and both faces in each
ratio; disclose the real size ([covers](covers.md) → Delivery checks). For every cover
type, repeat the run for labeled options A, B and C and wait for Amitai's pick before
promoting a final filename.
Delivery stays under this skill's rules: nothing is published or sent without Amitai's OK.

## Example requests
- "Create episode 8 about electricity infrastructure" -> ask for the exact headline
  if absent, or offer clearly labeled options; use both host photos in the main-episode layout.
- "Make the tokenized pieces digital" -> use the exact selected image and digital
  treatment above; preserve every unrelated component.
- "Make a cover for episode 1 short 1" -> Shorts cover art with hero: the interior of a
  two-seat robotaxi (Cybercab-style futuristic two-door car), seen so it is obvious there
  is NO steering wheel and NO pedals, just two seats; then `make_cover_title.py` with
  'מי ינצח' / 'במרוץ הרובוטקסי?' and 'פרק 1'.
