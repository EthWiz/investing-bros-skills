# Recording setup for lesson takes

Decided with Amitai on 2026-10-28, after lesson 1's first takes changed zoom between beats (720p QuickTime
recordings with Center Stage reframing him) and his first OBS test. Every lesson is recorded the same way, so
the takes match across beats and lessons.

## Camera
- His iPhone as a Continuity Camera, in OBS (source "iPhone Camera", 1920×1080, 30 fps), mounted in landscape
  on a fixed stand and not touched during a session.
- **Center Stage off, and Reactions off**: green camera icon in the menu bar → Video Effects, while OBS is the
  app using the camera. macOS keeps these per app, so QuickTime has its own. Center Stage is what zoomed beat 1
  in and later beats out; Reactions fire effects on hand gestures. Portrait, Studio Light and Desk View off too.
- The Blackmagic Camera app can't be an OBS source. Recording 4K on the phone is the alternative if punch-ins
  need more resolution; it adds a file transfer and an audio sync per take.

## OBS
- Settings → Video: base and output 1920×1080, 30 fps. Output: recording quality "High Quality, Medium File
  Size" (not "Small", which gave 2.6 Mb/s and a soft face), Hybrid MOV, hardware H.264.
- Audio: one source, the PD100X ("Audio Input Capture"). Global Mic/Auxiliary Audio is Disabled, otherwise the
  MacBook's built-in mic is mixed in. If "Capture Card Device" shows a meter, it's the iPhone's mic: mute it.
- Mic gain on the PD100X so normal speech peaks around −10 to −6 dB in OBS's mixer. A take that peaks at
  0 dBFS is clipped, and levelling to −14 LUFS later can't repair it.
- Framing guide: a screenshot of a good frame as an image source ("Ghost") at about 30% opacity on top,
  shown to line up and hidden before recording, or it is burned into the take.

## Framing and light
- Face centred left to right (the lesson layout keeps the space beside him free), the top of his head about
  10% from the top of the frame, eyes about a third of the way down. Retake the Ghost screenshot whenever
  the setup changes.
- A light in front of him, a little to one side, brighter than the background. More light means a faster
  shutter, so moving hands blur less, which helps every way of replacing the background.
- Gestures beside the body rather than across the face: hands crossing the face at speed break every cutout.

## Background
Takes go on the navy studio background (`investing-bros-brand` → `assets/lesson-background-navy-studio.jpg`),
put in by `make_lesson_base.py build` from the config's `background` block (video reference → Workflow).
- **Until the green screen arrives (`vision`):** a plain, smooth sheet behind him, with Apple Vision cutting
  him out. Known misses: a high grey chair back shows beside the ear and neck (use a low chair or raise the
  camera), and fast hands crossing the face leave patches of the sheet.
- **With the green screen (`chroma`):** taut, creases steamed out, 1–1.5 m behind him, filling the frame,
  lit evenly by its own light. Nothing green on him or in frame. A key removes only green, so the chair back
  has to be hidden or covered in green. Tune `key` on the first green take and keep it in the config.
- Models compared on 2026-10-28 (beat 1, take 2): Robust Video Matting was no better than Apple Vision;
  MatAnyone had the cleanest edges but erased hands that weren't in its first-frame mask. All three failed
  where the hands crossed the face. Revisit only if the green screen doesn't work out.

## Each session
1. Video Effects checked for OBS, then 10 seconds of leaning side to side and raising both hands: the frame
   must not move.
2. Line up with the Ghost overlay, then hide it.
3. Talk at normal volume and check the PD100X meter.
4. With the green screen, 5 seconds of the empty screen first (a reference for checking the key).
5. One take per beat; OBS names files by time, so rename them `Beat N - take M.mov` into `lesson-N/`.
