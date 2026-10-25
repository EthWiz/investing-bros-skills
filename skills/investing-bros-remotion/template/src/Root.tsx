import React from 'react';
import {Composition} from 'remotion';
import {Short} from './Short';
import type {ShortProps} from './props';
import sample from './sample-props.json';

export const FPS = 24;

// One composition, "Short". render_short.py passes the real props with --props;
// sample-props.json (episode 8, short 05) is what Studio shows by default.
export const RemotionRoot: React.FC = () => (
  <Composition
    id="Short"
    component={Short}
    width={1080}
    height={1920}
    fps={FPS}
    durationInFrames={1}
    defaultProps={sample as unknown as ShortProps}
    calculateMetadata={({props}) => ({
      durationInFrames: Math.round((props.baseDuration + props.endcardSeconds) * FPS),
    })}
  />
);
