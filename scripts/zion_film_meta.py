import json, os
from PIL import Image, ImageDraw, ImageFont
out="/tmp/w/out"; ch=open(f"{out}/chapters.txt").read().strip()
Y3="https://youtu.be/30zzYRt_Mgk"
title="Zion National Park: The Complete Story (Full Documentary)"
desc=f"""The complete Zion story in one watch: the flash floods and the Narrows, the mountain that fell and the lake it left behind, and the park that was carved out by petition and a mile-long tunnel through solid rock.

CHAPTERS
{ch}

Also available as three episodes in the playlist "America's National Parks: The Hidden History" (Part 3: {Y3}).

LISTEN AS A PODCAST
Apple Podcasts: https://podcasts.apple.com/us/podcast/americas-national-parks-the-hidden-history/id6827800067
Spotify: https://podcasters.spotify.com/pod/show/alphadog-studio9
En español: https://podcasts.apple.com/us/podcast/parques-nacionales-de-estados-unidos-la-historia-oculta/id6827801300

Subtitles: English, Español, Português.

SAFETY: Flash floods and rockfall are real hazards in Zion. Follow park closures and check current conditions before you go.

CREDITS: Filmed and photographed by AlphaDog Studio in Zion National Park (November 2021). Archival photos: National Park Service, Library of Congress / HAER, USGS, Wikimedia Commons (some under CC BY / CC BY-SA; every credit is in the pinned comments of each episode). Illustrated scenes are AI-assisted illustrations, not real footage. Narration is AI-generated (disclosed). Original music.

#Zion #ZionNationalPark #NationalParks #Documentary #History"""
open(f"{out}/desc_long.txt","w").write(desc)
IMG="/tmp/fbs/yellowstone-media/zion3/img"; W,H=1280,720
b=Image.open(f"{IMG}/z3_npg_tunnel_west_portal_1928.jpg").convert("RGB"); r=max(W/b.width,H/b.height); b=b.resize((int(b.width*r),int(b.height*r))); x=(b.width-W)//2; y=(b.height-H)//2; im=b.crop((x,y,x+W,y+H)).convert("RGBA")
ov=Image.new("RGBA",(W,H),(0,0,0,0)); ImageDraw.Draw(ov).rectangle((0,H-260,W,H),fill=(0,0,0,170)); im=Image.alpha_composite(im,ov).convert("RGB"); d=ImageDraw.Draw(im)
F="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def fit(t,sz,mw):
    while sz>20 and d.textbbox((0,0),t,font=ImageFont.truetype(F,sz))[2]>mw: sz-=2
    return ImageFont.truetype(F,sz)
d.text((60,H-235),"ZION: THE COMPLETE STORY",font=fit("ZION: THE COMPLETE STORY",92,W-120),fill=(255,255,255)); d.text((64,H-110),"Floods · a fallen mountain · a mile-long tunnel",font=fit("Floods · a fallen mountain · a mile-long tunnel",46,W-120),fill=(240,190,80))
im.save(f"{out}/thumb.jpg",quality=92)
m={"file":"zion_film_final.mp4","title":title,"description_file":"desc_long.txt","tags":["zion national park","zion","zion documentary","zion full documentary","utah","national parks","national parks history","documentary","history"],"category":"27","privacy":"public","thumbnail":"thumb.jpg","made_for_kids":False,"synthetic":False,"language":"en","playlist_title":"America's National Parks: The Hidden History",
  "captions":[{"file":f"zion_film.{l}.srt","language":l,"name":n} for l,n in (("en","English"),("es","Español"),("pt","Português"))]}
json.dump(m,open(f"{out}/meta_0_long.json","w"),ensure_ascii=False,indent=1)
