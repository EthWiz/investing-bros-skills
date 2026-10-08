#!/usr/bin/env python3
"""Build the HyperFrames composition (public/index.html) for an Investing Bros short.

Usage:
    python3 build_composition.py short.json --project DIR

DIR/public must already hold: input-video.mp4 (from make_input.py), logo.png
(brand wordmark), fonts/Heebo-{SemiBold,ExtraBold,Black}.woff2 and
vendor/gsap.min.js. Writes DIR/public/index.html, DIR/public/cards/*.html,
DIR/storyboard.json and DIR/transcript.json, then run
`npx hyperframes lint|snapshot|render` on DIR/public.

Layout (1080x1920): host video 1080x1216 at the top with the logo and a name
tag, proofread captions over the bottom of the video, one animated card at a
time in the band y=1250..1550 (above the Reels/Shorts UI, left of the side
buttons), an end card for the last seconds.

short.json (all times are seconds on the SOURCE timeline; they are mapped
through `pieces` to the clip's own time):
{
  "name": "short1_swift", "fps": 24,
  "pieces": [[843.69, 864.40], ...],                      # same as make_input.py
  "speaker": ["אמיתי רסקין", 843.69, 847.0],               # name tag + when
  "captions": [[843.69, 845.35, "אתה רוצה להעביר כסף|מישראל לארצות הברית —"], ...],
                                                         # | = line break, [..] = emerald
  "cards": [
    {"type": "route", "start": s, "end": e, "kicker": "...", "from": "ישראל", "to": "ארה״ב"},
    {"type": "stat", "start": s, "end": e, "kicker": "...", "value": 40, "suffix": "$",
     "value_at": t, "label": "עמלה|על העברה אחת", "note": "״...״", "note_at": t},
    {"type": "strike", "start": s, "end": e, "kicker": "...", "title": "SWIFT",
     "wrong": "מערכת תשלומים", "wrong_at": t, "right": "מערכת הודעות", "right_at": t},
    {"type": "statement", "start": s, "end": e, "kicker": "...", "chip": "מורכבת", "chip_at": t,
     "title": "לא בנויה|לעידן האינטרנט", "title_at": t},
    {"type": "list", "start": s, "end": e, "kicker": "...",
     "rows": [{"text": "...", "on": true, "at": t}, {"text": "...", "on": false, "at": t}],
     "conclusion": "...", "conclusion_at": t}
  ],
  "endcard": {"lines": ["הפרק המלא על טוקניזציה", "אחים להשקעות"], "seconds": 2.6}
}
Every on-screen word must be something the hosts said or a faithful label for
it (no invented numbers); every `*_at` should be when that word is spoken.
"""
import argparse
import html
import json
import os
import re
import sys

EMERALD = "#1FBF7A"
BAND = "left:56px;top:1250px;width:840px;height:300px"
LATIN = re.compile(r"[A-Za-z][A-Za-z0-9&'’.\-]*(?:\s+[A-Za-z0-9][A-Za-z0-9&'’.\-]*)*")


def snap(t, fps):
    return round(t * fps) / fps


class Timeline:
    def __init__(self, pieces, fps):
        self.fps = fps
        self.pieces = [(snap(p[0], fps), snap(p[1], fps)) for p in pieces]
        self.duration = round(sum(b - a for a, b in self.pieces) * fps) / fps

    def map(self, t):
        o = 0.0
        for a, b in self.pieces:
            if a - 0.05 <= t <= b + 0.05:
                return min(max(o + t - a, o), o + b - a)
            o += b - a
        raise ValueError(f"time {t} is not inside any piece")

    def q(self, t):
        return round(round(t * self.fps) / self.fps, 4)


def text(s):
    """Escape, wrap Latin runs in <bdi>, [..] -> emerald span, | -> line break."""
    out, pos = [], 0
    for m in LATIN.finditer(s):
        out.append(html.escape(s[pos:m.start()], quote=False))
        out.append(f"<bdi>{html.escape(m.group(0), quote=False)}</bdi>")
        pos = m.end()
    out.append(html.escape(s[pos:], quote=False))
    return "".join(out).replace("[", '<span class="em">').replace("]", "</span>").replace("|", "<br/>")


def close_gaps(items, max_gap=0.35):
    items = [list(x) for x in items]
    for i in range(len(items) - 1):
        gap = items[i + 1][0] - items[i][1]
        if 0 < gap < max_gap or gap < 0:
            items[i][1] = items[i + 1][0]
    return items


