---
name: investing-bros-episode-preparation
description: >-
  Prepare an upcoming Investing Bros / אחים להשקעות episode before recording:
  episode Drive folder with a brief/ subfolder, news ideas, deep-dive research,
  and sharing the prep docs with the brothers. Use when Amitai says things like
  "prep episode N", "news ideas for this week", "deep dive on X", "הכנה לפרק".
---
# Investing Bros episode preparation

Load `investing-bros-show` first — it has the naming, Drive tree, roles and WhatsApp rules this skill relies on.

For artwork requested during preparation, continue with `investing-bros-brand`, the single design source for show covers, episode covers, thumbnails and other graphics. Supply the topic and approved copy; do not define a separate visual style here.

## When to use
Before a recording: news ideas, a deep-dive brief, one-pagers or any other pre-show material.

## Inputs
- Episode number N **as Amitai states it** (don't derive it).
- Topic / deep-dive subject, if decided; otherwise take the week's plan from the deep-dive schedule.
- Language for group-facing docs (default Hebrew). Amitai may want English drafts in chat first — follow his ask for each send.

## Steps

### 1. Deep-dive schedule
1. First, find and read the single tentative deep-dive schedule Google Doc at the show root (suggested name: `לוח נושאי עומק (טנטטיבי)`). If none exists, create it there; never put it inside an episode folder.
2. Before each week's prep, confirm or update that week's planned subject and one-line angle with Amitai. All entries are tentative.
3. Treat later subjects as a queue: if Amitai chooses a different subject this week, shift the planned subject and every later one back one week. Drop nothing unless he says so.
4. Append new candidates, including ideas from the Tuesday ideas routine, to the end of the queue.
5. After the episode records, mark that week done with the actual subject and roll the queue forward.

### 2. Drive folder
1. Under the show root, find an existing `פרק N` folder (prefix match — see show conventions). Reuse it if found; otherwise create `פרק N — נושא`.
2. Inside it, create (or reuse) the subfolder `brief`.
3. Create **every** prep Google Doc inside `brief/` — never in the show root, never loose in the episode root. The schedule above is the sole root-level working Doc, not a prep Doc.

Typical docs in `brief/`: news/topic ideas, deep-dive brief, any one-pagers. Leave the episode root otherwise empty; the later skills fill it.

### 3. News segment (~10 ideas)
- All-In / tech-investor angle (see show conventions). Don't lead with rates, oil or price action unless Amitai asks for macro.
- Each idea: one crisp line + why it matters for investors + source URL.
- Preferred sources: Globes, Calcalist, TheMarker, Bank of Israel, Bloomberg, Reuters, Jerusalem Post, and primary company posts/blogs.

### 4. Deep dive
Structured brief: what it is → why now → key numbers (each sourced) → bull case / bear case → open questions for the hosts.

### 5. Share
Hand off to the WhatsApp owner (show conventions → WhatsApp) for group `אחים להשקעות`:
1. Set the Doc(s) to anyone-with-link Viewer.
2. Send the **Doc link(s)**, not a pasted brief.
3. Give the exact caption text (ending with the show tag), the links and context; ask for yes/no confirmation.

## Done when
- The schedule has this week's confirmed planned subject and one-line angle, with later subjects preserved in queue order.
- `פרק N — נושא` exists under the show root (no duplicate N), with `brief/` holding every prep Doc; nothing else in the episode root.
- Every factual claim has a source URL.
- The WhatsApp owner has the exact group, caption and links, and the send is confirmed.

## Hand back
Links to the episode folder and each Doc in `brief/`, and the WhatsApp send status.

## Never
- Invent numbers, quotes or events.
- Drive WhatsApp Web yourself.
- Create a second show root or a second folder for the same episode.
- Write your own code where this skill has a script, or work around a missing step without saying so — follow the working rules in `investing-bros-show`.
