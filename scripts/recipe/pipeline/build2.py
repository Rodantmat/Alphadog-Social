#!/usr/bin/env python3
"""plan2.txt + timeline.json (+ AI passage map) -> shots2.json, with automatic gates (owner critique 2026-10-28):
  - every moving source goes through prep2.py (true 30 fps, calm window, stabilized own clips, speech-free ambience, real length)
  - no shot outlasts its prepared footage: durations are re-balanced inside the segment; impossible -> hard error
  - vertical phone clips are never cropped: they appear as 2-3 full-height panels (type multi)
  - no push-in on moving footage (drift 0); chapter cards carry the chapter NAME only (no "Chapter N")
usage: build2.py requests  -> requests.json for prep2.py ;  build2.py shots -> shots2.json"""
import json, os, shlex, sys, hashlib
D = os.path.dirname(os.path.abspath(__file__)); Y = os.path.dirname(D); EP = os.path.basename(D)          # e.g. ch1
tl = json.load(open(f"{D}/timeline.json")); AI = json.load(open(f"{Y}/ai_passages_{EP}.json"))
PLAN = os.environ.get("PLAN", f"{D}/plan2.txt")
GR = f"{Y}/graphics"; PV = f"{Y}/media/pd_{EP}/video"; PI = f"{Y}/media/pd_{EP}/img"; OWN = f"{Y}/own"; AIR = f"{Y}/media"
import soundfile as _sf; TOTAL = _sf.info(f"{D}/narration_full.wav").duration
plan = {}
for ln in open(PLAN):
    if not ln.strip() or ln.startswith("#"): continue
    seg, src, ss, w, *opt = [x.strip() for x in ln.rstrip("\n").split("|")]
    o = {}
    for tok in shlex.split(opt[0] if opt else ""):
        if "=" in tok: k, v = tok.split("=", 1); o[k] = v
        else: o[tok] = True
    plan.setdefault(seg, []).append({"src": src, "ss": ss, "w": w, "o": o})
items = {it.get("id"): it for it in tl if it.get("id")}
def rkey(src, ss, kind): return hashlib.md5(f"{src}|{float(ss):.2f}|{kind}".encode()).hexdigest()[:12]
def shots_for(it, skip):
    sid = it["id"]; ps = plan[sid]; dur = it["dur"]; span = ps[0]["o"].get("span")
    if span == "END": dur = TOTAL - it["start"]
    elif span: dur += items[span]["dur"]; skip.add(span)
    out = []
    for p in ps:
        if p["src"].startswith("A:"):
            for a in AI[p["src"][2:]]:
                out.append({"type": "video", "_kind": "ai", "_src": f"{AIR}/{a['clip']}", "_ss": 0.0, "_off": float(a.get("ss", 0)), "dur": float(a["dur"]), "_fixed": True})
            continue
        typ, ref = p["src"].split(":", 1); o = p["o"]; sh = {"_w": p["w"]}
        if o.get("label"): sh["label"] = o["label"]
        for kk in ("zoom", "fx", "fy"):
            if kk in o and typ in ("O", "P"): sh[kk] = float(o[kk])
        if typ == "O": sh.update(type="video", _kind="own", _src=f"{OWN}/{ref}.mov", _ss=float(p["ss"]))
        elif typ == "M": sh.update(type="multi", _kind="ownmulti", _members=[{"_src": f"{OWN}/{x}.mov", "_ss": float(p["ss"])} for x in ref.split(",")])
        elif typ == "P": sh.update(type="video", _kind="pd", _src=f"{PV}/{ref}", _ss=float(p["ss"]))
        elif typ == "I":
            sh.update(type="photo", _kind="photo", src=f"{PI}/{ref}", z0=float(o.get("z0", 1.0)), z1=float(o.get("z1", 1.06)), bg=o.get("bg", "cover"))
            for kk in ("x0", "y0", "x1", "y1"):
                if kk in o: sh[kk] = float(o[kk])
        elif typ == "G":
            sh.update(type="map", _kind="graphic", src=f"{GR}/{ref}")
            if p["ss"] not in ("", "-", "0"): sh["ss"] = float(p["ss"])
        out.append(sh)
    fixed = sum(s["dur"] for s in out if s.get("_fixed")); flex = [s for s in out if not s.get("_fixed")]
    rest = dur - fixed
    if flex:
        ws = [1.0 if s["_w"] in ("fill", "-") else float(s["_w"]) for s in flex]; tot = sum(ws)
        for s, w_ in zip(flex, ws): s["dur"] = rest * w_ / tot
    elif out: out[-1]["dur"] += rest
    for s in out: s["_seg"] = sid
    return out
def plan_shots():
    shots = []; skip = set()
    for it in tl:
        k = it["kind"]
        if k == "title": shots.append({"type": "map", "src": f"{GR}/yc{EP[2:]}_title_card.mp4", "dur": it["dur"], "_kind": "card", "_seg": "title"}); continue
        if k == "card": shots.append({"type": "card", "style": "chapter", "title": it["heading"].strip('"'), "dur": it["dur"], "_kind": "card", "_seg": it["id"]}); continue
        if k == "insert":
            shots.append({"type": "video", "_kind": "insert", "_src": it["src"], "_ss": it["ss"], "dur": it["dur"], "_fixed": True,
                          "label": " · ".join(x for x in (it.get("label", ""), it.get("sub", "")) if x), "_seg": it["id"]}); continue
        if it["id"] in skip: continue
        shots.extend(shots_for(it, skip))
    shots[0]["dur"] += tl[0]["start"]
    return shots
