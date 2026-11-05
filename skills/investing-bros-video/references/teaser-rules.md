# Teaser rules (Amitai, Oct 2026; quality rules from episode 10, Nov 2026)

- **Length: short.** 30 s max (15-30 s); fewer, punchier moments beat more of them.
  `build_fullframe_teaser.py` warns above 30 s.
- **Only the speaking host on screen.** Every teaser clip shows just the person who is talking —
  never a full side-by-side while one host speaks (episode 10 v2 clip 2 was the bad example:
  Nadav's "excellent business at a fair price" line with Amitai still visible). Prefer that
  host's own Riverside camera track (sharp, full frame), or a native Riverside solo shot.
  Those tracks start a fraction of a second off the combined video (0.17 s on ep 8): align
  them by cross-correlating audio before using their timestamps, or lips won't match. If only
  the combined side-by-side exists for that moment, set `crop` to a 16:9 window of the
  speaker's half (verify which side — hosts can swap mid-recording; ep 10 swapped ~22:26 /
  raw ~1346 s). Mark a one-speaker SxS moment with `"sxs": true` so `--check` warns when the
  crop is missing. A full-frame SxS with no crop is only for a genuine two-person exchange
  (rare in a cold open). Don't zoom past a half-pane 16:9 crop — that looked blurry on
  episode 8. Each piece may set its own `source`/`audio`/`crop`.
- **Caption order.** Highlighted words must follow speech order; the renderer rejects cards out of
  time order or a highlight going backwards (the "15%" mix-up). Still compare cards to `words.json` by ear.
- **Moments: 10 candidates, AI picks 3.** Identify 10 teaser candidates, then choose the top 3
  most engaging and thought-provoking yourself - no host pick or approval of the moments is
  needed before building. List all 10 (timestamp, quote, why) with the 3 chosen in the hand-back.
- **Preview.** The episode owner always sees a teaser preview (Drive link) before anything is published;
  a host may still swap a moment after seeing it.

## Quality: every moment must land on its own (episode 10)

A viewer who has never heard the show sees the teaser first. Each moment must make
sense to them with no context, and the teaser must stay short and engaging.

- **Both hosts.** Every teaser must include at least one clip of Amitai and at least one
  of Nadav (verify speaker identity; hosts can swap sides mid-recording). The renderer
  `--check` warns when either host is missing.
- **Self-explanatory.** Before choosing a moment, read it as a stranger: who is speaking
  about what, and why it is interesting, must be clear from the clip alone.
- **No niche names without context.** A name most viewers don't know (episode 10:
  "Greg Abel") is out unless the same clip says who he is. Household names (Warren
  Buffett, Coca-Cola, Apple) are fine.
- **Punchy hooks only.** Every moment is a short, self-contained hook: a concrete number,
  a one-liner, or a sharp question. Prefer 2-3 strong moments over more weak ones; drop a
  moment rather than trim it into nonsense. Long setup/explainer clips are out — episode
  10's "20 hole punches" card (Charlie Munger's 20-investment punch-card) dragged and was
  too complicated for a cold open, even after extending it through Buffett's payoff; that
  is a **bad example**. The clip still ends on the sentence that makes its point (never
  mid-thought); "tease, don't resolve" means the *episode's* answer stays open. The
  renderer warns about any moment under 4 s (cut before payoff?) or over 12 s (not punchy).
- **Good examples (Amitai, episode 10):**
  - "If you'd invested $1,000 in Berkshire Hathaway, what would it be worth today?": a
    concrete number anyone can picture, posed as a question the episode answers.
  - Nadav: "Coca-Cola is a good moat": a famous company plus one clear idea.
  - **Episode 10 teaser v3 (reference cold open, ~25 s):** four punchy hooks, both hosts,
    each clip shows only the speaker:
    1. Amitai — $1,000 in Berkshire (1965) → $61M today.
    2. Nadav — you don't have to buy a mediocre business at an excellent price; you can buy
       an excellent business at a fair price (SxS cropped to Nadav only).
    3. Nadav — Coca-Cola moat: people who drink Coke don't drink anything else.
    4. Amitai — will Berkshire's success continue, or is it only downhill from here?
    Why it works: short (~25 s), self-explanatory numbers and household names, both hosts
    equally present, every moment is a one-liner or sharp question with no dragged setup,
    and no non-speaking host sharing the frame.
- **Revising a teaser after feedback:** keep the moments Amitai or Nadav liked as they
  are and replace or extend only the ones they flagged. Don't rebuild the whole teaser.

## Captions: wide safe margins

Captions went off screen on YouTube on episode 10. Captions now:
- stay inside a horizontal safe area of about **12% of the width on each side**
  (`brand.py` → `TEASER.caption.margin_pct`, 230-1690 px on 1920);
- **wrap** to a second line instead of running wide (`max_width`); a card that needs a
  third line is too long: split it into more cards;
- are checked by the renderer, which refuses to render when any wrapped line leaves the
  safe area. Check a config before rendering, without media:
  ```bash
  python3 <investing-bros-video>/scripts/build_fullframe_teaser.py "$EP/extras/teaser.json" --check
  ```
  It must print `CAPTIONS OK`. With no Heebo ExtraBold in `fonts`, it measures with a
  conservative estimate and says so; build the fonts first for an exact check.
- After rendering, look at the frame with the longest caption: the text sits well inside
  the frame, not near the edges.
