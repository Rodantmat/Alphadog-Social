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
def chunk(ss,mx=95):
    import re; out=[]
    for x in ss:
        while len(x)>mx:
            cuts=[m.end() for m in re.finditer(r'[,:;] |\s(?:and|but|to|that|where|with) ',x) if 35<=m.end()<=mx]
            if not cuts: break
            c=cuts[-1]; out.append(x[:c].strip()); x=x[c:].strip()
        out.append(x)
    return out
def shot(src,d,out,k,pre=None):
    if src.startswith("A:"):
        run(["ffmpeg","-v","error","-y","-stream_loop","-1","-i",f"{AI}/{src[2:]}.mp4","-t",f"{d:.3f}","-vf",f"scale=-2:{H},crop={W}:{H},fps={FPS},format=yuv420p","-an","-c:v","libx264","-preset","veryfast","-crf","20",out]); return
    p0=f"{IMG}/{src}.jpg"; im0=Image.open(p0).convert("RGB"); w0,h0=im0.size; mx,my=int(w0*0.045),int(h0*0.045)
    p=f"{out}.src.jpg"; im0.crop((mx,my,w0-mx,h0-my)).save(p,quality=95); im=Image.open(p); w,h=im.size
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
        ss=chunk(sents(SEGS[s])); L=sum(len(x) for x in ss); tt=t
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
    # overlay: hook title (first 4.5 s) + sentence captions, rendered with PIL (no drawtext: its line breaks rendered as tofu boxes)
    def wrap(txt,font,maxw):
        words=txt.split(); lines=[]; cur=""
        for w_ in words:
            t_=(cur+" "+w_).strip()
            if font.getbbox(t_)[2]<=maxw or not cur: cur=t_
            else: lines.append(cur); cur=w_
        if cur: lines.append(cur)
        return lines
    def card(lines,font,pad,line_gap,box,stroke):
        hs=[font.getbbox(l)[3]-font.getbbox(l)[1] for l in lines]; asc=font.getmetrics()[0]
        wmax=max(font.getbbox(l)[2] for l in lines); lh=font.getmetrics()[0]+font.getmetrics()[1]
        Wc=wmax+2*pad; Hc=len(lines)*lh+(len(lines)-1)*line_gap+2*pad
        im=Image.new("RGBA",(Wc,Hc),(0,0,0,0)); d=ImageDraw.Draw(im)
        if box: d.rounded_rectangle((0,0,Wc-1,Hc-1),radius=18,fill=(0,0,0,125))
        for i,l in enumerate(lines):
            w_=font.getbbox(l)[2]; d.text(((Wc-w_)//2,pad+i*(lh+line_gap)),l,font=font,fill=(255,255,255,255),stroke_width=stroke,stroke_fill=(0,0,0,255))
        return im
    ovs=[]  # (png, x, y, t0, t1)
    hk=card(wrap(it["hook"],F(70),700),F(70),10,8,False,5); hp=f"{tmp}/hook.png"; hk.save(hp); ovs.append((hp,(W-hk.width)//2,330,0,4.5))
    for i,(a_,b_,x) in enumerate(caps):
        cp=card(wrap(x,F(46),700),F(46),16,6,True,4); pp=f"{tmp}/cap{i}.png"; cp.save(pp); assert 1130+cp.height<=1440, f'caption too tall {cp.height} in {it["id"]}'; ovs.append((pp,(W-cp.width)//2,1130,a_,b_))
    cmd=["ffmpeg","-v","error","-y","-i",vo]
    for o in ovs: cmd+=["-i",o[0]]
    fc=""; last="0:v"
    for i,(pp,x_,y_,t0,t1) in enumerate(ovs):
        fc+=f"[{last}][{i+1}:v]overlay=x={x_}:y={y_}:enable='between(t,{t0:.2f},{t1:.2f})'[v{i}];"; last=f"v{i}"
    vt=f"{tmp}/vt.mp4"; run(cmd+["-filter_complex",fc.rstrip(";"),"-map",f"[{last}]","-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p",vt])
    # audio
    N=len(V); bed=music(n,it.get("key",n),N/SR); k=np.ones(SR//4)/(SR//4); duck=np.convolve(M.astype(np.float32),k,"same"); tt=np.arange(N)/SR
    gain=(0.17-0.12*duck); fade=np.minimum(1,np.minimum(tt/1.5,(N/SR-tt)/1.2)); mix=np.clip(V*0.95+bed*gain*fade,-1,1).astype(np.float32)
    open(f"{tmp}/mix.f32","wb").write(mix.tobytes())
    run(["ffmpeg","-v","error","-y","-f","f32le","-ar",str(SR),"-ac","1","-i",f"{tmp}/mix.f32","-af","loudnorm=I=-14:TP=-1.5:LRA=9","-c:a","aac","-b:a","160k",f"{tmp}/a.m4a"])
    fin=f"{OUT}/{it['file']}"
    run(["ffmpeg","-v","error","-y","-i",vt,"-i",f"{tmp}/a.m4a","-c:v","copy","-c:a","copy","-shortest","-movflags","+faststart",fin])
    print("OK",it["id"],round(dur(fin),1),"s",round(os.path.getsize(fin)/1e6,1),"MB",flush=True)
