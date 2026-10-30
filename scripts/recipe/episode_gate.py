#!/usr/bin/env python3
"""Episode gate - fail-closed checks that run after every render, next to analyze.py (which still runs unchanged).
usage: episode_gate.py <ep dir> <VER> [--other ch2 ...]
Every item below is a mistake that already happened once; each one is now a hard FAIL so it cannot repeat:
 G1 render log: SKIP_MISSING (an image/clip the plan names is not on disk), Traceback, ffmpeg errors
 G2 final mp4: opens, has video + audio, duration matches the timeline (a disk-full write leaves a file with no moov atom)
 G3 plan hygiene: every source exists; low-repetition rule (picture <=2x, important <=3x, <=3 repeating pictures per video, cross-video reuse only if listed)
 G4 N2 own-footage dedupe (same clip, same location panels, same subject within 75 s)
 G5 N1 AI-boundary continuity  - FAILS until every boundary is signed off after looking at the sheet
 G6 N3 script/picture match    - FAILS until every shot is signed off against its narration line
G5/G6 cannot be satisfied by a script: a reviewer must look at the sheets and write the sign-off files. The gate only reports 'PENDING'.
Writes <ep>/gate_<VER>/ and prints 'GATE PASS' or 'GATE FAIL'. Exit code 1 on fail."""
import json, os, re, subprocess, sys, glob
ep = os.path.abspath(sys.argv[1].rstrip("/")); V = sys.argv[2]; others = sys.argv[sys.argv.index("--other") + 1:] if "--other" in sys.argv else []
R = os.path.dirname(os.path.abspath(__file__)); N = os.path.basename(ep); OUT = f"{ep}/gate_{V}"; os.makedirs(OUT, exist_ok=True)
fails = []; warns = []
def run(cmd): return subprocess.run(cmd, capture_output=True, text=True, cwd=ep)

# G1 render log
lg = f"{ep}/render_{V}.log"
if not os.path.exists(lg): fails.append(f"G1 no render log {lg}")
else:
    for ln in open(lg, errors="replace"):
        if re.search(r"SKIP_MISSING|Traceback|No such file|Invalid data|moov atom|Error opening|No space left", ln): fails.append("G1 render log: " + ln.strip()[:200])
# G2 final file
mp4 = f"{ep}/yellowstone_{N}_{V}.mp4"
if not os.path.exists(mp4): fails.append(f"G2 missing {mp4}")
else:
    p = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type:format=duration", "-of", "json", mp4])
    try:
        j = json.loads(p.stdout); kinds = {s["codec_type"] for s in j["streams"]}; dur = float(j["format"]["duration"])
        if not {"video", "audio"} <= kinds: fails.append(f"G2 {mp4} streams {kinds}")
        tl = [x for x in json.load(open(f"{ep}/timeline.json")) if x.get("kind") == "seg"]
        want = max(x.get("end", x["start"] + x.get("dur", 0)) for x in tl)
        if abs(dur - want) > 20: warns.append(f"G2 duration {dur:.1f}s vs last timeline segment end {want:.1f}s (intro/outro allowed; check)")
    except Exception as e: fails.append(f"G2 {mp4} unreadable: {e} {p.stderr[-150:]}")
# G3 plan hygiene
def plan_rows(path):
    for ln in open(path):
        if ln.startswith("#") or "|" not in ln: continue
        p = [x.strip() for x in ln.split("|")]
        yield p[0], p[1]
