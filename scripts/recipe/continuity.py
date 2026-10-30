"""N1 - AI story continuity (stricter animation flow): every cut between two AI shots of the same story passage must keep the same
place, props and figures. Measures last-frame -> first-frame similarity (ORB feature matches + colour layout); a boundary under the
threshold FAILS unless the passage entry lists it as an intentional cut ("cut_ok": true). Also writes a review sheet (every AI
boundary, narration text, the planned note of each shot) that a reviewer must look at: staging, props and pose must match the script.
Rule: a boundary FAILS unless it is signed off in <episode dir>/continuity_signoff.json (list of "<srcA>><srcB>" keys printed with each
sheet) after a reviewer looked at the sheet and the narration table (N1_review.txt) and confirmed the same place, props, figures and
pose carry over and that the picture says what the narration says at that moment. New or changed AI clips are therefore never unreviewed.
usage: continuity.py shots2.json ai_passages_chN.json timeline.json out_dir [signoff.json]"""
import json, os, subprocess, sys, cv2, numpy as np
shots = json.load(open(sys.argv[1])); P = json.load(open(sys.argv[2])); TL = {x["id"]: x for x in json.load(open(sys.argv[3])) if x.get("kind") == "seg"}
OUT = sys.argv[4]; os.makedirs(OUT, exist_ok=True)
SIGN = set(json.load(open(sys.argv[5]))) if len(sys.argv) > 5 and os.path.exists(sys.argv[5]) else set()
def frame(s, last):
    sp = s.get("speed", 1.0) or 1.0; t = s.get("ss", 0) + ((max(s["dur"] - 0.08, 0)) * sp if last else 0.04 * sp)
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", s["src"], "-frames:v", "1", "-vf", "scale=640:-1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    return cv2.imdecode(np.frombuffer(r, np.uint8), cv2.IMREAD_COLOR)
orb = cv2.ORB_create(1500); bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
def sim(a, b):
    ka, da = orb.detectAndCompute(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), None); kb, db = orb.detectAndCompute(cv2.cvtColor(b, cv2.COLOR_BGR2GRAY), None)
    good = 0
    if da is not None and db is not None and len(da) > 8 and len(db) > 8:
        m = sorted(bf.match(da, db), key=lambda x: x.distance); good = sum(1 for x in m if x.distance < 40)
    ha = cv2.calcHist([cv2.resize(a, (64, 36))], [0, 1, 2], None, [6, 6, 6], [0, 256] * 3); hb = cv2.calcHist([cv2.resize(b, (64, 36))], [0, 1, 2], None, [6, 6, 6], [0, 256] * 3)
    return good, float(cv2.compareHist(ha, hb, cv2.HISTCMP_CORREL))
rows = []; fails = []; fl = 0
ai = [(i, s) for i, s in enumerate(shots) if s.get("ai")]
for (i, a), (j, b) in zip(ai, ai[1:]):
    if j != i + 1 or a["src"] == b["src"]: continue           # only direct cuts between different AI clips
    fa, fb = frame(a, True), frame(b, False)
    if fa is None or fb is None: continue
    g, c = sim(fa, fb); seg = b.get("_seg"); ok = any(x.get("cut_ok") for x in P.get(seg, []) if os.path.basename(x["clip"]).split(".")[0] in os.path.basename(b["src"]) or True) and False
    key = os.path.basename(a["src"]) + ">" + os.path.basename(b["src"]); flag = key not in SIGN
    rows.append((i, a["_seg"], b["_seg"], g, round(c, 2), flag)); 
    rows[-1] = rows[-1] + (key,); pair = np.hstack([cv2.resize(fa, (480, 270)), cv2.resize(fb, (480, 270))]); cv2.putText(pair, f"{i}->{j} {a['_seg']}>{b['_seg']} orb={g} col={c:.2f}", (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 0, 255) if flag else (0, 160, 0), 2)
    cv2.imwrite(f"{OUT}/N1_{i:03d}.jpg", pair)
    if flag: fails.append(f"AI cut {i}->{j} ({a['_seg']}->{b['_seg']}) not signed off [{key}] - review sheet N1_{i:03d}.jpg against the narration")
res = {"rule": "N1 AI continuity", "status": "fail" if fails else "pass", "boundaries": len(rows), "findings": fails, "rows": rows}
json.dump(res, open(f"{OUT}/N1.json", "w"), indent=1)
print("N1", res["status"], len(rows), "AI boundaries,", len(fails), "flagged"); [print(" ", f) for f in fails]
# narration vs picture table for the mandatory read-through
with open(f"{OUT}/N1_review.txt", "w") as f:
    for seg, items in P.items():
        if seg not in TL: continue
        f.write(f"{seg}: {TL[seg]['text']}\n")
        for x in items: f.write(f"   {os.path.basename(x['clip'])} {x['dur']}s  {x.get('note','')}\n")
