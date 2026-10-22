# Publish order

The overall order after Amitai's OK. Detail in `../SKILL.md` step 4. Every episode reaches this phase with exactly two completed segment videos (01 is the deep dive) and exactly three completed Shorts.

1. **RedCircle first** - publish the episode (after Amitai's OK). Same title as YouTube
   (`check_titles_match.py` must pass).
2. **Confirm on Spotify** - RedCircle feeds Spotify within a few hours; open the show page
   (https://open.spotify.com/show/4fREAemgQDMWIUK58N5Jjk) and find the episode.
3. **Spotify line in YouTube** - put `האזינו בספוטיפיי: <episode link>` (no `?si=`) in the
   episode description after the disclaimer, before chapters. Use the show link if Spotify
   hasn't listed it yet and swap it later; `check_copy.py --youtube` warns if the line is missing.
4. **Segment videos** (deep dive every episode) - Public after the full episode (with Amitai's OK); each description links
   the episode, and the episode description gets a line per segment, e.g. `הצלילה לעומק כסרטון נפרד: <URL>`. See `investing-bros-segment-video`.
5. **Then the Shorts** - uploaded only once the full episode is live, with its YouTube link (`?t=`)
   and the Spotify link from its YouTube description (ask Nadav if missing). See `investing-bros-shorts`.
