# Agent instructions

This repo holds the production skills for the Investing Bros (אחים להשקעות) podcast, in the Agent Skills format (`skills/<name>/SKILL.md`).

## Using the skills
- Always load `skills/investing-bros-show/SKILL.md` — shared facts, naming, Drive tree, roles, accounts and WhatsApp rules.
- Follow its **Working rules**: run the skill's scripts — don't write your own render, caption, animation, download or upload code. If a script can't do what's needed, stop, say what's missing and propose the change as a PR. Environment limits (Drive connector, Amitai's Mac, network) are in `skills/investing-bros-show/references/environment.md`.
- Then load the one skill for the task (the order is the episode flow in `README.md`):

| Task | Skill |
|---|---|
| Before recording: folder, news, deep dive | `investing-bros-episode-preparation` |
| Recording is in: combine, level, transcribe, cut list, trim | `investing-bros-post-production` |
| Titles, description (.txt), artwork copy brief | `investing-bros-title-description` |
| Visual identity, artwork, templates, covers and design QA | `investing-bros-brand` |
| Cold opens, intro, full video episode, promo teaser | `investing-bros-video` |
| Shorts with covers (incl. HyperFrames explainer cards), mid-form highlights | `investing-bros-shorts` |
| Review ping, RedCircle draft, YouTube, publish, Spotify check, WhatsApp share | `investing-bros-episode-upload` |

To see where an episode stands, list its Drive folder and compare it with each skill's **Done when**.

## Improving the skills
Several agents (Amitai's, Nadav's, Grokbot) work on the same episodes, so improvements land here in small steps, not in big rewrites.
1. **At the end of every run, ask what it taught.** If nothing, there's nothing to do.
2. **A mistake a script could catch becomes a check with a test**: `check_copy.py` (dashes, title layout, chapter times for YouTube and Spotify), `check_short.py`, `rtl_fix.py`. A check holds for every agent; a sentence in a SKILL.md gets missed.
3. **A missing or wrong step** is one line in the skill that owns the step. **A fact** (spelling, account, limit, decision) goes in `investing-bros-show` only.
4. **Something you couldn't verify or fix** becomes a GitHub issue (`gh issue create`), so the next agent doesn't rediscover it.
5. **One fix per PR, merged the same day.** Pull `main` before you start; long-lived branches are where agents' edits collide. Amitai merges; changes to anything about publishing or public posts always wait for him.
6. Once a lesson is a check or a rule, drop the episode story behind it from the SKILL.md (keep it in a reference if it's still useful).

## Editing the skills
- Shared show facts go in `investing-bros-show` only. Visual rules, templates and curated artwork live only in `investing-bros-brand`. Other skills consume them by name; do not duplicate design specifications.
- Each skill: frontmatter `name` = folder name (lowercase, hyphens), `description` says what it does **and** when to use it (include Amitai's Hebrew/English trigger phrases). Body sections: When to use → Inputs → Steps → Done when → Hand back → Never. **Done when** lists the files the skill leaves in the Drive folder (the validator requires the section).
- One skill per stage of the episode flow. `investing-bros-brand` is the cross-cutting design capability serving multiple stages, not an additional episode stage. A variant of a step (HyperFrames for shorts, the thumbnail for the copy) is a `references/` file of that skill, not a new skill.
- Code an agent should run goes in the skill's `scripts/`, with tests (`test_*.py`) where it can be tested. Longer reference material goes in `references/`.
- A script used by two skills is copied into both (`clip_captions.py`, `make_clip.sh`, `brand.py` in shorts and video): other scripts import them from their own folder, and skills may be installed separately. Edit both copies together — the validator fails if same-named scripts differ.
- Refer to other skills by name, not by relative path — skills may be installed separately.
- Never commit passwords, tokens or cookies; refer to secrets by env-var name.
- Before pushing: `python3 tools/validate_skills.py` and `python3 -m pytest skills` (CI runs both).
