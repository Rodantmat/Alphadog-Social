"""Q-FREEZE audit of prepared clips: lists prep/<key>.mp4 with a frozen run >= 0.4 s inside the window a shot uses.
usage: freeze_scan.py EPDIR [--drop]  (--drop removes them from prep/index.json so prep2 redoes them with the freeze-aware window)"""
import json, os, re, subprocess, sys
D = os.path.abspath(sys.argv[1]); P = json.load(open(f"{D}/prep/index.json")); sh = json.load(open(f"{D}/shots2.json")) if os.path.exists(f"{D}/shots2.json") else []
R = json.load(open(f"{D}/requests.json")); bad = []
for q in R:
    k = q["key"]; f = f"{D}/prep/{k}.mp4"
    if not os.path.exists(f) or q["kind"] == "ai": continue     # AI clips handled in build2 (near-static -> push-in)
    out = subprocess.run(["ffmpeg", "-nostats", "-i", f, "-vf", "scale=320:-2,freezedetect=n=0.002:d=0.4", "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"freeze_start: ([0-9.]+)", out)]; du = [float(x) for x in re.findall(r"freeze_duration: ([0-9.]+)", out)]
    use = min(q["need"] - 1.5, P.get(k, {}).get("len", 99))        # seconds the shot actually plays
    hits = [(s, d) for s, d in zip(st, du) if s < use]
    if hits: bad.append(k); print(k, q["kind"], os.path.basename(q["src"]), "frozen", hits)
if "--drop" in sys.argv and bad:
    for k in bad: P.pop(k, None)
    json.dump(P, open(f"{D}/prep/index.json", "w"), indent=1); print("dropped", len(bad))
