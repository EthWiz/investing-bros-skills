---
name: investing-bros-producer
description: >-
  Run an Investing Bros / אחים להשקעות episode end to end as its Producer: one
  state file (extras/pipeline.json), the next step on every track, approvals
  from the episode owner tied to file versions, review rounds, and the episode
  retro at the end. Use when post-production starts or resumes, "where does
  episode N stand", "מה הלאה בפרק", "תחקיר" or "retro".
---
# Investing Bros producer

The Producer is the agent running an episode's post-production. It owns the episode end to
end: the standing bundle (`investing-bros-show` → The show), every track's next step, the
helpers' hand-backs, the review rounds with the episode owner, publishing and the retro. This
skill holds the contracts ([gate map](references/gates.md), [state schema](references/state-schema.md))
and `scripts/pipeline.py`, which implements them.

## When to use
- The recording is in and post-production starts (with `investing-bros-post-production` for the audio).
- Resuming an episode, or asked where an episode stands.
- After every helper hand-back, owner reply or upload: record it and take the next step.
- After the last track is live: the retro.

## Inputs
- Episode number N as Amitai states it, and the episode owner (`investing-bros-show` → Episode
  owner): whoever started this episode's post-production.
- `$EP`: a local mirror of the episode's Drive folder in the Drive layout (root files, `extras/`,
  `segments/`, `Shorts/`, `video/`, `promo/`). Sync `extras/pipeline.json` to Drive `extras/`
  after every change; you are its only writer.

## Steps
```bash
P=<investing-bros-producer>/scripts/pipeline.py
python3 $P doctor [--online]                      # tools, fonts, Remotion, Whisper, rclone, Telegram env, YouTube channel, skill versions
python3 $P start "$EP" --episode N --owner amitai|nadav --by "<their words>"   # new episode
python3 $P migrate "$EP" --episode N --owner amitai|nadav [--by "..."]         # episode started before the pipeline
python3 $P next "$EP"                              # per track: next stage, owning skill, command, who it waits on
python3 $P advance "$EP" TRACK [STAGE]             # runs the stage's check; refuses on fail
python3 $P approve "$EP" TRACK STAGE --by "<Owner> HH:MM: <their words>"
python3 $P mark "$EP" ITEM --evidence "what you saw, where"
python3 $P waive "$EP" ITEM --by "<Owner> HH:MM: <their words>"
python3 $P note "$EP" --kind owner_fix|handback_returned|workaround "what happened"
python3 $P status "$EP"                            # every stage, stale ones with why, superseded uploads
python3 $P gate "$EP" --stage upload|review|done   # the post-production gate (CHECKLIST.md)
python3 $P retro "$EP"                             # after the last track is live
```
1. **Start.** Run `doctor`, then `start` (or `migrate` for an episode in flight: legacy marks and
   waivers become evidence, never approvals; record approvals already given with `approve` and
   the owner's words from the chat). If it isn't clear who owns the episode, ask in the first round.
2. **Loop on `next`.** Do the step it names with its owning skill, or hand it to the helper and
   say so; then `advance`. A failed check is logged; fix it and advance again. Never mark or
   advance from memory, a toast or another agent's word.
3. **Helpers** (segments, brand on Amitai's Mac, video) hand back to you, never to the hosts. Check
   each hand-back against its stage's evidence; send back what fails (`note --kind handback_returned`).
   You run `investing-bros-shorts` yourself; there is no Shorts bot.
4. **Review rounds.** Two rounds, and every approval stays the owner's own words. `next` names
   every approval that can be asked now, including two on the same track. Round 1 holds the cut
   list (each `[content]` cut as a question, every `[routine]` line still listed), the title, the
   segment ranges and the Short picks. Trim and copy have already run on the draft list, so a
   restore re-trims and re-copies only. Round 2 is the Telegram approval round: the six Private
   links, an A/B/C pick per asset, and the publish go (`investing-bros-episode-upload` step 3b).
   Record each answer with `approve`; the same quote may be passed to several (the way one quote
   covers the three Short picks). Promote an art pick onto the canonical file before `approve`.
   A change they ask for is `note --kind owner_fix` and the fixed stage goes through `advance`
   again. After the owner signs a round off, post the one round summary for the other brother
   (`investing-bros-show` → Telegram).
5. **Stale.** A changed input makes every stage made from it stale, and approvals of it with them
   (a new cut: the main renders, chapters and the overlapping Shorts/segments). The title approval
   (`main.title_ok`) follows only `כותרות-פרק-N.txt`: a description or chapter edit does not reopen
   it. `next` lists stale stages first; redo them and ask for the approval again in the next round.
6. **Uploads** are Private, with option A, through `investing-bros-episode-upload` →
   `yt_upload.py --thumbnail <option A> --record "$EP/extras/uploads/<track>.json"`. The upload
   record is the upload stage's evidence. The image sha256 is the sibling
   `extras/uploads/<asset>-thumb.json` (`--set-thumbnail` after a pick that is not A); it is not
   written into the upload record, so the swap does not stale `ok`. A re-upload makes that
   track's `ok` and the publish OK stale. A later art change of mind stales that art approval
   and `publish_ok`.
7. **Publish.** After the approval round, approve each asset `ok` and each art pick, then the
   owner's publish OK (`approve release publish_ok`; it needs those approvals and the current
   `cuts_ok`, and is never waived). Then `investing-bros-publish`; its `can-public` re-checks
   this state file and the thumbnail records every time. The publish gate counts a matching
   record as the thumb or cover tick, and a failed one stays open. Then the post-live
   obligations: the Spotify link swap and deleting superseded Private uploads (`status` lists them).
8. **Retro (תחקיר), unasked.** When `next` shows `release.retro`: `retro` drafts
   `extras/retro-פרק-N.md` from the events (what went wrong by stage, where time went, waits on the
   owner, repeats from the last retro), each finding classified (script check / one line in the
   owning skill / show fact / GitHub issue / no action, with the reason). Check every finding, hand
   the list to `investing-bros-skill-change`, send the owner one message with the PR and issue
   links, then `mark release.retro` and `advance release retro`. The retro never blocks publishing.

## Done when
- `extras/pipeline.json` shows every stage of every track current or waived by the episode
  owner, and `gate "$EP" --stage done` passes.
- `extras/retro-פרק-N.md` exists and its learnings PRs/issues are linked in the `release.retro` mark.

## Hand back
To the episode owner, once per round: what's ready for review (with links), what each pending
approval is about, anything blocked and on whom. At the end: the published links, the `status`
output and the retro's PR/issue links.

## Never
- Take an approval or waiver from anyone but the episode owner, or record one without their words.
- Treat a legacy mark or waiver as a fingerprinted approval, or approve a stale version.
- Let a helper message a host directly, or ping the owner with status updates instead of one batched round.
- Hand Shorts off to a separate Grok bot.
- Upload anything but Private, or a second copy of an asset that already has an upload record.
- Edit `extras/pipeline.json` by hand.
- Write your own code where a skill's script exists (`investing-bros-show` → Working rules).
