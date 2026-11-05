#!/usr/bin/env python3
"""Rule V45 gate: every Short/Reel/Story must look completely different from every other one (posted, queued, or in the same batch).
usage: reels_distinct_gate.py <candidate files/dirs...> [--against <files/dirs...>] [--max 0.05]
Samples 2 frames/s (the shared end card, last 3.5 s, is ignored), 17x16 dHash; a frame 'repeats' when a frame of another video is within Hamming 16/256. A video FAILS if more than
--max (default 5 %) of its frames repeat in any single other video, or if its cover (first 0.5 s) repeats any other video's cover/first 3 s.
Candidates are also compared with each other. Exit 1 on any failure."""
import glob, itertools, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image
a = sys.argv[1:]; mx = 0.05
if "--max" in a: i = a.index("--max"); mx = float(a[i + 1]); a = a[:i] + a[i + 2:]
cand_a, ref_a = (a[:a.index("--against")], a[a.index("--against") + 1:]) if "--against" in a else (a, [])
def expand(xs): return sorted({f for x in xs for f in (glob.glob(os.path.join(x, "*.mp4")) if os.path.isdir(x) else [x])})
def hashes(f):
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-vf", "fps=2,scale=72:128", f"{d}/%03d.png"], check=True)
        out = []
        for p in sorted(glob.glob(d + "/*.png")):
            g = np.asarray(Image.open(p).convert("L").resize((17, 16)), dtype=np.int16); out.append((g[:, 1:] > g[:, :-1]).flatten())
    return np.array(out[:-7] if len(out) > 14 else out)   # the shared CTA end card (last ~3.5 s) is by design identical
C = expand(cand_a); R = [f for f in expand(ref_a) if f not in C]
H = {f: hashes(f) for f in C + R}; bad = set()
def share(x, y): return float(((H[x][:, None, :] != H[y][None, :, :]).sum(2).min(1) <= 16).mean())
for c in C:
    for o in (C + R):
        if o == c: continue
        s = share(c, o); cv = bool(((H[c][:1, None, :] != H[o][None, :6, :]).sum(2).min() <= 16))
        if s > mx or cv:
            bad.add(c); print(f"REPEAT {os.path.basename(c)} vs {os.path.basename(o)}: {s:.0%} of frames{'; COVER repeats' if cv else ''}")
print(f"DISTINCT GATE {'FAIL' if bad else 'PASS'}: {len(C)} candidates vs {len(C) + len(R) - 1} others, {len(bad)} failing"); sys.exit(1 if bad else 0)
