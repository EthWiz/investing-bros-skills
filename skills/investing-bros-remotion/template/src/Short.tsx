import React from 'react';
import {AbsoluteFill, OffthreadVideo, Sequence, staticFile, useVideoConfig} from 'remotion';
import {fontFaces} from './brand';
import {Card} from './components/Card';
import {Captions, Cta, EndCard, Hook, NameTag} from './components/Overlays';
import type {ShortProps} from './props';

// Layer order, bottom to top: base video, explainer cards, hook, name tag, captions, CTA.
// Then the silent end card as a hard cut.
export const Short: React.FC<ShortProps> = (p) => {
  const {fps} = useVideoConfig();
  const body = Math.round(p.baseDuration * fps);
  return (
    <AbsoluteFill style={{background: 'black'}}>
      <style>{fontFaces()}</style>
      <Sequence durationInFrames={body}>
        <OffthreadVideo src={staticFile(p.base)} />
        {p.cards.map((c) => <Card key={c.id} spec={c} />)}
        <Hook hook={p.hook} />
        <NameTag tags={p.tags} />
        <Captions captions={p.captions} />
        <Cta cta={p.cta} />
      </Sequence>
      <Sequence from={body}>
        <EndCard episode={p.episode} title={p.endTitle} />
      </Sequence>
    </AbsoluteFill>
  );
};
