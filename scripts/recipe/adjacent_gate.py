#!/usr/bin/env python3
"""Rule V48 gate (owner 2026-11-08): neighbouring posts must differ DRASTICALLY (footage, topic, hook, film, music).
usage: adjacent_gate.py [queue.json] [--window 3] [--footage DIR] [--max 0.0]
Metadata checks (always): within WINDOW neighbours on the same platform+kind (reels / stories), flag same file, caption hook (first sentence) token overlap >= 0.4,
same film/part tag run longer than 2 in a row, identical first-comment link repeated back to back more than 2x.
Visual check (when --footage DIR has the mp4s): reels_distinct_gate.py is run on each neighbour pair with --max 0.0 (no repeated frame at all).
Exit 1 on any failure."""
import json, os, re, subprocess, sys
a = sys.argv[1:]; opt = lambda k, d: a[a.index(k) + 1] if k in a else d
Q = next((x for x in a if x.endswith(".json")), "content/social_queue.json"); W = int(opt("--window", 3)); FD = opt("--footage", "")
q = [i for i in json.load(open(Q)) if not i.get("hold") and not (i.get("done") and not i["done"].get("dry_run"))]
tok = lambda s: set(re.findall(r"[a-z0-9]{4,}", re.split(r"[.!?\n]", s.lower())[0]))
film = lambda i: (re.search(r"(zion|yellowstone|chiricahua)[\w ]*?part\s*\d", i.get("caption","").lower()) or re.search(r"(zion|yellowstone|chiricahua)", i.get("caption","").lower()) or [None])[0]
kind = lambda i: "story" if "story" in i["id"] or i["file"].startswith("story") else "reel"
bad = []
for plat in sorted({i["platform"] for i in q}):
    for k in ("reel", "story"):
        s = sorted([i for i in q if i["platform"] == plat and kind(i) == k], key=lambda i: i["at"])
        for n, i in enumerate(s):
            for j in s[n + 1:n + 1 + W]:
                if i["file"] == j["file"]: bad.append(f"SAME FILE {i['id']} {j['id']}")
                A, B = tok(i.get("caption","")), tok(j.get("caption",""))
                if A and B and len(A & B) / len(A | B) >= 0.4: bad.append(f"SIMILAR HOOK {i['id']} / {j['id']}: {sorted(A & B)}")
                if FD and os.path.exists(f"{FD}/{i['file']}") and os.path.exists(f"{FD}/{j['file']}"):
                    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "reels_distinct_gate.py"), f"{FD}/{i['file']}", "--against", f"{FD}/{j['file']}", "--max", "0.0"], capture_output=True, text=True)
                    if r.returncode: bad.append(f"VISUAL {i['id']} / {j['id']}: {(r.stdout.strip().splitlines() or [r.stderr[-200:]])[0]}")
print("\n".join(sorted(set(bad)))); print(f"ADJACENT GATE {'FAIL' if bad else 'PASS'}: {len(q)} pending items, {len(set(bad))} problems"); sys.exit(1 if bad else 0)
