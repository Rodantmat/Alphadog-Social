#!/usr/bin/env python3
"""Zion Part 3 Shorts + Stories: 1080x1920 full-screen stills (pan, no letterbox), narration from the film's own segment audio,
hook title, sentence captions, original synthesized music bed (different key/voicing per item), end card to the full documentary.
env: NARR IMG AI SEGS REL(thumb dir/out) OUT ; usage: build_shorts_p3.py [id ...]"""
import json, os, re, subprocess, sys, textwrap, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
NARR=os.environ["NARR"]; IMG=os.environ["IMG"]; AI=os.environ["AI"]; OUT=os.environ["OUT"]; THUMB=os.environ["THUMB"]
SEGS={s["id"]:s["text"] for s in json.load(open(os.environ.get("SEGS","content/zion/p3_segments.json")))}
SPEC=json.load(open(os.environ.get("SPEC","content/zion/tools/shorts_p3_spec.json")))
SR=48000; W,H=1080,1920; FPS=30; OWN=os.environ.get('OWN','content/zion/own/clips')
NUMW=set('one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million'.split())
STOPCAP=set('a an the in it its is he she they we i on of at to but and as for from this that there then when while after before with'.split())
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
want=sys.argv[1:]; os.makedirs(OUT,exist_ok=True)
def run(c): subprocess.run(c,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
def dur(p): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True).stdout)
def sents(x):
    import re; return [p.strip() for p in re.split(r'(?<=[.!?])(?<!St\.)(?<!Mr\.)(?<!Dr\.)(?<!U\.S\.)\s+',x) if p.strip()]
def chunk(ss,mx=88):
    import re; out=[]
    bad={'a','an','the','of','with','to','and','in','on','at','for','by','from','as','or','its','their','his','her','is','was','that','than','into','over','but','where','who','which'}
    for x in ss:
        while len(x)>mx:
            cands=[m.end() for m in re.finditer(r'[,:;] ',x)]
            cands+=[m.start() for m in re.finditer(r'\s(?=(?:and|but|to|that|where|with|because|which)\s)',x)]
            cands=[c for c in cands if 25<=c<=len(x)-20 and c<=mx]
            if not cands:
                cands=[m.start() for m in re.finditer(r' ',x) if 25<=m.start()<=len(x)-20 and m.start()<=mx and x[:m.start()].split()[-1].lower().strip(',.') not in bad]
            if not cands: break
            c=min(cands,key=lambda k:abs(k-len(x)/2)); out.append(x[:c].strip()); x=x[c:].strip()
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

