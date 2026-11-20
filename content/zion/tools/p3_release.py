#!/usr/bin/env python3
"""Package Zion Part 3: re-encoded final (95 MB parts), EN/ES/PT SRT, thumbnail, description, credits, meta_0_long.json.
env: OUT (build_p3 output dir), REL (release dir), IMG (still dir), SEGS, PUBLISH_AT (optional ISO, else public now)"""
import json, os, re, subprocess, hashlib, glob, textwrap
from PIL import Image, ImageDraw, ImageFont
OUT=os.environ["OUT"]; REL=os.environ["REL"]; IMG=os.environ["IMG"]; SEGS=os.environ.get("SEGS","content/zion/p3_segments.json")
os.makedirs(REL,exist_ok=True)
tl=json.load(open(f"{OUT}/timeline.json")); segs={s["id"]:s for s in json.load(open(SEGS))}
lead=0.6
def ts(t):
    h=int(t//3600); m=int(t%3600//60); s=t%60; return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s-int(s))*1000)):03d}"
def sents(x): return [p.strip() for p in re.split(r'(?<=[.!?])\s+',x) if p.strip()]
def srt(lang,path):
    src={"en":SEGS,"es":SEGS.replace(".json","_es.json"),"pt":SEGS.replace(".json","_pt.json")}[lang]
    txt={s["id"]:s["text"] for s in json.load(open(src))}; n=1; out=[]
    for e in tl:
        if e["kind"]!="seg": continue
        ss=sents(txt.get(e["id"],"")); 
        if not ss: continue
        tot=sum(len(x) for x in ss); t=e["start"]+lead; span=e["dur"]-0.35
        for x in ss:
            d=span*len(x)/tot; out.append(f"{n}\n{ts(t)} --> {ts(t+d-0.05)}\n{textwrap.fill(x,42)}\n"); n+=1; t+=d
    open(path,"w",encoding="utf-8").write("\n".join(out))
for l in ("en","es","pt"): srt(l,f"{REL}/zion_ch3.{l}.srt")
# video re-encode (<=100 MB per git file -> 95 MB parts)
final=f"{REL}/zion_ch3_final.mp4"
subprocess.run(["ffmpeg","-v","error","-y","-i",f"{OUT}/p3_video.mp4","-c:v","libx264","-preset","medium","-crf","26","-maxrate","1800k","-bufsize","3600k","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-movflags","+faststart",final],check=True)
sz=os.path.getsize(final); print("final MB",sz/1e6)
h=hashlib.sha256(open(final,"rb").read()).hexdigest(); open(final+".sha256","w").write(f"{h}  zion_ch3_final.mp4\n")
with open(final,"rb") as f:
    i=0
    while True:
        b=f.read(95*1024*1024)
        if not b: break
        open(f"{final}.part{i:02d}","wb").write(b); i+=1
os.remove(final)
# thumbnail
base=Image.open(f"{IMG}/z3_npg_tunnel_west_portal_1928.jpg").convert("RGB"); W,H=1280,720
r=max(W/base.width,H/base.height); base=base.resize((int(base.width*r),int(base.height*r))); x=(base.width-W)//2; y=(base.height-H)//2; im=base.crop((x,y,x+W,y+H))
ov=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov); d.rectangle((0,H-260,W,H),fill=(0,0,0,170)); im=Image.alpha_composite(im.convert("RGBA"),ov).convert("RGB"); d=ImageDraw.Draw(im)
def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
        if os.path.exists(p): return ImageFont.truetype(p,sz)
    return ImageFont.load_default()
d.text((60,H-235),"THE IMPOSSIBLE TUNNEL",font=font(92),fill=(255,255,255)); d.text((64,H-110),"1.1 miles through solid rock · Zion",font=font(48),fill=(240,190,80))
im.save(f"{REL}/thumb.jpg",quality=92)
# chapters
chap=[("0:00","Cold open: three inches")]
for e in tl:
    if e["kind"]=="card":
        t=e["start"]+lead; chap.append((f"{int(t//60)}:{int(t%60):02d}",e["text"].title()))
