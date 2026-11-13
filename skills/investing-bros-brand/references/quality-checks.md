# Quality checklist

Check the output itself, not the prompt. What a script can check, a script checks:
`scripts/check_cover.py` for every cover and thumbnail, `scripts/check_reference_index.py`
for downloaded references. This list is what only eyes can check.

## Before generation
- The exact reference and version (downloaded by Drive ID), requested topic and the
  supplied episode number.
- The exact approved title; no invented quotations, data or host credit.
- The format's layout and size target from [covers](covers.md),
  [Shorts covers](shorts-covers.md) or [video graphics](video-graphics.md).
- Main-episode, segment and individual Shorts covers: Codex is available and the plan
  calls for three clearly labeled options A/B/C. This is required until Amitai says the
  design is dialed in.
- Photo-cutout covers and face-format Shorts covers: the selected references and a
  separate original frame of each host from the same episode recording, taken from grids
  labelled by **verified** identity (start of recording and after any seat swap; face
  picks step 2), with episode, timestamp, identity and side recorded. Frames may come from any point in the episode, not necessarily the segment;
  sources from another episode, blurred frames and blinking frames are rejected.
- Mixed selections: the exact source image and side for every selected element.

## After generation
- All three options are present, labeled A/B/C in filenames, folders or the review
  presentation (never on the artwork), and made through the Codex backend. Review every
  option; record the episode owner's selection before assigning the final delivery filename.
- Read every Hebrew word letter by letter (אמיתי, רסקין, אחים להשקעות); `?` on the
  left; numbers and Latin names (`S&P 500`) in the right order.
- Headline and number match the supplied copy, not a guessed title. A/B/C options differ in art only. A Short cover is rendered only after the episode title and that Short's cover title are approved.
- Navy, cream paper and printed mustard dominate; no palette or style drift.
- Photo-cutout covers: each face against its own original; exactly one Amitai and one
  Nadav; open eyes looking at the lens (no stare, no downcast lids), real smiles with no
  mid-word or lopsided mouth, skin detail, clean hair edges, comparable
  scale; touch-ups within the [covers](covers.md) scope and disclosed. Two-strip
  headline, one polished photographic centerpiece, bottom-right show mark clear of the
  chin and duration badge; no name strip, clip art, cartoon rays or blurred sidebars.
- Options visibly differ in portraits and centerpieces; a recolour is not a new frame.
- Restrained paper edges and breathing room around faces and headline; the topic reads.
- Tokenization: physical paper is distinguishable from the digital fragments.
- At 160–200 px wide the headline and focal object are still identifiable.
- No cropped letters, stray generated text, invented logos or clutter inside the margins.
- Edits: unchanged regions match the exact source; don't claim perfect preservation if
  generation changed them.
- No tofu boxes, `؟` (U+061F, the Arabic question mark), literal `[` `]` brackets or
  missing letters in any headline (episode 10's thumbnails showed bracket tofu).
- The disc and strips are brand mustard `#D8A52E`, never a green disc (episode 10).
- The cover was made by Codex on Amitai's Mac or, when that host was unreachable or
  failed, by Codex CLI on the box (log and prompt in the workdir), not assembled
  with Pillow or another generator.
- Then `check_cover.py FILE --kind <kind> --episode N --register extras/artwork-register.json --title "<line>" …`
  (Shorts: `--config short.json`) must pass, with its output appended to
  `extras/cover-check.log`. It fails a headline with banned or missing glyphs (U+061F,
  brackets, box characters, niqqud, anything not in the font with `--font`), and an image
  with no brand mustard or a green area. `--allow-green "<Owner> HH:MM: <their words>"` only when
  the episode owner asked for green (Amitai outside episodes). Its warnings (real size below target) go in the hand-back.

## Repair
One localized imagegen edit for an isolated error, then re-inspect. If the Hebrew stays
wrong, generate the art text-free and typeset the words in Heebo
(`make_cover_title.py` for Shorts). Never quietly substitute a wrong name.

## Status
Each new artwork and square adaptation needs review. User approval of artwork never
authorizes external posting.
