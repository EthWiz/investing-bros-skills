import React from 'react';
import {Img, interpolate, staticFile} from 'remotion';
import {CREAM, FONT, MUSTARD, NAVY, clamp} from '../brand';
import {Paper, ease, enterRight, lerp, pop, useTime} from './kit';

// Name strips on the wall to his left when he says his name.
export const NameStrips: React.FC<{at: number; until: number}> = ({at, until}) => {
  const {t, fps} = useTime();
  if (t < at || t > until) return null;
  const k1 = pop(t, at, fps), k2 = pop(t, at + 0.15, fps);
  const out = 1 - ease(t, until - 0.3, until);
  return (
    <div style={{position: 'absolute', left: 70, top: 620, display: 'flex', flexDirection: 'column', alignItems: 'flex-start', opacity: out}}>
      <Paper text="אמיתי רסקין" size={60} style={{...enterRight(k1), transform: `${enterRight(k1).transform} rotate(-1deg)`}} />
      <Paper text="אחים להשקעות" size={46} bg={MUSTARD} style={{marginTop: -8, marginLeft: 26, ...enterRight(k2)}} />
    </div>
  );
};

// Lesson title, at most three seconds, at the end of the opening beat: the lesson number and the
// name as Amitai says it, one torn strip per line, on the wall to his left.
export const LessonTitle: React.FC<{lesson: number; lines: string[]; at: number; until: number}> = ({lesson, lines, at, until}) => {
  const {t, fps} = useTime();
  const end = Math.min(until, at + 3);
  if (t < at || t > end) return null;
  const out = 1 - ease(t, end - 0.3, end);
  const ks = [0, ...lines.map((_, i) => 0.12 * (i + 1))].map((d) => pop(t, at + d, fps));
  return (
    <div style={{position: 'absolute', left: 60, top: 230, display: 'flex', flexDirection: 'column', alignItems: 'flex-start', opacity: out}}>
      <Img src={staticFile('logo.png')} style={{width: 210, marginBottom: 18, marginLeft: 6, borderRadius: 6, opacity: ks[0]}} />
      <Paper text={`שיעור ${lesson}`} size={52} bg={MUSTARD} style={enterRight(ks[0])} />
      {lines.map((line, i) => <Paper key={i} text={line} size={74} style={{marginTop: -8, ...enterRight(ks[i + 1])}} />)}
    </div>
  );
};

// The disclaimer strip at the bottom, from the disclaimer's first words to the end of its beat.
export const DisclaimerStrip: React.FC<{start: number; end: number}> = ({start, end}) => {
  const {t, fps} = useTime();
  if (t < start || t > end) return null;
  const k = pop(t, start + 0.2, fps);
  const out = 1 - ease(t, end - 0.3, end);
  return (
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 34, display: 'flex', justifyContent: 'center', opacity: out,
      transform: `translateY(${(1 - k) * 80}px)`}}>
      <Paper text="תוכן לימודי, לא ייעוץ השקעות" size={50} />
    </div>
  );
};

// Where each agenda card sits while it is introduced (the wall to his left), and where it docks.
const CARD_TOP = 210, CARD_GAP = 132;
const DOCK = {left: 40, top: 34};

// The lesson's parts come in one by one (anchors ag1, ag2, ...), then shrink into the progress marker.
export const Agenda: React.FC<{parts: string[]; at: Record<string, number>; dock: number}> = ({parts, at, dock}) => {
  const {t, fps} = useTime();
  if (t < at.ag1 || t > dock + 0.8) return null;
  const d = ease(t, dock, dock + 0.7);
  return (
    <>
      {parts.map((label, i) => {
        const k = pop(t, at[`ag${i + 1}`] ?? Infinity, fps);
        if (k <= 0) return null;
        const x = lerp(70, DOCK.left + i * 30, d), y = lerp(CARD_TOP + i * CARD_GAP, DOCK.top, d);
        return (
          <div key={i} style={{position: 'absolute', left: x, top: y, transformOrigin: 'top left',
            opacity: interpolate(k, [0, 0.35], [0, 1], clamp) * (1 - interpolate(d, [0.6, 1], [0, 1], clamp)),
            transform: `translateX(${(1 - k) * 70}px) scale(${lerp(1, 0.3, d)})`}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 14, direction: 'rtl'}}>
              <div style={{width: 74, height: 74, borderRadius: 37, background: MUSTARD, color: NAVY, fontFamily: FONT,
                fontWeight: 900, fontSize: 46, display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: '0 6px 12px rgba(0,0,0,.35)'}}>{i + 1}</div>
              <Paper text={label} size={48} />
            </div>
          </div>
        );
      })}
    </>
  );
};

// Progress marker, top left for the rest of the lesson: one mark per part, the current one with its name.
export const Progress: React.FC<{parts: string[]; starts: (number | null)[]; from: number}> = ({parts, starts, from}) => {
  const {t, fps} = useTime();
  if (t < from) return null;
  const k = pop(t, from, fps);
  // starts keeps one position per part (null = not in this cut), so the marker never shifts a label
  const current = starts.reduce<number>((acc, s, i) => (s !== null && t >= s ? i + 1 : acc), 0);
  return (
    <div style={{position: 'absolute', left: DOCK.left, top: DOCK.top, display: 'flex', gap: 8, direction: 'rtl',
      alignItems: 'center', opacity: k, filter: 'drop-shadow(0 4px 8px rgba(0,0,0,.35))'}}>
      {parts.map((label, i) => {
        const n = i + 1, on = n === current, done = n < current;
        return (
          <div key={i} style={{height: 46, minWidth: 46, borderRadius: 23, padding: on ? '0 20px 0 8px' : 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
            background: on ? CREAM : done ? MUSTARD : 'rgba(9,36,59,.82)', color: on || done ? NAVY : CREAM,
            fontFamily: FONT, fontWeight: 900, fontSize: 26, border: `2px solid ${on ? CREAM : 'rgba(245,235,213,.5)'}`}}>
            <span style={{width: 30, height: 30, borderRadius: 15, display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: on ? MUSTARD : 'transparent'}}>{n}</span>
            {on ? <span style={{fontWeight: 800, fontSize: 26}}>{label}</span> : null}
          </div>
        );
      })}
    </div>
  );
};