BASE_CSS = """CARD .root{width:100%;height:100%;box-sizing:border-box;padding:28px 36px;display:flex;flex-direction:column;justify-content:center;gap:14px;font-family:'Heebo ExtraBold','Heebo Black',sans-serif;color:#fff;background:rgba(7,9,8,0.92);border:2px solid rgba(31,191,122,0.55);border-radius:28px}
CARD .kicker{font-family:'Heebo SemiBold',sans-serif;font-size:30px;color:var(--accent-0)}
CARD .title{font-family:'Heebo Black',sans-serif;font-size:76px;line-height:1.02;margin:0}
CARD .em{color:var(--accent-0)}"""

TYPE_CSS = {
    "route": """CARD .route{display:flex;flex-direction:row;align-items:center;gap:22px}
CARD .place{font-family:'Heebo Black',sans-serif;font-size:64px;line-height:1}
CARD .track{position:relative;flex:1;height:10px;background:rgba(255,255,255,0.12);border-radius:5px;overflow:hidden}
CARD .fill{position:absolute;right:0;top:0;height:10px;width:0;background:var(--accent-0);border-radius:5px}""",
    "stat": """CARD .row{display:flex;flex-direction:row;align-items:baseline;gap:22px}
CARD .num{opacity:0;font-family:'Heebo Black',sans-serif;font-size:150px;line-height:0.9;color:var(--accent-0);direction:ltr;unicode-bidi:isolate}
CARD .label{font-family:'Heebo ExtraBold',sans-serif;font-size:44px;line-height:1.1}
CARD .note{font-family:'Heebo SemiBold',sans-serif;font-size:36px;color:#C9D6CF;border-top:2px solid rgba(255,255,255,0.14);padding-top:14px}""",
    "strike": """CARD .title{font-size:96px;direction:ltr;unicode-bidi:isolate;letter-spacing:4px}
CARD .chips{display:flex;flex-direction:row;gap:18px}
CARD .chip{font-family:'Heebo ExtraBold',sans-serif;font-size:36px;padding:12px 24px;border-radius:999px}
CARD .no{background:rgba(255,255,255,0.08);color:#9AA6A0;text-decoration:line-through;text-decoration-thickness:4px}
CARD .yes{background:var(--accent-0);color:#06100B}""",
    "statement": """CARD .chip{align-self:flex-start;font-family:'Heebo ExtraBold',sans-serif;font-size:40px;padding:10px 26px;border-radius:999px;border:3px solid var(--accent-0);color:var(--accent-0)}""",
    "list": """CARD .rows{display:flex;flex-direction:column;gap:12px}
CARD .r{display:flex;flex-direction:row;align-items:center;gap:16px;font-family:'Heebo ExtraBold',sans-serif;font-size:40px}
CARD .dot{width:18px;height:18px;border-radius:9px;background:var(--accent-0);flex:0 0 auto}
CARD .off{color:#9AA6A0}
CARD .off .dot{background:transparent;border:3px solid #9AA6A0}
CARD .title{font-size:62px;color:var(--accent-0)}""",
    "end": """CARD .root{align-items:center;text-align:center;gap:10px;border-color:var(--accent-0);background:rgba(7,9,8,0.94)}
CARD .a{font-size:44px}
CARD .b{font-family:'Heebo Black',sans-serif;font-size:72px;color:var(--accent-0);line-height:1}""",
}


