import React from 'react';
import {interpolate} from 'remotion';
import {CREAM, FONT, HOOK_YELLOW, MUSTARD, NAVY, clamp} from '../../brand';
import {Paper, pop, useTime} from '../kit';
import {In, Scene, SidePanel} from '../panels';
import type {SceneProps} from '../types';

// Lesson 1, beat 5 (2008 and Satoshi). The white paper and the first block are drawn here, not images.

const Year: React.FC<{text: string; size?: number}> = ({text, size = 210}) => (
  <div style={{fontFamily: FONT, fontWeight: 900, fontSize: size, lineHeight: 0.95, color: HOOK_YELLOW,
    textShadow: '0 8px 20px rgba(0,0,0,.4)', direction: 'ltr'}}>{text}</div>
);

// The first page of the white paper, drawn (no image of the real file is staged).
const WhitePaper: React.FC<{at: number}> = ({at}) => {
  const {t, fps} = useTime();
  const k = pop(t, at, fps, 15, 120);
  const lines = [0.92, 0.88, 0.95, 0.7, 0.9, 0.93, 0.85, 0.6, 0.91, 0.88, 0.94, 0.5];
  return (
    <div style={{width: 430, height: 560, background: '#FBF8F1', borderRadius: 4, padding: '46px 44px', boxSizing: 'border-box',
      transform: `translateY(${(1 - k) * 80}px) rotate(${interpolate(k, [0, 1], [6, -3])}deg)`, opacity: k,
      boxShadow: '0 18px 40px rgba(0,0,0,.5)', direction: 'ltr', fontFamily: 'Times New Roman, serif', color: '#111'}}>
      <div style={{fontSize: 24, fontWeight: 700, textAlign: 'center', lineHeight: 1.25}}>Bitcoin: A Peer-to-Peer Electronic Cash System</div>
      <div style={{fontSize: 17, textAlign: 'center', marginTop: 16}}>Satoshi Nakamoto</div>
      <div style={{marginTop: 30}}>
        {lines.map((w, i) => (
          <div key={i} style={{height: 9, width: `${w * 100}%`, background: '#C9C4B8', marginBottom: 14, borderRadius: 2,
            marginTop: i === 4 || i === 8 ? 26 : 0}} />
        ))}
      </div>
    </div>
  );
};

// The text Satoshi left in the first block, typed out.
const GENESIS = 'The Times 03/Jan/2009 Chancellor on brink of second bailout for banks';
const GenesisBlock: React.FC<{at: number; typeAt: number}> = ({at, typeAt}) => {
  const {t, fps} = useTime();
  const k = pop(t, at, fps, 14, 150);
  const n = Math.floor(interpolate(t, [typeAt, typeAt + 2.4], [0, GENESIS.length], clamp));
  return (
    <div style={{width: 700, borderRadius: 24, background: CREAM, padding: '26px 34px 34px', boxSizing: 'border-box',
      transform: `scale(${interpolate(k, [0, 1], [0.85, 1])})`, opacity: k, boxShadow: '0 14px 30px rgba(0,0,0,.45)'}}>
      <div style={{display: 'flex', direction: 'rtl', justifyContent: 'space-between', alignItems: 'center'}}>
        <span style={{fontFamily: FONT, fontWeight: 900, fontSize: 46, color: NAVY}}>הבלוק הראשון</span>
        <span style={{fontFamily: 'Menlo, monospace', fontWeight: 700, fontSize: 30, color: MUSTARD}}>#0</span>
      </div>
      <div style={{marginTop: 18, minHeight: 130, background: NAVY, borderRadius: 12, padding: '18px 22px', direction: 'ltr',
        fontFamily: 'Menlo, monospace', fontSize: 30, lineHeight: 1.35, color: HOOK_YELLOW}}>
        {GENESIS.slice(0, n)}<span style={{opacity: n < GENESIS.length && Math.floor(t * 3) % 2 === 0 ? 1 : 0}}>▍</span>
      </div>
    </div>
  );
};

// Beat 5: 2008, the white paper, the first block, and who Satoshi is.
export const SatoshiPanel: React.FC<SceneProps> = ({at, start, end}) => (
  <SidePanel start={start} end={end} id="satoshi">
    <Scene from={start} to={at.s_paper}>
      <In at={at.s_2008}><Year text="2008" /></In>
      <In at={at.s_crisis} style={{marginTop: 26}}><Paper text="משבר פיננסי ענק" size={64} /></In>
      <In at={at.s_banks} style={{marginTop: 12}}><Paper text="בנקים קרסו" size={56} bg={MUSTARD} /></In>
    </Scene>
    <Scene from={at.s_paper} to={at.s_2009}>
      <div style={{display: 'flex', alignItems: 'center', gap: 50, direction: 'rtl'}}>
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 16}}>
          <In at={at.s_oct}><Paper text="אוקטובר 2008" size={50} bg={MUSTARD} /></In>
          <In at={at.s_name}><Paper text="סאטושי נקמוטו" size={58} /></In>
          <In at={at.s_nine}><Paper text="תשעה עמודים" size={50} /></In>
        </div>
        <WhitePaper at={at.s_doc} />
      </div>
    </Scene>
    <Scene from={at.s_2009} to={at.s_who}>
      <In at={at.s_2009} style={{marginBottom: 34}}><Paper text="ינואר 2009" size={60} bg={MUSTARD} /></In>
      <GenesisBlock at={at.s_block} typeAt={at.s_headline} />
    </Scene>
    <Scene from={at.s_who} to={end}>
      <In at={at.s_who}>
        <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 300, lineHeight: 1, color: HOOK_YELLOW, textAlign: 'center'}}>?</div>
      </In>
      <In at={at.s_who + 0.3} style={{marginTop: 10}}><Paper text="מי זה סאטושי" size={66} /></In>
    </Scene>
  </SidePanel>
);
