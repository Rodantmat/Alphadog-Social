"""N2 - no repeated own footage. usage: dedupe_plan.py <episode dir> <sheets dir> [--other chX ...]
FAIL: (a) the same own clip used twice in an episode (any panel, any time range); (b) two panels of one side-by-side shot from the same
source folder/location; (c) two own shots from the same source folder within 75 s of each other (reads as the same footage twice).
WARN: a clip already used in another episode of the series (prefer fresh footage)."""
import json, os, re, sys, glob, collections
ep = sys.argv[1].rstrip("/"); SH = sys.argv[2]; others = sys.argv[sys.argv.index("--other") + 1:] if "--other" in sys.argv else []
folder = {}; top = {}
for f in glob.glob(f"{SH}/*.json"):
    try: d = json.load(open(f))
    except Exception: continue
    if isinstance(d, list):
        for c in d:
            if isinstance(c, dict) and "id" in c: folder[c["id"]] = os.path.basename(f)[:-5]; top[c["id"]] = (c.get("labels") or [["", ""]])[0][1]
def parse(plan):
    rows = []
    for ln in open(plan):
        if ln.startswith("#") or "|" not in ln: continue
        p = [x.strip() for x in ln.split("|")]; m = re.match(r"([OM]):([0-9a-f,]+)", p[1])
        if m: rows.append((p[0], m.group(1), m.group(2).split(",")))
    return rows
rows = parse(f"{ep}/plan2.txt"); seg_t = {}
try:
    for x in json.load(open(f"{ep}/timeline.json")):
        if x.get("kind") == "seg": seg_t[x["id"]] = x["start"]
except Exception: pass
fails = []; warns = []; seen = {}
for seg, k, ids in rows:
    if k == "M" and len({folder.get(i, i) for i in ids}) < len(ids): fails.append(f"{seg}: panels {ids} come from the same location ({[folder.get(i) for i in ids]}) - side-by-side panels must be clearly different places")
    for i in ids:
        if i in seen: fails.append(f"{seg}: own clip {i} ({folder.get(i)}) already used in {seen[i]} of this episode")
        seen[i] = seg
last = {}
for seg, k, ids in sorted(rows, key=lambda r: seg_t.get(r[0], 0)):
    t = seg_t.get(seg, 0)
    for i in ids:
        fo = (folder.get(i), top.get(i))
        if fo in last and t - last[fo][0] < 75 and last[fo][1] != seg + i and last[fo][2] != seg: fails.append(f"{seg}: own clip {i} from {fo} only {t - last[fo][0]:.0f}s after {last[fo][2]} (same subject at the same location again)")
        last[fo] = (t, seg + i, seg)
for o in others:
    for seg, k, ids in parse(f"{os.path.dirname(os.path.abspath(ep))}/{o}/plan2.txt"):
        for i in ids:
            if i in seen: warns.append(f"clip {i} also used in {o}:{seg}")
st = "fail" if fails else "pass"
print("N2", st, len(seen), "own clips,", len(fails), "problems,", len(warns), "cross-episode reuses"); [print(" FAIL", f) for f in fails]; [print(" warn", w) for w in warns]
sys.exit(1 if fails else 0)
