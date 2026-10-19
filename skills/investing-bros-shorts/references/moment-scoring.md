# Scoring short candidates

Step 1 of `investing-bros-shorts`. Shorts are judged in the swipe feed: almost nobody sees a cover there, so the moment and its first second decide whether a short is watched. Score every candidate the same way so picks can be compared across episodes, and so the scores can later be checked against how the shorts actually did.

## Find ~10 candidates
Read the whole transcript (`segments.json`) and mark every stretch that could stand alone. Look for:
- **a number or fact that surprises** ("SWIFT is a messaging system, not a payments system");
- **a story that turns into a concept** (pizza for 10,000 BTC → why stablecoins exist);
- **a question one brother asks and the other answers** ("So what?" → liquidity);
- **pushback**: one brother doubts, corrects or argues with the other;
- **a clear "here's how it actually works"** that a viewer could repeat to a friend.

Include at least 3 candidates from the deep dive. The deep dive is what the episode sells; a short that opens its question and leaves the full answer to the episode is the one most likely to send viewers there.

## Score each 1–5

| Score | 1 | 3 | 5 |
|---|---|---|---|
| **hook**: the first sentence alone | context or filler ("אז…", "כן, אז…") | an interesting topic, said plainly | a number, a claim against intuition, a sharp question, or something at stake |
| **standalone** | needs the episode to make sense | needs one line of context the hook title can give | fully self-contained |
| **payoff** | trails off or keeps going | resolves, but not in one line | one idea that lands in a line you can end on |
| **friction** | one voice, no reaction | a reaction or a follow-up question | the brothers disagree, push back or surprise each other |

`score_moments.py` adds **pace** (speech rate against the episode median, 1–5), flags anything outside 20–45 s and any filler opener, and sorts by total. Pace is only a proxy; listen to the top picks before proposing them.

## Shape the pick
- **Open on the strongest line.** If the best sentence comes 10 s in, move that piece to the front and let the context follow. Move it, don't repeat it (the renderer rejects overlapping pieces), and keep its meaning: the "Never" rules in the skill still apply.
- **End on the payoff.** Cut right after the line that resolves the idea. No "so yeah", no wind-down.
- **20–45 seconds.** Going longer needs a reason (a story that can't be shorter); say it in the hand-back.
- **Hook title = an open question** the short answers only at the end, a faithful paraphrase of what is said, and **as short as possible**: one idea, ideally ≤ 6 words. Drop secondary details: `למה לסייברקאב אין הגה?`, not `למה לסייברקאב אין הגה ורק שני מקומות?`.
- **End card names what the episode adds**: "בפרק המלא: למה דווקא זהב?" and not a generic "לפרק המלא".

## Skip
Crosstalk; anything that sounds like a buy/sell call out of context; on-air mistakes (flag them instead); a stretch whose point depends on a chart or screen the viewer can't see.
