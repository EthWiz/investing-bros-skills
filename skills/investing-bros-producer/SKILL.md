---
name: investing-bros-producer
description: >-
  The Producer role for an Investing Bros / אחים להשקעות episode: the gate map
  every track passes (main, two segments, three Shorts, release) and the episode
  state file extras/pipeline.json. Use when you run an episode end to end, or
  need to know which gate comes next, who approves it and what makes it stale.
---
# Investing Bros producer

Contracts first: this skill holds the gate map and the state-file schema that the
pipeline script implements.

## When to use
Whenever an episode's post-production starts or resumes, and whenever a skill asks which
gate comes next or who approves it.

## Inputs
The episode folder (`$EP`) and its `extras/`.

## Steps
1. Read [the gate map](references/gates.md): tracks, stages, evidence, approver and what
   makes each stage stale.
2. Read [the state schema](references/state-schema.md): what `extras/pipeline.json` holds
   and how an in-flight episode migrates.

## Done when
- `extras/pipeline.json` matches the schema and every gate in the map has passed or been
  waived by the episode owner.

## Hand back
The state of each track and the next gate, with who it waits on.

## Never
- Treat a legacy mark or waiver as a fingerprinted approval.
- Write your own code where a skill's script exists (`investing-bros-show` → Working rules).
