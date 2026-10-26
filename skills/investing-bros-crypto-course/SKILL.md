---
name: investing-bros-crypto-course
description: >-
  Make the free seven-lesson Hebrew crypto course (קורס קריפטו) for the
  אחים להשקעות YouTube channel: the lesson plan, a slide deck per lesson
  in the show's brand with speaker notes, the recording script in beats, the
  lesson video (Amitai on camera, Remotion animations on top), and filing
  each lesson in its Drive folder. Carries Amitai's fixed stance (Bitcoin as
  the base, a small Ethereum position, great caution with every other token)
  and the disclaimer rules. Use when Amitai says "crypto course", "קורס
  קריפטו", "lesson N", "שיעור N", "slides for lesson N", "מצגת לשיעור",
  "תסריט לשיעור", "וידאו לשיעור", "beats", "קטעים" or asks about the course
  plan.
---
# Investing Bros crypto course

Load `investing-bros-show` first (naming, Drive tree, approvals) and `investing-bros-brand` for every visual decision. The lesson plan and each lesson's status are in [references/course-plan.md](references/course-plan.md); how a lesson video is made is in [references/video-production.md](references/video-production.md).

## When to use
Any work on the crypto course: planning a lesson, its slides, its script, recording and animating its video, filing it in Drive, or changing the course plan. The course is not an episode: it has no `פרק N` folder, RedCircle draft or episode number.

## Inputs
- Lesson number N **as Amitai states it**, and its topic from the course plan. A topic change is Amitai's call; update the plan when he makes it.
- For revisions: the lesson's existing deck link (course plan) or Drive folder.

## Course rules (decided 2026-10-26)
- Free, on the אחים להשקעות channel as one playlist, seven lessons, Hebrew, for Israeli beginners. Risk is covered inside each lesson, not as a lesson of its own. Each lesson stands on its own, since most viewers arrive from search.
- **The stance, the same in every lesson that touches it:** Bitcoin is the base; of all the altcoins, only Ethereum gets a small position; great caution with every other token, and in most cases don't touch it. Present it as Amitai's personal approach.
- **Disclaimer:** lesson 1 opens, right after the hook, with a short disclaimer beat: educational content, not investment advice; Amitai isn't a licensed investment adviser; invest only what you can afford to lose. In the video it is spoken with a strip at the bottom of the screen (`תוכן לימודי, לא ייעוץ השקעות`); the deck keeps it as a slide. Any slide stating the stance carries the line `זו הגישה האישית שלי ולא ייעוץ השקעות מותאם אישית`. Never say "buy now", a target price, or a percentage of anyone's portfolio.
- Facts follow the show's hard rules: every number, date and claim has a source URL in the speaker notes or the script, and Israel-specific facts (tax, exchanges, banks, funds) are checked again before recording because they change.

