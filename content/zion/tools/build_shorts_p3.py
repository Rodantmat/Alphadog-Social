#!/usr/bin/env python3
"""Zion Part 3 Shorts + Stories: 1080x1920 full-screen stills (pan, no letterbox), narration from the film's own segment audio,
hook title, sentence captions, original synthesized music bed (different key/voicing per item), end card to the full documentary.
env: NARR IMG AI SEGS REL(thumb dir/out) OUT ; usage: build_shorts_p3.py [id ...]"""
import json, os, subprocess, sys, textwrap, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
NARR=os.environ["NARR"]; IMG=os.environ["IMG"]; AI=os.environ["AI"]; OUT=os.environ["OUT"]; THUMB=os.environ["THUMB"]
SEGS={s["id"]:s["text"] for s in json.load(open(os.environ.get("SEGS","content/zion/p3_segments.json")))}
SPEC=json.load(open(os.environ.get("SPEC","content/zion/tools/shorts_p3_spec.json")))
SR=48000; W,H=1080,1920; FPS=30
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
want=sys.argv[1:]; os.makedirs(OUT,exist_ok=True)
def run(c): subprocess.run(c,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
def dur(p): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True).stdout)
def sents(x):
    import re; return [p.strip() for p in re.split(r'(?<=[.!?])(?<!St\.)(?<!Mr\.)(?<!Dr\.)(?<!U\.S\.)\s+',x) if p.strip()]
def shot(src,d,out,k,pre=None):
    if src.startswith("A:"):
        run(["ffmpeg","-v","error","-y","-stream_loop","-1","-i",f"{AI}/{src[2:]}.mp4","-t",f"{d:.3f}","-vf",f"scale=-2:{H},crop={W}:{H},fps={FPS},format=yuv420p","-an","-c:v","libx264","-preset","veryfast","-crf","20",out]); return
    p=f"{IMG}/{src}.jpg"; im=Image.open(p); w,h=im.size
    # cover: fill the frame, pan across the free axis (keeps most of the picture visible, no letterbox, mild scale only)
    sc=1.0+0.0
    if w/h>=W/H:   # wide: scale to height, pan horizontally
        a,b=(0.15,0.85) if k%2==0 else (0.85,0.15)
        vf=f"scale=-2:{H+1}:flags=lanczos,crop={W}:{H}:x='(iw-{W})*({a}+({b}-{a})*t/{d:.3f})':y=0"
    else:          # portrait/square: scale to width*1.0, pan vertically
        a,b=(0.1,0.9) if k%2==0 else (0.9,0.1)
        vf=f"scale={W+1}:-2:flags=lanczos,crop={W}:{H}:x=0:y='(ih-{H})*({a}+({b}-{a})*t/{d:.3f})'" if h*(W+1)/w>=H else f"scale=-2:{H+1}:flags=lanczos,crop={W}:{H}:x='(iw-{W})*0.5':y=0"
    run(["ffmpeg","-v","error","-y","-loop","1","-framerate",str(FPS),"-i",p,"-t",f"{d:.3f}","-vf",vf+f",fps={FPS},format=yuv420p","-an","-c:v","libx264","-preset","veryfast","-crf","20",out])
