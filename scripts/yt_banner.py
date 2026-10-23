#!/usr/bin/env python3
"""Render the AlphaDog Studio channel banner (2560x1440). usage: yt_banner.py LOGO_PNG OUT_JPG"""
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter
def font(cands, size):
    for p in cands:
        try: return ImageFont.truetype(p, size)
        except OSError: pass
    return ImageFont.load_default(size)
SERIF = ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"]
SANS = ["/usr/share/fonts/opentype/inter/Inter-Medium.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
BG=np.array([11,20,38],np.float32); MAR=np.array([84,40,32],np.float32); CREAM=(244,240,232)
W,H=2560,1440
r=np.random.default_rng(3)
f=sum(gaussian_filter(r.standard_normal((H//4+1,W//4+1)),s)*s for s in (40,20,10))
f=np.array(Image.fromarray(((f-f.min())/(f.max()-f.min())*255).astype(np.float32)).resize((W,H),Image.BICUBIC))
q=f/255*46; line=np.clip(1-np.abs(q-np.round(q))/0.035,0,1)*np.where(np.round(q)%5==0,0.22,0.09)
yy,xx=np.mgrid[0:H,0:W]; rr=np.sqrt(((xx-W/2)/(W*0.40))**2+((yy-H/2)/(H*0.26))**2)
glow=np.clip(1-rr,0,1)**1.6
arr=BG+(MAR-BG)*glow[...,None]*0.75
arr=arr+(np.array([244,240,232])-arr)*(line*(1-glow*0.9))[...,None]
b=Image.fromarray(np.clip(arr,0,255).astype(np.uint8)); d=ImageDraw.Draw(b)
LS=300; gap=46; cx,cy=W//2,H//2
av=Image.open(sys.argv[1]).convert("RGB").resize((LS,LS),Image.LANCZOS)
m=Image.new("L",(LS,LS),0); ImageDraw.Draw(m).ellipse([0,0,LS-1,LS-1],fill=255)
SBf=font(SERIF,96); tw=d.textlength("ALPHADOG STUDIO",font=SBf)
lx=int(cx-(LS+gap+tw)/2); b.paste(av,(lx,cy-LS//2),m); tx=lx+LS+gap
d.text((tx,cy-30),"ALPHADOG STUDIO",font=SBf,fill=CREAM,anchor="lm")
d.line([(tx+4,cy+44),(tx+124,cy+44)],fill=(214,160,82),width=4)
d.text((tx+2,cy+92),"Strange histories of American places",font=font(SANS,42),fill=(214,204,188),anchor="lm")
b.save(sys.argv[2],quality=88)
print("BANNER", sys.argv[2], b.size)
