---
name: investing-bros-analytics
description: >-
  Read-only YouTube Studio analytics for the Investing Bros / אחים להשקעות
  channel: lifetime or weekly stats for every episode and Short (views,
  watch time, AVD, avg % viewed, impressions, CTR, subs), traffic sources,
  retention and key moments, audience, plus RedCircle/Spotify stats when
  available. Produces a report Page and a short Telegram text. Use when
  Amitai asks for "analytics", "stats", "סטטיסטיקות", "how are the shorts
  doing", the weekly Sunday report, or an ad-hoc comparison such as
  thumbnails with faces vs without.
---
# Investing Bros analytics (YouTube Studio)

Load `investing-bros-show` first: accounts and Telegram destinations live there.

## When to use
- Weekly report: Sunday around 10:00 Israel time, covering the last 7 days and comparing with the prior week.
- Lifetime report on all uploads, on request.
- Ad-hoc analyses (e.g. thumbnail A/B: faces vs no faces). Always normalize for video age (compare at the same hours/days since publish, or per-day rates).

## Inputs
1. Box browser signed in to Google as `investingbros.grokbot@gmail.com` (`authuser=1`; `ami.grokbot` is `authuser=0`). Manager role on the channel. No password is stored; the browser session is the login.
2. Channel URL (always this one; Studio otherwise opens the account's empty **Grok Bot** channel):
   `https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw?authuser=1`
3. Lifetime overview deep link:
   `https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw/analytics/tab-overview/period-lifetime?authuser=1`
4. A working notes file, e.g. `/workspace/analytics/studio_<range>_<YYYY-MM-DD>.md`.

## Steps
Save what you collected to the notes file **after every step**: long browser runs get interrupted and unsaved data is lost.

1. **Access check.** Open the channel URL. Confirm the channel header says **אחים להשקעות**. At any sign-in, "verify it's you" or 2FA page: stop, enter nothing, ask Amitai, and post nothing to Telegram.
2. **Overview** (Analytics → Overview, pick the range). Record views, watch time (h), subscribers, the Top content list (title, published, AVD with avg %, views), Realtime (subs, views last 48 h) and Latest content (first-N-hours views, CTR, AVD).
3. **Advanced mode content table** (Overview → Advanced mode, Content dimension, same range). Collect per item: duration, views, watch time, AVD, avg % viewed, impressions, impressions CTR, likes, subscribers gained, plus the video ID.
   - The metric picker errors when watch time and AVD are selected together: do two passes and merge by title/ID.
   - The table has no Shorts/video type column: classify by duration (under 60 s = Short).
   - Export to CSV includes only the metrics currently selected: pick metrics first, then Export (Table data, Chart data, Totals).
4. **Content tab.** Record the Shorts vs videos split (views, %, number published, subs), the impressions funnel (impressions, % from YouTube recommending, CTR, views and watch time from impressions), traffic sources (views, %, watch h per source), External sources detail and YouTube search terms.
5. **Audience tab.** Monthly audience, new vs returning, age/gender, device type, geography, subtitle/CC use. Mark values "low sample" when viewers are few: at tiny samples demographics show 100%/0% and are not meaningful.
6. **Per-episode retention** (open each episode → Analytics → Engagement). Record AVD, avg % viewed, engaged views, the retention curve and the Key moments card.
   - The chart samples about every 23 s and values only appear on mouse hover: hover each point and note `time → %`, especially the 0:00–0:30 drop and the point where half the viewers are gone.
   - New videos show "No audience retention data available for this video yet. Processing can take up to two days." Record N/A and retry next run.
7. **Cross-check sources.** The channel lifetime table lags the video pages (e.g. ep1 showed 17 views in the table vs 24 on its page). Brand-new uploads may be missing from the table entirely (seen with פרק 2 and פרק 7). The per-video page's "since published" numbers are fresher than the lifetime table: prefer them, and record the source of every number (`video page` / `lifetime table` / `realtime`) in the report and History. Per-video Key moments cards may lack timestamps; record what's shown and mark the time N/A rather than guessing. List missing items.
8. **RedCircle / Spotify.** RedCircle: box browser, saved login (see `investing-bros-show`), show id `c798e000-7934-4f82-a0e3-59b78f0894c6` (RSS `https://feeds.redcircle.com/c798e000-7934-4f82-a0e3-59b78f0894c6`). Read the analytics dashboard only: per-episode downloads, totals for the range, and its export. Never edit episodes or settings. Spotify: the show is claimed on Spotify for Creators (owner: Amitai's personal account). `investingbros.grokbot@gmail.com` is a team member since 2026-10-22 with **Analytics: Reader** (all other tabs No access), via its own free Spotify account (signed up with "Continue with Google" in the box browser). Open the show home `https://creators.spotify.com/home/show/4fREAemgQDMWIUK58N5Jjk`. Try the analytics page (`/pod/show/.../analytics`); on 22 Oct it showed "Unable to load details", so fall back to the show home stats: all-time plays, followers, 30-day plays and consumption time, latest-episode plays and consumption. Baseline 2026-10-22: 1 play, 1 follower; ep8 1 play / 7m12s. Read-only. At any sign-in or verification page: stop, enter nothing, ask Amitai.
9. **Build the report Page (Canvas)** in this order:
   - Headline takeaway (one or two sentences).
   - Channel totals row: views, watch time, subs, impressions, CTR.
   - Every-upload table: type, title, published, duration, views, watch h, AVD, avg %, impressions, CTR, likes, subs, source.
   - Best/worst Shorts and best/worst episodes by views and avg % viewed.
   - Traffic sources.
   - Episode retention (key points, half-gone time, key moments).
   - Audience (with low-sample caveats).
   - What to try next (concrete, tied to the numbers).
   - Weekly runs: a vs-prior-week delta column. Ad-hoc: method and age normalization.
   - **Delivery:** the report is one Page (Canvas) updated in place each week (edit it, add the new week; don't create a new Page). Current Page: "אחים להשקעות: YouTube report, first days".
10. **Telegram.** See the Telegram section below.
11. **History.** Append the week's rows to the History CSV (see below) and upload it.

## Video ID map
`references/video-map.csv` (`video_id,title,type,published,thumbnail,thumbnail_since`) lists every public upload. `type` is `episode`, `short` or `clip` (segment videos). Studio's **Content** tab is the authoritative episode vs Short split.

Why it exists: Studio's lifetime/advanced table can silently omit videos (on 22 Oct פרק 2 and פרק 7 were missing; ep7 was re-uploaded recently, which may explain it). Each run:
1. Compare the table with the map. For any mapped video not in the table, open it by ID: `https://studio.youtube.com/video/<id>/analytics/tab-overview/period-default?authuser=1` and take its numbers from there (mark the source).
2. Add new uploads from the Content tab to the map (ID, title, type, publish date, thumbnail). פרק 2's ID is still unknown: read it from the Studio Content list and fill it in.
3. Record thumbnail changes: `thumbnail` = `faces` / `no_faces` / `unknown`, `thumbnail_since` = when the current thumbnail went live. Ep8 switched from a signpost graphic (no people) to the hosts' faces on 2026-10-22 ~09:57 Israel time; the channel is moving to faces on every thumbnail. For faces-vs-no-faces comparisons, split ep8's numbers at `thumbnail_since`.
Thumbnail A/B method (the channel is moving to faces thumbnails on every episode, so most tests will be swaps on existing videos):
- When a thumbnail changes on an existing video, log the swap in the map (`thumbnail`, `thumbnail_since`) first.
- Compare **before vs after on the same video**: CTR and views per hour from Studio's hourly / realtime data (Reach tab and Realtime card), using equal windows either side of `thumbnail_since` where possible.
- Plus compare against other videos **at the same age** (same hours/days since publish).
- Report it as an early read until each side has enough impressions; note the sample sizes.

4. Ignore test duplicates: Unlisted `VwkS1mnR1uI` and `CujyQKAJ-U8`, and the Private gold / S&P copies.

Commit map updates with the skill improvements (PR, as usual).

## History
Each weekly run appends to `investing-bros-youtube-weekly.csv` one row per video plus one channel-totals row (`video_id` = `CHANNEL`, `type` = `total`).

Columns: `week_start,week_end,video_id,title,type,thumbnail,published,views,watch_hours,avd,avg_pct_viewed,impressions,ctr,likes,subs_gained` (`thumbnail` = faces/no_faces/unknown from the map; dates ISO; `avd` as m:ss; `ctr`/`avg_pct_viewed` as percent numbers).

- Local copy: `/workspace/analytics/weekly/investing-bros-youtube-weekly.csv` (append, never rewrite past rows).
- Drive: [`אחים להשקעות/analytics`](https://drive.google.com/drive/folders/1zd32riRkKuW7XjVNY4doCRbhwt49HdC7) (folder id `1zd32riRkKuW7XjVNY4doCRbhwt49HdC7`, inside the show root `1Lk8WnfTWeIFLfw7ksQp3Uh62ukKCTz4a`; confirmed by Amitai 2026-10-22). Upload the updated file each week (replace the previous version). Seeded 2026-10-22 with a lifetime-baseline snapshot (week 2026-10-18..2026-10-22, titles tagged `[lifetime baseline]`); compute week-over-week deltas from the first real weekly run, not against this row set.
- Week-over-week deltas in the report come from this CSV, not from Studio date ranges.

## Targets
Starter targets for a new, small podcast channel. Early numbers are **noisy**: under ~100 views or ~1,000 impressions per video, or in a video's first days, treat them as directional only, and judge by the trend in the History CSV and against the channel's own videos (YouTube's own advice), not single readings.

| Metric | Baseline 22 Oct 2026 | Starter target | Good / stretch |
|---|---|---|---|
| Episode impressions CTR | 0.2–1.8% | ≥ 2% | 4–6% |
| Episode retention at 0:30 | ep1: 33% at 0:23 | ≥ 60% | 75%+ (podcasts often 75–90%) |
| Episode avg % viewed (30–60 min) | low | ≥ 20% | 30%+ |
| Short avg % viewed | 38–44% (one at 174%) | ≥ 60% | 80%+; >100% = loops |
| Short viewed vs swiped away | — | ≥ 60% | 70–80%+ |
| Subscriber conversion (subs gained / views) | — | ≥ 0.5% (1 per 200 views) | 1%+ |

Notes: CTR depends on traffic source (Home lowers it, channel page/search raise it) and should be read with retention: high CTR with low AVD is clickbait. Subscriber conversion has no official benchmark; it's a working target to compare episodes vs Shorts (Shorts usually convert lower).

Sources:
- YouTube Help, Impressions & CTR FAQ (half of channels/videos sit at 2–10%; new videos and <100 views vary more): https://support.google.com/youtube/answer/7628154
- TubeBuddy, compare against your own channel: https://www.tubebuddy.com/blog/youtube-channel-not-growing/
- Artiphik, 30-second retention by niche (podcast 75–90%): https://artiphik.com/blog/the-first-10-seconds-retention-playbook
- Humble & Brag, retention benchmarks (interviews/podcasts 25–35%; Shorts 70%+ healthy, <50% a problem): https://humbleandbrag.com/blog/youtube-audience-retention-benchmarks
- CreatorFlowX, AVR by niche (podcast median ~30%): https://creatorflowx.com/benchmarks/youtube-retention-by-niche
- Lenos, Shorts viewed-vs-swiped tiers: https://www.lenostube.com/en/youtube-audience-retention-average-good-and-best-benchmarks/
- Retensis, Shorts metrics and swipe-away targets: https://retensis.com/blog/youtube-shorts-analytics-metrics-explained

Revisit after ~4 weekly runs and set targets from the channel's own median.

## Telegram
The weekly report posts automatically (Amitai OK'd it on 22 Oct; no per-week approval) to chat `-5592316645` (`tg-achim`) **only**: a concise text (headline, 3–5 key numbers vs targets/last week, the Page link), ending with `sent by Grokbot`. Requested ad-hoc reports post the same way. If Studio access failed, post nothing and tell Amitai. Format will be iterated after the first report.

## Done when
- Notes file with every step's raw numbers and sources (`/workspace/analytics/…md`) and any CSV exports.
- Report Page link.
- History CSV appended (local + Drive) and video map updated.
- Telegram text posted to `-5592316645` (or a stated reason it was not).

## Hand back
Page link, headline takeaway, what's missing (processing retention, items not in the table, RedCircle/Spotify), targets hit/missed, and whether Telegram was posted.

## Never
- Change anything in Studio (titles, thumbnails, settings, comments). Strictly read-only.
- Enter credentials or pass a verification prompt yourself; print or store secrets.
- Report the Grok Bot channel's stats by mistake: check the header.
- Post to any Telegram chat other than `-5592316645`, or post when access failed.
- Rely on browser screenshots as records: they don't land in `/workspace`. Write numbers into the notes file.