def F(sz): return ImageFont.truetype(BOLD,sz)
def end_card(path,line1,line2,story):
    t=Image.open(THUMB).convert("RGB")
    bg=t.resize((W,H),Image.LANCZOS).filter(ImageFilter.GaussianBlur(40)); bg=Image.eval(bg,lambda v:int(v*0.35))
    w=720; hh=int(t.height*w/t.width); x0=(W-w)//2; y=540; bg.paste(t.resize((w,hh),Image.LANCZOS),(x0,y)); d=ImageDraw.Draw(bg)
    def ctr(txt,yy,f,col=(255,255,255)):
        b=d.textbbox((0,0),txt,font=f); d.text(((W-(b[2]-b[0]))//2,yy),txt,font=f,fill=col,stroke_width=4,stroke_fill=(0,0,0))
    ctr("THE FULL STORY",430,F(70),(255,200,60)); ctr(line1,y+hh+40,F(46)); ctr(line2,y+hh+115,F(40),(255,200,60))
    assert y+hh+115+60<=1220
    bg.save(path)
def music(n,key,total):
    roots=[110,123.47,98,116.54,103.83,130.81,92.5,138.59,87.31,146.83,82.41,155.56,110,98,123.47,116.54,130.81]
    r=roots[key%len(roots)]; minor=(key%2==0)
    ch=[[1,1.2 if minor else 1.25,1.5,2],[0.89,1.12,1.33,1.78],[1.2,1.5,1.8,2.25]] if True else None
    t=np.arange(int(total*SR))/SR; bed=np.zeros(len(t),np.float32); seg=int(SR*(9+key%5))
    for i in range(0,len(t),seg):
        c=ch[(i//seg+key)%len(ch)]; sl=slice(i,min(len(t),i+seg+SR*2)); x=t[sl]; y=np.zeros(len(x),np.float32)
        for j,m in enumerate(c):
            for det in (-0.6,0,0.8): y+=np.sin(2*np.pi*(r*m+det)*x+j+key)*(0.5/(1+j*0.4))
        env=np.minimum(1,np.minimum(np.arange(len(y))/(SR*2),(len(y)-np.arange(len(y)))/(SR*2))); bed[sl]+=(y*env).astype(np.float32)
    return bed/max(1e-6,np.abs(bed).max())
for n,it in enumerate(SPEC["items"]):
    if want and it["id"] not in want: continue
    story=it["kind"]=="story"; GAP=0.25; tmp=f"{OUT}/_{it['id']}"; os.makedirs(tmp,exist_ok=True)
    voice=[]; mask=[]; caps=[]; t=0.5
    lead=np.zeros(int(0.5*SR),np.float32); voice.append(lead); mask.append(np.zeros(len(lead),bool))
    for s in it["segs"]:
        p=f"{NARR}/{s}.m4a"; d=dur(p)
        raw=subprocess.run(["ffmpeg","-v","error","-i",p,"-f","f32le","-ac","1","-ar",str(SR),"-"],capture_output=True).stdout; a=np.frombuffer(raw,np.float32)
        tot=d+GAP; arr=np.zeros(int(tot*SR),np.float32); arr[:len(a)]=a[:len(arr)]; m=np.zeros(len(arr),bool); m[:len(a)]=True; voice.append(arr); mask.append(m)
        ss=sents(SEGS[s]); L=sum(len(x) for x in ss); tt=t
        for x in ss:
            dd=d*len(x)/L; caps.append((tt,tt+dd,x)); tt+=dd
        t+=tot
    narr_len=t; ECARD=2.5 if story else 3.0; total=narr_len+ECARD
    V=np.concatenate(voice); V=np.concatenate([V,np.zeros(int(total*SR)-len(V),np.float32)]); M=np.concatenate(mask+[np.zeros(len(V)-sum(len(x) for x in mask),bool)])
    # shots
    imgs=it["imgs"]; per=(narr_len)/len(imgs); clips=[]
    for k,src in enumerate(imgs):
        o=f"{tmp}/s{k}.mp4"; shot(src,per,o,k); clips.append(o)
    ec=f"{tmp}/end.png"; end_card(ec,it["end1"],it["end2"],story)
    eo=f"{tmp}/end.mp4"; run(["ffmpeg","-v","error","-y","-loop","1","-framerate",str(FPS),"-i",ec,"-t",f"{ECARD}","-vf","format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","20",eo])
    open(f"{tmp}/c.txt","w").write("".join(f"file '{os.path.abspath(c)}'\n" for c in clips+[eo]))
    vo=f"{tmp}/v.mp4"; run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",f"{tmp}/c.txt","-c","copy",vo])
    # overlay: hook title (first 4.5 s) + captions
    hook="\n".join(textwrap.wrap(it["hook"],17)); open(f"{tmp}/hook.txt","w").write(hook)
    flt=f"drawtext=fontfile={BOLD}:textfile={tmp}/hook.txt:fontsize=70:fontcolor=white:borderw=5:bordercolor=black:x=(w-text_w)/2:y=330:line_spacing=10:enable='between(t,0,4.5)'"
    for i,(a,b,x) in enumerate(caps):
        open(f"{tmp}/cap{i}.txt","w").write("\n".join(textwrap.wrap(x,23)))
        flt+=f",drawtext=fontfile={BOLD}:textfile={tmp}/cap{i}.txt:fontsize=48:fontcolor=white:borderw=4:bordercolor=black:box=1:boxcolor=black@0.45:boxborderw=14:x=(w-text_w)/2:y=1130:line_spacing=8:enable='between(t,{a:.2f},{b:.2f})'"
    vt=f"{tmp}/vt.mp4"; run(["ffmpeg","-v","error","-y","-i",vo,"-vf",flt,"-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p",vt])
    # audio
    N=len(V); bed=music(n,it.get("key",n),N/SR); k=np.ones(SR//4)/(SR//4); duck=np.convolve(M.astype(np.float32),k,"same"); tt=np.arange(N)/SR
    gain=(0.17-0.12*duck); fade=np.minimum(1,np.minimum(tt/1.5,(N/SR-tt)/1.2)); mix=np.clip(V*0.95+bed*gain*fade,-1,1).astype(np.float32)
    open(f"{tmp}/mix.f32","wb").write(mix.tobytes())
    run(["ffmpeg","-v","error","-y","-f","f32le","-ar",str(SR),"-ac","1","-i",f"{tmp}/mix.f32","-af","loudnorm=I=-14:TP=-1.5:LRA=9","-c:a","aac","-b:a","160k",f"{tmp}/a.m4a"])
    fin=f"{OUT}/{it['file']}"
    run(["ffmpeg","-v","error","-y","-i",vt,"-i",f"{tmp}/a.m4a","-c:v","copy","-c:a","copy","-shortest","-movflags","+faststart",fin])
    print("OK",it["id"],round(dur(fin),1),"s",round(os.path.getsize(fin)/1e6,1),"MB",flush=True)
