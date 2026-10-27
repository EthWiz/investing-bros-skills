import React from 'react';
import {AbsoluteFill, OffthreadVideo, interpolate, staticFile} from 'remotion';
import {GOLD, HOOK_YELLOW, NAVY, WHITE, clamp, FONT} from '../brand';
import {fontFaces} from '../brand';
import {Agenda, DisclaimerStrip, LessonTitle, NameStrips, Progress} from './overlays';
import {SCENES} from './scenes';
import {NavyPaper, ease, lerp, useTime} from './kit';
import type {LessonProps, Mode, Segment} from './types';

// Face position in the 1920x1080 base (between the eyes and the mouth); zooms and the bubble keep it in place.
const FX = 840, FY = 450;

type Cam = {bx: number; by: number; bw: number; bh: number; br: number; vx: number; vy: number; vw: number};

const BUBBLE = 360, BUBBLE_SCALE = 0.45;
const camFor = (s: Segment): Cam => {
  if (s.mode === 'side') return {bx: 0, by: 0, bw: 1920, bh: 1080, br: 0, vx: 520, vy: 0, vw: 1920};
  if (s.mode === 'bubble') {
    return {bx: 1920 - 56 - BUBBLE, by: 1080 - 56 - BUBBLE, bw: BUBBLE, bh: BUBBLE, br: BUBBLE / 2,
      vw: 1920 * BUBBLE_SCALE, vx: BUBBLE / 2 - FX * BUBBLE_SCALE, vy: BUBBLE / 2 - FY * BUBBLE_SCALE - 10};
  }
  const z = s.zoom ?? 1;
  return {bx: 0, by: 0, bw: 1920, bh: 1080, br: 0, vw: 1920 * z, vx: FX - FX * z, vy: FY - FY * z};
};

const segIndex = (segs: Segment[], t: number) => {
  const i = segs.findIndex((s) => t < s.end);
  return i < 0 ? segs.length - 1 : i;
};

// A change of layout glides over 0.6 s; a zoom change within 'full' is a hard cut (the second "camera").
const modeBlend = (segs: Segment[], t: number) => {
  const i = segIndex(segs, t);
  const cur = segs[i], prev = segs[i - 1];
  const p = prev && prev.mode !== cur.mode ? ease(t, cur.start, cur.start + 0.6) : 1;
  return {cur, prev: prev ?? cur, p};
};

const camAt = (segs: Segment[], t: number): Cam => {
  const {cur, prev, p} = modeBlend(segs, t);
  const a = camFor(prev.mode === cur.mode ? cur : prev), b = camFor(cur);
  const o = {} as Cam;
  (Object.keys(b) as (keyof Cam)[]).forEach((k) => (o[k] = lerp(a[k], b[k], p)));
  return o;
};

const Camera: React.FC<{base: string; segs: Segment[]}> = ({base, segs}) => {
  const {t} = useTime();
  const c = camAt(segs, t);
  const bubble = c.br > 1;
  return (
    <div style={{position: 'absolute', left: c.bx, top: c.by, width: c.bw, height: c.bh, borderRadius: c.br, overflow: 'hidden',
      background: NAVY, boxShadow: bubble ? `0 0 0 ${interpolate(c.br, [0, 180], [0, 7], clamp)}px ${HOOK_YELLOW}, 0 14px 30px rgba(0,0,0,.5)` : 'none'}}>
      <OffthreadVideo src={staticFile(base)} style={{position: 'absolute', left: c.vx, top: c.vy, width: c.vw, height: (c.vw * 9) / 16}} />
    </div>
  );
};

// Captions: calm two lines at the bottom, the word being said in gold. They sit under Amitai:
// centred in 'full', on his side in 'side', and left of the bubble in 'bubble'.
const CAP: Record<Mode, {x: number; w: number}> = {
  full: {x: 960, w: 1300},
  side: {x: 1400, w: 860},
  bubble: {x: 790, w: 1300},
};

const Captions: React.FC<{p: LessonProps}> = ({p}) => {
  const {t} = useTime();
  const c = p.captions.find((x) => t >= x.start && t < x.end);
  if (!c) return null;
  const {cur, prev, p: k} = modeBlend(p.segments, t);
  const x = lerp(CAP[prev.mode].x, CAP[cur.mode].x, k), w = lerp(CAP[prev.mode].w, CAP[cur.mode].w, k);
  const disclaimer = p.beats.find((b) => b.n === p.disclaimerBeat);
  const raised = disclaimer && t >= disclaimer.start && t < disclaimer.end;
  const spoken = c.words.reduce((acc, wd, i) => (t >= wd.start - 1e-6 ? i : acc), -1);
  const fade = interpolate(t, [c.start, c.start + 0.12], [0, 1], clamp);
  return (
    <div style={{position: 'absolute', left: x - w / 2, width: w, bottom: raised ? 132 : 44, display: 'flex', justifyContent: 'center', opacity: fade}}>
      <div style={{direction: 'rtl', textAlign: 'center', fontFamily: FONT, fontWeight: 800, fontSize: 50, lineHeight: 1.28,
        textWrap: 'balance', textShadow: '0 3px 8px rgba(0,0,0,.75), 0 0 3px rgba(0,0,0,.9)'} as React.CSSProperties}>
        {c.words.map((wd, i) => (
          <React.Fragment key={i}><bdi dir="auto" style={{color: i === spoken ? GOLD : WHITE}}>{wd.w}</bdi>{i < c.words.length - 1 ? ' ' : ''}</React.Fragment>
        ))}
      </div>
    </div>
  );
};

// soft shade at the bottom so white captions read over the wall
const Shade: React.FC = () => (
  <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 300,
    background: 'linear-gradient(to top, rgba(0,0,0,.5), rgba(0,0,0,0))'}} />
);

// Layer order, bottom to top: background, full-screen (bubble) scenes, Amitai, shade, side panels,
// strips and cards, captions.
export const Lesson: React.FC<LessonProps> = (p) => {
  if (!p.beats.length || !p.segments.length) return <AbsoluteFill style={{background: NAVY}} />;
  const first = p.beats[0];
  const scenes = (mode: Mode) => p.segments.filter((s) => s.mode === mode && s.scene).map((s, i) => {
    const Scene = SCENES[s.scene!];
    return Scene ? <Scene key={`${mode}-${i}`} at={p.at} start={s.start} end={s.end} content={s.content ?? {}} assets={p.assets ?? {}} /> : null;
  });
  const disclaimer = p.beats.find((b) => b.n === p.disclaimerBeat);
  return (
    <AbsoluteFill style={{background: NAVY}}>
      <style>{fontFaces()}</style>
      <NavyPaper id="bg" />
      {scenes('bubble')}
      <Camera base={p.base} segs={p.segments} />
      <Shade />
      {scenes('side')}
      {p.at.name !== undefined && <NameStrips at={p.at.name} until={p.at.name + 4} />}
      {p.at.title !== undefined && <LessonTitle lesson={p.lesson} lines={p.title} at={p.at.title} until={first.end} />}
      {disclaimer && <DisclaimerStrip start={disclaimer.start} end={disclaimer.end} />}
      {p.at.ag_dock !== undefined && <Agenda parts={p.parts} at={p.at} dock={p.at.ag_dock} />}
      {p.at.ag_dock !== undefined && (
        <Progress parts={p.parts} from={p.at.ag_dock + 0.5} starts={p.partStarts} />
      )}
      <Captions p={p} />
    </AbsoluteFill>
  );
};