def card_body(c, cid):
    """Return (html body, [(abs_or_rel, kind, selector, params)]) — times 'rel' to card start or ('src', t)."""
    k = f'<div class="kicker" id="{cid}-k">{text(c["kicker"])}</div>' if c.get("kicker") else ""
    an = [(0.10, "fade-in", f"#{cid}-k", {})] if k else []
    t = c["type"]
    if t == "route":
        body = (k + f'<div class="route"><div class="place" id="{cid}-a">{text(c["from"])}</div>'
                f'<div class="track"><div class="fill" id="{cid}-fill"></div></div>'
                f'<div class="place" id="{cid}-b">{text(c["to"])}</div></div>')
        an += [(0.30, "fade-in", f"#{cid}-a", {}), (0.55, "grow", f"#{cid}-fill", {"w": 380}),
               (1.60, "scale-pop", f"#{cid}-b", {})]
    elif t == "stat":
        body = (k + f'<div class="row"><div class="num" id="{cid}-numbox">{text(c.get("prefix", ""))}'
                f'<span id="{cid}-num">0</span>{text(c.get("suffix", ""))}</div>'
                f'<div class="label" id="{cid}-l">{text(c.get("label", ""))}</div></div>')
        at = ("src", c.get("value_at", c["start"]))
        an += [(at, "fade-in", f"#{cid}-numbox", {}), (at, "count", f"#{cid}-num", {"to": c["value"]}),
               (0.40, "slide-in", f"#{cid}-l", {})]
        if c.get("note"):
            body += f'<div class="note" id="{cid}-n">{text(c["note"])}</div>'
            an.append((("src", c.get("note_at", c["start"])), "fade-in", f"#{cid}-n", {}))
    elif t == "strike":
        body = (k + f'<div class="title" id="{cid}-t">{text(c["title"])}</div><div class="chips">'
                f'<div class="chip no" id="{cid}-no">{text(c["wrong"])}</div>'
                f'<div class="chip yes" id="{cid}-yes">{text(c["right"])}</div></div>')
        an += [(0.20, "scale-pop", f"#{cid}-t", {}),
               (("src", c.get("wrong_at", c["start"])), "slide-in", f"#{cid}-no", {}),
               (("src", c.get("right_at", c["start"])), "scale-pop", f"#{cid}-yes", {})]
    elif t == "statement":
        body = k
        if c.get("chip"):
            body += f'<div class="chip" id="{cid}-c">{text(c["chip"])}</div>'
            an.append((("src", c.get("chip_at", c["start"])), "scale-pop", f"#{cid}-c", {}))
        body += f'<h2 class="title" id="{cid}-t">{text(c["title"])}</h2>'
        an.append((("src", c.get("title_at", c["start"])), "mask", f"#{cid}-t", {}))
    elif t == "list":
        rows = "".join(
            f'<div class="r{"" if r.get("on", True) else " off"}" id="{cid}-r{i}"><span class="dot"></span>{text(r["text"])}</div>'
            for i, r in enumerate(c["rows"]))
        body = k + f'<div class="rows">{rows}</div>'
        an += [(("src", r.get("at", c["start"])), "slide-in", f"#{cid}-r{i}", {}) for i, r in enumerate(c["rows"])]
        if c.get("conclusion"):
            body += f'<div class="title" id="{cid}-t">{text(c["conclusion"])}</div>'
            an.append((("src", c.get("conclusion_at", c["start"])), "mask", f"#{cid}-t", {}))
    elif t == "end":
        a, b = (c["lines"] + ["", ""])[:2]
        body = f'<div class="a" id="{cid}-a">{text(a)}</div><div class="b" id="{cid}-b">{text(b)}</div>'
        an += [(0.10, "fade-in", f"#{cid}-a", {}), (0.30, "scale-pop", f"#{cid}-b", {})]
    else:
        raise ValueError(f"unknown card type {t}")
    return body, an


def card_html(cid, ctype, body):
    css = (BASE_CSS + "\n" + TYPE_CSS[ctype]).replace("CARD", f'.card[data-card-id="{cid}"]')
    return f'<div class="card" data-card-id="{cid}">\n<style>\n{css}\n</style>\n<div class="root" dir="rtl">\n{body}\n</div>\n</div>\n'


def gsap(kind, sel, t, p):
    if kind == "fade-in":
        return f"tl.fromTo('{sel}',{{opacity:0}},{{opacity:1,duration:0.4,ease:'power2.out'}},{t});"
    if kind == "slide-in":
        return f"tl.fromTo('{sel}',{{opacity:0,x:60}},{{opacity:1,x:0,duration:0.45,ease:'power2.out'}},{t});"
    if kind == "scale-pop":
        return f"tl.fromTo('{sel}',{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.45,ease:'back.out(1.6)'}},{t});"
    if kind == "mask":
        return f"tl.fromTo('{sel}',{{clipPath:'inset(0 0 0 100%)'}},{{clipPath:'inset(0 0 0 0%)',duration:0.6,ease:'power2.inOut'}},{t});"
    if kind == "grow":
        return f"tl.fromTo('{sel}',{{width:0}},{{width:{p['w']},duration:1.0,ease:'power2.inOut'}},{t});"
    if kind == "count":
        return (f"(function(){{const o={{v:0}};tl.to(o,{{v:{p['to']},duration:0.9,ease:'power2.out',onUpdate:function(){{"
                f"const el=document.querySelector('{sel}');if(el)el.textContent=__fmt(o.v);}}}},{t});}})();")
    raise ValueError(kind)


