# Shorts style — from Amitai's approved reference (ref_amitai_cybercab.mp4, Ep1)

## Spec
- **Hook:** two stacked torn-paper strips, cream on top and yellow below, heavy dark (navy/black) Heebo text, centred just above the vertical middle (top of strips ≈ 0.37 H). Static, on screen from frame 1. Spec says it fades at ~1 s; **in the reference frames it stays until ~2.5 s** (visible at 2.4 s, gone by 2.8 s).
- **Persistent graphics:** the torn-paper podcast logo top-left (≈ x 56, y 150, 210 px wide at 1080). A small yellow name tag top-right with black text ("אמתי רסקין"). It appears ~0.5 s in and is **gone before the CTA** (absent from ~26 s in a 32.7 s ref).
- **Captions:** white heavy sans, subtle dark outline/shadow, NO box. Only keywords and numbers turn bright yellow (not every active word). 1–4 words per line, fast, lower third (≈ 0.76 H, above the platform UI).
- **Framing:** static tight head-and-shoulders close-up, no zooms, no jump cuts except to remove silence. 
- **No** b-roll, music or SFX.
- **CTA (~3 s before speech ends):** "הקישור לפרק המלא בתיאור" over the chest (≈ 0.61 H) with a yellow down arrow under it. **In the reference frames it is a cream torn-paper strip with dark text, not a translucent dark-grey rounded box**; the spec text and the frames disagree. v5 follows the frames.
- **End card (hard cut, ~3 s, silent):** dark navy (#09243B) background, top to bottom: big torn-paper logo; cream **pill** "פרק 1" with navy text (frames; the spec says small white text); the episode title "האם טסלה תנצח את המרוץ של נהיגה אוטונומית?" in bold white, two lines; the CTA in yellow; a yellow down arrow.
- **Loudness:** −14 LUFS integrated, peak below −1 dB.

## Noticed in the frames
- The ref is 720×1280 at 25 fps; ours render 1080×1920 at 24 fps.
- The ref's end card has a faint ghost of the frozen video/logo behind the navy, and **a caption from the speech ("רכב יותר קטן,") leaks onto the end card**. That's a bug: don't copy it.
- Strips are near-horizontal (≈ 0–1°), so they are tilted less than brand-rules allows.
- Hebrew punctuation is correct RTL ("?" on the left end).

## What the repo skill needs (gaps found building v5)
- `build_fullbleed.py`: a hook paper-strip option (PNG strips), caption Y as a config value, a keyword-only highlight mode, a persistent tag in output time (tags are in source time, which breaks with reordered pieces), a CTA overlay, and a hard-cut end card appended after the speech (the current end card dims the last 2.8 s *over* speech).
- `check_short.py`: should not warn "silence at the end" for a silent end card.

## Motion captions (Nadav, v6)
- **Rule:** 1 motion caption per ~20 s of Short (45 s → 2), spaced ~20 s apart, never overlapping the hook, CTA or end card.
- **What:** the key phrase or number from the speech, as one torn-paper strip (cream #F5EBD5 or mustard) with navy/black Heebo Black text (~96 px), tilted ±2°, centred in the caption zone (top of strip ≈ y 1370 at 1080×1920).
- **Motion (calm):** 0.3 s fade in plus a 50 px slide up, hold ~1.5–2 s, 0.3 s fade out. The normal word captions are removed for that window.
- **Built with:** `work/motion_caps.py` (uses `strip()` from `work/strips.py`, PIL+raqm) → `mc1.png`/`mc2.png`; added by hand to the generated `NAME_fb.sh` as `fade … alpha=1` and `overlay` with an animated `y` and `enable='between(t,a,b)'`; Cap events in those windows deleted from the `.ass`. This isn't in the repo skill yet; it belongs in `build_fullbleed.py` as a `motion` list `[[out_t0, out_t1, "text", "cream|mustard"]]`.
- v6 picks: "סיכון מאוד גדול" 10.8–12.9 s (cream), "פוקוס מטורף בעלויות" 31.1–33.5 s (mustard).

## Principle (Nadav, confirmed)
**Amitai's Short is the base template.** Every template element (hook strips, logo, name tag, captions, framing, CTA, end card, loudness) stays exactly as in v5/v6. Our additions (motion captions, explainers) are only layered on top. They never replace or restyle the template.

## Motion explainers (v7, replaces the v6 fade-and-slide)
- Same rule: 1 per ~20 s, outside hook/CTA/end card, normal captions hidden in that window.
- Built from the old reel pipeline's animation code (`/workspace/podcast/ep1/reel/mg.py`: `seg`, `ease_out`, `ease_back` pop-in/scale and staged reveals), restyled to the brand: navy/cream/mustard torn-paper strips (`strip()` from `work/strips.py`), navy Heebo Black, navy-outlined flat icons, **no glow, coins, cyan or orange** from the old card style. No SFX.
- Explainer 1 "סיכון מאוד גדול" (10.8–12.9 s): mustard warning triangle pops in (ease_back scale) with a damped wobble, then the cream strip wipes in right-to-left and settles at −2°; fade/scale out 0.3 s.
- Explainer 2 "פוקוס מטורף בעלויות" (31.1–33.5 s): mustard strip scale-pops and slides in from the right to +2°; three cream cost bars pop up in sequence, then shrink as a mustard down-arrow draws; fade out 0.3 s.
- Script: `work/explainers_v7.py` renders 1080×520 RGBA PNG sequences (`ex1/`, `ex2/`, 24 fps). They're overlaid at y=1110 in the hand-patched `ep1_lidar_v7_fb.sh` (`-itsoffset` + `overlay enable=between`). Not in the repo skill yet; it belongs in `build_fullbleed.py`/`build_composition.py` as brand card types.