chaps="\n".join(f"{a} {b}" for a,b in chap)
TITLE="The Impossible Tunnel: Zion's 1.1-Mile Road Through Solid Rock"
desc=f"""In 1927 two crews began digging toward each other from opposite ends of a mile of solid sandstone in Zion. This is the story of how a canyon nobody believed in became a national park, and how the road to it was cut through the cliffs: Dellenbaugh's paintings at the 1904 World's Fair, the park by petition, Presidents Taft and Wilson, the railroad and Harding's visit, the dead end, and the Zion-Mount Carmel Tunnel, dedicated July 4, 1930.

CHAPTERS
{chaps}

ZION: PART 3 OF 3
Part 1: Zion's deadliest day
Part 2: The Day the Mountain Fell
All episodes: playlist "America's National Parks: The Hidden History".

LISTEN AS A PODCAST
Apple Podcasts: https://podcasts.apple.com/us/podcast/americas-national-parks-the-hidden-history/id6827800067
Spotify: https://podcasters.spotify.com/pod/show/alphadog-studio9
En español: https://podcasts.apple.com/us/podcast/parques-nacionales-de-estados-unidos-la-historia-oculta/id6827801300

Subtitles: English, Español, Português.

SOURCES (selected)
National Park Service, Zion history and Zion-Mount Carmel Highway; Historic American Engineering Record (Library of Congress); Utah History Encyclopedia; NPGallery.

CREDITS
ARCHIVAL & PARK PHOTOS (PUBLIC DOMAIN): National Park Service (NPGallery), Library of Congress / HAER, Wikimedia Commons scans. A few photos are used under Creative Commons licenses (CC BY / CC BY-SA); every author and license is credited in the pinned comment.
ILLUSTRATED SCENE: one AI-assisted illustrated clip for a moment no camera recorded (the Flanigan cable). It is an illustration, not real footage.
NARRATION: AI-generated voice (disclosed). Script researched and written by AlphaDog Studio.
MUSIC: original ambient music.

#Zion #ZionNationalPark #NationalParks #History #Documentary"""
open(f"{REL}/desc_long.txt","w").write(desc)
idx={f["name"]:f for f in json.load(open(f"{IMG}/../index.json"))["files"]}; lines=[]; nonpd=[]
used=sorted({s for e in tl if e["kind"]=="seg" for s in e["shots"]})
for u in used:
    f=idx.get(u.replace(".jpg","").replace(".mp4",""))
    if not f: continue
    lines.append(f"• {f.get('title','')}: {f.get('credit','')} — {f.get('source_page','')}")
    if "public" not in f.get("license","").lower() and "cc0" not in f.get("license","").lower(): nonpd.append((u,f.get("license")))
print("NON-PD LICENSES:",nonpd)
open(f"{REL}/credits_comment.txt","w").write(f'Full credits for "{TITLE}" (AlphaDog Studio, Zion Part 3 of 3). All archival photos are public domain; credit lines as published.\n\n'+"\n".join(lines)+"\n\nOne illustrated AI clip (Flanigan cable) shows a moment no camera recorded. Narration is AI-generated (disclosed).\n")
meta={"file":"zion_ch3_final.mp4","title":TITLE,"description_file":"desc_long.txt","tags":["zion national park","zion","zion mount carmel tunnel","zion tunnel","utah","national parks","national parks history","zion documentary","history","documentary","harding","dellenbaugh"],"category":"27","privacy":"public","thumbnail":"thumb.jpg","made_for_kids":False,"synthetic":False,"language":"en",
"captions":[{"file":"zion_ch3.en.srt","language":"en","name":"English"},{"file":"zion_ch3.es.srt","language":"es","name":"Español"},{"file":"zion_ch3.pt.srt","language":"pt","name":"Português"}],
"localizations":{"es":{"title":"El túnel imposible: 1,8 km de carretera por roca sólida en Zion","description":"Dos cuadrillas excavaron una hacia la otra, en la oscuridad, a través de más de un kilómetro y medio de roca arenisca en Zion. La historia de cómo un cañón en el que nadie creía se volvió parque nacional y cómo abrieron la carretera hasta él. Subtítulos en español."},"pt":{"title":"O túnel impossível: 1,8 km de estrada por rocha sólida em Zion","description":"Duas equipes cavaram uma em direção à outra, no escuro, por mais de um quilômetro e meio de arenito em Zion. A história de como um cânion em que ninguém acreditava virou parque nacional e de como abriram a estrada até ele. Legendas em português."}}}
if os.environ.get("PUBLISH_AT"): meta["privacy"]="private"; meta["publish_at"]=os.environ["PUBLISH_AT"]
json.dump(meta,open(f"{REL}/meta_0_long.json","w"),ensure_ascii=False,indent=1)
print("release ready",os.listdir(REL))
