// The data one crypto-course lesson video (16:9) needs. scripts/make_lesson_props.py writes it.
// All times are seconds on the lesson timeline (the trimmed takes joined in beat order, no speed-up).

export type LWord = {w: string; start: number; end: number};
export type LCaption = {start: number; end: number; words: LWord[]};

// How the frame is laid out for a stretch of the lesson:
//  full:   only Amitai (zoom 1 = wide, >1 = punch-in; a zoom change is a hard cut, like a second camera)
//  side:   Amitai moves right, a navy panel on the left carries the scene
//  bubble: a full-screen scene, Amitai in a circle bottom right (his side)
// `scene` names the lesson's component for a side or bubble stretch (lesson/scenes.ts).
export type Mode = 'full' | 'side' | 'bubble';
export type Segment = {start: number; end: number; mode: Mode; zoom?: number; scene?: string};

export type LessonProps = {
  base: string;                  // the joined takes in public/ (make_lesson_base.py)
  duration: number;
  lesson: number;
  title: string[];               // the lesson name as Amitai says it, one strip per line
  parts: string[];               // the lesson's parts, Amitai's words (the agenda and the progress marker)
  partStarts: number[];          // when each part starts (same order as parts)
  disclaimerBeat: number;        // the beat with the disclaimer strip; captions rise above it
  beats: {n: number; start: number; end: number}[];
  segments: Segment[];
  captions: LCaption[];
  at: Record<string, number>;    // graphic anchors: key -> the time its word is spoken
};

// What a lesson's own scene component gets: the anchors and its segment's span.
export type SceneProps = {at: Record<string, number>; start: number; end: number};
