from PIL import Image, ImageDraw, ImageFont
import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'strips.py')).read().split('def title')[0])
GOLD=(245,183,31);WHITE=(255,255,255)
def font(s,w="Black"):return ImageFont.truetype(f"fonts/Heebo-{w}.ttf",s,layout_engine=ImageFont.Layout.RAQM)
def arrow(d,cx,y,s,col):
    d.rectangle([cx-s*0.18,y,cx+s*0.18,y+s*0.5],fill=col);d.polygon([(cx-s*0.5,y+s*0.45),(cx+s*0.5,y+s*0.45),(cx,y+s)],fill=col)
c=Image.new("RGBA",(1080,1920),NAVY+(255,));d=ImageDraw.Draw(c)
lg=Image.open("logo.png").convert("RGBA");lg=lg.resize((520,int(lg.height*520/lg.width)));c.alpha_composite(lg,(540-lg.width//2,420))
y=440+lg.height+30;f=font(48);w=d.textlength("פרק 3",font=f,direction="rtl");d.rounded_rectangle([540-w/2-34,y,540+w/2+34,y+80],40,fill=CREAM)
d.text((540,y+40),"פרק 3",font=f,fill=NAVY,anchor="mm",direction="rtl");y+=130
f=font(64,"ExtraBold")
for line in ("ספייס אקס: החברה המובילה הבאה","או הייפ מהחלל?"):d.text((540,y),line,font=f,fill=WHITE,anchor="mm",direction="rtl");y+=88
y+=40;d.text((540,y),"הקישור לפרק המלא בתיאור",font=font(48,"ExtraBold"),fill=GOLD,anchor="mm",direction="rtl");arrow(d,540,y+50,90,GOLD)
c.convert("RGB").save("v5_end.png")
