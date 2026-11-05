# Editing the skills

The repo's rules for any change to a skill (moved here from `AGENTS.md`).

- Shared show facts go in `investing-bros-show` only. Visual rules, templates and curated artwork
  live only in `investing-bros-brand`. Other skills consume them by name; do not duplicate design
  specifications.
- Each skill: frontmatter `name` = folder name (lowercase, hyphens), `description` says what it
  does **and** when to use it (include Amitai's Hebrew/English trigger phrases; a phrase belongs to
  one skill only, `tools/triggers.txt`), 300–400 characters. Body sections, in this order: When to
  use → Inputs → Steps → Done when → Hand back → Never. **Done when** lists the files the skill
  leaves in the Drive folder.
- One skill per stage of the episode flow. `investing-bros-brand` (design), `investing-bros-remotion`
  (animation), `investing-bros-producer` (running the episode) and `investing-bros-skill-change`
  (changing the skills) are cross-cutting, not episode stages. Remotion is the only animation
  framework; its template lives in `skills/investing-bros-remotion/template/` (exact versions,
  `package-lock.json`, never `node_modules/`). A variant of a step is a `references/` file of that
  skill, not a new skill.
- Code an agent should run goes in the skill's `scripts/`, with tests (`test_*.py`) where it can be
  tested. Longer reference material, dated decision stories and legacy tools go in `references/`.
- A script used by several skills is copied into each, as identical copies: `clip_captions.py`,
  `make_clip.sh`, `brand.py` (shorts, video); `edit_map.py` (post-production, title-description,
  video, shorts, segment-video); `render_cuts.py`, `verify_sync.py` (video, segment-video);
  `episode_owner.py` (producer, post-production, publish, brand); `episode_gates.py` (producer,
  post-production); `pipeline_state.py` (producer, publish). Other scripts import them from their
  own folder, because skills may be installed separately. Edit all copies together; the validator
  fails if same-named scripts differ.
- Refer to other skills by name, never by relative path.
- Never commit passwords, tokens or cookies; refer to secrets by env-var name.
- Before pushing: `python3 tools/validate_skills.py` and `python3 -m pytest skills tools`. CI runs
  both, and again before building the release ZIPs. The validator fails on retired wording
  (`tools/retired_phrases.txt`), and warns about copied rules (`tools/copied_rules_allow.txt` for
  boilerplate), show facts outside `investing-bros-show`, and trigger phrases in the wrong
  description. After a merge, GitHub rebuilds the per-skill ZIPs on the `skills-latest` release.
