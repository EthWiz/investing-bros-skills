# Two cover styles for every Short

Create two distinct 1080×1920 JPEG covers per Short by default: the existing
illustrated Financial Journal cover and a real-frame speaker cover. Keep the same
topic, episode number and faithful hook across the pair. A request to revise just
one existing cover does not require regenerating its partner. Follow
`investing-bros-show` for filenames and `investing-bros-shorts` for delivery.

## A. Existing illustrated style

Retain the existing illustrated workflow and the selected reference for the series.
For the cut-newspaper variant, inspect
`assets/references/shorts-illustrated-example.png` for headline treatment only
(the bundled image is a 1280×505 crop, not a full vertical cover):

- Navy textured paper background; one topic-relevant gold/engraved illustration
  over a mustard sun in the centre/lower half.
- Upper-third headline on overlapping cream and mustard torn-paper strips, heavy
  navy type, tight padding, subtle opposite tilts, paper fibres and soft shadow.
- Small cream `פרק N` tab on the lower edge of the mustard headline strip.
- No host-credit strip (removed Oct 2026); show logo bottom-right.
- Keep the headline and episode label inside the central square for grid crops.

The earlier
top-logo illustrated variant in [prompts](prompts.md) remains available when
continuing a series using that reference; do not silently restyle existing covers.
The new photographic cover is an additional deliverable, not a replacement.

Generate the illustration without text when using the deterministic title-overlay
workflow in `investing-bros-short-covers`. Keep its existing renderer and assets.

## B. Real-frame speaker style

Aim for an engaged, credible moment from the podcast: flattering through frame
selection, not exaggerated expressions or synthetic beautification. Inspect
`assets/references/shorts-real-frame-layout.jpg`
for hierarchy only. That example was AI-assisted: its portrait and room are NOT
approved source pixels. Always obtain the actual speaker and room from video.

### Select a real frame

1. Prefer clean original Riverside host tracks or the episode master before text
   overlays. Verify which host is on screen; never infer identity from seat alone.
2. Inspect a timestamped contact sheet around the Short's discussion, then inspect
   nearby frames at finer intervals. Select a sharp frame with open eyes, a focused
   gaze and a composed, natural expression. A subtle smile or natural speaking
   mouth is fine; avoid blinks, awkward mouth shapes, motion blur and forced shock.
3. If the first frame looks tired, search further in the actual recording. Do not
   open eyes, change gaze, reshape facial features, smooth skin, swap faces or
   synthesize an expression. Do not send the photograph through image generation.
4. Keep the real room background from the same frame. No generated room extensions,
   added plants, replacement backgrounds, illustrated discs or artificial cutouts.
   Crop and resize proportionally; avoid enlarging a face until eyes or chin clip.
5. Prefer a frame from that Short's source discussion. If none is usable, search
   elsewhere in the same episode without implying a reaction that did not occur.
   Record the source video, exact timestamp, timebase, host and crop in the Short's
   existing notes. Retain the unretouched extracted frame with working assets.
6. If only a captioned Short is accessible, locate the clean source. Do not use AI
   to erase labels over the face/hair or pretend that a reconstructed face is real.
   Report the missing clean source if it cannot be retrieved; never silently
   substitute a generated portrait or declare both cover variants complete.

### Compose the cover

- Use a full-bleed 9:16 photograph with its original room background. No rectangular
  border, navy mat, white frame, white silhouette outline or glow.
- Place the compact, solid torn-paper show logo at the **top-left**.
- Use a **two- or three-word Hebrew headline**, normally two lines: cream torn
  strip above mustard torn strip, heavy navy lettering, restrained paper shadow.
  Keep it faithful to the clip. Reuse approved copy; if it is too long, offer a
  shorter version instead of silently changing its meaning.
- Place the headline below the face, generally over the chest, with clear eyes
  and mouth. Adjust the crop and title scale together to keep text readable.
- Centre a **small cream torn-paper tab reading `פרק N` directly underneath the
  headline**, touching or slightly overlapping its lower edge, like the main
  episode cover. Do not put it in a bottom corner or a separate smooth badge.
- Include **only the logo, headline and episode tab**. No company/ticker label,
  speaker-name tag, host-credit strip, subtitles, underline, arrows or extra copy.