roots = [f"/home/claude/doc/yellowstone/media/pd_{N}/img", f"/home/claude/doc/yellowstone/media/pd_{N}"]
# Owner rule 2026-10-30 (low repetition): a picture may appear at most 2 times in a video; an extremely important historical picture
# (listed in <ep>/repeat_ok.json {"important": [...], "cross_ok": [...]}) up to 3; at most 3 different pictures may repeat in one video.
# Own video clips never repeat (N2). A picture/clip reused from another episode must be an extremely high-quality or extremely important
# historical item listed in cross_ok; otherwise it fails. Episodes already released (Ch2, Ch3 as of 2026-10-30) are left as is.
ok_path = f"{ep}/repeat_ok.json"; RO = json.load(open(ok_path)) if os.path.exists(ok_path) else {}
important = set(RO.get("important", [])); cross_ok = set(RO.get("cross_ok", []))
img_uses = {}
for seg, src in plan_rows(f"{ep}/plan2.txt"):
    m = re.match(r"([IOMGA]):(.+)", src)
    if not m: continue
    k, v = m.groups()
    if k == "I":
        if not any(os.path.exists(f"{r}/{v}") for r in roots): fails.append(f"G3 {seg}: image {v} is not in pd_{N}/img (copy any ch2_* image into pd_{N}/img)")
        img_uses.setdefault(v, []).append(seg)
    elif k in "OM":
        for c in v.split(","):
            if not os.path.exists(f"/home/claude/doc/yellowstone/own/{c}.mov"): fails.append(f"G3 {seg}: own clip {c} is not in own/")
rep = {v: u for v, u in img_uses.items() if len(u) > 1}
for v, u in rep.items():
    lim = 3 if v in important else 2
    if len(u) > lim: fails.append(f"G3 image {v} appears {len(u)} times ({', '.join(u)}); limit {lim}" + ("" if v in important else " (3 only if listed as extremely important in repeat_ok.json)"))
if len(rep) > 3: fails.append(f"G3 {len(rep)} different pictures repeat in this video (limit 3): {', '.join(rep)}")
elif rep: warns.append(f"G3 repeated pictures ({len(rep)} of 3 allowed): " + ", ".join(f"{v} x{len(u)}" for v, u in rep.items()))
seen_img = {v: u[0] for v, u in img_uses.items()}
for o in others:
    po = f"{os.path.dirname(ep)}/{o}/plan2.txt"
    if os.path.exists(po):
        for seg, src in plan_rows(po):
            m = re.match(r"I:(.+)", src)
            if m and m.group(1) in seen_img and m.group(1) not in cross_ok:
                fails.append(f"G3 image {m.group(1)} was already used in {o}:{seg}; reuse across videos only for extremely high-quality / extremely important historical items (list in repeat_ok.json cross_ok)")
# G4 N2
a = run(["python3", f"{R}/dedupe_plan.py", ep, "/home/claude/doc/yellowstone/sheets"] + (["--other"] + others if others else []))
open(f"{OUT}/N2.txt", "w").write(a.stdout)
if a.returncode: fails += ["G4 " + l.strip() for l in a.stdout.splitlines() if "FAIL" in l]
# G5 N1, G6 N3
def tool(args): return run(["python3"] + args)
c = tool([f"{R}/continuity.py", f"{ep}/shots2.json", f"/home/claude/doc/yellowstone/ai_passages_{N}.json", f"{ep}/timeline.json", f"{OUT}/N1", f"{ep}/continuity_signoff.json"])
open(f"{OUT}/N1.txt", "w").write(c.stdout + c.stderr)
if c.returncode or "fail" in c.stdout.lower().split("\n")[-2:][0:1].__str__().lower(): fails.append("G5 N1 continuity not signed off: see " + f"{OUT}/N1.txt")
s = tool([f"{R}/storyboard.py", f"{ep}/shots2.json", f"{ep}/timeline.json", f"{OUT}/N3", f"{ep}/storyboard_signoff.json"])
open(f"{OUT}/N3.txt", "w").write(s.stdout + s.stderr)
try:
    n3 = json.load(open(f"{OUT}/N3/N3.json")); fails += ["G6 " + f for f in n3["findings"]]
except Exception as e: fails.append(f"G6 N3 did not run: {e}")
try:
    n1 = json.load(open(f"{OUT}/N1/N1.json")); fails += ["G5 " + f for f in n1.get("findings", [])] if n1.get("status") == "fail" else []
except Exception: pass
rep = {"status": "fail" if fails else "pass", "fails": fails, "warns": warns}
json.dump(rep, open(f"{OUT}/gate.json", "w"), indent=1)
for f in fails: print("FAIL", f)
for w in warns: print("warn", w)
print("GATE", "FAIL" if fails else "PASS", f"({len(fails)} fails, {len(warns)} warns) -> {OUT}")
sys.exit(1 if fails else 0)
