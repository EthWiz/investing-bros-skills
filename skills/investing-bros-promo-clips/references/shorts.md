# Shorts (Reels / YouTube Shorts / TikTok)

## Defaults (unless Amitai says otherwise)
- **Count:** propose 4–6 candidates; render the 3–5 he picks.
- **Length:** 20–60 s. Under 45 s is usually better.
- **Canvas:** vertical 1080×1920, 30 fps (`--format vertical`).
- **Captions:** always burned in, Hebrew, from the transcript, proofread. Most people watch muted.
- **Source:** recording video when it exists (`make_clip.sh` shows the whole frame over a blurred fill, so both hosts stay visible). Audio-only → audiogram over the show cover.

## What makes a good moment
- **Hook in the first 3 seconds.** Start on a strong claim, a surprising number, or a question — not on "אז…" or a greeting. Trim the lead-in.
- **Stands alone.** A viewer who hasn't heard the episode should get it. No "like we said before".
- **One idea.** A single take, number or story. Cut before the tangent.
- **Ends clean** — on a punchline or conclusion, not mid-sentence.
- Good sources: the sharpest news item, the deep dive's key number or bull/bear clash, each host's investment idea in one breath.

## Avoid
- Anything that sounds like a buy/sell recommendation out of context. If a clip names a stock with a view, end the caption block with `אין כאן המלצת השקעה`.
- Clips where audio is crosstalk or a host is off-mic.
- Numbers the hosts got wrong on air — flag those to Amitai instead.

## Platform safe zones
Platform UI covers roughly the top 15% and bottom 20% of vertical video. `clip_captions.py --format vertical` places captions above the bottom zone; keep any extra text overlay out of those bands.

## Naming
`promo/short-01-<slug>.mp4`, numbered in the order Amitai would post them.
