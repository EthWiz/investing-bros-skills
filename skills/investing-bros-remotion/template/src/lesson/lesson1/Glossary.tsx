import React from 'react';
import {AbsoluteFill} from 'remotion';
import {CREAM, FONT, MUSTARD} from '../../brand';
import {Paper, useTime} from '../kit';
import {In, SidePanel} from '../panels';
import type {SceneProps} from '../types';

// Lesson 1, beat 6. Each definition is Amitai's own words from the take, not the script's.
// Three words, each on the moment it is said.
const TERMS = [
  {key: 'g1', term: 'בלוקצ׳יין', def: 'פנקס חשבונות משותף שאי אפשר לזייף'},
  {key: 'g2', term: 'קריפטו', def: 'כל המטבעות שרצים על הטכנולוגיה הזאת'},
  {key: 'g3', term: 'ביטקוין', def: 'מטבע הקריפטו הראשון, הסבא של כולם'},
];

export const GlossaryPanel: React.FC<SceneProps> = ({at, start, end}) => {
  const {t} = useTime();
  const active = TERMS.reduce((acc, x, i) => (t >= at[x.key] ? i : acc), -1);
  return (
    <SidePanel start={start} end={end} id="glossary">
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'flex-start', paddingRight: 110, direction: 'rtl'}}>
        <In at={at.g0} style={{marginBottom: 40}}><Paper text="שלוש מילים" size={56} bg={MUSTARD} /></In>
        {TERMS.map((x, i) => (
          <In key={x.key} at={at[x.key]} style={{marginBottom: 34, opacity: t < at[x.key] ? 0 : i === active ? 1 : 0.55}}>
            <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-start', direction: 'rtl'}}>
              <Paper text={x.term} size={70} />
              <div style={{marginTop: 10, marginRight: 8, fontFamily: FONT, fontWeight: 600, fontSize: 40, color: CREAM}}>{x.def}</div>
            </div>
          </In>
        ))}
      </AbsoluteFill>
    </SidePanel>
  );
};
