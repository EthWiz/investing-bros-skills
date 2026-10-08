---
name: investing-bros-cover-art
description: >-
  Write the image-generation prompt (and headline options) for an Investing
  Bros / אחים להשקעות episode's YouTube thumbnail, in the channel's gold
  cinematic style and built for click-through. Use when Amitai asks for
  "cover art", "a thumbnail", "תמונה ממוזערת", "תמונת פרק", "קאבר לפרק" or a
  prompt to give an AI image tool for episode N.
---
# Investing Bros cover art (YouTube thumbnail)

Load `investing-bros-show` first.

The thumbnail is drawn by an AI image tool (Amitai uses Gemini / Grok); this skill writes the prompt and the headline. It is the one place the channel's **gold cinematic** style applies — shorts and teasers use the black/emerald brand from `investing-bros-show`.

## When to use
After the episode's topic and title are settled (usually after post-production), when Amitai asks for cover art, a thumbnail, or "a prompt for an AI".

## Inputs
- Episode number N and the episode's real content: the transcript or chapters (post-production) — the thumbnail sells what is actually in the episode.
- The channel's existing thumbnails for style: https://www.youtube.com/@nadavruskin905/videos (thumbnails at `https://i.ytimg.com/vi/<VIDEO_ID>/maxresdefault.jpg`).

## The channel style (episodes 1–6)
- Dark cinematic, photoreal scene, often at night; warm gold/amber light against black and navy.
- **One** glowing focal object that *is* the episode's idea (the robotaxi, the rocket, the reactor).
- Huge bold 3D Hebrew headline in metallic gold, thick black outline, soft glow — bottom centre (or top).
- A small gold rounded pill `פרק N`; under it small white `נדב ואמיתי רסקין`.
- Show logo in the top-left corner (the agent leaves that space empty; the logo is added after).

## Steps
1. **Find the hook in the episode.** Read the chapters/transcript and name the single idea a viewer would click for. Prefer the episode's real thesis over its keyword — episode 6 is about money, stocks and banks moving onto the blockchain, not about bitcoin.
2. **Write 2–3 headline options**, each:
   - 2–4 words, readable on a phone at thumbnail size in under a second
   - true to what the hosts said (a question is fine: "המניה שלך על הבלוקצ'יין?")
   - different from the video title — the thumbnail and title should add up, not repeat (title `פרק 6 – מהפכת הטוקניזציה`, thumbnail `וול סטריט עוברת לבלוקצ'יין`)
   - no investment promises, no "you'll get rich", no fake urgency
3. **Pick one focal object** that shows the hook as a transformation or a contrast (a dollar bill dissolving into golden blockchain cubes; a reactor glowing over a dark landscape). One object, not a collage.
4. **Fill the prompt** (English instructions, Hebrew text quoted exactly):
   ```
   YouTube thumbnail, 16:9, 1280x720, cinematic photoreal, premium finance-podcast style.
   One clear focal point in the center: <FOCAL OBJECT, described as a transformation or contrast>.
   Background: <SETTING tied to the topic>, dark, at night, softly lit.
   Dramatic warm gold and amber rim light against deep black and navy shadows, high contrast,
   shallow depth of field, no clutter.
   Bottom center: huge bold 3D Hebrew headline in metallic gold with a thick black outline and
   soft glow, exactly: "<HEADLINE>".
   Under it a small gold rounded pill reading "פרק <N>", and under that small white text
   "נדב ואמיתי רסקין".
   Leave the top-left corner empty for the channel logo. No other text, no watermarks.
   ```
   Worked example: [references/examples.md](references/examples.md).
5. **Check the result** before handing it on (if Amitai sends it back, or you generated it): Hebrew letters correct and right-to-left (AI tools garble Hebrew — regenerate or fix the text in Canva), headline readable when shrunk to ~160 px wide, the focal object obvious, top-left clear for the logo, nothing that looks like a real company's logo unless the episode is about that company.

## Hand back
Send Amitai: the prompt (in a code block, ready to paste), the 2–3 headline options with the one used marked, and two lines of advice:
- check it on a phone at thumbnail size;
- YouTube Studio's **Test & compare** can A/B up to three thumbnails on the published video — worth running with two of the headlines.
Finished images go to the episode's `promo/` folder.

## Never
- Put claims on the thumbnail the episode doesn't make, or investment promises.
- Repeat the video title word for word on the thumbnail.
- Alter the show logo or draw a new one — leave the corner empty for the real logo.
- Use images or likenesses you don't have rights to unless Amitai supplies them.