## Steps
1. **Plan.** Read the lesson's row in the course plan. Write the outline (one sentence per part, 12–16 slides) and confirm it with Amitai before building.
2. **Research.** Collect sources for every fact. If something can't be verified, leave it out or mark it in the speaker notes as unchecked.
3. **Deck.** Build it as a Claude Slides artifact: brand palette and Heebo from `investing-bros-brand`, Hebrew right-to-left as in [references/slides-rtl.md](references/slides-rtl.md), speaker notes in Hebrew on every slide as talking points. Title the deck `קורס קריפטו - שיעור N: <נושא>` (plain hyphen). Add the deck link to the course plan.
4. **Review.** Send Amitai the deck link and apply his changes. The link is private until he shares it from the deck's Share menu.
5. **Drive.** Export the deck as a PDF (the deck page's export, which needs a claude.ai sign-in; if the browser isn't signed in, ask Amitai to sign in or to export it himself) and upload it to the lesson's folder as `מצגת-שיעור-N.pdf`, replacing any older file of that name. Confirm it shows as `application/pdf`.
6. **Script.** When Amitai asks, write the recording script from the deck, split into numbered beats (`קטע N: <נושא> (כ-X שניות)`): one point each, 20–60 seconds, recorded as separate takes. Open with a hook, keep the disclaimer to one short beat, end with a recap and the pointer to the next lesson; aim for about 10 minutes. Under each beat put an italic `על המסך:` line for the editor (only you, a card beside you, or full screen with you in a corner), then the spoken text. End with a sources list. Create it as a Google Doc named `תסריט-שיעור-N` in the lesson's folder (Drive `create_file` from right-to-left HTML), with keep-with-next on each heading and its `על המסך` line.
7. **Record and collect the takes.** Amitai records each beat as its own take, face to camera, ideally in 4K. Takes arrive under his own names (`Beat 1 - take 1.mov`), often in a local `lesson-N/` folder. Check each one with `ffprobe` and say in the hand-back if they are below 4K (720p is upscaled, so punch-ins stay small). With several takes of a beat, use the latest unless he says otherwise. Recording can come in batches: a lesson can be cut from the beats recorded so far.
8. **Transcribe.** Run Whisper on each take, word by word (see [references/video-production.md](references/video-production.md) → Workflow). The words file per take, `קטע-NN.json`, is the transcript of record: it goes to Drive and the captions are rebuilt from it. Proofread against what Amitai actually said, not against the script: he departs from it, and captions and card text must follow what he said.
9. **Animate and render.** Each lesson has a config, `references/lessons/lesson-N-video.json`: the trims, the proofread words, the anchor phrase for every graphic and the layout. `scripts/make_lesson_base.py` trims and joins the takes, `make_lesson_props.py` and `render_lesson.py` (in `investing-bros-remotion`) build the props and render the 16:9 `Lesson` composition. Look at the stills before the full render. The approach is in the video reference: face first, graphics on the spoken word, one or two custom scenes per lesson plus reusable cards, captions throughout. Build custom scenes for the beats that are recorded, as components in the template (`src/lesson/lessonN/`). A cut made before every beat is recorded is a draft, `שיעור-N-וידאו-טיוטה.mp4`. Every custom scene is also wanted in 9:16 for Shorts (not built yet for lesson 1).
10. **File in Drive.** Put in the lesson folder's `extras/`: the takes as `קטע-NN.mp4` (`make_lesson_base.py build --extras`, a stream copy), the joined base `שיעור-N-בסיס.mp4`, the Whisper words `קטע-NN.json` and the captions `שיעור-N-כתוביות.srt` (`make_lesson_props.py --srt`). The video (`שיעור-N-וידאו.mp4`, or the draft) goes in the lesson folder itself. Choosing the upload route: the Drive connector works for the small text files. Videos go with `scripts/drive.sh put FILE FOLDER_ID` when the rclone remote `show` is set up (optional, see `investing-bros-show` → environment). Otherwise, stage the files in the Drive layout in a local `להעלאה-לדרייב/` folder and ask Amitai to drag them in. Confirm afterwards that they are in Drive.
11. **Review and upload.** Amitai reviews the cut; send him a 720p copy under 30 MB if he will watch on his phone. Titles, description and upload follow the episode skills he names (`investing-bros-title-description`, `investing-bros-episode-upload`); nothing goes public without his OK. Shorts from the lesson follow `investing-bros-shorts`.

## Done when
- The lesson's folder `קורס קריפטו/שיעור N — נושא/` holds `מצגת-שיעור-N.pdf` (and the Google Doc `תסריט-שיעור-N` when a script was asked for).
- When a video was made: in `extras/` the takes `קטע-NN.mp4`, their Whisper words `קטע-NN.json`, the joined base `שיעור-N-בסיס.mp4` and the captions `שיעור-N-כתוביות.srt`; the video `שיעור-N-וידאו.mp4` (or the draft `-טיוטה`) in the lesson folder; its Shorts in `Shorts/`. The lesson's config `references/lessons/lesson-N-video.json` and any new scene are merged in this repo.
- The course plan lists the lesson's deck and script links and current status.

## Hand back
The deck link, the Drive folder link, the sources used, any fact left unchecked, and anything about the right-to-left layout not yet checked in the rendered deck. For a video: its length, the takes' resolution, which beats are in it, the stills sheet, any words in the captions you couldn't confirm from the audio, and which files are in Drive (or still waiting to be dragged in).

## Never
- Recommend a specific amount, percentage, entry price or timing.
- Present any token other than Bitcoin and Ethereum as something to buy.
- Put English words inside a Hebrew sentence on a slide (see the RTL reference).
- Make the lesson video by presenting the deck slide by slide, or open it with a full-screen graphic in the first 30 seconds.
- Put text on a lesson graphic that Amitai doesn't say, or a number he doesn't say. The one exception: a document he describes, shown as a page (the white paper's title, the text in the first block), in its original language.
- Create a second `קורס קריפטו` folder or a second folder for the same lesson; find them by the `שיעור N` prefix.
