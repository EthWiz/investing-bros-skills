import type React from 'react';
import {Chain} from './Chain';
import {Conflict} from './Conflict';
import {DoubleSpend} from './DoubleSpend';
import {GrowthBars} from './GrowthBars';
import {Mining} from './Mining';
import {MoneyFlow} from './lesson1/MoneyFlow';
import {SatoshiPanel} from './lesson1/Satoshi';
import {PriceDrop} from './PriceDrop';
import {PrivateKey} from './PrivateKey';
import {Terms} from './Terms';
import type {SceneProps} from './types';

// Scene components by the name a segment's `scene` uses. What each one needs (mode, anchors,
// content keys, assets) is in scenes.json, which make_lesson_props.py checks; the two must list
// the same names (test_render_lesson.py). Reusable scenes sit in lesson/, a lesson's own under
// lesson<N>/. A 'bubble' scene draws the whole frame behind Amitai's circle; a 'side' scene draws
// inside SidePanel. Text comes from the segment's content in the config, never from the component.
export const SCENES: Record<string, React.FC<SceneProps>> = {
  terms: Terms,
  'double-spend': DoubleSpend,
  'growth-bars': GrowthBars,
  'price-drop': PriceDrop,
  mining: Mining,
  chain: Chain,
  conflict: Conflict,
  'private-key': PrivateKey,
  'lesson1-money-flow': MoneyFlow,
  'lesson1-satoshi': SatoshiPanel,
};
