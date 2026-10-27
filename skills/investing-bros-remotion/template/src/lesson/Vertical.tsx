import React from 'react';
import {AbsoluteFill} from 'remotion';
import {NAVY, fontFaces} from '../brand';
import {NavyPaper} from './kit';
import {SCENES} from './scenes';
import manifest from './scenes.json';
import type {LessonProps} from './types';

// "LessonScenes" (1080x1920): the lesson's scenes alone, on navy, from the same props as the Lesson,
// for checking a scene's 9:16 layout before it becomes part of a Short. Only scenes that scenes.json
// marks `vertical` are drawn; the rest of the timeline stays empty navy. No camera, no captions.
const VERTICAL = new Set(Object.entries(manifest).filter(([k, v]) => !k.startsWith('_') && (v as {vertical?: boolean}).vertical).map(([k]) => k));

export const LessonScenes: React.FC<LessonProps> = (p) => (
  <AbsoluteFill style={{background: NAVY}}>
    <style>{fontFaces()}</style>
    <NavyPaper id="vbg" />
    {p.segments.filter((s) => s.scene && VERTICAL.has(s.scene)).map((s, i) => {
      const Scene = SCENES[s.scene!];
      return <Scene key={i} at={p.at} start={s.start} end={s.end} content={s.content ?? {}} assets={p.assets ?? {}} />;
    })}
  </AbsoluteFill>
);
