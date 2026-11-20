#!/usr/bin/env python3
"""Zion Part 3 simple documentary builder (ffmpeg + numpy + PIL only).
plan: SEG | I:<img>.jpg | - | w | opts   or   SEG | A:<clip>  (AI clip, from AI dir)
env: NARR (dir of sNNN.m4a), IMG, AI (dir with clips), SEGS (p3_segments.json), PLAN, OUT, LIMIT (first N segments for tests)
Output: OUT/p3_video.mp4 (1920x1080, 30 fps, voice+music bed) , OUT/timeline.json"""
import json, os, subprocess, sys, shutil, hashlib, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
NARR=os.environ["NARR"]; IMG=os.environ["IMG"]; AI=os.environ.get("AI",""); SEGS=json.load(open(os.environ["SEGS"]))
PLAN=os.environ["PLAN"]; OUT=os.environ["OUT"]; LIMIT=int(os.environ.get("LIMIT","0")); W,H,FPS,SR=1920,1080,30,48000
os.makedirs(OUT+"/clips",exist_ok=True); os.makedirs(OUT+"/tmp",exist_ok=True)
def run(c): subprocess.run(c,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
def dur(p): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True).stdout)
FONT=lambda sz: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",sz) if os.path.exists("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf") else ImageFont.load_default()
plan={}
for ln in open(PLAN):
    if not ln.strip() or ln.startswith("#"): continue
    seg,src,ss,w,*o=[x.strip() for x in ln.rstrip("\n").split("|")]; plan.setdefault(seg,[]).append(src)
