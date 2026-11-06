#!/usr/bin/env python3
"""V45 gate against the COMMITTED reference fingerprints (content/qa/frame_hashes.npz: every posted/queued Short, Reel, Story) so the posted files need not be on disk.
usage: hash_gate.py <candidate.mp4 ...>   -> compares each candidate with every reference of a different name; exit 1 on a repeat (>5 % shared frames or cover repeat)."""
import sys, os, glob, subprocess, tempfile, numpy as np
from PIL import Image
Z = np.load(os.path.join(os.path.dirname(__file__), "../../content/qa/frame_hashes.npz"))
REF = {k[:-3]: np.unpackbits(Z[k], axis=1)[:, :256].astype(bool) for k in Z.files if k.endswith("__h")}
def hashes(f):
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-vf", "fps=2,scale=72:128", f"{d}/%03d.png"], check=True)
        out = [(lambda g: (g[:, 1:] > g[:, :-1]).flatten())(np.asarray(Image.open(p).convert("L").resize((17, 16)), dtype=np.int16)) for p in sorted(glob.glob(d + "/*.png"))]
    return np.array(out)
bad = 0
for f in sys.argv[1:]:
    n = os.path.basename(f)[:-4].replace("_ig", "").replace("_v2", ""); H = hashes(f); A = (H[:-7] if len(H) > 14 else H).astype(bool)
    for k, h in REF.items():
        if k == n: continue
        B = h[:-7] if len(h) > 14 else h
        s = float(((A[:, None, :] != B[None, :, :]).sum(2).min(1) <= 16).mean()); cv = bool(((A[:1, None, :] != B[None, :6, :]).sum(2).min() <= 16))
        if s > 0.05 or cv: bad += 1; print(f"REPEAT {n} vs {k}: {s:.0%}{' COVER' if cv else ''}")
print("HASH GATE", "FAIL" if bad else "PASS", f"({len(REF)} references)"); sys.exit(1 if bad else 0)
