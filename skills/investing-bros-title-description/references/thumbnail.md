# Thumbnail (YouTube cover art)

Step 6 of `investing-bros-title-description`.

The thumbnail is drawn by an AI image tool (Amitai uses Gemini / Grok); this step writes the prompt and the headline. Thumbnails follow their own layout (below); shorts and teasers use the navy/gold brand from `investing-bros-show`.

## Inputs
- Episode number N and the episode's real content: the transcript or chapters (post-production) — the thumbnail sells what is actually in the episode.
- The channel's existing thumbnails for style: https://www.youtube.com/@nadavruskin905/videos (thumbnails at `https://i.ytimg.com/vi/<VIDEO_ID>/maxresdefault.jpg`).

## The channel layout (keep every episode)
- Dark cinematic, photoreal scene, often at night.
- **One** glowing focal object that *is* the episode's idea (the robotaxi, the rocket, the reactor).
- Huge bold 3D Hebrew headline with a thick black outline and soft glow — bottom centre (or top).
- A small rounded pill `פרק N`; under it small white `נדב ואמיתי רסקין`.
- Show logo in the top-left corner (the agent leaves that space empty; the logo is added after).

## Colour: restraint, one main colour
Not always gold — what matters is that it isn't too much.
- **One accent colour per thumbnail** on a dark (black / near-black) ground, plus white. The accent carries the light on the focal object, the headline and the pill. No second accent, no rainbow glow, no busy colour grading.
- Pick the accent from the topic: gold/amber for energy, cars, space or "big money"; emerald for fintech, stablecoins and money moving; electric blue for cloud, AI and data. Whatever fits the episode's object.
- Vary it from the previous episode's thumbnail so the channel grid doesn't look like one video repeated (episodes 1, 3, 5 and 6 were all gold).
- Calm composition: one object, lots of dark negative space, nothing in the corners but the logo spot.

## Steps
1. **Find the hook in the episode.** Read the chapters/transcript and name the single idea a viewer would click for. Prefer the episode's real thesis over its keyword — episode 6 is about money, stocks and banks moving onto the blockchain, not about bitcoin.
2. **Write 2–3 headline options**, each:
   - 2–4 words, readable on a phone at thumbnail size in under a second
   - true to what the hosts said (a question is fine: "המניה שלך על הבלוקצ'יין?")
   - different from the video title — the thumbnail and title should add up, not repeat (title `פרק 6 - מהפכת הטוקניזציה`, thumbnail `וול סטריט עוברת לבלוקצ'יין`)
   - no investment promises, no "you'll get rich", no fake urgency
3. **Pick one focal object and one accent colour.** The object shows the hook as a transformation or a contrast (a dollar bill dissolving into glowing blockchain cubes; a reactor glowing over a dark landscape) — one object, not a collage. Choose the accent as above.
4. **Fill the prompt** (English instructions, Hebrew text quoted exactly):
   ```
   YouTube thumbnail, 16:9, 1280x720, cinematic photoreal, premium finance-podcast style.
   One clear focal point in the center: <FOCAL OBJECT, described as a transformation or contrast>.
   Background: <SETTING tied to the topic>, dark, at night, softly lit, lots of negative space.
   Restrained palette: near-black and deep shadows, white, and a single accent colour, <ACCENT>,
   which carries the light on the object, the headline and the pill. No other colours, no
   colourful glow, high contrast, shallow depth of field, calm and uncluttered.
   Bottom center: huge bold 3D Hebrew headline in <ACCENT> (or white with an <ACCENT> glow) with a
   thick black outline, exactly: "<HEADLINE>".
   Under it a small <ACCENT> rounded pill reading "פרק <N>", and under that small white text
   "נדב ואמיתי רסקין".
   Leave the top-left corner empty for the channel logo. No other text, no watermarks.
   ```
   Worked example: [references/examples.md](thumbnail-examples.md).
5. **Check the result** before handing it on (if Amitai sends it back, or you generated it): Hebrew letters correct and right-to-left (AI tools garble Hebrew — regenerate or fix the text in Canva), headline readable when shrunk to ~160 px wide, the focal object obvious, really only one accent colour (regenerate if the tool added a second glow colour), top-left clear for the logo, nothing that looks like a real company's logo unless the episode is about that company.

## What to hand over
Send Amitai: the prompt (in a code block, ready to paste), the 2–3 headline options with the one used marked, the accent colour and why, and two lines of advice:
- check it on a phone at thumbnail size;
- YouTube Studio's **Test & compare** can A/B up to three thumbnails on the published video — worth running with two of the headlines.
The finished image goes in the episode's `promo/` folder as `thumbnail-פרק-N.jpg`.

## Never
- Put claims on the thumbnail the episode doesn't make, or investment promises.
- Repeat the video title word for word on the thumbnail.
- Alter the show logo or draw a new one — leave the corner empty for the real logo.
- Use images or likenesses you don't have rights to unless Amitai supplies them.