segs=SEGS[:LIMIT] if LIMIT else SEGS
def frame_canvas(path,out):
    """fit image over a blurred, darkened cover background (never crops the photo); 2400x1350 canvas for the slow zoom"""
    cw,ch=2400,1350; im=Image.open(path).convert("RGB")
    bg=im.copy(); s=max(cw/bg.width,ch/bg.height); bg=bg.resize((int(bg.width*s)+1,int(bg.height*s)+1),Image.LANCZOS)
    l,t=(bg.width-cw)//2,(bg.height-ch)//2; bg=bg.crop((l,t,l+cw,t+ch)).filter(ImageFilter.GaussianBlur(40)); bg=Image.eval(bg,lambda v:int(v*0.35))
    s=min(cw*0.94/im.width,ch*0.94/im.height); fg=im.resize((int(im.width*s),int(im.height*s)),Image.LANCZOS)
    bg.paste(fg,((cw-fg.width)//2,(ch-fg.height)//2)); bg.save(out,quality=93)
def shot_still(img,d,out,k):
    cv=f"{OUT}/tmp/cv_{hashlib.md5(img.encode()).hexdigest()[:10]}.jpg"
    if not os.path.exists(cv): frame_canvas(img,cv)
    n=max(2,round(d*FPS)); z0,z1=(1.0,1.07) if k%2==0 else (1.07,1.0)
    vf=(f"scale=w='trunc(2400*({z0}+({z1}-{z0})*t/{d:.3f})/2)*2':h=-2:eval=frame,crop={W}:{H},fps={FPS},format=yuv420p,fade=t=in:st=0:d=0.35")
    run(["ffmpeg","-v","error","-y","-loop","1","-framerate",str(FPS),"-i",cv,"-t",f"{d:.3f}","-vf",vf,"-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",out])
def shot_ai(clip,d,out):
    run(["ffmpeg","-v","error","-y","-stream_loop","-1","-i",clip,"-t",f"{d:.3f}","-vf",f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p,fade=t=in:st=0:d=0.35","-an","-c:v","libx264","-preset","veryfast","-crf","18",out])
def card(text,d,out):
    im=Image.new("RGB",(W,H),(10,10,12)); dr=ImageDraw.Draw(im)
    if os.environ.get("CARDBG") and os.path.exists(os.environ["CARDBG"]):
        b=Image.open(os.environ["CARDBG"]).convert("RGB"); s=max(W/b.width,H/b.height); b=b.resize((int(b.width*s)+1,int(b.height*s)+1)); b=b.crop(((b.width-W)//2,(b.height-H)//2,(b.width-W)//2+W,(b.height-H)//2+H)).filter(ImageFilter.GaussianBlur(10)); im=Image.eval(b,lambda v:int(v*0.25)); dr=ImageDraw.Draw(im)
    f=FONT(84); words=text.upper().split(); lines=[]; cur=""
    for w_ in words:
        t=(cur+" "+w_).strip()
        if dr.textlength(t,font=f)>W-360 and cur: lines.append(cur); cur=w_
        else: cur=t
    lines.append(cur); y=(H-len(lines)*110)//2
    for ln in lines: dr.text(((W-dr.textlength(ln,font=f))//2,y),ln,font=f,fill=(255,255,255),stroke_width=2,stroke_fill=(0,0,0)); y+=110
    dr.rectangle(((W-240)//2,y+20,(W+240)//2,y+26),fill=(255,200,60)); p=f"{OUT}/tmp/card.png"; im.save(p)
    run(["ffmpeg","-v","error","-y","-loop","1","-framerate",str(FPS),"-i",p,"-t",f"{d:.3f}","-vf",f"fps={FPS},format=yuv420p,fade=t=in:st=0:d=0.6,fade=t=out:st={d-0.6:.2f}:d=0.6","-c:v","libx264","-preset","veryfast","-crf","18",out])
def chap(s):
    c=s["chapter"]; c=c.split("(")[0].strip(); c=c.replace("COLD OPEN — ","").replace("CLOSER — ","")
    return c.strip('"').strip()
timeline=[]; vids=[]; voice=[]; mask=[]; t=0.0; last_ch=None; GAP=0.35
def add_silence(sec,v=False):
    global t; n=int(sec*SR); voice.append(np.zeros(n,np.float32)); mask.append(np.full(n,v,bool)); t+=sec
add_silence(0.6)
for s in segs:
    ch=chap(s)
    if ch!=last_ch and not s["chapter"].startswith("COLD OPEN"):
        o=f"{OUT}/clips/card_{ch[:12].replace(' ','_')}.mp4"; card(ch,4.0,o); vids.append(o); timeline.append({"kind":"card","text":ch,"start":round(t,2),"dur":4.0}); add_silence(4.0)
    last_ch=ch if not s["chapter"].startswith("COLD OPEN") else last_ch
    p=f"{NARR}/{s['id']}.m4a"; d=dur(p); tot=d+GAP
    raw=subprocess.run(["ffmpeg","-v","error","-i",p,"-f","f32le","-ac","1","-ar",str(SR),"-"],capture_output=True).stdout; a=np.frombuffer(raw,np.float32)
    arr=np.zeros(int(tot*SR),np.float32); arr[:len(a)]=a[:len(arr)]; voice.append(arr); m=np.zeros(len(arr),bool); m[:len(a)]=True; mask.append(m)
    srcs=plan[s["id"]]; fixed=0.0; shots=[]
    for src in srcs:
        if src.startswith("A:"):
            c=f"{AI}/{src[2:]}.mp4"
            if os.path.exists(c): shots.append(("ai",c)); continue
        elif src.startswith("I:"):
            pth=f"{IMG}/{src[2:]}"
            if os.path.exists(pth): shots.append(("img",pth))
    assert shots,("no media for",s["id"])
    per=tot/len(shots)
    for k,(ty,pth) in enumerate(shots):
        o=f"{OUT}/clips/{s['id']}_{k}.mp4"
        if not os.path.exists(o): (shot_ai(pth,per,o) if ty=="ai" else shot_still(pth,per,o,k))
        vids.append(o)
    timeline.append({"kind":"seg","id":s["id"],"start":round(t,2),"dur":round(tot,2),"shots":[os.path.basename(p) for _,p in shots]}); t+=tot
add_silence(3.0)  # end hold
last=[v for v in vids if v.endswith(".mp4")][-1]
endhold=f"{OUT}/clips/endhold.mp4"; run(["ffmpeg","-v","error","-y","-sseof","-0.1","-i",last,"-vf",f"tpad=stop_mode=clone:stop_duration=3.0,fade=t=out:st=2.4:d=0.6,fps={FPS}","-t","3.0","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",endhold]); vids.append(endhold)
# lead-in black 0.6 s
lead=f"{OUT}/clips/lead.mp4"; run(["ffmpeg","-v","error","-y","-f","lavfi","-i",f"color=c=black:s={W}x{H}:r={FPS}","-t","0.6","-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p",lead]); vids.insert(0,lead)
open(OUT+"/concat.txt","w").write("".join(f"file '{os.path.abspath(v)}'\n" for v in vids))
run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",OUT+"/concat.txt","-c","copy",OUT+"/video_only.mp4"])
# ---- audio: voice + synthesized music bed (original, slow pads; chord changes per ~45 s; ducked under voice)
V=np.concatenate(voice); M=np.concatenate(mask); N=len(V); tt=np.arange(N)/SR
chords=[[110,164.81,220,277.18],[98,146.83,196,246.94],[130.81,196,261.63,329.63],[87.31,130.81,174.61,220]]  # Am9-ish, G, C, F
bed=np.zeros(N,np.float32); seg_len=45*SR
for i in range(0,N,seg_len):
    ch=chords[(i//seg_len)%len(chords)]; sl=slice(i,min(N,i+seg_len+SR*3)); x=tt[sl]; y=np.zeros(len(x),np.float32)
    for j,f in enumerate(ch):
        for det in (-0.7,0.0,0.9): y+=np.sin(2*np.pi*(f+det)*x+j)*(0.5/(1+j*0.4))
    y*=0.5+0.5*np.sin(2*np.pi*0.07*x+1.3)**2
    env=np.minimum(1,np.minimum((np.arange(len(y)))/(SR*3),(len(y)-np.arange(len(y)))/(SR*3)))
    bed[sl]+=(y*env).astype(np.float32)
bed/= max(1e-6,np.abs(bed).max()); k=np.ones(SR//4)/(SR//4); duck=np.convolve(M.astype(np.float32),k,"same")
gain=(0.16-0.11*duck); fade=np.minimum(1,np.minimum(tt/3,(N/SR-tt)/4)); mix=V*0.9+bed*gain*fade
mix=np.clip(mix,-1,1).astype(np.float32); open(OUT+"/mix.f32","wb").write(mix.tobytes())
run(["ffmpeg","-v","error","-y","-f","f32le","-ar",str(SR),"-ac","1","-i",OUT+"/mix.f32","-af","loudnorm=I=-16:TP=-1.5:LRA=9","-c:a","aac","-b:a","192k",OUT+"/audio.m4a"])
run(["ffmpeg","-v","error","-y","-i",OUT+"/video_only.mp4","-i",OUT+"/audio.m4a","-c:v","copy","-c:a","copy","-shortest","-movflags","+faststart",OUT+"/p3_video.mp4"])
json.dump(timeline,open(OUT+"/timeline.json","w"),indent=1)
print("DONE",OUT+"/p3_video.mp4",round(dur(OUT+"/p3_video.mp4"),1),"s")
