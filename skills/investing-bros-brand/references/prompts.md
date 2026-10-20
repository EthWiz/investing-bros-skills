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
unrelated clippings. All Hebrew text exact and right-to-left. Where a format carries
the host credit, it is exactly 'עם אמיתי ונדב רסקין'. אמיתי has five letters א מ י ת י;
do not drop the middle י.

## Main cover
{BASE_STYLE}
Large two-strip masthead: 'אחים' on cream, 'להשקעות' on mustard. Below: two inward-facing
midcentury chairs, one round table, two coffees and one folded newspaper, all as
engraved cutouts. One rough mustard backing disc. Exact host strip at bottom.
Follow assets/references/main-cover.png. No portraits, extra title or episode number.

## Episode cover
{BASE_STYLE}
Square 1:1. Layout (top to bottom):
- Headline at the top, centred: exact '{HEADLINE_LINE_1}' on a large cream torn strip
  and '{HEADLINE_LINE_2}' on a large mustard torn strip, navy text, very large.
- Directly under it: small cream number tab exact 'פרק {EPISODE_NUMBER}'.
- Below: ONE BIG, dramatic, impactful main visual filling most of the lower area:
  {HERO_AND_MEANING}. Supporting detail, if useful: {SUPPORTING_DETAIL_OR_NONE}.
  Rough mustard backing disc allowed. NO folded newspaper or paper base under it.
- Bottom-RIGHT corner: compact show mark, 'אחים' on a small cream strip above
  'להשקעות' on a small mustard strip.
- NO host credit strip and no names. No other text, letters or numbers anywhere.
Keep strip/number hierarchy like episode-07-gold.png, but not its layout (masthead top,
newspaper, host strip are the pre-episode-3 structure). Do not reuse its gold ingot
unless this episode is about gold. A company wordmark (e.g. SPACEX with its X swoosh)
in the headline strip only when Amitai asks for it.
For the YouTube thumbnail, compose this square cover per layouts.md → Widescreen
YouTube thumbnail; do not generate a separate wide image.

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

## Vertical Shorts cover
Approved on episode 1 short 1. Unchanged by the episode 3 episode-cover rule (show mark
at top and host strip stay here until Amitai says otherwise). Attach the episode's approved square cover and
episode-07-gold.png as style references, named in the prompt by their file names.
{BASE_STYLE}
Vertical 9:16 Shorts / Reels cover, saved as {OUTPUT_NAME}. Match the attached
{EPISODE_COVER_FILE} (this episode's approved cover, same illustration style) and
episode-07-gold.png (the show's Financial Journal identity). One rough mustard
backing disc behind the subject, generous navy breathing room. No glossy cinematic
scene, no metallic or 3D text, no neon, no charts, no clutter.
Layout (top to bottom):
- Top: compact show mark, two small torn strips: 'אחים' on cream above 'להשקעות' on mustard.
- Headline in the upper-middle (keep it inside the centre square region of the frame
  so a 1:1 crop still shows it): line 1 exact '{HEADLINE_LINE_1}' on a cream torn
  strip, line 2 exact '{HEADLINE_LINE_2}' on a mustard torn strip. Large, very legible
  at thumbnail size.
- Middle: hero illustration — {HERO_AND_MEANING}, engraved mustard/cream halftone
  style like the reference. No brand logos.
- Below the hero: small cream pill label exact 'פרק {EPISODE_NUMBER}'.
- Bottom: small host strip exact 'עם אמיתי ונדב רסקין' on cream.
All Hebrew text must be exact, spelled exactly as given, right-to-left, no extra
words, letters or numbers anywhere else. Keep important text away from the right edge.

## Other formats
{BASE_STYLE}
Create {SHORTS_COVER_OR_DISCUSSION_CARD_OR_LOWER_THIRD} using its normalized layout.
Exact text: {COPY}. Adapt illustration placement to this aspect ratio. Label this a
proposed format adaptation until reviewed. Do not merely stretch a square image.

## Codex backend (Grokbot on Amitai's Mac)
When Grokbot makes artwork and Amitai's Mac (machine
566a74b2-614d-458f-be63-660743243124) is connected, run the prompt through Codex there
with the device shell (Shell with that machineId); otherwise use Grokbot's own image
tool with the same prompt. Codex uses Amitai's ChatGPT plan, never an API key.
1. Before a run, refresh the Mac's `~/.agents/skills` copies from this repo's `main`
   (Codex reads them), only after Amitai approves that exact command.
2. Workdir `/Users/amitairuskin/Pictures/investing-bros/episode-<N>/short-<NN>/` (or
   `episode-<N>/cover/` for the square cover). Put the references there
   (`ref-episode-<N>-cover.png` and `ref-episode-07-gold.png`, from this skill's
   assets) and the filled prompt as `prompt.txt`. CopyToBox/CopyFromBox need
   absolute `/Users/amitairuskin/...` paths; `~` is not expanded.
3. Start the prompt with `Use $imagegen to create`, put the square-crop rule first,
   then the template above, and add: "Output will be upscaled to 1080x1920 afterwards;
   do not resize. Write your final image_gen prompt to <name>-prompt.txt and copy the
   final PNG into this folder. After saving, check every Hebrew word is spelled exactly
   as above and there is no stray text; if wrong, regenerate or edit once. Report the
   final file name and pixel size (sips)."
4. Run, allowing about 5 minutes (Shell `block_until_ms` ≥ 600000):
   ```bash
   cd <workdir> && env -u OPENAI_API_KEY ~/.nvm/versions/node/v22.23.1/bin/codex exec \
     --skip-git-repo-check -i ref-episode-<N>-cover.png -i ref-episode-07-gold.png \
     -- "$(cat prompt.txt)" < /dev/null > codex.log 2>&1
   ```
   `env -u OPENAI_API_KEY` keeps billing on the ChatGPT plan. `--skip-git-repo-check`
   is needed outside a trusted folder. `-i` takes several values, so `--` must come
   before the prompt or Codex fails with "a value is required for '--image'".
   Never print or copy `~/.codex/auth.json`. Verified with codex-cli 0.163.0.
5. Built-in `$imagegen` is gpt-image-2 (per OpenAI docs) with no model, quality or
   size control: it picks the size (square 1254×1254, 9:16 941×1672). Copy the PNG to
   the box and upscale there:
   `ffmpeg -i in.png -vf scale=1080:1920:flags=lanczos out.png`. Check the centre 1:1
   crop (`-vf crop=1080:1080:0:420`) still shows the headline, then run the quality
   checks. A square episode cover uses the same steps at 1:1 (drop the 1080x1920
   upscale line and the crop check; disclose the real size, per layouts).
Delivery stays under this skill's rules: nothing is published or sent without Amitai's OK.

## Example requests
- "Create episode 8 about electricity infrastructure" -> ask for the exact headline
  if absent, or offer clearly labeled options; illustrate one relevant object.
- "Make the tokenized pieces digital" -> use the exact selected image and digital
  treatment above; preserve every unrelated component.
- "Create a gold Short cover" -> use the gold reference and vertical layout, preserve
  supplied wording/episode number, recompose and check safe areas.
- "Make a cover for episode 1 short 1" -> Vertical Shorts cover with headline
  'למה לסייברקאב' / 'אין הגה?' and hero: the interior of a two-seat robotaxi (Tesla
  Cybercab-style futuristic two-door car), seen so it is obvious there is NO steering
  wheel and NO pedals, just two seats.