def build(cfg):
    fps = cfg.get("fps", 24)
    tl = Timeline(cfg["pieces"], fps)
    D = tl.duration
    cards = []
    for i, c in enumerate(cfg["cards"]):
        cards.append((c.get("id", f"c{i + 1}"), c, tl.q(tl.map(c["start"])), tl.q(tl.map(c["end"]))))
    if cfg.get("endcard"):
        secs = cfg["endcard"].get("seconds", 2.6)
        cards.append(("end", {"type": "end", "lines": cfg["endcard"]["lines"]}, tl.q(D - secs), tl.q(D)))
    for (a_id, _, _, a_end), (b_id, _, b_start, _) in zip(cards, cards[1:]):
        if b_start < a_end:
            raise ValueError(f"cards {a_id} and {b_id} overlap")

    js = ["const tl=window.gsap.timeline({paused:true});",
          "window.__fmt=function(v){return String(Math.round(v));};"]
    hosts, files = [], {}
    for cid, c, s, e in cards:
        body, an = card_body(c, cid)
        files[cid] = card_html(cid, c["type"], body)
        hosts.append(f'<div class="card-host clip" id="card-{cid}" data-card-id="{cid}" data-start="{s:.4f}" '
                     f'data-duration="{e - s:.4f}" data-track-index="2" style="{BAND};visibility:hidden;opacity:0;">\n{files[cid]}</div>')
        host = f".card-host[data-card-id=\"{cid}\"]"
        js.append(f"tl.set('{host}',{{visibility:'visible'}},{s});")
        js.append(f"tl.fromTo('{host}',{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.4,ease:'power2.out'}},{s});")
        for when, kind, el, p in an:
            t = tl.q(tl.map(when[1])) if isinstance(when, tuple) else tl.q(s + when)
            t = min(max(t, s), e)
            js.append(gsap(kind, f'.card[data-card-id="{cid}"] {el}', t, p))
        if cid != "end":
            js.append(f"tl.to('{host}',{{opacity:0,duration:0.3,ease:'power2.in'}},{tl.q(e - 0.3)});")
            js.append(f"tl.set('{host}',{{visibility:'hidden'}},{e});")

    caps = close_gaps([(tl.map(a), tl.map(b), t) for a, b, t in cfg["captions"]])
    capdivs = [f'<div class="cap clip" id="cap-{i}" data-start="{tl.q(s):.4f}" data-duration="{tl.q(e) - tl.q(s):.4f}" '
               f'data-track-index="3"><span dir="rtl">{text(t)}</span></div>' for i, (s, e, t) in enumerate(caps)]

    tag = ""
    if cfg.get("speaker"):
        name, ts, te = cfg["speaker"]
        tag = f'<div id="name-tag" dir="rtl">{text(name)}</div>'
        js.append(f"tl.fromTo('#name-tag',{{opacity:0,x:40}},{{opacity:1,x:0,duration:0.4,ease:'power2.out'}},{tl.q(tl.map(ts))});")
        js.append(f"tl.to('#name-tag',{{opacity:0,duration:0.3}},{tl.q(tl.map(te) - 0.3)});")
    js.append("window.__timelines=window.__timelines||{};window.__timelines['talking-head-recut']=tl;")

    index = f"""<!doctype html>
<html lang="he">
<head>
<meta charset="utf-8" />
<style>
@font-face{{font-family:'Heebo ExtraBold';src:url('fonts/Heebo-ExtraBold.woff2') format('woff2');font-display:block}}
@font-face{{font-family:'Heebo Black';src:url('fonts/Heebo-Black.woff2') format('woff2');font-display:block}}
@font-face{{font-family:'Heebo SemiBold';src:url('fonts/Heebo-SemiBold.woff2') format('woff2');font-display:block}}
:root{{--bg:#070908;--text:#ffffff;--accent-0:{EMERALD};--accent-1:#E8F5EE;--accent-2:#9AA6A0;--accent-3:#0E5C3F;--accent-4:#C9D6CF}}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;width:100%;height:100%;overflow:hidden;background:#070908;font-family:'Heebo ExtraBold','Heebo Black',sans-serif}}
#stage{{position:relative;width:100%;height:100%;overflow:hidden;background:#070908}}
.video-wrapper{{position:absolute;left:0;top:0;width:1080px;height:1216px;overflow:hidden}}
.video-wrapper video{{width:100%;height:100%;object-fit:cover}}
#topfade{{position:absolute;left:0;top:0;width:1080px;height:380px;background:linear-gradient(to bottom,rgba(7,9,8,0.75),rgba(7,9,8,0))}}
#fade{{position:absolute;left:0;top:936px;width:1080px;height:280px;background:linear-gradient(to bottom,rgba(7,9,8,0),rgba(7,9,8,1))}}
#logo{{position:absolute;left:56px;top:150px;width:210px;height:auto;filter:drop-shadow(0 4px 14px rgba(0,0,0,0.6))}}
#name-tag{{position:absolute;right:56px;top:170px;font-family:'Heebo ExtraBold',sans-serif;font-size:34px;color:#06100B;background:{EMERALD};padding:8px 22px;border-radius:999px;opacity:0}}
.card-host{{position:absolute;pointer-events:none;overflow:hidden}}
.card-host .card{{position:relative;width:100%;height:100%;overflow:hidden}}
.cap{{position:absolute;left:56px;top:1010px;width:860px;height:220px;display:flex;align-items:center;justify-content:center;text-align:center;font-family:'Heebo ExtraBold',sans-serif;font-size:60px;line-height:1.15;color:#fff;text-shadow:0 3px 0 #000,0 0 18px rgba(0,0,0,0.85)}}
.cap .em{{color:{EMERALD}}}
</style>
</head>
<body>
<div id="stage" data-composition-id="talking-head-recut" data-start="0" data-duration="{D:.4f}" data-fps="{fps}" data-width="1080" data-height="1920">
<div class="video-wrapper" id="video-wrap">
<video id="bg-video" src="input-video.mp4" playsinline data-has-audio="true" data-start="0" data-duration="{D:.4f}" data-track-index="1"></video>
</div>
<div id="fade"></div>
<div id="topfade"></div>
<img id="logo" src="logo.png" alt="אחים להשקעות" />
{tag}
{chr(10).join(hosts)}
{chr(10).join(capdivs)}
<script src="vendor/gsap.min.js"></script>
<script>
(function(){{
{chr(10).join(js)}
}})();
</script>
</div>
</body>
</html>
"""
    words = []
    for s, e, t in caps:
        ws = re.sub(r"[\[\]|]", " ", t).split()
        total = sum(len(w) for w in ws) or 1
        cur = s
        for w in ws:
            d = (e - s) * len(w) / total
            words.append({"text": w, "start": round(cur, 3), "end": round(cur + d, 3)})
            cur += d
    storyboard = {"schemaVersion": 3,
                  "composition": {"fps": fps, "width": 1080, "height": 1920, "durationSeconds": D,
                                  "layout": "portrait", "themeId": "investing-bros-emerald", "seed": 6},
                  "videoTrack": {"sourcePath": "input-video.mp4", "startSec": 0, "endSec": D,
                                 "bounds": {"x": 0, "y": 0, "width": 1080, "height": 1216}},
                  "subtitles": {"enabled": True},
                  "cards": [{"id": cid, "type": c["type"], "startSec": s, "endSec": e, "zone": "lower-third", "accentIndex": 0}
                            for cid, c, s, e in cards]}
    return index, files, storyboard, words


REQUIRED = ["input-video.mp4", "logo.png", "vendor/gsap.min.js", "fonts/Heebo-ExtraBold.woff2",
            "fonts/Heebo-Black.woff2", "fonts/Heebo-SemiBold.woff2"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--project", required=True)
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8"))
    pub = os.path.join(a.project, "public")
    missing = [f for f in REQUIRED if not os.path.exists(os.path.join(pub, f))]
    if missing:
        sys.exit("error: missing in public/: " + ", ".join(missing) + " (see the skill's Steps 2–3)")
    index, files, sb, words = build(cfg)
    os.makedirs(os.path.join(pub, "cards"), exist_ok=True)
    for cid, h in files.items():
        open(os.path.join(pub, "cards", f"{cid}.html"), "w", encoding="utf-8").write(h)
    open(os.path.join(pub, "index.html"), "w", encoding="utf-8").write(index)
    json.dump(sb, open(os.path.join(a.project, "storyboard.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(words, open(os.path.join(a.project, "transcript.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{cfg['name']}: {sb['composition']['durationSeconds']:.2f} s, {len(files)} card(s), "
          f"{len(cfg['captions'])} caption(s) -> {pub}/index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
