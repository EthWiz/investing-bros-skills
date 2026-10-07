# Agent instructions

This repo holds the production skills for the Investing Bros (אחים להשקעות) podcast, in the Agent Skills format (`skills/<name>/SKILL.md`).

## Using the skills
- Always load `skills/investing-bros-show/SKILL.md` — shared facts, naming, Drive tree, roles, accounts and WhatsApp rules.
- Then load the one skill for the task:

| Task | Skill |
|---|---|
| Before recording: folder, news, deep dive | `investing-bros-episode-preparation` |
| Recording is in: combine, level, transcribe, trim, Docs, video episode, review ping | `investing-bros-post-production` |
| Vertical shorts | `investing-bros-shorts` |
| Episode teaser / per-host cold open | `investing-bros-teaser` |
| Episode artwork | `investing-bros-cover-art` (placeholder) |
| Upload to RedCircle (draft) | `investing-bros-episode-upload` |
| Share the published episode | `investing-bros-share-new-episode` |

## Editing the skills
- Shared facts go in `investing-bros-show` only. Other skills refer to it by name; don't copy facts into them.
- Each skill: frontmatter `name` = folder name (lowercase, hyphens), `description` says what it does **and** when to use it (include Amitai's Hebrew/English trigger phrases). Body sections: When to use → Inputs → Steps → Hand back → Never.
- Code an agent should run goes in the skill's `scripts/`, with tests (`test_*.py`) where it can be tested. Longer reference material goes in `references/`.
- A script used by two skills is copied into both (`clip_captions.py`, `make_clip.sh`, `brand.py` in shorts and teaser). Edit both copies together — the validator fails if same-named scripts differ.
- Refer to other skills by name, not by relative path — skills may be installed separately.
- Never commit passwords, tokens or cookies; refer to secrets by env-var name.
- Before pushing: `python3 tools/validate_skills.py` and `python3 -m pytest skills` (CI runs both).
