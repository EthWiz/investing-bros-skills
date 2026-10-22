# Thumbnail copy and artwork handoff

This skill owns the words. `investing-bros-brand` owns the visual system and artwork.
Load `investing-bros-show` for shared facts and exact host spelling.

1. Use the supplied episode number and read the relevant transcript/chapters.
2. Preserve an approved headline. Otherwise offer 2-3 concise, truthful headline
   options grounded in the actual episode. Do not invent urgency, claims or returns.
3. Hand the brand skill the episode number, topic, approved headline (one headline
   serves both the square cover and the 16:9 thumbnail made from it)
   and relevant transcript context. Include a usable frame of each host from this same
   episode recording; any point in the episode is valid, but another episode's portraits
   are not. Include the exact selected edit target if supplied.
4. When the user requests finished artwork, continue with `investing-bros-brand` in the
   same task. Until Amitai says the design is dialed in, it returns three clearly labeled
   Codex options A/B/C for the main-episode cover set and Amitai picks one. Do not stop
   at a copy brief if visual production was requested.
5. Return headline choices/brief and the brand skill's deliverables where applicable.

Do not maintain a second palette, image prompt or layout template in this skill.
Refer to investing-bros-brand for examples, format specifications and visual QA.
