import type React from 'react';
import {GlossaryPanel} from './lesson1/Glossary';
import {MoneyFlow} from './lesson1/MoneyFlow';
import {SatoshiPanel} from './lesson1/Satoshi';
import type {SceneProps} from './types';

// Each lesson's custom scenes, by the name a segment's `scene` uses. A 'bubble' scene draws the
// whole frame behind Amitai's circle; a 'side' scene draws inside SidePanel. Add a lesson's
// scenes under lesson<N>/ and list them here (make_lesson_props.py refuses unknown names).
export const SCENES: Record<string, React.FC<SceneProps>> = {
  'lesson1-money-flow': MoneyFlow,
  'lesson1-satoshi': SatoshiPanel,
  'lesson1-glossary': GlossaryPanel,
};
