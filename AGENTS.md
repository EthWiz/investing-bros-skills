# Agent instructions

This repo holds the production skills for the Investing Bros (אחים להשקעות) podcast, in the Agent Skills format (`skills/<name>/SKILL.md`).

## Using the skills
- Always load `skills/investing-bros-show/SKILL.md` — shared facts, naming, Drive tree, roles, accounts and WhatsApp rules.
- Follow its **Working rules**: run the skill's scripts — don't write your own render, caption, animation, download or upload code. If a script can't do what's needed, stop, say what's missing and propose the change as a PR. Environment limits (Drive connector, Amitai's Mac, network) are in `skills/investing-bros-show/references/environment.md`.
- Then load the one skill for the task (the order is the episode flow in `README.md`):

| Task | Skill |
|---|---|
| Before recording: folder, news, deep dive | `investing-bros-episode-preparation` |
| Run an episode end to end as its Producer: the state file, the next step per track, review rounds, the retro | `investing-bros-producer` |
| Recording is in: combine, level, transcribe, cut list, trim (and start the Producer) | `investing-bros-post-production` |
| Titles, description (.txt), artwork copy brief | `investing-bros-title-description` |
| Visual identity, artwork, templates, covers and design QA | `investing-bros-brand` |
| Animation: rendering shorts and animated explainer cards (Remotion template) | `investing-bros-remotion` |
| Cold opens, intro, full video episode, promo teaser | `investing-bros-video` |
| Exactly 3 shorts with Codex covers (rendered with `investing-bros-remotion`), optional mid-form highlights — **Producer runs this skill directly** (no separate Shorts bot) | `investing-bros-shorts` |
| Exactly 2 standalone search-first segment videos: 01 deep dive, 02 next-best qualifying topic | `investing-bros-segment-video` |
| Review ping, RedCircle draft, YouTube, publish, Spotify check, WhatsApp share | `investing-bros-episode-upload` |
| Going Public after Amitai's OK: RedCircle → episode → segments → Shorts, each verified live, ticked checklist | `investing-bros-publish` |
| Weekly (Sunday) and ad-hoc YouTube/podcast analytics, read-only; the weekly Telegram report | `investing-bros-analytics` |
| A lesson to add to the skills: update a skill, learnings PR, the retro's findings | `investing-bros-skill-change` |
| The free 7-lesson crypto course: lesson plan, slides, scripts in beats, lesson videos with Remotion, lesson folders (not an episode) | `investing-bros-crypto-course` |

To see where an episode stands, list its Drive folder and compare it with each skill's **Done when**.

## Improving and editing the skills
Load `investing-bros-skill-change`: it is the single home of how a lesson becomes a check, a line
in the owning skill, a show fact or an issue (one fix per PR, same day; Amitai merges), and of the
repo's editing rules (`references/editing-rules.md`). For an episode, the Producer's retro hands its
findings to it. Before pushing: `python3 tools/validate_skills.py` and `python3 -m pytest skills tools`.
