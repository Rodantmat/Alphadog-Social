"""N3 - script / picture match review. Builds one sheet per group of narration lines: the exact narration text and one frame for every shot
shown during it (photo, own clip, AI clip, graphic), with the label the viewer sees. A reviewer must read each narration line and confirm that
what is on screen shows what is being SAID at that moment (the object, person, place and event named - not just the topic).
Every shot needs a sign-off; any shot not signed off fails the episode, and any shot on the 'reject' list fails it outright.
usage: storyboard.py shots2.json timeline.json out_dir [signoff.json]  -> out_dir/SB_<n>.jpg, N3.json, SB_pending.txt"""
import json, os, subprocess, sys, cv2, numpy as np, textwrap
shots = json.load(open(sys.argv[1])); TL = {x["id"]: x for x in json.load(open(sys.argv[2])) if x.get("kind") == "seg"}
OUT = sys.argv[3]; os.makedirs(OUT, exist_ok=True)
SIGN = json.load(open(sys.argv[4])) if len(sys.argv) > 4 and os.path.exists(sys.argv[4]) else {"ok": [], "reject": []}
ok = set(SIGN.get("ok", [])); rej = set(SIGN.get("reject", []))
def thumb(s):
    src = s.get("src") or (s.get("srcs") or [{}])[0].get("src")
    if not src or not os.path.exists(src): return np.zeros((135, 240, 3), np.uint8), "missing"
    if src.lower().endswith((".jpg", ".jpeg", ".png")): im = cv2.imread(src)
    else:
        sp = s.get("speed", 1.0) or 1.0; t = (s.get("ss") or 0) + s["dur"] * sp * 0.5
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        im = cv2.imdecode(np.frombuffer(r, np.uint8), cv2.IMREAD_COLOR)
    if im is None: return np.zeros((135, 240, 3), np.uint8), "unreadable"
    h, w = im.shape[:2]; k = 240 / w; return cv2.resize(im, (240, max(1, int(h * k)))), os.path.basename(src)
def key(s): return f"{s.get('_seg')}:{os.path.basename(str(s.get('src') or [x.get('src') for x in s.get('srcs', [])]))}:{round(s.get('ss') or 0, 1)}"
groups = {}
for i, s in enumerate(shots): groups.setdefault(s.get("_seg"), []).append((i, s))
fails = []; pend = []; sheets = []; cur = []; t0 = 0.0; clock = {}
for i, s in enumerate(shots): clock.setdefault(s.get("_seg"), t0); t0 += s["dur"]
for seg, items in groups.items():
    if seg not in TL: continue
    tiles = []
    for i, s in items:
        im, name = thumb(s); k = key(s); st = "REJECT" if k in rej else ("ok" if k in ok else "PENDING")
        if st == "REJECT": fails.append(f"shot {i} ({seg}) rejected: does not match the narration [{k}]")
        elif st == "PENDING": pend.append(k); fails.append(f"shot {i} ({seg}) not reviewed against the narration [{k}]")
        tile = np.zeros((im.shape[0] + 44, 240, 3), np.uint8); tile[:im.shape[0]] = im
        cv2.putText(tile, f"#{i} {s['dur']:.1f}s {st}", (3, im.shape[0] + 16), cv2.FONT_HERSHEY_SIMPLEX, .45, (0, 0, 255) if st != "ok" else (0, 170, 0), 1)
        cv2.putText(tile, (s.get("label") or name)[:38], (3, im.shape[0] + 36), cv2.FONT_HERSHEY_SIMPLEX, .38, (230, 230, 230), 1); tiles.append(tile)
    H = max(t.shape[0] for t in tiles); row = np.hstack([np.pad(t, ((0, H - t.shape[0]), (0, 0), (0, 0))) for t in tiles[:7]])
    W = max(row.shape[1], 1200); head = np.zeros((70, W, 3), np.uint8)
    for n, ln in enumerate(textwrap.wrap(f"{seg} @{clock[seg]:.0f}s  {TL[seg]['text']}", 150)[:3]): cv2.putText(head, ln, (6, 18 + 20 * n), cv2.FONT_HERSHEY_SIMPLEX, .5, (255, 255, 255), 1)
    cur.append(np.vstack([head, np.pad(row, ((0, 0), (0, W - row.shape[1]), (0, 0)))]))
    if len(cur) == 4: sheets.append(np.vstack(cur)); cur = []
if cur: sheets.append(np.vstack(cur))
for n, sh in enumerate(sheets): cv2.imwrite(f"{OUT}/SB_{n:02d}.jpg", sh, [cv2.IMWRITE_JPEG_QUALITY, 80])
open(f"{OUT}/SB_pending.txt", "w").write("\n".join(pend))
json.dump({"rule": "N3 script/picture match", "status": "fail" if fails else "pass", "findings": fails, "sheets": len(sheets)}, open(f"{OUT}/N3.json", "w"), indent=1)
print("N3", "fail" if fails else "pass", len(sheets), "sheets,", len(pend), "pending,", len(rej & {key(s) for s in shots}), "rejected")
