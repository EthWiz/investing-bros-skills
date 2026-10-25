import React from 'react';
import {AbsoluteFill, OffthreadVideo, staticFile} from 'remotion';
import {fontFaces} from './brand';
import {Card} from './components/Card';
import {Captions, Cta, Hook, NameTag} from './components/Overlays';
import type {ShortProps} from './props';

// Layer order, bottom to top: base video, explainer cards, hook, name tag, captions, CTA.
// No end card (Shorts best practice, Amitai 2026-10-25): the short ends on the payoff with
// the CTA strip and its arrow pointing down to the description, and loops.
export const Short: React.FC<ShortProps> = (p) => (
  <AbsoluteFill style={{background: 'black'}}>
    <style>{fontFaces()}</style>
    <OffthreadVideo src={staticFile(p.base)} />
    {p.cards.map((c) => <Card key={c.id} spec={c} />)}
    <Hook hook={p.hook} />
    <NameTag tags={p.tags} />
    <Captions captions={p.captions} highlight={p.captionHighlight} style={p.captionStyle} />
    <Cta cta={p.cta} />
  </AbsoluteFill>
);
