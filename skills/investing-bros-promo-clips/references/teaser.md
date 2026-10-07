# Teaser (episode trailer)

A 30–60 s trailer that makes people want the full episode. Shared on WhatsApp/Instagram around release.

## Defaults (unless Amitai says otherwise)
- **Length:** 30–60 s total.
- **Structure:** 2–4 short moments (5–15 s each) joined, strongest hook first. Optionally end on 2–3 s of the show cover (an audiogram clip of the episode outro).
- **Canvas:** square 1080×1080 (`--format square`) — plays well in WhatsApp and feeds. Add a vertical version only if asked.
- **Captions:** burned in, Hebrew, proofread — same as shorts.
- **Every clip in one teaser must use the same `--format`**; `make_teaser.sh` joins them with short fades.

## Picking moments
- Tease, don't resolve: a question raised, a number dropped, a disagreement starting. Cut before the answer.
- Cover the episode's range: one news beat, the deep dive, maybe an investment idea.
- Same "never" rules as shorts: nothing out of context that sounds like a recommendation; flag on-air mistakes.

## Naming
`promo/teaser.mp4` (and `promo/teaser-vertical.mp4` if made).
