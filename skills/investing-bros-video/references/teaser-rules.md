# Teaser rules (Amitai, Oct 2026)

- **Length: 30 s max** (15-30 s). `build_fullframe_teaser.py` warns above 30 s.
- **Full frame, never zoomed.** Don't crop into a side-by-side frame - it looked blurry and
  too zoomed on episode 8. Omit `crop` to show the whole frame (fit + pad).
- **Best source per moment.** Each piece may set its own `source`/`audio`/`crop`, e.g. the
  speaker's own Riverside camera track (sharp, full frame). Those tracks start a fraction of a
  second off the combined video (0.17 s on ep 8): align them by cross-correlating audio before
  using their timestamps, or lips won't match. If only a side-by-side exists (ep 6), show it whole.
- **Caption order.** Highlighted words must follow speech order; the renderer rejects cards out of
  time order or a highlight going backwards (the "15%" mix-up). Still compare cards to `words.json` by ear.
- **Moments: 10 candidates, AI picks 3.** Identify 10 teaser candidates, then choose the top 3
  most engaging and thought-provoking yourself - no host pick or approval of the moments is
  needed before building. List all 10 (timestamp, quote, why) with the 3 chosen in the hand-back.
- **Preview.** Amitai always sees a teaser preview (Drive link) before anything is published;
  a host may still swap a moment after seeing it.
