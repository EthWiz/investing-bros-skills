---
name: investing-bros-short-covers
description: >-
  Produce two vertical (1080×1920) Investing Bros / אחים להשקעות Short covers:
  the existing illustrated cut-newspaper theme and a natural podcast video-frame
  theme with real speakers. Use for Short covers, קאבר לשורט, תמונת שער לשורט,
  Shorts thumbnails, or selecting a real frame without editing the speaker's face.
---
# Investing Bros Short covers

## When to use
Make covers for a new Short, or revise the specific variant Amitai identifies.
Load `investing-bros-show` and `investing-bros-brand` first. Brand owns all visual
specifications, including both cover styles in `references/shorts-covers.md`.
This skill owns cover production and consumes those specifications.

## Inputs
Use the episode number, Short identifier, faithful headline, clean source video,
selected illustrated series reference and existing Short notes. Reuse session values.

## Steps
1. Read `investing-bros-brand` → `references/shorts-covers.md`. Create both styles
   for each new Short unless Amitai explicitly requests one. For a revision, edit
   only the requested variant. Preserve the existing illustrated style.
2. **Illustrated cover:** no host-name strip; logo bottom-right (Amitai, Oct 2026). Retain the text-free artwork generation and exact Hebrew
   overlay flow. Use `scripts/make_torn_title.py` helpers (PIL + raqm, RTL):
   ```python
   from make_torn_title import title_block, torn_strip, shadow, CREAM
   tb = title_block("דאטה סנטרים", "בחלל?", "פרק 3", width=1010)
   ```
   Its CLI `python3 scripts/make_torn_title.py ART.jpg OUT.jpg` reproduces the old
   episode-3 example, including hardcoded copy and paint-over regions; do not use
   those defaults for another topic. `RUBIK` points at the box font path. Follow
   the show's script-change rules when parameterization is needed. The existing
   example stays at [assets/amitai-short-cover-example.png](assets/amitai-short-cover-example.png);
   its design specification and canonical copy are now in the brand skill.
3. **Real-frame cover:** select an actual frame and alternate the featured host
   according to the brand reference. Composite graphic layers without regenerating
   or retouching the photograph. Render with `scripts/make_real_frame_cover.py FRAME.jpg OUT.jpg "line1" "line2" "פרק N" [--face-cx 0.5]`
   (v2 torn-strip hook; spec in brand `shorts-covers.md` → v2 measurements), one per host.
   Use the brand's layout and QA, not the legacy `make_cover.py` layout. Record source video, timestamp/timebase, host and crop in
   `youtube-שורט-NN.md`. If clean footage or a suitable compositor is unavailable,
   report the missing input/capability; never substitute a synthetic face.
4. Inspect both outputs at full and thumbnail size and in grid crops using the
   brand checks. Verify actual dimensions and exact Hebrew. Export JPEGs using
   `investing-bros-show` → Naming, then file both beside the Short in the current
   episode's `Shorts/` folder. Keep existing variants; do not overwrite one with
   the other. Record the selected publishing variant in the existing notes.

## Done when
- Both 1080×1920 JPEGs named in `investing-bros-show` sit beside each new Short in
  its episode's `Shorts/` folder, and both pass the brand checks.
- The existing Short notes identify both cover paths, the photographic host and
  source timestamp/timebase, any alternation exception and selected variant
  (or pending selection). Missing clean footage is reported as incomplete.

## Hand back
Show the two covers together, labelled illustrated and real-frame, with the latter's
host and source timestamp. Include file links and any unresolved source/QA issue.

## Never
- Replace the existing illustrated deliverable with the photographic variant.
- Alter a speaker's eyes, face, expression or room to improve a real-frame cover.
- Treat an AI-assisted layout reference as an authentic podcast still.
- Claim that documenting a layout implements a renderer, or bypass the show's
  script-change rules when a required capability is missing.