MOTION=int(os.environ.get("MOTION","1"))
if MOTION>=2:
    import cv2
    A=W/H
    def ease_(u): u=min(1.0,max(0.0,u)); return u*u*(3-2*u)          # smoothstep ease in/out
    def load_scene(src,fo=None):
        im=Image.open(f"{IMG}/{src}.jpg").convert("RGB"); w0,h0=im.size; mx,my=int(w0*0.045),int(h0*0.045)
        a=np.asarray(im.crop((mx,my,w0-mx,h0-my)))
        if a.shape[0]>2400: f=2400/a.shape[0]; a=cv2.resize(a,(int(a.shape[1]*f),2400),interpolation=cv2.INTER_AREA)
        g=cv2.cvtColor(a,cv2.COLOR_RGB2GRAY).astype(np.float32); g=cv2.GaussianBlur(g,(0,0),3)
        gx=cv2.Sobel(g,cv2.CV_32F,1,0); gy=cv2.Sobel(g,cv2.CV_32F,0,1); e=cv2.GaussianBlur(np.hypot(gx,gy),(0,0),max(a.shape)/25)
        hh,ww=e.shape; e=e**2; ys,xs=np.mgrid[0:hh,0:ww]; tot=e.sum()+1e-6
        fx,fy=float((e*xs).sum()/tot),float((e*ys).sum()/tot)
        if fo: fx,fy=fo[0]*a.shape[1],fo[1]*a.shape[0]
        return {"a":a,"fx":fx,"fy":fy}
    def window(sc,k,u):
        a=sc["a"]; h,w=a.shape[:2]; hc=min(h,w/A); e=ease_(u)
        z0,z1=(1.0,1.10) if k%2==0 else (1.10,1.0); z=z0+(z1-z0)*e; hw=hc/z; ww=hw*A
        fr_x=max(0.0,w-hc*A); fr_y=max(0.0,h-hc)           # free travel at z=1
        fx=min(max(sc["fx"],ww/2),w-ww/2); fy=min(max(sc["fy"],hw/2),h-hw/2)
        ox,oy=-0.35*fr_x*(1 if fx>w/2 else -1)*-1, -0.35*fr_y*(1 if fy>h/2 else -1)*-1
        # start away from the focus point, end on it (push-in) or the reverse (pull-out)
        sx,sy=fx+(-0.35*fr_x if fx>w/2 else 0.35*fr_x), fy+(-0.35*fr_y if fy>h/2 else 0.35*fr_y)
        t0,t1=((sx,sy),(fx,fy)) if k%2==0 else ((fx,fy),(sx,sy))
        cx=t0[0]+(t1[0]-t0[0])*e; cy=t0[1]+(t1[1]-t0[1])*e
        cx=min(max(cx,ww/2),w-ww/2); cy=min(max(cy,hw/2),h-hw/2)
        return cx-ww/2,cy-hw/2,hw
    def frame_of(sc,k,u):
        x0,y0,hw=window(sc,k,u); s_=H/hw
        M=np.float32([[s_,0,-x0*s_],[0,s_,-y0*s_]])
        return cv2.warpAffine(sc["a"],M,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
    class VScene:
        """own video clip (720x1280 proxy, already rotated): plays in REAL TIME from a start offset, no loop, no freeze, no zoom"""
        def __init__(s_,spec):
            name,_,off=spec[2:].partition("@"); s_.cap=cv2.VideoCapture(f"{OWN}/{name}.mp4"); s_.fps=s_.cap.get(cv2.CAP_PROP_FPS) or 30.0
            s_.n=int(s_.cap.get(cv2.CAP_PROP_FRAME_COUNT)); s_.off=float(off or 0); s_.last=None; s_.name=name
            s_.cap.set(cv2.CAP_PROP_POS_FRAMES,int(s_.off*s_.fps)); s_.i=int(s_.off*s_.fps)-1
        def get(s_,u):
            want_=int((s_.off+max(0.0,u))*s_.fps)
            if want_>=s_.n: raise SystemExit(f"own clip {s_.name} too short: needs frame {want_} of {s_.n} (choose another clip/offset)")
            while s_.i<want_:
                ok,fr=s_.cap.read(); s_.i+=1
                if not ok: raise SystemExit(f"own clip {s_.name} read failed at {s_.i}")
                s_.last=fr
            fr=cv2.cvtColor(s_.last,cv2.COLOR_BGR2RGB); h_,w_=fr.shape[:2]
            if (w_,h_)!=(W,H): fr=cv2.resize(fr,(W,H),interpolation=cv2.INTER_CUBIC)
            return fr
    def render_motion(imgs,bounds,total,endpng,out,D=0.5):
        scs=[VScene(x) if x.startswith('V:') else load_scene(x,FOCUS.get(x)) for x in imgs]; endim=np.asarray(Image.open(endpng).convert("RGB").resize((W,H)))
        n=len(imgs); B=[0.0]+bounds+[bounds_end[0]]            # scene k covers B[k]..B[k+1]; end card after narration
        NF=int(round(total*FPS))
        pr=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-an","-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p",out],stdin=subprocess.PIPE)
        def scene_frame(k,t):
            if k==n: return endim
            t0=B[k]-D/2 if k>0 else 0.0; t1=B[k+1]+D/2
            if isinstance(scs[k],VScene): return scs[k].get(t-t0)
            return frame_of(scs[k],k,(t-t0)/(t1-t0))
        for f in range(NF):
            t=f/FPS; k=0
            while k<n and t>=B[k+1]+D/2: k+=1
            fr=scene_frame(k,t)
            if k<n and t>=B[k+1]-D/2:       # dissolve into the next scene (both keep moving)
                al=ease_((t-(B[k+1]-D/2))/D); fr=cv2.addWeighted(fr,1-al,scene_frame(k+1,t),al,0)
            elif k>0 and t<B[k]+D/2 and False: pass
            pr.stdin.write(np.ascontiguousarray(fr).tobytes())
        pr.stdin.close(); pr.wait()
        if pr.returncode: raise SystemExit("motion render failed")
bounds_end=[0.0]
FOCUS={}
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
FOCUS.update(SPEC.get("focus",{}))
def anchor_time(segids,segst_,phrase):
    """start time of a phrase (case-insensitive, within one segment's text; spread over the segment's audio by character position)"""
    for sid,st_ in zip(segids,segst_):
        txt=SEGS[sid]; i=txt.lower().find(phrase.lower())
        if i>=0:
            d_=dur(f"{NARR}/{sid}.m4a"); return st_+d_*i/max(1,len(txt))
    print("WARN anchor not found:",phrase); return None
for n,it in enumerate(SPEC["items"]):
    if want and it["id"] not in want: continue
    story=it["kind"]=="story"; GAP=0.25; tmp=f"{OUT}/_{it['id']}"; os.makedirs(tmp,exist_ok=True)
    voice=[]; mask=[]; caps=[]; t=0.5; segst=[]
    lead=np.zeros(int(0.5*SR),np.float32); voice.append(lead); mask.append(np.zeros(len(lead),bool))
    for s in it["segs"]:
        p=f"{NARR}/{s}.m4a"; d=dur(p)
        raw=subprocess.run(["ffmpeg","-v","error","-i",p,"-f","f32le","-ac","1","-ar",str(SR),"-"],capture_output=True).stdout; a=np.frombuffer(raw,np.float32)
        segst.append(t); tot=d+GAP; arr=np.zeros(int(tot*SR),np.float32); arr[:len(a)]=a[:len(arr)]; m=np.zeros(len(arr),bool); m[:len(a)]=True; voice.append(arr); mask.append(m)
        ss=chunk(sents(SEGS[s])); L=sum(len(x) for x in ss); tt=t
        for x in ss:
            dd=d*len(x)/L; caps.append((tt,tt+dd,x)); tt+=dd
        t+=tot
    narr_len=t; ECARD=2.5 if story else 3.0; total=narr_len+ECARD
    V=np.concatenate(voice); V=np.concatenate([V,np.zeros(int(total*SR)-len(V),np.float32)]); M=np.concatenate(mask+[np.zeros(len(V)-sum(len(x) for x in mask),bool)])
    # shots
    imgs=it["imgs"]; ec=f"{tmp}/end.png"; end_card(ec,it["end1"],it["end2"],story)
    if MOTION>=2:
        n_=len(imgs); b=[]; prev=0.0; starts=[c[0] for c in caps]
        for k in range(1,n_):
            tgt=k*narr_len/n_; sl=narr_len/n_
            def pick_from(L,tol):
                ok=[c for c in L if c-prev>=2.6 and narr_len-c>=2.6 and abs(c-tgt)<=tol*sl]; return min(ok,key=lambda c:abs(c-tgt)) if ok else None
            ph_=(it.get("at") or [None]*n_)[k-1] if it.get("at") else None
            if ph_:
                tt_=anchor_time(it["segs"],segst,ph_)
                if tt_ is not None and tt_-prev>=2.2 and narr_len-tt_>=2.2: b.append(tt_); prev=tt_; continue
            pk=pick_from(segst,0.45)
            if pk is None: pk=pick_from(starts,0.35)
            if pk is None: pk=tgt
            b.append(pk); prev=pk
        bounds_end[0]=narr_len; vo=f"{tmp}/v.mp4"; render_motion(imgs,b,total,ec,vo)
    else:
        per=(narr_len)/len(imgs); clips=[]
        for k,src in enumerate(imgs):
            o=f"{tmp}/s{k}.mp4"; shot(src,per,o,k); clips.append(o)
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
            w_=font.getbbox(l)[2]; x_=(Wc-w_)//2; y_=pad+i*(lh+line_gap)
            for j_,wd in enumerate(l.split(" ")):
                core=re.sub(r"[^A-Za-z0-9'-]","",wd); first=(j_==0 and i==0)
                gold=bool(re.search(r"\d",wd)) or core.lower().split("-")[0] in NUMW or (core[:1].isupper() and not first and core.lower() not in STOPCAP)
                d.text((x_,y_),wd,font=font,fill=(255,205,70,255) if gold else (255,255,255,255),stroke_width=stroke,stroke_fill=(0,0,0,255)); x_+=font.getlength(wd+" ")
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