- Use the brand palette for overlays; retain natural photographic colours.
- Start from `shorts-real-frame` in `assets/templates/layouts.json`; coordinates
  are adjustable guides. Keep the headline and episode tab visible in the centre
  square (y=420–1500 at 1080×1920). Check the full portrait and grid crops; the
  top-left logo can fall outside the square crop. Do not cover the eyes to fit it.

Composite the logo, paper and exact RTL text onto the extracted frame with a
deterministic layout tool. Image generation may make separate paper assets, never
the photograph or final flattened photographic cover. The legacy `make_cover.py`
layout and the hardcoded illustrated `make_torn_title.py` CLI do not implement
this design automatically. Use their reusable assets/helpers only where suitable;
if a required composition capability is absent, follow the show's script-change
workflow rather than using a generative portrait workaround.

### Alternate hosts across Shorts

Create one photographic cover per Short, alternating Amitai and Nadav across the
ordered batch. Continue from the most recent recorded photographic cover when
available; otherwise start with Amitai, then Nadav. For revisions, keep the existing
host unless asked to switch. Record the chosen host in the existing Short notes so
later batches can continue the sequence. Both hosts must be represented in a
multi-Short batch when suitable footage exists. Prefer a speaker relevant to the
clip; if alternation would imply false attribution or no usable frame exists,
use the relevant host and record the exception. Never fabricate a reaction merely
to satisfy alternation. Generate both host versions of one Short only if requested.

### Review

Compare the selected frame with the cover: face, eyes, expression and room must
remain photographic and unretouched. Verify the three permitted text elements,
Hebrew spelling, episode number, top-left logo, centred torn episode tab and absence
of borders/extra labels. Inspect at full size, ~200 px wide, and square/4:5 crops.
Check actual 1080×1920 dimensions. Present both styles together, with the host and
source timestamp for the photographic option; do not claim proven CTR improvement.

### v2 measurements — "torn-strip hook" real-frame cover (Amitai, Oct 2026)

Approved references (real ep8 frames, one per host):
`assets/references/shorts-real-frame-nadav-ep8.png` and
`assets/references/shorts-real-frame-amitai-ep8.png`. Drive copy:
[Brand Resources/references/shorts-thumbnails](https://drive.google.com/drive/folders/1Z2O0iYmq7XaZKSDQY6-LSnaux6INs7Ub).
These supersede `shorts-real-frame-layout.jpg` as the layout reference (they are real frames).

Generated **alongside** the illustrated cover for every new Short, one version per host
(Amitai and Nadav each get their own frame when both speak in the clip; otherwise the speaker).
Use when the clip has a strong, natural face moment; the illustrated cover stays the default
for topic-led clips until Amitai picks.

| Element | Position (fraction of 1080×1920) | Spec |
|---|---|---|
| Photo | full bleed | real frame, proportional cover-crop, face fills ~upper 2/3, eyes ≈ 0.35–0.45 H. No zoom past source resolution. |
| Logo | x 0.075, y 0.025, width 0.20 W | `assets/logo-solid.png` (cream `אחים` strip over mustard `להשקעות`, black type) |
| Headline line 1 | strip centre y ≈ 0.75 H, width 0.74 W (x 0.13–0.87) | cream `#FBEEDF` torn strip, tilt ≈ +0.8° |
| Headline line 2 | directly below, overlapping ~6% | mustard `#FCAF02` torn strip, same width, tilt ≈ −0.6° |
| Episode tab | centred, touching mustard lower edge (≈ 0.88–0.91 H) | small cream `#FDF0E2` torn tab, `פרק N`, ~64 px type |
| Text | — | Rubik Black (wght 900), ink `#011526` (near-navy), RTL, 2–3 word hook, e.g. `כשהריבית / עולה` |

Colours sampled from both reference PNGs (Nadav/Amitai: cream #FBEEDF/#FBEFDE,
mustard #FCAF02/#FDB202, tab #FDF0E2/#FCF2E3, ink #011526/#011324). Strips: rough torn
edges with thin white paper fringe and soft shadow (`make_torn_title._paper`).
Renderer: `investing-bros-short-covers/scripts/make_real_frame_cover.py`.
Name: `<short>-cover-real-<host>.jpg` beside `<short>-cover.jpg`.
