import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {CREAM, FONT, NAVY, clamp, seedOf, tornClip} from '../brand';
import type {CardMode, CardSpec, Step} from '../props';
import {ICONS} from './icons';
import {Logo} from './Overlays';

// Where each card mode sits on the 1080x1920 frame.
//  inset: most of the frame, a 40 px frame of the host video around it (house default)
//  full:  covers the frame, slides up over the host and away again; logo, tag and captions stay on top
//  card:  the older 1000x700 card in the middle
const BOX: Record<CardMode, {left: number; top: number; width: number; height: number}> = {
  inset: {left: 40, top: 40, width: 1000, height: 1840},
  full: {left: 0, top: -40, width: 1080, height: 2000},
  card: {left: 40, top: 570, width: 1000, height: 700},
};
const TITLE = {inset: [108, 88], full: [116, 92], card: [84, 70]} as const;
const ICON_SCALE = {inset: 1.35, full: 1.35, card: 0.6} as const;

const TitleWords: React.FC<{text: string; lt: number}> = ({text, lt}) => {
  const {fps} = useVideoConfig();
  return (
    // direction rtl: the first word sits on the right and lands first
    <div style={{display: 'flex', justifyContent: 'center', gap: 22}}>
      {text.split(' ').map((w, i) => {
        const k = spring({frame: Math.round(lt * fps) - 4 - i * 3, fps, config: {damping: 14}});
        return <span key={i} style={{display: 'inline-block', transform: `translateX(${(1 - k) * -40}px)`, opacity: k}}>{w}</span>;
      })}
    </div>
  );
};

const StepView: React.FC<{step: Step; lt: number; opacity: number; mode: CardMode}> = ({step, lt, opacity, mode}) => {
  const Icon = ICONS[step.visual];
  const size = step.title.length < 14 ? TITLE[mode][0] : TITLE[mode][1];
  return (
    <AbsoluteFill style={{opacity, alignItems: 'center', justifyContent: 'center', paddingBottom: mode === 'card' ? 30 : 260}}>
      {Icon && (
        // icons draw at 620x500; scaled to fit the card (layout margins follow the scale)
        <div style={{transform: `scale(${ICON_SCALE[mode]})`, margin: `${(ICON_SCALE[mode] - 1) * 250}px 0`}}>
          <Icon lt={lt} value={step.value} />
        </div>
      )}
      <div style={{marginTop: 40, filter: 'drop-shadow(0 5px 8px rgba(0,0,0,.4))'}}>
        <div style={{background: CREAM, color: NAVY, fontFamily: FONT, fontWeight: 900, fontSize: size, padding: '14px 44px 22px',
          clipPath: tornClip(seedOf(step.title)), direction: 'rtl', whiteSpace: 'nowrap'}}>
          <TitleWords text={step.title} lt={lt} />
        </div>
      </div>
      {step.subtitle ? (
        <div style={{marginTop: 34, color: CREAM, fontFamily: FONT, fontWeight: 600, fontSize: mode === 'card' ? 48 : 58, direction: 'rtl',
          opacity: interpolate(lt, [0.35, 0.7], [0, 1], clamp)}}>{step.subtitle}</div>
      ) : null}
    </AbsoluteFill>
  );
};

export const Card: React.FC<{spec: CardSpec}> = ({spec}) => {
  const f = useCurrentFrame();
  const {fps, height} = useVideoConfig();
  const t = f / fps;
  if (t < spec.start || t >= spec.end) return null;
  const lt0 = t - spec.start, box = BOX[spec.mode];
  const kin = spring({frame: Math.round(lt0 * fps), fps, config: {damping: 15, stiffness: 160}});
  const kout = interpolate(t, [spec.end - 0.3, spec.end], [0, 1], clamp);
  const i = spec.steps.reduce((acc, s, j) => (t >= s.at - 1e-6 ? j : acc), 0);
  const x = i ? interpolate(t, [spec.steps[i].at, spec.steps[i].at + 0.3], [0, 1], clamp) : 1;
  const transform = spec.mode === 'full'
    ? `translateY(${(1 - kin) * height - kout * (height + 80)}px)`                        // slides up in, up and out
    : `translateY(${(1 - kin) * 90}px) scale(${interpolate(kin, [0, 1], [0.92, 1]) * (1 - 0.04 * kout)})`;
  const opacity = spec.mode === 'full' ? 1 : interpolate(kin, [0, 0.3], [0, 1], clamp) * (1 - kout);
  return (
    <>
      <div style={{position: 'absolute', ...box, transform, opacity, filter: 'drop-shadow(0 14px 24px rgba(0,0,0,.55))'}}>
        <div style={{position: 'absolute', inset: 0, background: NAVY, overflow: 'hidden',
          clipPath: tornClip(seedOf(spec.id), spec.mode === 'full' ? 2 : 1.2, 3)}}>
          <svg width="100%" height="100%" style={{position: 'absolute', opacity: 0.18}}>
            <filter id={`paper-${spec.id}`}><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={4} /></filter>
            <rect width="100%" height="100%" filter={`url(#paper-${spec.id})`} />
          </svg>
          {i > 0 && x < 1 && <StepView step={spec.steps[i - 1]} lt={t - spec.steps[i - 1].at} opacity={1 - x} mode={spec.mode} />}
          <StepView step={spec.steps[i]} lt={t - spec.steps[i].at} opacity={x} mode={spec.mode} />
        </div>
      </div>
      {spec.mode !== 'card' && <Logo />}
    </>
  );
};
