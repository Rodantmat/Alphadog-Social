#!/usr/bin/env python3
"""Colour-variety gate (owner correction 2026-11-27: 'overdose of black and white ... diversify'). 
usage: color_mix_qa.py file.mp4 ... ; FAIL if a video has >40% near-grayscale sample frames, or its first frame (the grid cover) is grayscale,
or a batch of >=3 consecutive files has >50% grayscale covers/frames overall."""
import sys, cv2, numpy as np
BW=22; MAXBW=0.40; fail=0; rows=[]
for fn in sys.argv[1:]:
    c=cv2.VideoCapture(fn); fps=c.get(5) or 30; N=int(c.get(7)); sat=[]
    for i in range(0,max(N-int(fps*3),1),int(fps*1.5)):   # skip the end card
        c.set(1,i); ok,f=c.read()
        if not ok: break
        sat.append(cv2.cvtColor(f[200:-300],cv2.COLOR_BGR2HSV)[...,1].mean())
    c.release(); sat=np.array(sat); share=float((sat<BW).mean()); cover=sat[0]>=BW if len(sat) else False
    ok=share<=MAXBW and cover; fail+=not ok; rows.append((share,cover))
    print(f"{fn.split('/')[-1]}: grayscale frames {share:.0%}, cover {'colour' if cover else 'GRAYSCALE'} -> {'ok' if ok else 'FAIL'}")
if len(rows)>=3 and np.mean([r[0] for r in rows])>0.5: fail+=1; print("BATCH too grayscale")
print("COLOUR-MIX QA:", "FAIL" if fail else "PASS"); sys.exit(1 if fail else 0)