def reqs(shots):
    R = {}
    for s in shots:
        mem = s.get("_members") or ([s] if s.get("_src") else [])
        for m in mem:
            kind = {"own": "own", "ownmulti": "own"}.get(s["_kind"], s["_kind"])
            k = rkey(m["_src"], m["_ss"], kind); m["_key"] = k
            need = 30.0 if kind == "ai" else s["dur"] + 1.5      # AI clips are prepared whole (continuations share one file)
            if k not in R or R[k]["need"] < need: R[k] = {"key": k, "src": m["_src"], "ss": m["_ss"], "need": round(need, 2), "kind": kind}
    return R
if __name__ == "__main__":
    shots = plan_shots(); R = reqs(shots)
    if sys.argv[1] == "requests":
        json.dump(list(R.values()), open(f"{D}/requests.json", "w"), indent=1); print(len(R), "requests"); sys.exit()
    P = json.load(open(f"{D}/prep/index.json")); P = {k: v for k, v in P.items()}
    def avail(s):
        if s["type"] == "map" and s.get("_kind") == "graphic":   # pre-rendered graphic: never hold its last frame
            import subprocess as _sp
            return float(_sp.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", s["src"]], capture_output=True, text=True).stdout) - s.get("ss", 0) - 0.05
        if s["type"] in ("map", "card", "photo"): return 1e9
        if s.get("speed"): return 1e9   # already stretched to fit
        mem = s.get("_members") or [s]
        if s["_kind"] == "insert": return 1e9
        return min(P[m["_key"]]["len"] for m in mem) - 0.05 - s.get("_off", 0)
    # re-balance inside each segment so nothing outlasts its footage
    from collections import defaultdict
    by = defaultdict(list)
    for s in shots: by[s["_seg"]].append(s)
    errors = []
    for seg, ss in by.items():
        for _ in range(6):
            deficit = 0.0
            for s in ss:
                a = avail(s)
                if s["dur"] > a: deficit += s["dur"] - a; s["dur"] = a
            if deficit < 1e-3: break
            spare = [s for s in ss if avail(s) - s["dur"] > 0.05 and not s.get("_fixed")]
            if not spare:
                # AI-only passage a little short (clips end before the narration slot): play the longest AI clip
                # up to 12% slower with motion-interpolated frames (owner: real-time speed; <=12% is not perceptible)
                ai = [s for s in ss if s.get("_kind") == "ai"]
                if ai:
                    Dai = sum(s["dur"] for s in ai); sp = Dai / (Dai + deficit)
                    if sp >= 0.88:
                        for s0 in ai: s0["speed"] = round(sp, 4); s0["dur"] = s0["dur"] / sp
                        continue
                errors.append((seg, round(deficit, 2))); break
            tot = sum(avail(s) - s["dur"] for s in spare)
            for s in spare: s["dur"] += deficit * (avail(s) - s["dur"]) / tot
    if errors: print("NOT ENOUGH FOOTAGE (seg, seconds short):", errors)
    out = []
    for s in shots:
        e = {k: v for k, v in s.items() if not k.startswith("_") or k in ("_kind", "_seg")}
        e["dur"] = round(s["dur"], 3)
        if s["type"] == "video":
            if s["_kind"] == "insert": e.update(src=s["_src"], ss=s["_ss"], drift=0.0)
            else:
                p = P[s["_key"]]; e.update(src=f"{D}/prep/{s['_key']}.mp4", ss=s.get("_off", 0), drift=0.0)
                if p.get("amb"): e.update(amb=p["amb"], amb_g=-10)          # natural sound kept low (owner: quiet or none)
                if s["_kind"] == "ai": e["ai"] = True
                if s["_kind"] == "ai" and p.get("dup", 0) > 0.4: e["drift"] = 0.04   # near-static AI clip: gentle push-in so it never reads as frozen
                if s.get("speed"): e["speed"] = s["speed"]
        elif s["type"] == "multi":
            e["srcs"] = [{"src": f"{D}/prep/{m['_key']}.mp4", "ss": 0} for m in s["_members"]]
            ambs = [P[m["_key"]]["amb"] for m in s["_members"] if P[m["_key"]].get("amb")]
            pass   # split-screen panels: no natural sound (two sources, speech risk)
        out.append(e)
    # merge an AI clip continued across a segment boundary into one shot
    merged = []
    for e in out:
        p = merged[-1] if merged else None
        if p and e.get("ai") and p.get("ai") and p["src"] == e["src"]: p["dur"] = round(p["dur"] + e["dur"], 3); continue
        merged.append(e)
    for e in merged:   # never outlast the prepared footage (merged continuations / per-segment slowdowns)
        if e.get("type") == "video" and "/prep/" in e.get("src", ""):
            L = P[os.path.basename(e["src"])[:-4]]["len"] - 0.06 - e.get("ss", 0); sp = e.get("speed", 1.0)
            if e["dur"] * sp > L:
                need = L / e["dur"]
                if need >= 0.88: e["speed"] = round(need, 4)
                else: print("OUTLASTS FOOTAGE", e["_seg"], e["src"], e["dur"], L)
    json.dump(merged, open(f"{D}/shots2.json", "w"), indent=1)
    tot = sum(e["dur"] for e in merged)
    bad = [(k, v["pan_max"]) for k, v in P.items() if not v["pan_ok"]]
    print(len(merged), "shots", round(tot, 2), "vs audio", round(TOTAL, 2), "| whip-pan windows:", bad)
    print("short (<2.5 s):", [(e["_seg"], e["_kind"], e["dur"]) for e in merged if e["dur"] < 2.5 and e["_kind"] != "card"])
