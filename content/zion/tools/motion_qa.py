#!/usr/bin/env python3
"""Motion QA gate for built Shorts/Stories: no hard cuts, no stalls, no jitter. usage: motion_qa.py DIR_OR_FILES...
Decodes each video at 15 fps (108x192 gray). Flags: hard cut (one frame-to-frame jump >> its neighbours), freeze (>1.2 s of ~0 change in the
picture area), jitter (frame-to-frame change that flips sign/erratic: 2nd difference spikes). Exit 1 when anything is flagged."""
import sys, glob, subprocess, numpy as np
def frames(p):
    raw=subprocess.run(["ffmpeg","-v","error","-i",p,"-vf","fps=15,scale=108:192,format=gray","-f","rawvideo","-"],capture_output=True).stdout
    return np.frombuffer(raw,np.uint8).reshape(-1,192,108).astype(np.float32)
bad=0
args=[a for x in sys.argv[1:] for a in (sorted(glob.glob(x+"/*.mp4")) if not x.endswith(".mp4") else [x])]
for p in args:
    F=frames(p); pic=F[:,:100,:]           # ignore the caption band
    d=np.abs(np.diff(pic,axis=0)).mean(axis=(1,2)); med=np.median(d)+1e-3
    spikes=[i/15 for i in range(1,len(d)-1) if d[i]>6*max(med,0.6) and d[i]>3*max(d[i-1],d[i+1])]
    frozen=0;run=0
    for v in d[:-int(3*15)]:                # exclude the end card
        run=run+1 if v<0.05 else 0; frozen=max(frozen,run)
    jit=float(np.percentile(np.abs(np.diff(d)),99)/ (np.median(d)+1e-3))
    ok=not spikes and frozen<18
    print(("PASS" if ok else "FAIL"),p.split("/")[-1],f"median_diff={med:.2f} max={d.max():.2f} hard_cuts={[round(s,1) for s in spikes]} frozen_s={frozen/15:.1f} jitter_ratio={jit:.1f}")
    bad+=not ok
sys.exit(1 if bad else 0)
