#!/usr/bin/env python3
"""V49 animation acceptance gate (owner 2026-11-10: be VERY strict with AI animations; match audio/story/script; no hallucinations, drift, craziness).
usage: anim_gate.py SPEC.json OUTDIR   (env GEMINI_API_KEY)
SPEC: [{"id":"S08","clip":"path.mp4","intent":"what the script says this clip must show","era":"present day / 1966 ...","narration":"the sentence(s) spoken over it"}]
Per clip: 8 frames spread over the clip are reviewed by a vision model with the rubric below, plus local drift checks (frame-to-frame structural jump).
A clip PASSES only if every rubric score >= 8/10 AND overall >= 8.5 AND no hard flag. Anything else = REJECT (regenerate; never 'good enough').
Writes OUTDIR/anim_report.json + OUTDIR/<id>_sheet.jpg. Exit 1 if any REJECT."""
import base64, json, os, subprocess, sys, time, urllib.request, glob
import numpy as np, cv2
spec = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True); GK = os.environ["GEMINI_API_KEY"].strip()
RUBRIC = """You are a ruthless QA reviewer for AI-generated animation clips used in a history documentary (stylised flat illustration look, red/orange Navajo sandstone canyon). Review the 8 frames (in time order) of ONE clip.
Score each criterion 0-10 (10 = flawless, 8 = acceptable, below 8 = reject):
 intent: frames show exactly what the intent says, nothing contradicting it.
 anatomy: people/animals/hands/faces/limbs correct, no extra/missing/melted parts (small generic far-away figures are fine).
 objects: vehicles, buildings, tools, machines look like real plausible objects, no impossible geometry, no gibberish text/signs/logos.
 era: nothing anachronistic for the stated era (vehicles, clothing, machines, buildings).
 physics: motion/water/fire/dust/rock behave plausibly; no rock/water that changes shape magically; no objects appearing/disappearing/morphing between frames.
 consistency: the scene stays the same scene from first to last frame (no drift of layout, colours, style, camera, cliffs changing shape).
 style: matches the house style (clean flat graphic illustration, red/orange/cream canyon walls); no photoreal glitches, smearing, noise, watermark.
 sync: the content fits the narration being spoken over it, with no misleading detail.
Also list hard_flags (strings) for: morphing, extra limbs, garbled text, anachronism, wrong location/geology, melted faces, watermark, flicker, anything weird or distracting.
Return ONLY JSON: {"scores":{criterion:int},"overall":float,"hard_flags":[...],"notes":"one sentence on the worst problem"}"""
def frames(clip, n=8):
    cap = cv2.VideoCapture(clip); N = int(cap.get(7)); fs = []
    for k in range(n):
        cap.set(1, int((N - 1) * k / (n - 1))); ok, f = cap.read()
        if ok: fs.append(f)
    return fs
def drift(fs):  # structural jump between consecutive sampled frames (low-res edge maps); high jump = morphing/scene change
    g = [cv2.Canny(cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (160, 90)), 60, 140).astype(np.float32) for f in fs]
    return [round(float(np.mean(np.abs(a - b)) / 255), 3) for a, b in zip(g, g[1:])]
def ask(parts):
    for model in ("gemini-2.5-flash",):
        try:
            r = urllib.request.urlopen(urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GK}",
                data=json.dumps({"contents": [{"parts": parts}], "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}).encode(),
                headers={"Content-Type": "application/json"}), timeout=120)
            return json.loads(json.loads(r.read())["candidates"][0]["content"]["parts"][0]["text"])
        except Exception as e: print("gemini", model, str(e)[:120].replace(GK, "***")); time.sleep(4)
    return None
rep = []; bad = 0
for c in spec:
    fs = frames(c["clip"]); d = drift(fs)
    parts = [{"text": RUBRIC + f"\n\nINTENT: {c['intent']}\nERA: {c.get('era','n/a')}\nNARRATION OVER THIS CLIP: {c.get('narration','n/a')}"}]
    for f in fs:
        ok, b = cv2.imencode(".jpg", cv2.resize(f, (768, int(768 * f.shape[0] / f.shape[1]))), [cv2.IMWRITE_JPEG_QUALITY, 85])
        parts.append({"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(b).decode()}})
    j = ask(parts) or {"scores": {}, "overall": 0, "hard_flags": ["reviewer unavailable"], "notes": "no review"}
    low = {k: v for k, v in j["scores"].items() if v < 8}; flags = list(j.get("hard_flags", []))
    if max(d or [0]) > 0.16: flags.append(f"drift jump {max(d)} between sampled frames")
    ok = not low and j.get("overall", 0) >= 8.5 and not flags and len(j["scores"]) >= 8
    bad += not ok; rep.append({"id": c["id"], "verdict": "PASS" if ok else "REJECT", "low": low, "flags": flags, "overall": j.get("overall"), "drift": d, "notes": j.get("notes")})
    print(c["id"], rep[-1]["verdict"], "overall", j.get("overall"), "low", low, "flags", flags, "|", j.get("notes"))
    sh = np.vstack([np.hstack([cv2.resize(f, (320, 180)) for f in fs[:4]]), np.hstack([cv2.resize(f, (320, 180)) for f in fs[4:8]])]) if len(fs) == 8 else None
    if sh is not None: cv2.imwrite(f"{out}/{c['id']}_sheet.jpg", sh)
json.dump(rep, open(f"{out}/anim_report.json", "w"), indent=1)
print(f"ANIM GATE {'FAIL' if bad else 'PASS'}: {len(spec)} clips, {bad} rejected"); sys.exit(1 if bad else 0)
