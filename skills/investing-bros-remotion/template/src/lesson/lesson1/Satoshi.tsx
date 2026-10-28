import React from 'react';
import {Img, interpolate, staticFile} from 'remotion';
import {CREAM, FONT, HOOK_YELLOW, MUSTARD, NAVY, clamp} from '../../brand';
import {Paper, pop, useTime} from '../kit';
import {In, Scene, SidePanel} from '../panels';
import type {SceneProps} from '../types';

// Lesson 1, beat 5 (2008 and Satoshi): the white paper's real first page (a staged image) and the
// text of the first block, typed out.

const Year: React.FC<{text: string; size?: number}> = ({text, size = 210}) => (
  <div style={{fontFamily: FONT, fontWeight: 900, fontSize: size, lineHeight: 0.95, color: HOOK_YELLOW,
    textShadow: '0 8px 20px rgba(0,0,0,.4)', direction: 'ltr'}}>{text}</div>
);

// The real first page of the white paper: an image the config stages (its source is recorded there).
const WhitePaper: React.FC<{at: number; src: string}> = ({at, src}) => {
  const {t, fps} = useTime();
  const k = pop(t, at, fps, 15, 120);
  return (
    <Img src={staticFile(src)} style={{width: 430, background: '#FFF', borderRadius: 4,
      transform: `translateY(${(1 - k) * 80}px) rotate(${interpolate(k, [0, 1], [6, -3])}deg)`, opacity: k,
      boxShadow: '0 18px 40px rgba(0,0,0,.5)'}} />
  );
};

// The text Satoshi left in the first block, typed out.
const GenesisBlock: React.FC<{at: number; typeAt: number; title: string; text: string}> = ({at, typeAt, title, text}) => {
  const {t, fps} = useTime();
  const k = pop(t, at, fps, 14, 150);
  const n = Math.floor(interpolate(t, [typeAt, typeAt + 2.4], [0, text.length], clamp));
  return (
    <div style={{width: 700, borderRadius: 24, background: CREAM, padding: '26px 34px 34px', boxSizing: 'border-box',
      transform: `scale(${interpolate(k, [0, 1], [0.85, 1])})`, opacity: k, boxShadow: '0 14px 30px rgba(0,0,0,.45)'}}>
      <div style={{display: 'flex', direction: 'rtl', justifyContent: 'space-between', alignItems: 'center'}}>
        <span style={{fontFamily: FONT, fontWeight: 900, fontSize: 46, color: NAVY}}>{title}</span>
        <span style={{fontFamily: 'Menlo, monospace', fontWeight: 700, fontSize: 30, color: MUSTARD}}>#0</span>
      </div>
      <div style={{marginTop: 18, minHeight: 130, background: NAVY, borderRadius: 12, padding: '18px 22px', direction: 'ltr',
        fontFamily: 'Menlo, monospace', fontSize: 30, lineHeight: 1.35, color: HOOK_YELLOW}}>
        {text.slice(0, n)}<span style={{opacity: n < text.length && Math.floor(t * 3) % 2 === 0 ? 1 : 0}}>▍</span>
      </div>
    </div>
  );
};

// 2008, the white paper, the first block, and who Satoshi is. Words from the segment's content; the month
// (s_oct, oct) and the closing question (s_who, who) show only when the config gives them.
export const SatoshiPanel: React.FC<SceneProps> = ({at, start, end, content: c, assets}) => (
  <SidePanel start={start} end={end} id="satoshi">
    <Scene from={start} to={at.s_paper}>
      <In at={at.s_2008}><Year text={c.year} /></In>
      <In at={at.s_crisis} style={{marginTop: 26}}><Paper text={c.crisis} size={64} /></In>
      <In at={at.s_banks} style={{marginTop: 12}}><Paper text={c.banks} size={56} bg={MUSTARD} /></In>
    </Scene>
    <Scene from={at.s_paper} to={at.s_2009}>
      <div style={{display: 'flex', alignItems: 'center', gap: 50, direction: 'rtl'}}>
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 16}}>
          {at.s_oct !== undefined && c.oct ? <In at={at.s_oct}><Paper text={c.oct} size={50} bg={MUSTARD} /></In> : null}
          <In at={at.s_name}><Paper text={c.name} size={58} /></In>
          <In at={at.s_nine}><Paper text={c.nine} size={50} /></In>
        </div>
        <WhitePaper at={at.s_doc} src={assets.whitepaper} />
      </div>
    </Scene>
    <Scene from={at.s_2009} to={at.s_who ?? end}>
      <In at={at.s_2009} style={{marginBottom: 34}}><Paper text={c.jan} size={60} bg={MUSTARD} /></In>
      <GenesisBlock at={at.s_block} typeAt={at.s_headline} title={c.block} text={c.genesis} />
    </Scene>
    {at.s_who !== undefined && c.who ? (
      <Scene from={at.s_who} to={end}>
        <In at={at.s_who}>
          <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 300, lineHeight: 1, color: HOOK_YELLOW, textAlign: 'center'}}>?</div>
        </In>
        <In at={at.s_who + 0.3} style={{marginTop: 10}}><Paper text={c.who} size={66} /></In>
      </Scene>
    ) : null}
  </SidePanel>
);
