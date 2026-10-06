# Investing Bros skills (אחים להשקעות)

Shared, versioned agent skills for producing the **Investing Bros / אחים להשקעות** podcast (Amitai & Nadav Raskin).
Any agent — Claude, Codex, Grokbot — can read and follow these.

## Layout

```
skills/
  investing-bros-episode-preparation/SKILL.md   # pre-recording: Drive folder, news + deep-dive research, share prep
  investing-bros-post-production/SKILL.md       # after recording: stitch/trim/transcribe, Hebrew RTL + ? fix
  investing-bros-episode-upload/SKILL.md        # RedCircle upload (draft by default, publish only on explicit OK)
  investing-bros-share-new-episode/SKILL.md     # after publish: gather copy, share to WhatsApp group
```

Each skill is one folder with a `SKILL.md` (YAML frontmatter `name` + `description`, then the steps) — the Agent Skills format used by Claude and Codex.

## Using them

- **Claude Code**: copy or symlink a skill folder into `~/.claude/skills/` (personal) or `.claude/skills/` (project).
- **Codex**: copy or symlink into `~/.codex/skills/` (or point Codex at this repo; it also reads `AGENTS.md`).
- **Grokbot**: keeps its own copy in sync with this repo.

## Contributing

- Small focused edits; one skill per folder. Keep the frontmatter `description` short — agents use it to decide when to load the skill.
- Never commit passwords, tokens, or cookies. Refer to secrets by env-var name only (e.g. `REDCIRCLE_PASSWORD`).
- Some steps mention Grokbot-specific agents (e.g. "Amitai Personal" owns WhatsApp Web). Other agents should treat those as "hand this step to whoever owns that account".
- Open a PR (or push to `main` for trivial fixes) and note what changed and why.

## Show conventions (quick reference)

- Episode titles in Hebrew: `פרק N – <title>`.
- Spell SpaceX as **ספייסאקס**.
- Hebrew title/description on RedCircle need the RTL + `?` marks fix (see post-production step 7).
- Uploads are drafts first; share the draft link before publishing.
- News segment leans All-In-style tech (models, launches, big raises/IPOs, hacks, startup drama) over macro/rates.
- Episode format: ~10 min news, ~20 min deep dive, ~5 min each for an investment idea.
