# Lesson video: beats, face first, Remotion on top

Decided with Amitai on 2026-10-26 for lesson 1, and the default for every lesson. Motion and rendering belong to `investing-bros-remotion`; colours, type and artwork to `investing-bros-brand`. This page says how a lesson video is put together.

## The approach
- **Amitai's face carries the lesson; graphics punctuate it.** The video is not the deck presented slide by slide. The deck stays a handout in the lesson folder; the video is built from the script.
- **Nothing static for long.** No more than about 12 seconds on screen without a change: a graphic coming in, a reveal, a punch-in or a cut. Word-timed reveals give most of these for free.
- **The first 30 seconds are face only.** No full-screen graphic there; a graphic at 0:05 reads as a webinar. The lesson title shows for 3 seconds at most.
- **The disclaimer is one short beat** (about 10 seconds), spoken, with a strip at the bottom of the screen: `תוכן לימודי, לא ייעוץ השקעות`. No full disclaimer slide in the video.
- **No agenda slide.** Say what the lesson covers in one sentence, show the parts as small cards for a few seconds, then keep them as a progress marker in a corner for the whole lesson (one mark per part).
- Length: about 10 minutes, 8 to 12 at most. A lesson that runs over is split, not sped up.

## Beats
A beat is one point of the lesson, 20 to 60 seconds, recorded as its own take. The script (SKILL.md step 6) is written in numbered beats, each with an `על המסך:` line that picks one of these:

| On screen | When | Remotion |
|---|---|---|
| Only Amitai | Opening, disclaimer, summary, any beat that is an argument rather than a mechanism | none, or a lower strip |
| A card beside him, his face stays in view | Definitions, short lists, the end card: terms or items appear one at a time on the word that names them | existing `card` mode, or `inset` for a larger card |
| Full screen, his face in a small corner bubble | Mechanisms that need a picture: how money moves today, double spending, the shared ledger, the chain, consensus | needs a new mode (see What still has to be built) |
| Background footage | Dates and history, such as 2009 and Satoshi: headlines, the first page of a document | stills staged into the composition; no stock footage |

## Workflow
1. **Script in beats** (SKILL.md step 6). Read it aloud once and time it before recording.
2. **Record each beat as a separate take**, face to camera with a teleprompter, in 4K, so the edit can punch in to 1080p and a single camera looks like two angles. A stumble costs one beat, not the lesson.
3. **Word timings.** Transcribe each take word by word with the show's tools (`transcribe_clip.py` in `investing-bros-shorts`, then `make_captions.py` in `investing-bros-remotion`), against the script as the proofread text. Every graphic is anchored to a spoken word, so re-timing a graphic is a one-line change, not frame counting.
4. **Graphics.** Each beat's `על המסך` line becomes an entry in the lesson's props: the word it starts on, the mode, and its content. Card text is Amitai's own words from the script; a number on screen is one he says.
5. **Captions on the whole lesson**, calmer than the Shorts: two lines at the bottom (`caption_style: "line"` in `investing-bros-remotion`), not the kinetic Shorts style.
6. **Render, review, file.** Amitai reviews the cut before anything is uploaded. Nothing goes public without his OK.

## Animations: build few, reuse them
- **Per lesson, one or two custom animations** for the beats that teach, and everything else from a small set of reusable cards (a term card, a row of items that tick on, an end card). Animating every beat in every lesson doesn't ship.
- **Build each custom animation as one component with props**, so it can play twice with a different ending. Lesson 1: the double-spend animation plays once as the problem (the shekel reaches Dani and Yossi) and once with the shared ledger behind it (the second payment is rejected).
- **Right to left.** Graphics enter from the right, and flows (money moving, steps, a chain) run right to left, Amitai's side on the right. Hebrew in Heebo; brand colours from `investing-bros-brand`.
- **Every custom animation in 16:9 and 9:16** from the start, so it doubles as a Short: two or three Shorts per lesson. Shorts then follow `investing-bros-shorts`.

Lesson 1, first version: full animations for double spending (beats 7 and 8) and the chain with a block someone changes (beat 9); everything else as cards. Later, if the format works: money passing through intermediaries (beat 4), the bank's ledger becoming everyone's copy (beat 8), and Proof of Work vs Proof of Stake (beat 10).

## What still has to be built
The `investing-bros-remotion` template renders vertical Shorts today. A lesson needs, as template changes in that skill (each a PR with a test, per the show's working rules, never a one-off edit in a work folder):
- a 16:9 lesson composition that takes the recorded takes, the word timings and the lesson's props;
- the full-screen mode with Amitai in a corner bubble;
- the progress marker and the lower disclaimer strip;
- the reusable cards above, and each lesson's custom animations.

Until these exist, stop at the script and the recordings, and propose the template change to Amitai rather than building a renderer in the course folder.

## Files
In the lesson's Drive folder: the takes in `extras/` (`קטע-NN.mp4`, NN = the beat number in the script), the finished lesson as `שיעור-N-וידאו.mp4` in the folder itself, and Shorts made from the lesson in `Shorts/`.
