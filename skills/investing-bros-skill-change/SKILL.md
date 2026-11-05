---
name: investing-bros-skill-change
description: >-
  Turn a lesson into a small, checked change to the Investing Bros / אחים
  להשקעות skills repo: classify it, find every place the rule lives, update
  them or point to one owner, retire the old wording, run the validator and
  tests, and open a one-fix PR. Use for "update the skill", "add this to the
  skills", "learnings PR", "תעדכן את הסקיל", or the Producer's end-of-episode hand-off.
---
# Investing Bros skill change

The single home of how the skills improve. Several agents (Amitai's, Nadav's, Grokbot) work on the
same episodes, so improvements land in small steps, never big rewrites. The repo rules for any edit
are in [references/editing-rules.md](references/editing-rules.md).

## When to use
- A run taught something: a mistake, a missing or wrong step, a new fact or decision.
- The Producer's retro (`investing-bros-producer` → `pipeline.py retro`) hands over its findings.
- Amitai or Nadav asks to change a skill.

## Inputs
- The lesson in one or two sentences, with where it happened (episode, stage, quote if a host said it).
- A clone of `EthWiz/investing-bros-skills` with `gh` signed in.

## Steps
1. **Pull `main` and branch** (`git switch main && git pull && git switch -c learn/<short-topic>`).
   Long-lived branches are where agents' edits collide.
2. **Classify the lesson** (the retro classifies each finding the same way):
   - a mistake a script could catch → a **check with a test** in that skill's script (`check_copy.py`,
     `check_short.py`, `rtl_fix.py`, the pipeline's stage checks). A check holds for every agent;
     a sentence in a SKILL.md gets missed;
   - a missing or wrong step → **one line in the skill that owns the step**;
   - a fact (spelling, account, limit, decision) → **`investing-bros-show` only**;
   - something you couldn't verify or fix → a **GitHub issue** (`gh issue create`), so the next agent
     doesn't rediscover it;
   - nothing new → no change; say why.
3. **Find every site of the rule:** `python3 scripts/rule_sites.py "<topic words>"` lists each line in
   every skill, reference, `AGENTS.md`, `README.md` and `tools/*.txt` that mentions it, and the owner.
4. **Update all of them, or replace the copies with a pointer** to the owning skill by name. A rule
   lives in one place; others refer to it.
5. **Retire the old wording:** add the superseded phrase to `tools/retired_phrases.txt`, so a copy
   that still says it fails the validator.
6. Once a lesson is a check or a rule, drop the episode story behind it from the SKILL.md (keep it in
   a reference if it is still useful).
7. **Run** `python3 tools/validate_skills.py` and `python3 -m pytest skills tools`; fix every error.
8. **One fix per PR**, merged the same day: a short title, what changed and why, the lesson it comes
   from. Amitai merges; changes to anything about publishing or public posts always wait for him.

## Done when
- The PR is open with one fix, the validator and pytest pass, and CI is green.
- Every site `rule_sites.py` listed is updated or points to the owner, and the old wording is in
  `tools/retired_phrases.txt`.
- An issue exists for anything that couldn't be fixed.

## Hand back
The PR link (or the issue link), its classification, and the sites changed. For a retro: one line per
finding with its PR or issue, for the Producer's single message to the episode owner.

## Never
- Bundle several lessons into one PR, or rewrite a skill wholesale.
- Fix one copy of a rule and leave the others saying something else.
- Put a fact anywhere but `investing-bros-show`, or a design rule anywhere but `investing-bros-brand`.
- Merge, or push to `main`.
- Write your own code where a skill's script exists (`investing-bros-show` → Working rules).
