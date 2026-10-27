import React from 'react';
import {AbsoluteFill} from 'remotion';
import {CREAM, FONT, MUSTARD} from '../brand';
import {Paper, useTime} from './kit';
import {In, SidePanel} from './panels';
import type {SceneProps} from './types';

// Reusable 'side' scene: a heading, then terms that come in one by one, each with Amitai's
// definition under it; the term being explained stays bright, the earlier ones dim.
// content: {heading: {text, at}, items: [{term, def, at}]} (`at` already resolved to seconds).
type Item = {term: string; def?: string; at: number};

export const Terms: React.FC<SceneProps> = ({start, end, content}) => {
  const {t} = useTime();
  const items: Item[] = content.items;
  const active = items.reduce((acc, x, i) => (t >= x.at ? i : acc), -1);
  const size = items.length > 3 ? 58 : 70;
  return (
    <SidePanel start={start} end={end} id={`terms-${start}`}>
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'flex-start', paddingRight: 110, direction: 'rtl'}}>
        <In at={content.heading.at} style={{marginBottom: 40}}><Paper text={content.heading.text} size={56} bg={MUSTARD} /></In>
        {items.map((x, i) => (
          <In key={i} at={x.at} style={{marginBottom: 34, opacity: t < x.at ? 0 : i === active ? 1 : 0.55}}>
            <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-start', direction: 'rtl'}}>
              <Paper text={x.term} size={size} />
              {x.def ? (
                <div style={{marginTop: 10, marginRight: 8, fontFamily: FONT, fontWeight: 600, fontSize: 40, color: CREAM}}>{x.def}</div>
              ) : null}
            </div>
          </In>
        ))}
      </AbsoluteFill>
    </SidePanel>
  );
};
