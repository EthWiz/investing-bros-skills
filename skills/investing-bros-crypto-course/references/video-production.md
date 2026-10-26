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
| Only Amitai | Opening, disclaimer, summary, any beat that is an argument rather than a mechanism | `full`, with punch-ins; strips on the wall |
| A card beside him, his face stays in view | Definitions, short lists, the end card: terms or items appear one at a time on the word that names them | `side` with a scene in the panel |
| Full screen, his face in a small corner bubble | Mechanisms that need a picture: how money moves today, double spending, the shared ledger, the chain, consensus | `bubble` with a scene |
| Background footage | Dates and history, such as 2009 and Satoshi: headlines, the first page of a document | `side`; documents drawn in the scene, no stock footage |

## Workflow
Each lesson has one config, `references/lessons/lesson-N-video.json` (lesson 1 is the worked example): the takes and their trims, the proofread words of each take, an anchor phrase for every graphic, and the layout. Paths below: `CC` = this skill's `scripts/`, `RM` = `investing-bros-remotion`'s `scripts/`, `WORK` = a work folder outside the repo.

1. **Script in beats** (SKILL.md step 6). Read it aloud once and time it before recording.
2. **Record each beat as a separate take**, face to camera with a teleprompter, ideally in 4K, so the edit can punch in to 1080p and a single camera looks like two angles. A stumble costs one beat, not the lesson. Lesson 1's takes came in 720p (`Beat N - take 1.mov`); they work upscaled, with punch-ins of 1.2x at most.
3. **Trims.** `python3 CC/make_lesson_base.py suggest lesson-N-video.json --takes-dir DIR` prints a from/to per take: 0.3 s before the speech, 0.45 s after it, ignoring the click of the camera starting and stopping. Put them in the config and check them against the words in step 4.
4. **Words.** Transcribe each whole take (they are short) with Whisper, word by word:
   `whisper קטע-NN.mp4 --model large-v3-turbo --model_dir ~/.cache/whisper --language he --word_timestamps True --output_format json --condition_on_previous_text False --fp16 False --output_dir WORK/words`
   (the Homebrew `whisper` command on Amitai's Mac; elsewhere `transcribe_clip.py` in `investing-bros-shorts` writes a format the props script also reads). Six takes, 3.5 minutes of speech, took about 10 minutes on the Mac's CPU. Whisper makes up words over silence at the end of a take ("תודה רבה."): trim them out.
5. **Proofread** each take into the config's `proofread`: what Amitai said, not the script. He departs from it ("או הבנק המרכזי", "קוראים לזה אינפלציה", "מילה שנייה היא קריפטו"), and captions and card text follow what he said. Where the audio can't be checked and Whisper is garbled, mark the guess in the config's `notes` and in the hand-back.
6. **Base.** `python3 CC/make_lesson_base.py build lesson-N-video.json --takes-dir DIR -o WORK/base.mp4 --extras WORK/drive/extras` trims the takes, scales them to 1920×1080, joins them in beat order and levels the audio to -14 LUFS; `--extras` also writes the takes as `קטע-NN.mp4` for Drive. No speed change.
7. **Props.** `python3 RM/make_lesson_props.py lesson-N-video.json --words-dir WORK/words -o WORK/props.json --srt WORK/drive/extras/שיעור-N-כתוביות.srt`. It aligns the proofread words to Whisper's timings, makes two-line captions that keep sentences whole, resolves every anchor phrase to the moment it is said, and refuses a phrase it can't find, an unknown scene, a full-screen or side graphic in the first 30 s, and a punch-in over 1.25x. Re-timing a graphic = changing its phrase or offset in the config.
8. **Stills, then render.** `python3 RM/render_lesson.py --props WORK/props.json --base WORK/base.mp4 --fonts FONTS --logo LOGO --out WORK/lesson.mp4 --stills 25,38,50,64,90,100,120,140,160,180` (Heebo TTFs from `brand.py fonts` in `investing-bros-shorts`, the logo from `investing-bros-brand`). Check the sheet: captions under Amitai, nothing over his face, every card's text readable, the panel edges flush with the frame. Then the same command without `--stills`, in the background (3:16 took 8.5 minutes on 10 cores).
9. **File and review.** Drive files as in SKILL.md step 10. Amitai reviews the cut (a 720p copy under 30 MB for his phone: the full file can't be sent there). Nothing goes public without his OK.

## Layout (lesson 1, the default)
Amitai sits in the middle of the frame, with the wall to his left free. The composition (`src/lesson/` in the template) does the rest:
- **Only Amitai (`full`):** zoom 1 is the wide shot. Punch-ins of 1.1–1.2x are hard cuts at a sentence start (`[beat, "first words", -0.15]`), so the face beats change every 5–15 s. Use zoom 1 while something sits on the wall (name, title, agenda).
- **Name and title:** the name strips (`אמיתי רסקין` / `אחים להשקעות`) when he says his name; the title strips (`שיעור N` + the name as he says it) for 3 s at most, near the end of the opening beat. Both on the wall to his left.
- **Disclaimer:** the strip `תוכן לימודי, לא ייעוץ השקעות` at the bottom for the whole disclaimer beat; captions move up above it.
- **Agenda:** the parts come in on the wall one by one as he names them (`ag1`, `ag2`, …), then shrink into the progress marker top left (the top right is his head once he moves). The marker shows the current part by name for the rest of the lesson.
- **Card beside him (`side`):** he slides right and a navy panel with a torn edge comes in from the left, one beat long. Scenes inside it change on his words.
- **Full screen (`bubble`):** the scene covers the frame and Amitai sits in a gold-ringed circle bottom right, on his side; flows run right to left, starting from him.
- **Captions:** two calm lines at the bottom, the word being said in gold, under Amitai: centred in `full`, on his side in `side`, left of the circle in `bubble`.

## Animations: build few, reuse them
- **Per lesson, one or two custom animations** for the beats that teach, and everything else from a small set of reusable cards (a term card, a row of items that tick on, an end card). Animating every beat in every lesson doesn't ship.
- **Build each custom animation as one component with props**, so it can play twice with a different ending. Lesson 1: the double-spend animation plays once as the problem (the shekel reaches Dani and Yossi) and once with the shared ledger behind it (the second payment is rejected).
- **Right to left.** Graphics enter from the right, and flows (money moving, steps, a chain) run right to left, Amitai's side on the right. Hebrew in Heebo; brand colours from `investing-bros-brand`.
- **Every custom animation in 16:9 and 9:16** from the start, so it doubles as a Short: two or three Shorts per lesson. Shorts then follow `investing-bros-shorts`. (The lesson 1 scenes exist in 16:9 only so far.)
- **Build for the beats that are recorded.** Plan the custom scenes from the script, but build first the ones whose beats are in hand: a scene for a beat not yet recorded can't be timed or checked.
- **A document Amitai talks about may appear as a page** (the white paper's first page, the text Satoshi left in the first block), in its own language, drawn in the composition. That is the only English on a lesson graphic, and the only text he doesn't say word for word.

Lesson 1 so far (beats 1–6, a draft): the money moving through the intermediaries (beat 4, `lesson1-money-flow`, full screen), 2008 and Satoshi (beat 5, `lesson1-satoshi`, side panel) and the three words (beat 6, `lesson1-glossary`, side panel). Next, when the beats are recorded: double spending (beats 7 and 8), the chain with a block someone changes (beat 9); later, if the format works, the bank's ledger becoming everyone's copy (beat 8) and Proof of Work vs Proof of Stake (beat 10).

## Files
In the lesson's Drive folder:
- the lesson folder itself: the video `שיעור-N-וידאו.mp4`, or `שיעור-N-וידאו-טיוטה.mp4` for a cut made before every beat is recorded;
- `extras/`: the takes `קטע-NN.mp4` (NN = the beat number in the script), their Whisper words `קטע-NN.json`, the joined base `שיעור-N-בסיס.mp4` and the captions `שיעור-N-כתוביות.srt`, so the next pass can start from Drive without transcribing again;
- `Shorts/`: Shorts made from the lesson.

The config `references/lessons/lesson-N-video.json` and the lesson's scenes live in this repo, not in Drive.

## Still to build
- 9:16 versions of the custom scenes, for Shorts.
- A `check_lesson.py` like `check_short.py` (captions inside the frame, dead air at the cuts, loudness); today the stills sheet is the check.
- Lesson 1's other scenes once beats 7–14 are recorded: double spending (beats 7 and 8) and the chain with a changed block (beat 9) first.
