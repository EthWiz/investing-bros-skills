import React from 'react';
import {Composition} from 'remotion';
import {Short} from './Short';
import type {ShortProps} from './props';
import sample from './sample-props.json';
import {Lesson} from './lesson/Lesson';
import type {LessonProps} from './lesson/types';
import {LessonScenes} from './lesson/Vertical';

export const FPS = 24;
export const LESSON_FPS = 30;   // the takes are 30 fps; the lesson keeps their frame rate

// "Short": render_short.py passes the real props with --props; sample-props.json (episode 8,
// short 05) is what Studio shows by default. "Lesson": a 16:9 crypto-course lesson; render_lesson.py
// passes its props (make_lesson_props.py). "LessonScenes": the same props, 9:16, only the scenes that
// lay themselves out vertically (render_lesson.py --vertical), to check them before a Short uses them.
const EMPTY_LESSON = {base: 'base.mp4', duration: 1, lesson: 1, title: [], parts: [], partStarts: [], disclaimer: null,
  beats: [], segments: [], captions: [], at: {}, assets: {}} as LessonProps;

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Short"
      component={Short}
      width={1080}
      height={1920}
      fps={FPS}
      durationInFrames={1}
      defaultProps={sample as unknown as ShortProps}
      calculateMetadata={({props}) => ({
        durationInFrames: Math.round(props.baseDuration * FPS),
      })}
    />
    <Composition
      id="Lesson"
      component={Lesson}
      width={1920}
      height={1080}
      fps={LESSON_FPS}
      durationInFrames={1}
      defaultProps={EMPTY_LESSON}
      calculateMetadata={({props}) => ({
        durationInFrames: Math.round(props.duration * LESSON_FPS),
      })}
    />
    <Composition
      id="LessonScenes"
      component={LessonScenes}
      width={1080}
      height={1920}
      fps={LESSON_FPS}
      durationInFrames={1}
      defaultProps={EMPTY_LESSON}
      calculateMetadata={({props}) => ({
        durationInFrames: Math.round(props.duration * LESSON_FPS),
      })}
    />
  </>
);
