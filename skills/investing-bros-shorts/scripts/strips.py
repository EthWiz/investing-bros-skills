from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random, math
random.seed(7)
F="fonts/Heebo-Black.ttf"
NAVY=(9,36,59);CREAM=(245,235,213);MUST=(216,165,46)
def strip(text,bg,size,tilt):
    f=ImageFont.truetype(F,size,layout_engine=ImageFont.Layout.RAQM)
    l,t,r,b=f.getbbox(text,direction="rtl",language="he")
    w,h=r-l+size*0.9,(b-t)+size*0.55
    W,H=int(w+60),int(h+60)
    m=Image.new("L",(W,H),0);d=ImageDraw.Draw(m)
    pts=[];x0,y0,x1,y1=30,30,30+w,30+h
    n=18
    for i in range(n+1): pts.append((x0+(x1-x0)*i/n, y0+random.uniform(-4,5)))
    for i in range(1,8): pts.append((x1+random.uniform(-6,4), y0+(y1-y0)*i/8))
    for i in range(n,-1,-1): pts.append((x0+(x1-x0)*i/n, y1+random.uniform(-5,4)))
    for i in range(7,0,-1): pts.append((x0+random.uniform(-4,6), y0+(y1-y0)*i/8))
    d.polygon(pts,fill=255)
    paper=Image.new("RGBA",(W,H),bg+(255,))
    noise=Image.effect_noise((W,H),18).convert("L")
    paper=Image.composite(Image.blend(paper,Image.merge("RGBA",[noise]*3+[Image.new("L",(W,H),255)]),0.06),paper,m)
    paper.putalpha(m)
    td=ImageDraw.Draw(paper)
    td.text((W/2,H/2),text,font=f,fill=NAVY,anchor="mm",direction="rtl",language="he")
    sh=Image.new("RGBA",(W,H),(0,0,0,0));sh.putalpha(m.point(lambda v:v*0.45).filter(ImageFilter.GaussianBlur(6)))
    out=Image.new("RGBA",(W+12,H+12),(0,0,0,0));out.alpha_composite(sh,(8,10));out.alpha_composite(paper,(0,0))
    return out.rotate(tilt,resample=Image.BICUBIC,expand=True)
def title(scale,path,cx,y):
    a=strip("למה טסלה ויתרה",CREAM,int(92*scale),1.6)
    b=strip("על לידאר?",MUST,int(92*scale),-1.2)
    c=Image.new("RGBA",(1080,1920),(0,0,0,0))
    c.alpha_composite(a,(int(cx-a.width/2),y)); c.alpha_composite(b,(int(cx-b.width/2+40*scale),y+a.height-int(95*scale)))
    c.save(path)
title(1.0,"hook_big.png",540,290)
title(0.5,"hook_small.png",700,135)
