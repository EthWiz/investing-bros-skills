# Chapters when a new teaser is prepended

When the old opening is replaced by a new teaser + intro, chapter times move:

1. First chapter is `00:00 טעימה מהפרק` (the teaser).
2. Shift every other chapter by (new teaser + intro length) - (removed opening length).
   Use `scripts/find_offset_and_shift.py`.
3. A chapter that shifts **before zero** or into the teaser is re-pointed to the start of
   the episode body (the first second after the intro).
4. Keep **8-14 chapters**; merge or drop to stay in range.
5. A **low-score offset match** from find_offset_and_shift.py isn't trusted: check the shifted
   times against the new transcript (the chapter's opening words should be spoken there).
6. Run `check_copy.py --description` (and `--spotify` for the RedCircle copy).
