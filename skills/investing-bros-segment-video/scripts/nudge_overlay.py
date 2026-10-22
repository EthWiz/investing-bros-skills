# Nudge v2: top-right, below YouTube card teaser. Writes strips, arrow, and combined overlay.
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
random.seed(7)
FONT="/usr/share/fonts/truetype/sand-box/google/Rubik/Rubik-VariableFont_wght.ttf"
f=ImageFont.truetype(FONT,60); f.set_variation_by_name("Black")
CREAM=(0xFB,0xEE,0xDF,255); MUST=(0xFC,0xAF,0x02,255); NAVY=(0x01,0x15,0x26,255)
W,H=1920,1080; R=1870
def torn(d,x0,y0,x1,y1,col,j=8):
    p=[]
    for x in range(x0,x1+1,16): p.append((x,y0+random.randint(-j,j)))
    for y in range(y0,y1+1,12): p.append((x1+random.randint(-j,j),y))
    for x in range(x1,x0-1,-16): p.append((x,y1+random.randint(-j,j)))
    for y in range(y1,y0-1,-12): p.append((x0+random.randint(-j,j),y))
    d.polygon(p,fill=col)
def rtext(d,t,xr,yc):
    b=d.textbbox((0,0),t,font=f,direction="rtl",language="he")
    d.text((xr-b[2],yc-(b[1]+b[3])/2),t,font=f,fill=NAVY,direction="rtl",language="he")
def shadowed(draw_fn):
    a=Image.new("RGBA",(W,H),(0,0,0,0)); draw_fn(ImageDraw.Draw(a))
    sh=Image.new("RGBA",(W,H),(0,0,0,0)); sh.putalpha(a.getchannel("A").point(lambda v:int(v*0.55)))
    sh=sh.filter(ImageFilter.GaussianBlur(10))
    out=Image.new("RGBA",(W,H),(0,0,0,0)); out.alpha_composite(sh,(6,8)); out.alpha_composite(a); return out
def strips(d):
    random.seed(7)
    torn(d,R-370,309,R,403,CREAM); rtext(d,"לפרק המלא",R-34,354)
    torn(d,R-345,411,R-8,505,MUST); rtext(d,"לחצו כאן",R-43,456)
def arrow(d):  # big up arrow, mustard fill + navy outline, right side above strips
    cx=R-60; top=212; bot=304
    pts=[(cx,top),(cx+47,top+51),(cx+19,top+51),(cx+19,bot),(cx-19,bot),(cx-19,top+51),(cx-47,top+51)]
    d.polygon(pts,fill=MUST,outline=NAVY,width=6)
s=shadowed(strips); a=shadowed(arrow)
s.save("/workspace/nudge-strips.png"); a.save("/workspace/nudge-arrow.png")
c=s.copy(); c.alpha_composite(a); c.save("/workspace/nudge-overlay.png")
