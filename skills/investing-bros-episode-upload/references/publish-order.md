# Publish order

The overall order after Amitai's OK. Detail in `../SKILL.md` step 4.

1. **RedCircle first** - publish the episode (after Amitai's OK). Same title as YouTube
   (`check_titles_match.py` must pass).
2. **Confirm on Spotify** - RedCircle feeds Spotify within a few hours; open the show page
   (https://open.spotify.com/show/4fREAemgQDMWIUK58N5Jjk) and find the episode.
3. **Spotify line in YouTube** - put `האזינו בספוטיפיי: <episode link>` (no `?si=`) in the
   episode description after the disclaimer, before chapters. Use the show link if Spotify
   hasn't listed it yet and swap it later; `check_copy.py --youtube` warns if the line is missing.
4. **Deep-dive video** - Public after the full episode (with Amitai's OK); its description links
   the episode, and the episode description gets `הצלילה לעומק כסרטון נפרד: <URL>`. See `investing-bros-deep-dive`.
5. **Then the Shorts** - with the episode's YouTube and Spotify links.
