"""Stat card for Zion P1 s039 (V-rule: a data beat instead of a 15 s single photo)."""
import sys
sys.path.insert(0, "/home/claude/doc/yellowstone/graphics/src")
from gfx import *
from cards import push_render
from PIL import Image, ImageFilter, ImageOps, ImageDraw, ImageFont
W2, H2 = 3840, 2160
CF={"deaths":("own_al_1110175504","ANGELS LANDING","17+","recorded deaths","Many happened where people felt safe"),"hoover":("/home/claude/doc/zion/media/pd_ch2/img/z2_nps_cable_mtn_before_2015","THE SENTINEL ROCK AVALANCHE","90","Hoover Dams of concrete","to rebuild the missing mountainside"),"island":("/home/claude/doc/zion/media/pd_ch2/img/z2_npg_sentinel_slide_color_1","APRIL 12, 1995","430","people cut off at Zion Lodge","by the Park Service's count"),"zero":("/home/claude/doc/zion/media/pd_ch2/img/z2_nps_weeping_rock_dust_2023","ROCKFALL IN ZION","0","visitors killed by a rockfall","according to the Park Service"),"odds":("own_al_1110182354","ANGELS LANDING PERMITS","8%","odds on the busiest days","Nearly 400,000 permits in two years")}
k=sys.argv[2] if len(sys.argv)>2 else "deaths"; c=CF[k]
bg = ImageOps.fit(Image.open(c[0] + ".jpg" if c[0].startswith("/") else f"/home/claude/doc/zion/media/pd_ch1/img/{c[0]}.jpg").convert("RGB"), (W2, H2))
bg = bg.filter(ImageFilter.GaussianBlur(18)); bg = Image.eval(bg, lambda v: int(v * 0.38))
d = ImageDraw.Draw(bg)
fk = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 84) if __import__("os").path.exists("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf") else ImageFont.truetype(SERIFB, 84)
fb = ImageFont.truetype(SERIFB, 420); fs = ImageFont.truetype(SERIFB, 120)
d.text((W2/2, 640), c[1], font=fk, fill=GOLD, anchor="mm")
d.text((W2/2, 1080), c[2], font=fb, fill=CREAM, anchor="mm")
d.text((W2/2, 1420), c[3], font=fs, fill=TEXT, anchor="mm")
d.line((W2/2-260, 1580, W2/2+260, 1580), fill=GOLD, width=6)
d.text((W2/2, 1720), c[4], font=ImageFont.truetype(SERIFB, 92), fill=MUTED, anchor="mm")
bg.reduce(4).save(f"/home/claude/doc/zion/graphics/p1_stat_{k}.jpg")
push_render(bg, float(sys.argv[1]) if len(sys.argv) > 1 else 7.0, f"/home/claude/doc/zion/graphics/zc{"2" if k in ("hoover","island","zero") else "1"}_stat_{k}.mp4")
