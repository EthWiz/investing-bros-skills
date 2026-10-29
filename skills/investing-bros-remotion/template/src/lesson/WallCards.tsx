import React from 'react';
import {interpolate} from 'remotion';
import {CREAM, FONT, GOLD, HOOK_YELLOW, MUSTARD, NAVY, clamp} from '../brand';
import {Paper, ease, enterRight, pop, useTime} from './kit';
import type {SceneProps} from './types';

// 'full' scenes: cards on the wall to Amitai's left while he stays on camera (lesson 2's "כרטיס ליד
// הפנים"). They sit above his video, in the free wall space, never over his face; the segment's end
// (the next segment, often a plain 'full' one) takes them off. Allowed in the first 30 s, like the
// name strips, since they aren't a side panel or a full-screen graphic.
const WALL: React.CSSProperties = {position: 'absolute', left: 70, top: 200, width: 600, height: 560,
  display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'flex-start', direction: 'rtl'};

const Fade: React.FC<{from: number; to: number; children: React.ReactNode}> = ({from, to, children}) => {
  const {t, fps} = useTime();
  if (t < from || t > to + 0.3) return null;
  const k = pop(t, from, fps);
  const out = 1 - ease(t, to, to + 0.3);
  return <div style={{...WALL, ...enterRight(k), opacity: Math.min(enterRight(k).opacity as number, out)}}>{children}</div>;
};

// content: {cards: [{big, sub?, kicker?, pair?: [a, b], at}]}. Each card replaces the one before it
// (beat 2: "21 מיליון" then "77%"); `pair` draws "a ≠ b" (beat 6). Text comes from the config.
type Card = {big?: string; sub?: string; kicker?: string; pair?: [string, string]; at: number};

export const WallCard: React.FC<SceneProps> = ({end, content}) => {
  const cards: Card[] = content.cards;
  return (
    <>
      {cards.map((c, i) => (
        <Fade key={i} from={c.at} to={i + 1 < cards.length ? cards[i + 1].at - 0.05 : end - 0.3}>
          {c.kicker ? <Paper text={c.kicker} size={40} bg={MUSTARD} style={{marginBottom: -6, marginRight: 12}} /> : null}
          {c.pair ? (
            <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 6}}>
              <Paper text={c.pair[0]} size={52} />
              <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 96, color: HOOK_YELLOW, marginRight: 40, lineHeight: 1,
                textShadow: '0 4px 10px rgba(0,0,0,.6)'}}>≠</div>
              <Paper text={c.pair[1]} size={52} />
            </div>
          ) : c.big ? <Paper text={c.big} size={c.big.length > 13 ? 64 : c.big.length > 9 ? 80 : 104} /> : null}
          {c.sub ? (
            <div style={{marginTop: 14, marginRight: 10, maxWidth: 560, fontFamily: FONT, fontWeight: 700, fontSize: 42, lineHeight: 1.2,
              color: CREAM, textShadow: '0 3px 8px rgba(0,0,0,.8)'}}><bdi dir="auto">{c.sub}</bdi></div>
          ) : null}
        </Fade>
      ))}
    </>
  );
};

// content: {heading?: {text, at}, items: [{label, token, at, flip?}]}: each asset (מניה, אג״ח, קרן)
// comes in as a cream strip on the word that names it, then turns into a gold token (`flip`, or
// 0.7 s after `at`). Beat 4 of lesson 2: "לוקחים נכס אמיתי ... ומנפיקים אותו כטוקן".
type Asset = {label: string; token: string; at: number; flip?: number};

const Token: React.FC<{text: string; k: number}> = ({text, k}) => (
  <div style={{width: 120, height: 120, borderRadius: 60, background: GOLD, border: `6px solid ${HOOK_YELLOW}`,
    display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 8px 18px rgba(0,0,0,.45)',
    fontFamily: FONT, fontWeight: 900, fontSize: text.length > 3 ? 30 : 40, color: NAVY,
    transform: `scaleX(${k}) scale(${interpolate(k, [0, 1], [0.6, 1], clamp)})`}}>
    <bdi dir="auto">{text}</bdi>
  </div>
);

export const Tokenize: React.FC<SceneProps> = ({end, content}) => {
  const {t, fps} = useTime();
  const items: Asset[] = content.items;
  const from = content.heading?.at ?? items[0].at;
  if (t < from || t > end + 0.3) return null;
  const out = 1 - ease(t, end - 0.3, end);
  return (
    <div style={{...WALL, opacity: out, gap: 22}}>
      {content.heading ? (
        <Paper text={content.heading.text} size={46} bg={MUSTARD} style={{marginBottom: 10, ...enterRight(pop(t, content.heading.at, fps))}} />
      ) : null}
      {items.map((x, i) => {
        if (t < x.at) return <div key={i} style={{height: 120}} />;
        const flip = x.flip ?? x.at + 0.7;
        const k = pop(t, x.at, fps);
        const f = pop(t, flip, fps, 16, 200);
        return (
          <div key={i} style={{display: 'flex', alignItems: 'center', gap: 22, height: 120, ...enterRight(k)}}>
            <Paper text={x.label} size={54} style={{opacity: t < flip ? 1 : interpolate(f, [0, 1], [1, 0.5], clamp)}} />
            <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 60, color: CREAM, opacity: t < flip ? 0 : f}}>←</div>
            {t >= flip ? <Token text={x.token} k={f} /> : null}
          </div>
        );
      })}
    </div>
  );
};
