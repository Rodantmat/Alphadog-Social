#!/usr/bin/env python3
"""AlphaDog Studio - render-stage auditor ("frame analyzer") for content/recipe/recipe.yaml.

Checks the rules with stage=render and check auto/warn on a finished video:
  picture : Q1 cut inside shot, R7 flash shots, Q2 shake, Q3 freeze, Q4 black/fade-through-black, Q5 frame rate,
            Q7 sharpness/exposure/upscale, Q8 bars, Q9 duplicate shots
  text    : Q6 foreign text/logos, T2 our text spelled right / size / safe area, O2 privacy, V1 vertical safe area,
            V2 shorts length + caption size + captions timed to voice, V3 faces under captions
  meaning : P2 frame-vs-narration CLIP similarity (lowest 5 %), A4 AI-artifact CLIP scan
  audio   : U1 loudness/true peak, U2 voice over bed (estimate when no stems), U3 dead air/clipping, U5 Spanish track
  subs    : T1 six languages present, EN drift vs actual speech (faster-whisper word timestamps)
  owner review Yellowstone Ch1 (EDITING_RULES V15-V22, A6):
            F1 micro-stutter (repeated frames, cadence), F2 frozen runs, F3 crop/upscale vs source + soft frames, F4 whip pans,
            F5 first shot, F6 end card (name OCR, logo template, filled next-video slot), F7 no 'CHAPTER ONE' numbering,
            F8 background speech (silero VAD on --stems, on the mix outside planned voice, on shot ambience files)
Output: <out>/report.json + <out>/sheet_<rule>_<n>.jpg (flagged frames labeled with rule id + time).

usage: analyze.py VIDEO [--srt-dir DIR --srt-prefix NAME] [--mode auto|long|vertical] [--shots shots.jsonl [--patch p.jsonl]]
                  [--timeline timeline.json] [--es-audio FILE] [--recipe recipe.yaml] [--out DIR] [--skip ocr,clip,whisper,faces]
                  [--stems DIR] [--voice-mask mask.npy] [--logo logo.png] [--channel-name NAME]
"""
import argparse, difflib, json, math, os, re, subprocess, sys, time
import numpy as np, cv2

T0 = time.time()
ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--mode", default="auto")
ap.add_argument("--srt-dir", default="")
ap.add_argument("--srt-prefix", default="")
ap.add_argument("--shots", default="")
ap.add_argument("--patch", default="")
ap.add_argument("--timeline", default="")
ap.add_argument("--es-audio", default="")
ap.add_argument("--allow-text", default="", help="file with extra allowed on-screen text, one per line")
ap.add_argument("--recipe", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../content/recipe/recipe.yaml"))
ap.add_argument("--out", default="recipe_qa")
ap.add_argument("--skip", default="")
ap.add_argument("--ocr-every", type=float, default=0.0, help="seconds between OCR samples (default 3 long / 0.5 vertical)")
ap.add_argument("--max-dur", type=float, default=0.0, help="debug: analyze only the first N seconds")
ap.add_argument("--whisper-model", default="base")
ap.add_argument("--stems", default="", help="dir with stem_amb.wav / stem_sfx.wav of this cut (F8: any speech in them fails)")
ap.add_argument("--voice-mask", default="", help="100 Hz .npy mask, 1 where narration/interview voice is planned (F8)")
ap.add_argument("--logo", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../assets/brand/alphadog_studio_logo_400.png"), help="owner logo reference for F6")
ap.add_argument("--channel-name", default="AlphaDog Studio")
ap.add_argument("--dump-features", action="store_true", help="debug: save per-frame features to <out>/features.npz")
A = ap.parse_args()
SKIP = set(x for x in A.skip.split(",") if x)
os.makedirs(A.out, exist_ok=True)
def log(*a): print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)

# ------------------------------------------------------------------ probe
pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=index,codec_type,width,height,r_frame_rate,avg_frame_rate,nb_frames,duration,channels,sample_rate:stream_tags=language",
                                "-of", "json", A.video], capture_output=True, text=True).stdout)
VS = [s for s in pr["streams"] if s["codec_type"] == "video"][0]
AS = [s for s in pr["streams"] if s["codec_type"] == "audio"]
W0, H0 = int(VS["width"]), int(VS["height"])
num, den = map(int, VS["r_frame_rate"].split("/")); FPS = num / den
DUR = float(pr["format"]["duration"])
if A.max_dur: DUR = min(DUR, A.max_dur)
MODE = A.mode if A.mode != "auto" else ("vertical" if H0 > W0 else "long")
VERT = MODE == "vertical"
log("video", W0, H0, round(FPS, 3), "fps", round(DUR, 2), "s", MODE, len(AS), "audio streams")

# ------------------------------------------------------------------ rules (recipe)
RULES = {}
try:
    import yaml
    for r in yaml.safe_load(open(A.recipe))["rules"]: RULES[r["id"]] = r
except Exception as e:
    log("recipe not loaded:", e)
MINE = ["P2", "A4", "O2", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "R7", "U1", "U2", "U3", "U5", "T1", "T2", "V1", "V2", "V3",
        "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8"]
REP = {rid: {"rule": RULES.get(rid, {}).get("rule", ""), "check": RULES.get(rid, {}).get("check", "auto"), "status": "pass", "summary": "", "findings": []} for rid in MINE}
def find(rid, t, msg, sev="fail", t_end=None, box=None, **kw):
    f = {"t": round(float(t), 2), "tc": tc(t), "msg": msg, "sev": sev}
    if t_end is not None: f["t_end"] = round(float(t_end), 2)
    if box is not None: f["box"] = [int(v) for v in box]
    f.update(kw); REP[rid]["findings"].append(f)
def summ(rid, s): REP[rid]["summary"] = s
def skip(rid, why): REP[rid]["status"] = "skipped"; REP[rid]["summary"] = why
def tc(t): t = max(0.0, float(t)); return f"{int(t // 60)}:{t % 60:05.2f}"

# ------------------------------------------------------------------ optional inputs: shot list, timeline, subtitles
SHOTS = []
if A.shots and os.path.exists(A.shots):
    SHOTS = [json.loads(l) for l in open(A.shots) if l.strip()]
    if A.patch and os.path.exists(A.patch):
        for l in open(A.patch):
            if l.strip(): x = json.loads(l); SHOTS[x["i"]] = x["shot"]
    e = [0.0]
    for s in SHOTS: e.append(e[-1] + s["dur"])
    fr = [round(x * 30) for x in e]                    # render_v2 rounds shot edges to 30 fps frames
    for i, s in enumerate(SHOTS): s["_a"] = fr[i] / 30; s["_b"] = fr[i + 1] / 30; s["_i"] = i
    log("shot list", len(SHOTS), "shots, total", round(SHOTS[-1]["_b"], 2), "s")
TL = json.load(open(A.timeline)) if A.timeline and os.path.exists(A.timeline) else []
CHAP = sorted(set([x["start"] for x in TL if x["kind"] in ("card", "title")] + [x["start"] + x["dur"] for x in TL if x["kind"] in ("card", "title")]))
INSERTS = [(x["start"], x["start"] + x["dur"]) for x in TL if x["kind"] == "insert"]
INTRO_END = min([x["start"] for x in TL if x["kind"] == "title"], default=0.0)
def shot_at(t):
    for s in SHOTS:
        if s["_a"] <= t < s["_b"]: return s
    return None
def in_insert(t): return any(a - 0.2 <= t <= b + 0.2 for a, b in INSERTS)

def parse_srt(p):
    out = []
    raw = open(p, encoding="utf-8-sig").read().replace("\r", "")
    for b in re.split(r"\n\s*\n", raw.strip()):
        l = b.strip().split("\n")
        k = next((i for i, x in enumerate(l) if "-->" in x), None)
        if k is None: continue
        def ts(x):
            m = re.match(r"\s*(\d+):(\d+):(\d+)[,.](\d+)", x); h, mi, s, ms = m.groups(); return int(h) * 3600 + int(mi) * 60 + int(s) + int(ms) / 10 ** len(ms)
        a, e_ = l[k].split("-->"); out.append((ts(a), ts(e_), " ".join(l[k + 1:]).strip()))
    return out
SRT = {}
LANGS = {"en": ["en"], "es": ["es"], "fr": ["fr"], "pt": ["pt", "pt-BR"], "ja": ["ja"], "zh": ["zh-Hans", "zh", "zh-CN", "zh-Hant"]}
if A.srt_dir:
    for k, alts in LANGS.items():
        for a_ in alts:
            p = os.path.join(A.srt_dir, f"{A.srt_prefix}.{a_}.srt")
            if os.path.exists(p):
                try: SRT[k] = parse_srt(p); break
                except Exception as e: log("srt parse fail", p, e)
EN = SRT.get("en", [])
def narration_at(a, b):
    return " ".join(t for x, y, t in EN if y > a and x < b)

# ------------------------------------------------------------------ pass A: every frame at low res
LW, LH = (180, 320) if VERT else (320, 180)
def dark_stats(g):
    q = np.percentile(g, (50, 90, 99)); return float(g.mean()), float(g.std()), float(q[2]), float(q[0]), float(q[1])
SFPS = 2.0 if VERT else 1.0
JDIR = os.path.join(A.out, "_frames"); os.makedirs(JDIR, exist_ok=True)
for f_ in os.listdir(JDIR): os.remove(os.path.join(JDIR, f_))
# one decode: every frame at low res to the pipe + full-res samples (SFPS) as JPEG for pass B
# + a native-resolution centre crop (1/4 x 1/4 of the frame, gray) on a second pipe: new grain/detail between real frames
#   separates repeated frames (F1 stutter, F2 freeze) from slow real motion far better than the 320x180 picture
import threading
CRW, CRH = (W0 // 4) // 2 * 2, (H0 // 4) // 2 * 2
crop_r, crop_w = os.pipe()
cmd = ["ffmpeg", "-v", "error"] + (["-t", str(DUR)] if A.max_dur else []) + ["-i", A.video, "-an", "-sn"] + \
      ["-filter_complex", f"[0:v]split=3[a][b][c];[a]scale={LW}:{LH}:flags=area[lo];[b]fps={SFPS}[hi];"
                          f"[c]crop={CRW}:{CRH}:{(W0 - CRW) // 2}:{(H0 - CRH) // 2},format=gray[cr]",
       "-map", "[lo]", "-pix_fmt", "bgr24", "-f", "rawvideo", "pipe:1", "-map", "[hi]", "-q:v", "2", os.path.join(JDIR, "%06d.jpg"),
       "-map", "[cr]", "-pix_fmt", "gray", "-f", "rawvideo", f"pipe:{crop_w}"]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10 ** 7, pass_fds=(crop_w,))
os.close(crop_w)
DC = []                                                     # mean |diff| of consecutive native-res centre crops
def _crop_reader():
    fb = CRW * CRH; pv = None
    with os.fdopen(crop_r, "rb", buffering=4 * fb) as f:
        while True:
            b_ = f.read(fb)
            if len(b_) < fb: break
            c_ = np.frombuffer(b_, np.uint8).astype(np.int16)
            DC.append(float(np.abs(c_ - pv).mean()) if pv is not None else 0.0); pv = c_
_crt = threading.Thread(target=_crop_reader, daemon=True); _crt.start()
FB = LW * LH * 3
Ym, Ys, Y99, CORR, HOV, DX, DY, RESP, DIFF, P50, P90, D16, HS, LAPL = ([] for _ in range(14))
CW, CH = (LW // 5, LH // 5)
corner_acc = []; acc = None; acc_n = 0
prev = None; last_nd = None
han = cv2.createHanningWindow((LW, LH), cv2.CV_32F)
while True:
    buf = p.stdout.read(FB)
    if len(buf) < FB: break
    im = np.frombuffer(buf, np.uint8).reshape(LH, LW, 3)
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    gf = g.astype(np.float32)
    LAPL.append(float(cv2.Laplacian(g, cv2.CV_16S).var()))
    m, sd, p99, p50, p90 = dark_stats(g); Ym.append(m); Ys.append(sd); Y99.append(p99); P50.append(p50); P90.append(p90)
    sm = cv2.resize(gf, (64, 36) if not VERT else (36, 64), interpolation=cv2.INTER_AREA)
    gn = (sm - sm.mean()) / (sm.std() + 1e-3)
    hsv = cv2.cvtColor(cv2.resize(im, (64, 36) if not VERT else (36, 64), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2HSV)
    h = cv2.calcHist([hsv], [0, 1], None, [16, 4], [0, 180, 0, 256]).flatten(); h /= (h.sum() + 1e-6)
    dark = p50 < 18 and p90 < 45                       # median-based: burned-in captions do not hide a fade
    s16 = cv2.resize(gf, (16, 9) if not VERT else (9, 16), interpolation=cv2.INTER_AREA).flatten(); D16.append(((s16 - s16.mean()) / (s16.std() + 1e-3)).astype(np.float16))
    HS.append(h.astype(np.float16))
    if prev is not None:
        ref = last_nd if (dark or prev[3]) and last_nd is not None else prev
        CORR.append(float((gn * ref[0]).mean())); HOV.append(float(np.minimum(h, ref[1]).sum()))
        (dx, dy), resp = cv2.phaseCorrelate(prev[2].copy(), gf.copy(), han); DX.append(dx); DY.append(dy); RESP.append(resp)   # copies: OpenCV 5 windows the inputs in place
        DIFF.append(float(np.abs(sm - prev[4]).mean()))
    else:
        CORR.append(1.0); HOV.append(1.0); DX.append(0.0); DY.append(0.0); RESP.append(1.0); DIFF.append(0.0)
    prev = (gn, h, gf, dark, sm)
    if not dark: last_nd = prev
    # corner statistics per 1 s chunk (static logo bugs)
    cs = np.stack([gf[:CH, :CW], gf[:CH, -CW:], gf[-CH:, :CW], gf[-CH:, -CW:]])
    if acc is None: acc = [np.zeros_like(cs), np.zeros_like(cs), np.zeros_like(gf), np.zeros_like(gf)]
    acc[0] += cs; acc[1] += cs * cs; acc[2] += gf; acc[3] += gf * gf; acc_n += 1
    if acc_n == int(round(FPS)):
        mu = acc[0] / acc_n; sdv = np.sqrt(np.maximum(acc[1] / acc_n - mu * mu, 0)); mc = acc[2] / acc_n
        sc = np.sqrt(np.maximum(acc[3] / acc_n - mc * mc, 0))
        corner_acc.append((mu.astype(np.float32), sdv.astype(np.float32), float(np.median(sc))))
        acc = None; acc_n = 0
p.wait(); _crt.join(timeout=120)
N = len(Ym); Ym, Ys, Y99, CORR, HOV, DX, DY, RESP, DIFF, P50, P90, LAPL = map(np.array, (Ym, Ys, Y99, CORR, HOV, DX, DY, RESP, DIFF, P50, P90, LAPL))
DC = np.array((DC + [0.0] * N)[:N], np.float32)
D16 = np.array(D16, np.float32); HS = np.array(HS, np.float32)
DARK = (P50 < 18) & (P90 < 45)
BLACK = (P50 < 10) & (P90 < 18)
log("pass A", N, "frames")
if A.dump_features: np.savez_compressed(os.path.join(A.out, "features.npz"), DC=DC, DIFF=DIFF, DX=DX, DY=DY, RESP=RESP, LAPL=LAPL, DARK=DARK, P50=P50)

# ---- cut detection (fade-to-black aware)
cuts = []
j = 1
while j < N:
    if DARK[j]:                                           # a dark run: one boundary at its centre if content changes across it
        k = j
        while k < N and DARK[k]: k += 1
        if j < FPS * 0.3 or k > N - FPS * 0.3: pass
        elif k < N and (CORR[k] < 0.6 or HOV[k] < 0.6) and k - j < FPS * 3: cuts.append(((j + k) / 2, "dip"))
        elif k < N and k - j >= FPS * 3: cuts.append((j, "dip")); cuts.append((k, "dip"))
        j = k + 1; continue
    lo, hi = max(1, j - 6), min(N, j + 7)
    nb = [x for x in range(lo, hi) if x != j and not DARK[x]]
    mc = np.median(CORR[nb]) if nb else 1.0; mh = np.median(HOV[nb]) if nb else 1.0
    flat = Ys[j] < 5
    if P50[j] < 25 or P50[j - 1] < 25 or j < FPS * 0.3 or j > N - FPS * 0.3: j += 1; continue     # dim frames: fades/cards (handled as dips)
    c_cut = (not flat) and CORR[j] < 0.55 and mc - CORR[j] > 0.3
    h_cut = HOV[j] < 0.5 and mh - HOV[j] > 0.3
    dim = P50[j] < 45 or P50[j - 1] < 45                 # low-light scenes: noise/flicker - require both signals
    if (c_cut and h_cut) if dim else (c_cut or h_cut): cuts.append((j, "hard"))
    j += 1
# fade dips that never reach black (captions/vignette on top): local luma minimum at < 50 % of both sides + content change
for j in range(10, N - 10):
    if DARK[j] or P50[j] > min(P50[j - 3:j + 4]): continue
    pre, post = P50[j - 10:j - 2].max(), P50[j + 3:j + 11].max()
    if min(pre, post) < 30 or P50[j] > 0.5 * min(pre, post): continue
    a, b2 = j - 6, j + 6
    c = float(D16[a] @ D16[b2]) / D16.shape[1]; hh = float(np.minimum(HS[a], HS[b2]).sum())
    if c < 0.5 or hh < 0.6: cuts.append((j, "dip"))
# merge cuts closer than 6 frames
cuts.sort(); mc_ = []
for c in cuts:
    if mc_ and c[0] - mc_[-1][0] < 6: continue
    mc_.append(c)
CUTS = [c[0] / FPS for c in mc_]
SEG = []
b = [0.0] + CUTS + [N / FPS]
for i in range(len(b) - 1):
    if b[i + 1] - b[i] > 0.02: SEG.append((b[i], b[i + 1]))
log("cuts", len(CUTS), "segments", len(SEG))

# ---- align shot list with detected cuts (offset search)
OFFSET = 0.0
if SHOTS:
    exp = np.array([s["_a"] for s in SHOTS[1:]])
    best = (-1, 0.0)
    for off in np.arange(-1.5, 1.5001, 1 / 30):
        e2 = exp + off; m = sum(1 for c in CUTS if np.min(np.abs(e2 - c)) < 0.12)
        if m > best[0]: best = (m, off)
    OFFSET = float(best[1])
    for s in SHOTS: s["_a"] += OFFSET; s["_b"] += OFFSET
    exp = exp + OFFSET
    matched = sum(1 for c in CUTS if np.min(np.abs(exp - c)) < 0.2)
    log(f"shot list offset {OFFSET:+.3f}s; {matched}/{len(CUTS)} detected cuts match planned boundaries ({len(exp)} planned)")

# ------------------------------------------------------------------ Q1 / R7
if SHOTS:
    exp = np.array([s["_a"] for s in SHOTS[1:]])
    for c, kind in mc_:
        t = c / FPS
        if np.min(np.abs(exp - t)) < 0.2: continue
        s = shot_at(t)
        if s is None: continue
        if s["type"] in ("map", "card"): continue          # animated maps / card text reveals
        find("Q1", t, f"scene change inside shot {s['_i']} ({s['type']}, {os.path.basename(s.get('src', ''))}, {s['_a']:.2f}-{s['_b']:.2f})",
             shot=s["_i"], src=os.path.basename(s.get("src", "")))
    summ("Q1", f"{len(CUTS)} detected cuts vs {len(SHOTS)} planned shots (offset {OFFSET:+.2f}s)")
else:
    skip("Q1", "no shot list: every detected cut counts as a shot boundary (flashes reported under R7)")
for a, b_ in SEG:
    d = b_ - a
    pl = shot_at((a + b_) / 2)
    if pl is not None and pl["type"] in ("card", "map") and pl["_a"] - 0.3 <= a and b_ <= pl["_b"] + 0.3: continue   # fades inside our cards/maps
    if np.median(P50[int(a * FPS):max(int(a * FPS) + 1, int(b_ * FPS))]) < 25: continue                 # a dark fade remnant, not a visible flash
    if a < 0.05 or b_ > N / FPS - 0.05:
        if d < 0.6: continue                                # fade-in/out remnants at the very start/end
    if d < 1.2: find("R7", a, f"shot on screen {d:.2f}s (< 1.2 s)", t_end=b_, dur=round(d, 2))
    elif d < 2.0:
        s = shot_at((a + b_) / 2)
        scen = s is None or s["type"] in ("video", "photo")
        find("R7", a, f"shot on screen {d:.2f}s (scenery < 2 s)", sev="fail" if (s is not None and scen and not s.get("ai")) else "warn", t_end=b_, dur=round(d, 2))
summ("R7", f"{len(SEG)} on-screen shots, shortest {min((b_ - a for a, b_ in SEG), default=0):.2f}s")

# ------------------------------------------------------------------ Q3 freeze, Q2 shake, Q5 cadence
jit = []; stutter = []
for a, b_ in SEG:
    i0, i1 = int(round(a * FPS)), int(round(b_ * FPS))
    if i1 - i0 < FPS * 0.8: continue
    s = shot_at((a + b_) / 2)
    typ = s["type"] if s else "?"
    d = DIFF[i0 + 2:i1 - 1]; dk = DARK[i0 + 2:i1 - 1]
    d = np.where(dk, np.nan, d)
    if len(d) < 10: continue
    first = np.nanmedian(d[: max(3, len(d) // 2)])
    moving = first > 0.6
    if moving and typ not in ("map", "card", "photo"):
        run = 0; best = (0, 0)
        for k, x in enumerate(d):
            if not np.isnan(x) and x < 0.12: run += 1
            else: run = 0
            if run > best[0]: best = (run, k)
        if best[0] / FPS > 0.6:
            t_end = a + (best[1] + 3) / FPS; t0_ = t_end - best[0] / FPS
            find("Q3", t0_, f"picture frozen {best[0] / FPS:.2f}s inside a moving {typ} shot", t_end=t_end, dur=round(best[0] / FPS, 2))
        z = (d < 0.02) & ~np.isnan(d)
        if len(d) > 30 and 0.25 < z.mean() < 0.6:
            stutter.append((a, b_, float(z.mean())))
    # shake
    if i1 - i0 > FPS * 1.2 and typ not in ("map", "card"):
        tx = np.stack([DX[i0 + 5:i1 - 4], DY[i0 + 5:i1 - 4]], 1); ok = (RESP[i0 + 5:i1 - 4] > 0.08) & ~DARK[i0 + 5:i1 - 4]
        if len(tx) > 24 and ok.mean() > 0.7:
            tx = np.where(ok[:, None], tx, 0)
            sm_ = np.stack([np.convolve(tx[:, q], np.ones(9) / 9, "same") for q in (0, 1)], 1)
            r = (tx - sm_)[5:-5]; okr = ok[5:-5]
            if okr.sum() > 10:
                j_ = float(np.sqrt((r[okr] ** 2).sum(1).mean())); jit.append(j_)
                if j_ > 1.8: find("Q2", (a + b_) / 2, f"jitter {j_:.2f}px ({typ})", t_end=b_, jitter=round(j_, 2))
summ("Q3", "moving shots checked for frozen runs > 0.6 s (maps/cards/stills exempt)")
summ("Q2", f"median jitter {np.median(jit) if jit else 0:.2f}px over {len(jit)} shots; limit 1.8")
q5 = []
if abs(FPS - round(FPS)) > 0.02 and abs(FPS - 29.97) > 0.02 and abs(FPS - 23.976) > 0.02: q5.append(f"odd frame rate {FPS:.3f}")
if round(FPS) not in (24, 25, 30, 60): q5.append(f"frame rate {FPS:.2f} not in 24/25/30/60")
exp_frames = (float(VS.get("duration") or DUR)) * FPS if not A.max_dur else N
if abs(N - exp_frames) > FPS: q5.append(f"decoded {N} frames vs {exp_frames:.0f} expected")
for m_ in q5: find("Q5", 0, m_)
for a, b_, z in stutter: find("Q5", a, f"judder: {z:.0%} repeated frames in a moving shot", sev="warn", t_end=b_)
summ("Q5", f"{FPS:.3f} fps CFR, {N} frames; {len(stutter)} shots with repeated-frame cadence")

# ------------------------------------------------------------------ F1 stutter, F2 freeze, F3 crop/soft, F4 whip pan (owner review Yellowstone Ch1)
STILL_EXT = (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp", ".gif")
def is_moving_plan(s):
    """planned moving-picture shot: video/multi/insert footage; not maps, cards, graphics, photos or still sources"""
    if s is None: return True
    if s.get("type") not in ("video", "multi") or s.get("_kind") in ("card", "graphic", "photo", "map"): return False
    if s.get("src_still") or str(s.get("src", "")).lower().endswith(STILL_EXT): return False
    return True
MUNITS = [(a, b_, s) for a, b_, s in ([(s["_a"], s["_b"], s) for s in SHOTS] if SHOTS else [(a, b_, None) for a, b_ in SEG]) if is_moving_plan(s)]
def unit_name(s, a):
    if s is None: return f"shot at {tc(a)}"
    nm = os.path.basename(str(s.get("src", ""))) or s.get("type", "?")
    return f"shot {s['_i']} ({'ai' if s.get('ai') else s.get('_kind', s.get('type'))} {nm})"
def interior(a, b_, s):
    """frame indices of a shot's interior: 3 frames off each cut, fades skipped, dark frames dropped (DC[k] = frame k vs k-1)"""
    k0 = int(round(a * FPS)) + 3 + int(round(float((s or {}).get("fin") or 0) * FPS))
    k1 = int(round(b_ * FPS)) - 2 - int(round(float((s or {}).get("fout") or 0) * FPS))
    k0, k1 = max(1, k0), min(N, k1)
    if k1 - k0 < 1: return np.array([], int)
    idx = np.arange(k0, k1); return idx[~DARK[idx]]
def rolling(x, half, fn):
    if len(x) == 0: return x
    xp = np.pad(x, half, mode="edge"); w = np.lib.stride_tricks.sliding_window_view(xp, 2 * half + 1)
    return fn(w, axis=1)
CAD = {5: "1 in 5 = 24->30 fps pulldown", 6: "1 in 6 = 25->30 fps", 4: "1 in 4 (~22-24 fps source)", 3: "1 in 3 (20 fps source)", 2: "1 in 2 (15 fps source)"}
def cadence(pos):
    if len(pos) < 4: return "too few repeats to read a cadence"
    best = (0.0, None)
    for per in (5, 6, 4, 3, 2):
        conc = np.bincount(pos % per, minlength=per).max() / len(pos)
        if conc >= (0.6 if per >= 4 else 0.75) and conc - 1 / per > best[0]: best = (conc - 1 / per, per)
    return f"regular cadence {CAD[best[1]]}" if best[1] else "irregular (variable-frame-rate source / dropped frames)"
F1_LIM = 0.03; F1_REF = 0.6; F1_REL = 0.4
f1_rows = []; f1_static = 0
f2_n = 0; f4_rows = []; soft_n = 0
SPX = (1080.0 / min(LW, LH)) * FPS                       # low-res px/frame -> px/s at 1080p
SPD = np.hypot(DX, DY) * SPX
SPD_OK = np.where((RESP > 0.3) & ~DARK, SPD, np.nan)
for a, b_, s in MUNITS:
    idx = interior(a, b_, s)
    if len(idx) < 24: continue
    nm = unit_name(s, a); sev_ = "fail" if SHOTS else "warn"
    d = DC[idx]
    # F1: a repeated frame shows (almost) no new detail while the frames on BOTH sides of it do (a dip, then catch-up):
    #     d[k] < 40 % of min(max d[k-3..k-1], max d[k+1..k+3]). Smooth slow-downs, static-but-live scenes and motion onsets have
    #     no such two-sided dip, so they do not count; 24->30 pulldown, VFR duplicates and zoompan rounding holds do.
    nb_l = np.array([d[max(0, k - 3):k].max() if k > 0 else 0.0 for k in range(len(d))])
    nb_r = np.array([d[k + 1:k + 4].max() if k + 1 < len(d) else 0.0 for k in range(len(d))])
    nb = np.minimum(nb_l, nb_r); valid = nb >= F1_REF; valid[:3] = False; valid[-3:] = False
    if valid.mean() < 0.3: f1_static += 1
    else:
        rp = valid & (d < F1_REL * nb)
        ratio = float(rp.sum() / max(1, valid.sum()))
        cad = cadence(idx[rp]) if rp.sum() else ""
        f1_rows.append({"t": round(a, 2), "shot": s["_i"] if s else None, "repeat_ratio": round(ratio, 3), "judged": round(float(valid.mean()), 2)})
        if ratio > F1_LIM and rp.sum() >= 3:
            fps_ = f", source {s['src_fps']:g} fps{' VFR' if s.get('src_vfr') else ''}" if s and s.get("src_fps") else ""
            first = idx[rp][0] / FPS
            find("F1", first, f"micro-stutter: {ratio:.0%} repeated frames in {nm}; {cad}{fps_}", sev=sev_, t_end=b_, ratio=round(ratio, 3),
                 shot=s["_i"] if s else None, cadence=cad)
    # F2: the picture stops abruptly and stays stopped >= 0.3 s (held last frame / stalled source): a run of frames with
    #     < 25 % of the motion right before it, entered within 2 frames, and quieter than the shot's own quiet real frames
    k = 0
    while k < len(d):
        if k < 6: k += 1; continue
        M = float(np.median(d[max(0, k - 12):k]))
        if M < F1_REF or d[k] >= 0.25 * M or d[k - 1] < 0.5 * M: k += 1; continue
        e_ = k
        while e_ < len(d) and d[e_] < 0.25 * M and idx[e_] == idx[e_ - 1] + 1: e_ += 1
        n_ = e_ - k
        if n_ / FPS >= 0.3:
            outside = np.concatenate([d[:k], d[e_:]])
            quiet = float(np.percentile(outside, 25)) if len(outside) > 10 else M
            lvl = float(np.median(d[k:e_]))
            if lvl < 0.5 * quiet:
                ta, tb = (idx[k] - 1) / FPS, idx[e_ - 1] / FPS
                tail = idx[e_ - 1] >= idx[-1] - 1
                find("F2", ta, f"picture frozen {n_ / FPS:.2f}s inside moving {nm}" + (" - frozen tail: the shot outlasts its footage" if tail else ""),
                     sev=sev_, t_end=tb, dur=round(n_ / FPS, 2)); f2_n += 1
        k = max(e_, k + 1)
    # F4: camera speed (global phase-correlation shift) above ~270 px/s at 1080p
    sp = rolling(SPD_OK[idx], 3, np.nanmedian) if np.isfinite(SPD_OK[idx]).sum() > 10 else np.full(len(idx), np.nan)
    fast = np.nan_to_num(sp, nan=0.0) > 270
    runs = []; k = 0
    while k < len(fast):
        if not fast[k]: k += 1; continue
        e_ = k
        while e_ < len(fast) and fast[e_]: e_ += 1
        if (e_ - k) / FPS >= 0.3: runs.append((k, e_))
        k = e_
    if runs:
        k, e_ = max(runs, key=lambda r: np.nanmax(sp[r[0]:r[1]]))
        pk = float(np.nanmax(sp[k:e_])); tot = sum(r[1] - r[0] for r in runs) / FPS
        pre = sp[max(0, runs[0][0] - 15):runs[0][0]]; pre = float(np.nanmedian(pre)) if len(pre) and np.isfinite(pre).any() else None
        sudden = pre is not None and pre < 110 and runs[0][0] > 15
        f4_rows.append((a, pk))
        find("F4", idx[runs[0][0]] / FPS, f"fast camera move: up to {pk:.0f} px/s (limit 270) for {tot:.1f}s in {nm}" + (f" - sudden (from {pre:.0f} px/s)" if sudden else ""),
             sev=sev_, t_end=idx[runs[-1][1] - 1] / FPS, peak_px_s=round(pk), fast_s=round(tot, 2), t_peak=round(idx[k + int(np.nanargmax(sp[k:e_]))] / FPS, 2))
    # F3 (warn): frames that go soft against their neighbours (focus hunting, motion blur, bad frames)
    lp = LAPL[idx]; lref = rolling(lp, 15, np.median)
    soft = (lp < 0.5 * lref) & (lref > 30)
    k = 0; worst = None
    while k < len(soft):
        if not soft[k]: k += 1; continue
        e_ = k
        while e_ < len(soft) and soft[e_]: e_ += 1
        if e_ - k >= 3:
            r_ = float(np.median(lp[k:e_] / lref[k:e_]))
            if worst is None or r_ < worst[0]: worst = (r_, k, e_)
        k = e_
    if worst:
        soft_n += 1
        find("F3", idx[worst[1]] / FPS, f"soft frames: sharpness drops to {worst[0]:.0%} of the neighbouring frames for {(worst[2] - worst[1]) / FPS:.2f}s in {nm}",
             sev="warn", t_end=idx[worst[2] - 1] / FPS, kind="soft")
# F2 (warn): an animated graphic/map that opens on a held frame right after moving footage reads as a freeze at the cut
if SHOTS:
    for i, s in enumerate(SHOTS):
        if i == 0 or s.get("_kind") != "graphic" or not is_moving_plan(SHOTS[i - 1]): continue
        k0 = int(round(s["_a"] * FPS)) + 1; k1 = min(N, int(round(s["_b"] * FPS)) - 2)
        if k1 - k0 < FPS * 2: continue
        st = (DIFF[k0:k1] < 0.05) & (DC[k0:k1] < 0.3)
        n_ = 0
        while n_ < len(st) and st[n_]: n_ += 1
        if n_ / FPS >= 0.8 and (~st[n_:]).sum() > FPS * 0.5:
            find("F2", s["_a"], f"graphic opens on a held frame for {n_ / FPS:.2f}s right after moving footage (reads as a freeze at the cut): {os.path.basename(str(s.get('src', '')))}",
                 sev="warn", t_end=s["_a"] + n_ / FPS, dur=round(n_ / FPS, 2), kind="held_open")
REP["F1"]["shots"] = f1_rows
summ("F1", f"{len(f1_rows)} moving shots measured ({f1_static} too static to judge); repeated frame = new detail (native-res centre crop) < {F1_REL:.0%} "
           f"of the frames on both sides; fail > {F1_LIM:.0%}; worst {max((r['repeat_ratio'] for r in f1_rows), default=0):.0%}")
summ("F2", f"abrupt frozen runs >= 0.3 s inside moving shots: {f2_n} (+ animated graphics opening on a held frame >= 0.8 s, warn)")
summ("F4", f"global motion (phase correlation, 0.23 s median) > 270 px/s at 1080p for >= 0.3 s: {len(f4_rows)} of {len(MUNITS)} moving shots")
REP["F3"]["soft_shots"] = soft_n

# ------------------------------------------------------------------ Q4 black
def near_chapter(t, w=2.0): return any(abs(t - c) < w for c in CHAP)
k = 0
while k < N:
    if not DARK[k]: k += 1; continue
    e_ = k
    while e_ < N and DARK[e_]: e_ += 1
    d = (e_ - k) / FPS; ta, tb = k / FPS, e_ / FPS
    nblack = int(BLACK[k:e_].sum())
    if d > 0.25 and not (ta < 1.0 or tb > N / FPS - 2.5):
        # dim run: count the fade ramps around it as well (fade-through-black length)
        a_ = k
        while a_ > 0 and Ym[a_ - 1] < Ym[a_] + 40 and Ym[a_ - 1] < 70 and k - a_ < FPS * 2: a_ -= 1
        b2 = e_
        while b2 < N - 1 and Ym[b2] < 70 and b2 - e_ < FPS * 2: b2 += 1
        if near_chapter(ta) or near_chapter(tb):
            find("Q4", ta, f"dark {d:.2f}s at a chapter boundary (allowed)", sev="info", t_end=tb)
        elif nblack / FPS > 0.25:
            find("Q4", ta, f"black {nblack / FPS:.2f}s (fade-through-black {(b2 - a_) / FPS:.2f}s) inside a chapter", t_end=tb, dur=round(d, 2))
        else:
            find("Q4", ta, f"near-black picture {d:.2f}s (very dark scene, not a fade)", sev="warn", t_end=tb, dur=round(d, 2))
    k = e_
summ("Q4", f"dark runs > 0.25 s outside the first 1 s / last 2.5 s and chapter boundaries; cut dips ({0.24:.2f}s fades) allowed")

# ---- static corner logos (Q6)
logo = {}
for ci, (mu, sdv, center_sd) in enumerate(corner_acc):
    if center_sd < 5: continue                                # the whole picture is still
    for q in range(4):
        st = sdv[q] < 1.2
        gy, gx = np.gradient(mu[q]); ed = np.hypot(gx, gy) > 12
        n = int((st & ed).sum())
        if n >= max(12, 0.02 * st.size): logo.setdefault(q, []).append((ci, n))
QN = ["top-left", "top-right", "bottom-left", "bottom-right"]
for q, L in logo.items():
    runs = []; cur = [L[0]]
    for x in L[1:]:
        if x[0] - cur[-1][0] <= 2: cur.append(x)
        else: runs.append(cur); cur = [x]
    runs.append(cur)
    for r in runs:
        if len(r) < 3: continue
        t = r[0][0] + 0.5; s = shot_at(t)
        if s and s["type"] in ("map", "card"): continue
        if s and q == 2 and s.get("label"): continue        # our lower-third label sits bottom-left
        if VERT: continue                                      # vertical: our burned text is checked by OCR (V1)
        bw, bh = W0 // 5, H0 // 5; bx = 0 if q in (0, 2) else W0 - bw; by = 0 if q < 2 else H0 - bh
        find("Q6", t, f"static detail in {QN[q]} corner for {len(r)} s while the picture moves (logo/bug?)", sev="warn", t_end=r[-1][0] + 1, box=[bx, by, bx + bw, by + bh])

# ------------------------------------------------------------------ pass B: samples at full res
OCR_EVERY = A.ocr_every or (0.5 if VERT else 3.0)
ocr = None
if "ocr" not in SKIP:
    try:
        from rapidocr_onnxruntime import RapidOCR
        ocr = RapidOCR()
    except Exception as e: log("OCR unavailable:", e)
face = None
if "faces" not in SKIP:
    for fp in ("/tmp/yunet.onnx", os.path.join(os.path.dirname(os.path.abspath(__file__)), "yunet.onnx")):
        if os.path.exists(fp) and os.path.getsize(fp) > 10000:
            try: face = cv2.FaceDetectorYN.create(fp, "", (640, 360), 0.75, 0.3, 50); break
            except Exception as e: log("YuNet failed:", e)
    if face is None:
        try: haar = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml"); face = ("haar", haar)
        except Exception: pass
clip = None
if "clip" not in SKIP:
    try:
        import torch, open_clip
        torch.set_num_threads(os.cpu_count() or 2)
        model, _, prep = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
        tok = open_clip.get_tokenizer("ViT-B-32"); model.eval(); clip = (torch, model, prep, tok)
        log("CLIP ViT-B-32 loaded")
    except Exception as e: log("CLIP unavailable:", e)
from PIL import Image
SAMPLES = []      # dict(t, lap, up, mean, hash, bars, ocr, faces, emb)
si = 0; clip_batch = []
JPGS = sorted(os.listdir(JDIR))
def dhash(g):
    s = cv2.resize(g, (17, 16), interpolation=cv2.INTER_AREA); return int("".join("1" if v else "0" for v in (s[:, 1:] > s[:, :-1]).flatten()), 2)
def bars(g):
    h_, w_ = g.shape; r = {}
    def run_(arr):
        n = 0
        for v in arr:
            if v: n += 1
            else: break
        return n
    rm = g.mean(1); rs = g.std(1); cm = g.mean(0); cs_ = g.std(0)
    def edge(prof, n):                                     # a real bar ends in a hard step into the picture
        if n == 0 or n + 6 >= len(prof): return 0
        return n if prof[n + 2: n + 6].mean() - prof[:n].mean() > 20 else 0
    r["top"] = edge(rm, run_((rm < 14) & (rs < 4))); r["bottom"] = edge(rm[::-1], run_(((rm < 14) & (rs < 4))[::-1]))
    r["left"] = edge(cm, run_((cm < 14) & (cs_ < 4))); r["right"] = edge(cm[::-1], run_(((cm < 14) & (cs_ < 4))[::-1]))
    return r
def overlay_style(im, box):
    """our burned-in text: white/gold fill with a dark outline, or dark text on our Spotify-green button"""
    x0, y0, x1, y1 = [int(round(v)) for v in box]; x0, y0 = max(0, x0), max(0, y0)
    c = im[y0:y1, x0:x1]
    if c.size == 0: return False
    hsv = cv2.cvtColor(c, cv2.COLOR_BGR2HSV); H_, S_, V_ = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    white = (V_ > 215) & (S_ < 45); gold = (H_ > 10) & (H_ < 25) & (S_ > 110) & (V_ > 170)
    dark = V_ < 50; green = (H_ > 60) & (H_ < 80) & (S_ > 140) & (V_ > 150)
    return bool(((white | gold).mean() > 0.10 and dark.mean() > 0.04 and (y1 - y0) >= 38) or green.mean() > 0.30)
def blurfill(g):
    h_, w_ = g.shape
    if VERT:
        a_, c_, b_ = g[: h_ // 6], g[h_ // 3: 2 * h_ // 3], g[-h_ // 6:]
    else:
        a_, c_, b_ = g[:, : w_ // 8], g[:, w_ // 3: 2 * w_ // 3], g[:, -w_ // 8:]
    l = lambda x: cv2.Laplacian(x, cv2.CV_32F).var()
    lc = l(c_); return lc > 30 and l(a_) < 0.08 * lc and l(b_) < 0.08 * lc
for jf in JPGS:
    t = (si + 0.5) / SFPS - 1 / FPS; si += 1               # ffmpeg fps=N emits, for tick k, the last source frame before (k + 0.5) / N
    im = cv2.imread(os.path.join(JDIR, jf))
    if im is None or im.shape[:2] != (H0, W0): continue
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    sc = 1080 / min(W0, H0)
    gs = cv2.resize(g, (int(W0 * sc * 0.5), int(H0 * sc * 0.5)), interpolation=cv2.INTER_AREA)          # 960x540 / 540x960
    lap = float(cv2.Laplacian(gs, cv2.CV_32F).var())
    small = cv2.resize(g, (int(W0 * sc / 2.25), int(H0 * sc / 2.25)), interpolation=cv2.INTER_AREA)
    up = cv2.resize(small, (g.shape[1], g.shape[0]), interpolation=cv2.INTER_CUBIC)
    lf = float(cv2.Laplacian(g, cv2.CV_32F).var()); lu = float(cv2.Laplacian(up, cv2.CV_32F).var())
    S = {"t": t, "lap": lap, "up": lu / (lf + 1e-3), "lapfull": lf, "mean": float(g.mean()), "std": float(g.std()),
         "hi": float((g > 250).mean()), "lo": float((g < 6).mean()), "hash": dhash(g), "bars": bars(g), "bfill": blurfill(g), "jpg": os.path.join(JDIR, jf)}
    if ocr is not None and ((si - 1) % max(1, int(round(OCR_EVERY * SFPS))) == 0):
        osc = 1280 / max(W0, H0) if not VERT else 1.0
        oim = cv2.resize(im, (int(W0 * osc), int(H0 * osc)), interpolation=cv2.INTER_AREA) if osc != 1.0 else im
        try: res, _ = ocr(oim)
        except Exception as e: res = None
        S["ocr"] = [{"box": [float(min(q[0] for q in r_[0])) / osc, float(min(q[1] for q in r_[0])) / osc, float(max(q[0] for q in r_[0])) / osc, float(max(q[1] for q in r_[0])) / osc],
                     "text": r_[1], "conf": float(r_[2])} for r_ in (res or [])]
        for o in S["ocr"]: o["ov"] = overlay_style(im, o["box"])
    if face is not None and (VERT or si % 2 == 0):
        fs = 640 / max(W0, H0); fim = cv2.resize(im, (int(W0 * fs), int(H0 * fs)))
        if isinstance(face, tuple):
            dets = face[1].detectMultiScale(cv2.cvtColor(fim, cv2.COLOR_BGR2GRAY), 1.1, 6, minSize=(24, 24))
            S["faces"] = [[x / fs, y / fs, (x + w) / fs, (y + h) / fs, 0.9] for x, y, w, h in (dets if len(dets) else [])]
        else:
            face.setInputSize((fim.shape[1], fim.shape[0])); _, dets = face.detect(fim)
            S["faces"] = [[d[0] / fs, d[1] / fs, (d[0] + d[2]) / fs, (d[1] + d[3]) / fs, float(d[-1])] for d in (dets if dets is not None else [])]
    SAMPLES.append(S)
    if clip is not None:
        cim = im
        if S.get("ocr"):
            cim = im.copy(); bl = cv2.GaussianBlur(cv2.resize(im, (W0 // 8, H0 // 8)), (9, 9), 0); bl = cv2.resize(bl, (W0, H0))
            for o in S["ocr"]:
                x0, y0, x1, y1 = [int(v) for v in o["box"]]; x0, y0 = max(0, x0 - 12), max(0, y0 - 12); x1, y1 = x1 + 12, y1 + 12
                cim[y0:y1, x0:x1] = bl[y0:y1, x0:x1]
        clip_batch.append((len(SAMPLES) - 1, clip[2](Image.fromarray(cv2.cvtColor(cv2.resize(cim, (int(W0 * 288 / min(W0, H0)), int(H0 * 288 / min(W0, H0)))), cv2.COLOR_BGR2RGB)))))
        if len(clip_batch) >= 32:
            with clip[0].no_grad():
                emb = clip[1].encode_image(clip[0].stack([x[1] for x in clip_batch])); emb = emb / emb.norm(dim=-1, keepdim=True)
            for (ix, _), e_ in zip(clip_batch, emb.numpy()): SAMPLES[ix]["emb"] = e_
            clip_batch = []
    if si % 200 == 0: log("pass B", si, "samples")
if clip is not None and clip_batch:
    with clip[0].no_grad():
        emb = clip[1].encode_image(clip[0].stack([x[1] for x in clip_batch])); emb = emb / emb.norm(dim=-1, keepdim=True)
    for (ix, _), e_ in zip(clip_batch, emb.numpy()): SAMPLES[ix]["emb"] = e_
log("pass B", len(SAMPLES), "samples")
def samples_in(a, b_, margin=0.2): return [S for S in SAMPLES if a + margin <= S["t"] <= b_ - margin]
def seg_of(t):
    for a, b_ in SEG:
        if a <= t < b_: return (a, b_)
    return (t, t)

# ------------------------------------------------------------------ Q7 sharpness/exposure/upscale, Q8 bars
UNITS = [(s["_a"], s["_b"], s) for s in SHOTS] if SHOTS else [(a, b_, None) for a, b_ in SEG]
lapv = []
for a, b_, s in UNITS:
    ss = samples_in(a, b_)
    if not ss: continue
    typ = s["type"] if s else "?"
    if typ in ("card", "map"): continue
    lp = float(np.median([x["lap"] for x in ss])); upr = float(np.median([x["up"] for x in ss])); lapv.append(lp)
    hi = float(np.median([x["hi"] for x in ss])); lo = float(np.median([x["lo"] for x in ss])); mn = float(np.median([x["mean"] for x in ss]))
    tm = ss[len(ss) // 2]["t"]; nm = os.path.basename(s.get("src", "")) if s else ""
    if lp < 12 and float(np.median([x["std"] for x in ss])) > 20: find("Q7", tm, f"blurry: Laplacian var {lp:.1f} ({typ} {nm})", sev="warn", lap=round(lp, 1))
    if not VERT and upr > 0.62 and lp < 120 and typ == "video": find("Q7", tm, f"soft/upscaled source: {upr:.0%} of detail survives a 480p round-trip ({nm})", sev="warn", up_ratio=round(upr, 2))
    if hi > 0.20: find("Q7", tm, f"blown-out: {hi:.0%} pixels clipped white ({nm})", sev="warn")
    if mn < 28 and lo > 0.35 and not (s and s.get("ai")): find("Q7", tm, f"very dark: mean luma {mn:.0f}, {lo:.0%} crushed ({nm})", sev="warn")
    # bars
    bb = [x["bars"] for x in ss if x["mean"] > 30 and not x["bfill"]]
    if bb and typ not in ("card",):
        for side in ("top", "bottom", "left", "right"):
            dim = H0 if side in ("top", "bottom") else W0
            fr_ = np.mean([x[side] > 0.015 * dim for x in bb])
            if fr_ >= 0.5:
                th = int(np.median([x[side] for x in bb]))
                find("Q8", tm, f"{side} bar {th}px ({typ} {nm})", t_end=b_, box=[0, 0, W0, th] if side == "top" else [0, H0 - th, W0, H0] if side == "bottom" else [0, 0, th, H0] if side == "left" else [W0 - th, 0, W0, H0])
    if any(x["bfill"] for x in ss): REP["Q8"].setdefault("blurred_fill", []).append(round(tm, 1))
summ("Q7", f"median Laplacian var {np.median(lapv) if lapv else 0:.0f} over {len(lapv)} shots (warn: < 12 blurry, > 62 % detail surviving 480p round-trip = upscaled)")
summ("Q8", f"bars = uniform black edge >= 1.5 % on half the shot's samples; blurred-fill shots (allowed): {len(REP['Q8'].get('blurred_fill', []))}")

# ------------------------------------------------------------------ Q9 duplicates
def ham(a, b_): return bin(a ^ b_).count("1")
units = []
for a, b_, s in UNITS:
    ss = [x for x in samples_in(a, b_) if x["std"] > 25 and x["mean"] > 30]
    if s and s["type"] in ("card", "map"): continue
    if ss: units.append((a, b_, s, [x["hash"] for x in ss], [x.get("emb") for x in ss]))
dups = 0
for i in range(len(units)):
    for j in range(i + 2, len(units)):
        a1, b1, s1, h1, e1 = units[i]; a2, b2, s2, h2, e2 = units[j]
        if a2 - b1 < 3: continue
        d = min(ham(x, y) for x in h1 for y in h2)
        if d > 40: continue                                    # 256-bit gradient hash: <= 40 differing bits
        cs_ = max((float(x @ y) for x in e1 for y in e2 if x is not None and y is not None), default=None)
        if cs_ is not None and cs_ < 0.95: continue            # and CLIP agrees it is the same picture
        same_src = s1 and s2 and s1.get("src") == s2.get("src")
        intro = a1 < INTRO_END
        if same_src or intro:
            REP["Q9"].setdefault("planned_reuse", []).append({"a": tc(a1), "b": tc(a2), "src": os.path.basename(s1.get("src", "")) if s1 else "", "hamming": d})
            continue
        sev_q9 = "fail" if (cs_ is not None or d <= 26) else "warn"   # hash only (no CLIP): 27-40 bits = different scenes in practice (Yellowstone ch1 review)
        dups += sev_q9 == "fail"
        find("Q9", a2, sev=sev_q9, msg= f"looks like the shot at {tc(a1)} (hash distance {d}/256" + (f", CLIP {cs_:.3f})" if cs_ is not None else ")") + (f": {os.path.basename(s1.get('src', ''))} vs {os.path.basename(s2.get('src', ''))}" if s1 else ""), t_end=b2, other=round(a1, 2))
summ("Q9", f"{len(units)} shots hashed; {dups} unplanned look-alike pairs; planned reuse/intro previews: {len(REP['Q9'].get('planned_reuse', []))}")

# ------------------------------------------------------------------ audio
AUD = os.path.join(A.out, "_a16.wav")
WORDS = []
if AS:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", A.video, "-vn"] + (["-t", str(DUR)] if A.max_dur else []) + ["-ac", "1", "-ar", "16000", AUD])
    r = subprocess.run(["ffmpeg", "-nostats", "-i", A.video, "-vn"] + (["-t", str(DUR)] if A.max_dur else []) + ["-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    summ_ = r[r.rfind("Summary:"):]
    I = re.search(r"I:\s+(-?[\d.]+) LUFS", summ_); TP = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summ_); LRA = re.search(r"LRA:\s+([\d.]+) LU", summ_)
    I = float(I.group(1)) if I else None; TP = float(TP.group(1)) if TP and TP.group(1) != "-inf" else None
    REP["U1"]["measured"] = {"integrated_lufs": I, "true_peak_dbtp": TP, "lra": float(LRA.group(1)) if LRA else None}
    if I is not None and abs(I + 14) > 1: find("U1", 0, f"integrated loudness {I:.1f} LUFS (target -14 +-1)")
    if TP is not None and TP > -1.5: find("U1", 0, f"true peak {TP:.1f} dBTP (limit -1.5)")
    summ("U1", f"I {I} LUFS, TP {TP} dBTP")
    # U3 dead air + clipping
    r = subprocess.run(["ffmpeg", "-nostats", "-i", A.video, "-vn"] + (["-t", str(DUR)] if A.max_dur else []) + ["-af", "silencedetect=noise=-50dB:d=1.5", "-f", "null", "-"], capture_output=True, text=True).stderr
    ss_ = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r)]; se_ = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r)]
    for k_, a in enumerate(ss_):
        b_ = se_[k_] if k_ < len(se_) else DUR
        if a < 0.8 or b_ > DUR - 2.0: continue
        find("U3", a, f"dead air {b_ - a:.1f}s (< -50 dB)", t_end=b_)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", A.video, "-vn"] + (["-t", str(DUR)] if A.max_dur else []) + ["-f", "f32le", "-"], capture_output=True).stdout
    x = np.abs(np.frombuffer(raw, np.float32)); ch = int(AS[0].get("channels", 2)); sr = int(AS[0].get("sample_rate", 48000))
    hot = x >= 0.999
    if hot.any():
        hh = np.flatnonzero(hot); runs = np.split(hh, np.flatnonzero(np.diff(hh) > ch) + 1)
        clipped = [r_ for r_ in runs if len(r_) >= 3 * ch]
        for r_ in clipped[:20]: find("U3", r_[0] / ch / sr, f"clipping: {len(r_) // ch} consecutive full-scale samples")
        REP["U3"]["clipped_runs"] = len(clipped)
    summ("U3", f"silences > 1.5 s at -50 dB: {len([f for f in REP['U3']['findings'] if 'dead' in f['msg']])}; full-scale sample runs: {REP['U3'].get('clipped_runs', 0)}")
    del raw, x
    # whisper
    if "whisper" not in SKIP:
        try:
            from faster_whisper import WhisperModel
            wm = WhisperModel(A.whisper_model, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 2)
            import soundfile as sf
            a16w, _ = sf.read(AUD, dtype="float32")
            segs, info = wm.transcribe(a16w, language="en", word_timestamps=True, vad_filter=False, beam_size=1, condition_on_previous_text=False)
            for sg in segs:
                for w in (sg.words or []): WORDS.append((float(w.start), float(w.end), w.word.strip()))
            log("whisper", len(WORDS), "words")
        except Exception as e: log("whisper unavailable:", e)
else:
    for rid in ("U1", "U2", "U3"): skip(rid, "no audio stream")

# U2 voice over bed (no stems): inside speech regions the loud frames are voice, the troughs between words are the bed.
# p90 - p10 of 20 ms levels in speech regions; calibrated on Episode 1 stems (true voice-music median 18.0 dB -> estimate 19.6 dB)
if WORDS and AS:
    import soundfile as sf
    a16, sr16 = sf.read(AUD, dtype="float32")
    hop = sr16 // 50; n = len(a16) // hop
    db = 20 * np.log10(np.sqrt((a16[: n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-7)
    reg = np.zeros(n, bool)
    for a, b_, w in WORDS: reg[max(0, int(a * 50) - 20): int(b_ * 50) + 21] = True
    for a, b_ in INSERTS: reg[int(a * 50): int(b_ * 50)] = False
    if reg.sum() > 100:
        v = float(np.percentile(db[reg], 90)); bed = float(np.percentile(db[reg], 10)); gap = v - bed
        REP["U2"]["measured"] = {"voice_p90_db": round(v, 1), "bed_p10_db": round(bed, 1), "voice_over_bed_db": round(gap, 1), "method": "estimate (no stems): p90 - p10 of 20 ms levels inside speech regions"}
        if gap < 15: find("U2", 0, f"voice only ~{gap:.1f} dB over the music/ambience bed (target 18; estimate)", sev="warn")
        for w0 in range(0, int(DUR), 30):
            a_, b2 = w0 * 50, (w0 + 30) * 50; r_ = reg[a_:b2]
            if r_.sum() > 500:
                gg = float(np.percentile(db[a_:b2][r_], 90) - np.percentile(db[a_:b2][r_], 10))
                if gg < 12: find("U2", w0, f"voice ~{gg:.1f} dB over bed in {tc(w0)}-{tc(w0 + 30)} (estimate)", sev="warn", t_end=w0 + 30)
        summ("U2", f"estimated voice-over-bed {gap:.1f} dB (no stems; p90-p10 inside speech; Ep1 stems: estimate 19.6 vs true 18.0)")
    else: skip("U2", "not enough speech to estimate")
elif AS: skip("U2", "no stems and no transcript")
# U5 Spanish track
es_streams = [s for s in AS if (s.get("tags", {}) or {}).get("language", "") in ("spa", "es")]
es_dur = None
if es_streams: es_dur = float(es_streams[0].get("duration") or 0)
elif A.es_audio and os.path.exists(A.es_audio):
    es_dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", A.es_audio], capture_output=True, text=True).stdout or 0)
if es_dur is None: skip("U5", "skipped (no input): no Spanish audio stream or --es-audio file")
else:
    if abs(es_dur - DUR) > 0.5: find("U5", 0, f"Spanish track {es_dur:.2f}s vs video {DUR:.2f}s")
    summ("U5", f"Spanish track {es_dur:.2f}s vs video {DUR:.2f}s (chapter-mark alignment not checked)")

# ------------------------------------------------------------------ T1 subtitles
norm = lambda s: re.sub(r"[^a-z0-9']", "", s.lower())
if VERT:
    skip("T1", "vertical: captions are burned in (checked under V2)")
elif not A.srt_dir:
    skip("T1", "skipped (no input): no SRT directory")
else:
    miss = [k for k in LANGS if k not in SRT]
    for k in miss: find("T1", 0, f"missing subtitle track: {k}")
    for k, cues in SRT.items():
        if not cues: find("T1", 0, f"{k}: empty"); continue
        if cues[-1][1] > DUR + 1: find("T1", cues[-1][0], f"{k}: last cue ends at {cues[-1][1]:.1f}s, after the video ({DUR:.1f}s)")
        if EN and abs(cues[-1][1] - EN[-1][1]) > 3: find("T1", cues[-1][0], f"{k}: ends {cues[-1][1] - EN[-1][1]:+.1f}s vs EN", sev="warn")
        if WORDS:
            spk = [(a, b_) for a, b_, w in WORDS if not in_insert(a)]
            cov = np.mean([any(x - 0.3 <= (a + b_) / 2 <= y + 0.3 for x, y, _ in cues) for a, b_ in spk[::3]]) if spk else 1
            REP["T1"].setdefault("coverage", {})[k] = round(float(cov), 3)
            if cov < 0.92: find("T1", 0, f"{k}: only {cov:.0%} of spoken words fall inside a cue", sev="warn")
    if EN and WORDS:
        sw = []; cue_of = []
        for ci, (a, b_, t) in enumerate(EN):
            for k_, w in enumerate(t.split()):
                if norm(w): sw.append(norm(w)); cue_of.append((ci, k_))
        ww = [norm(w) for _, _, w in WORDS]
        sm = difflib.SequenceMatcher(None, sw, ww, autojunk=False)
        first = {}
        for blk in sm.get_matching_blocks():
            for q in range(blk.size):
                ci, k_ = cue_of[blk.a + q]
                if k_ == 0 and ci not in first: first[ci] = WORDS[blk.b + q][0]
        drift = [(EN[ci][0], EN[ci][0] - ws) for ci, ws in first.items() if abs(EN[ci][0] - ws) < 3]
        if drift:
            d_ = np.array([x[1] for x in drift]); ad = np.abs(d_)
            REP["T1"]["drift"] = {"cues_matched": len(drift), "cues": len(EN), "median_abs_s": round(float(np.median(ad)), 3), "p95_abs_s": round(float(np.percentile(ad, 95)), 3),
                                  "median_signed_s": round(float(np.median(d_)), 3), "note": "positive = subtitle appears after the word is spoken"}
            if abs(np.median(d_)) > 0.3: find("T1", 0, f"EN subtitles systematically {np.median(d_):+.2f}s off the voice (limit 0.3)")
            if np.percentile(ad, 95) > 1.0: find("T1", 0, f"EN cue-start error p95 {np.percentile(ad, 95):.2f}s (> 1.0)", sev="warn")
            # local drift: rolling median over 15 cues
            dd = sorted(drift)
            for k_ in range(0, len(dd) - 15, 15):
                w_ = np.array([x[1] for x in dd[k_:k_ + 15]])
                if abs(np.median(w_)) > 0.5: find("T1", dd[k_][0], f"EN subtitles {np.median(w_):+.2f}s off the voice around here", sev="fail", t_end=dd[k_ + 14][0])
            summ("T1", f"{len(SRT)}/6 languages; EN offset (signed median) {np.median(d_):+.2f}s, |error| median {np.median(ad):.2f}s / p95 {np.percentile(ad, 95):.2f}s over {len(drift)}/{len(EN)} cues (whisper word timing ~0.1-0.3 s itself)")
        else: summ("T1", f"{len(SRT)}/6 languages; drift not measurable")
    else: summ("T1", f"{len(SRT)}/6 languages; drift not measured (no transcript)")

# ------------------------------------------------------------------ OCR rules: Q6, T2, O2, V1, V2, V3
ALLOW = ["alphadog studio", "america's national parks", "the hidden history", "now on spotify", "full episode on spotify", "full story on the channel",
         "what happened next", "started 11 years of war"]
if A.allow_text and os.path.exists(A.allow_text): ALLOW += [l.strip().lower() for l in open(A.allow_text) if l.strip()]
for s in SHOTS:
    for k_ in ("label", "title", "kicker", "sub"):
        if s.get(k_): ALLOW.append(str(s[k_]).lower())
ALLOW_N = [norm(x.replace(" ", "")) for x in ALLOW]
SPOKEN = " ".join(t for _, _, t in EN).lower()
def text_ours(txt, t):
    n = norm(txt.replace(" ", "")).replace("'", "")
    if len(n) < 3: return True
    for a in ALLOW_N:
        a = a.replace("'", "")
        if n in a or (len(a) > 3 and difflib.SequenceMatcher(None, n, a).ratio() > 0.8): return True
    if VERT and WORDS:                                         # captions = the words being spoken
        near = norm("".join(w for a, b_, w in WORDS if t - 4 <= a <= t + 4)).replace("'", "")
        if n in near or difflib.SequenceMatcher(None, n, near).find_longest_match(0, len(n), 0, len(near)).size >= 0.6 * len(n): return True
    return False
PRIV = [(r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b", "phone number"), (r"[\w.]+@[\w-]+\.\w+", "e-mail"), (r"\b(driver'?s? licen[cs]e|passport|social security|date of birth|\bdob\b|id card)\b", "ID document"),
        (r"\b\d{2,5}\s+\w+\s+(street|st|avenue|ave|road|rd|drive|dr|lane|ln|blvd|boulevard)\b", "street address"), (r"^(?=.*\d)(?=.*[A-Z])[A-Z0-9]{2,4}[- ]?[A-Z0-9]{3,4}$", "plate-like code")]
SAFE = (170, 400, 910, 1220)
caps = []; cap_match = []; tracked = {}
if ocr is None:
    for rid in ("Q6", "T2", "V1"): REP[rid]["summary"] = (REP[rid]["summary"] + "; " if REP[rid]["summary"] else "") + "OCR unavailable"
for S in SAMPLES:
    if "ocr" not in S: continue
    t = S["t"]; s = shot_at(t)
    typ = s["type"] if s else "?"
    for o in S["ocr"]:
        if o["conf"] < 0.7 or len(norm(o["text"])) < 3: continue
        x0, y0, x1, y1 = o["box"]; bh = y1 - y0; bw = x1 - x0
        txt = o["text"]
        for rx, what in PRIV:
            if re.search(rx, txt, re.I if what != "plate-like code" else 0):
                if what == "plate-like code" and (typ in ("map", "card") or text_ours(txt, t) or re.search(r"(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC|EST|NO)", txt.upper().replace("UULY", "JULY"))): continue
                find("O2", t, f"{what} on screen: '{txt}'", sev="fail" if what != "plate-like code" else "warn", box=o["box"])
        ours = typ in ("map", "card") or text_ours(txt, t)
        overlay = VERT and bh >= 28 and o.get("ov", False)
        if VERT:
            if overlay:
                if not (x0 >= SAFE[0] - 6 and x1 <= SAFE[2] + 6 and y0 >= SAFE[1] - 10 and y1 <= SAFE[3] + 14):
                    find("V1", t, f"burned-in text outside the safe area: '{txt}' box {int(x0)},{int(y0)}-{int(x1)},{int(y1)}", box=o["box"])
                caps.append((t, bh, txt, o["box"]))
                if WORDS: cap_match.append((t, text_ours(txt, t)))
                if not ours: find("Q6", t, f"text not ours (not in captions/titles): '{txt}'", sev="warn", box=o["box"])
            else:
                edge = x1 < SAFE[0] + 40 or x0 > SAFE[2] - 40 or y1 < SAFE[1] or y0 > SAFE[3]
                if edge and not ours: tracked.setdefault((int((x0 + x1) / 2 / (W0 / 6)), int((y0 + y1) / 2 / (H0 / 10))), []).append((t, txt, o["box"]))
                elif not ours: find("Q6", t, f"text in the picture (sign/stamp in source?): '{txt}'", sev="warn", box=o["box"], kind="scene")
            continue
        # long form
        own = [str(x.get(k2)) for x in SHOTS if x["_a"] - 0.5 <= t < x["_b"] + 0.5 for k2 in ("label", "title", "kicker", "sub") if x.get(k2)]
        mine = (typ == "card" or (y0 > 0.82 * H0 and x0 < 0.12 * W0)) and any(len(norm(txt.replace(" ", ""))) >= 3 and (norm(txt.replace(" ", "")) in norm(w.replace(" ", "")) or difflib.SequenceMatcher(None, norm(txt.replace(" ", "")), norm(w.replace(" ", ""))).ratio() > 0.8) for w in own)
        if ours and not mine and typ not in ("map", "card"): continue          # text in the picture that happens to match our words
        if ours:
            if s and typ not in ("map",) and bh < 26: find("T2", t, f"our text small ({bh:.0f}px): '{txt}'", sev="warn", box=o["box"])
            if typ != "map" and (x0 < 0.03 * W0 or x1 > 0.97 * W0 or y0 < 0.03 * H0 or y1 > 0.97 * H0): find("T2", t, f"our text outside title-safe: '{txt}'", box=o["box"])
            continue
        edge = (x1 < 0.25 * W0 or x0 > 0.75 * W0) and (y1 < 0.22 * H0 or y0 > 0.78 * H0)
        capl = y0 > 0.70 * H0 and abs((x0 + x1) / 2 - W0 / 2) < 0.15 * W0 and bw > 0.2 * W0
        key_ = (int((x0 + x1) / 2 / (W0 / 8)), int((y0 + y1) / 2 / (H0 / 8)))
        if capl: find("Q6", t, f"burned-in caption/name strap from a source? '{txt}'", box=o["box"], kind="caption", sev="fail" if typ in ("video", "?") else "warn")
        elif edge: tracked.setdefault(key_, []).append((t, txt, o["box"]))
        else: find("Q6", t, f"text in the picture (sign/document/title in source?): '{txt}'", sev="warn", box=o["box"], kind="scene")
for key_, L in tracked.items():                           # corner text seen in >= 2 samples of one shot = watermark/bug
    L.sort(); grp = [L[0]]
    def flush(g):
        if len(g) >= 2 or (len(g) == 1 and len(norm(g[0][1])) >= 6):
            s0 = shot_at(g[0][0]); bx = g[0][2]
            cx = [(x[2][0] + x[2][2]) / 2 for x in g]; cy = [(x[2][1] + x[2][3]) / 2 for x in g]
            still = max(cx) - min(cx) < 0.015 * W0 and max(cy) - min(cy) < 0.015 * H0                       # a watermark does not move with the picture
            hard = len(g) >= 2 and still and (s0 is None or s0["type"] == "video") and (bx[3] - bx[1]) < 0.06 * H0
            find("Q6", g[0][0], f"edge text seen {len(g)}x (watermark/stamp/channel bug?): '{g[0][1]}'", sev="fail" if hard else "warn", box=bx, t_end=g[-1][0], kind="watermark")
    for x in L[1:]:
        if x[0] - grp[-1][0] <= max(OCR_EVERY, 1 / SFPS) * 1.6 and seg_of(x[0]) == seg_of(grp[-1][0]): grp.append(x)
        else: flush(grp); grp = [x]
    flush(grp)
# T2: every planned label/title read back from the picture
if SHOTS and ocr is not None:
    for s in SHOTS:
        want = s.get("label") or (s.get("title") if s["type"] == "card" else None)
        if not want: continue
        got = [o["text"] for S in samples_in(s["_a"], s["_b"], 0.4) if "ocr" in S for o in S["ocr"] if o["conf"] > 0.6]
        if not got: continue                                   # not sampled (OCR every few s) - no verdict
        best = max(difflib.SequenceMatcher(None, norm(want.replace(" ", "")), norm(g.replace(" ", ""))).ratio() for g in got)
        if best < 0.85:
            joined = norm("".join(got)); r2 = difflib.SequenceMatcher(None, norm(want.replace(" ", "")), joined).find_longest_match(0, len(norm(want.replace(" ", ""))), 0, len(joined)).size / max(1, len(norm(want.replace(" ", ""))))
            if r2 < 0.85: find("T2", (s["_a"] + s["_b"]) / 2, f"planned text '{want}' read as {got[:3]} (match {max(best, r2):.0%})", sev="warn")
if VERT:
    if W0 != 1080 or H0 != 1920: find("V1", 0, f"resolution {W0}x{H0} (want 1080x1920)")
    summ("V1", f"{len(caps)} burned-in text boxes checked against x 170-910, y 400-1220")
    if DUR >= 60: find("V2", DUR, f"duration {DUR:.2f}s (YouTube Shorts need < 60 s)")
    # font size from OCR box height: all-caps boxes ~0.74 x font size, mixed case (ascenders/descenders) ~0.84 x
    fe = [(c[0], c[1] / (0.74 if not re.search(r"[a-z]", c[2]) else 0.84), c[2], c[3]) for c in caps]
    hs = [x[1] for x in fe]
    if hs:
        med = float(np.median(hs)); REP["V2"]["caption_font_px_est"] = {"median": round(med, 1), "p10": round(float(np.percentile(hs, 10)), 1), "min": round(min(hs), 1)}
        if med < 58: find("V2", 0, f"captions small: estimated font {med:.0f}px (rule >= 58 px)")
        for c in [x for x in fe if x[1] < 52][:10]: find("V2", c[0], f"small text: est. font {c[1]:.0f}px: '{c[2]}'", sev="warn", box=c[3])
    if cap_match:
        rate = float(np.mean([m_ for _, m_ in cap_match])); REP["V2"]["captions_match_voice"] = round(rate, 3)
        if rate < 0.7: find("V2", 0, f"only {rate:.0%} of caption samples match the words spoken within +-2.5 s", sev="warn")
    hook = (WORDS and WORDS[0][0] < 1.5) or any(S["t"] < 1.5 and S.get("ocr") for S in SAMPLES)
    if not hook: find("V2", 0, "nothing said or shown as text in the first 1.5 s (hook)", sev="warn")
    summ("V2", f"duration {DUR:.2f}s; caption font est. median {REP['V2'].get('caption_font_px_est', {}).get('median')}px; captions match voice {REP['V2'].get('captions_match_voice')}")
    # V3 faces vs caption boxes
    nf = 0
    for S in SAMPLES:
        if not S.get("faces") or "ocr" not in S: continue
        for fb in S["faces"]:
            if fb[4] < 0.75: continue
            nf += 1; fa = (fb[2] - fb[0]) * (fb[3] - fb[1])
            for o in S["ocr"]:
                x0, y0, x1, y1 = o["box"]
                if y1 - y0 < 28 or o["conf"] < 0.7 or not o.get("ov"): continue
                iw = max(0, min(x1, fb[2]) - max(x0, fb[0])); ih = max(0, min(y1, fb[3]) - max(y0, fb[1]))
                if fa > 0 and iw * ih / fa > 0.15:
                    find("V3", S["t"], f"burned-in text covers a face: '{o['text']}' ({iw * ih / fa:.0%} of the face)", box=[fb[0], fb[1], fb[2], fb[3]])
    summ("V3", f"{nf} faces checked against caption boxes" + ("" if face is not None else " (no face detector)"))
else:
    for rid in ("V1", "V2", "V3"): skip(rid, "long-form video (vertical rules n/a)")
    summ("Q6", f"OCR every {OCR_EVERY:g}s; corner logo scan every 1 s")
    summ("T2", "our labels/titles read back and checked for size (>= 26 px) and title-safe area")
# O2 close-up faces in real footage (long form)
if not VERT and face is not None:
    for S in SAMPLES:
        s = shot_at(S["t"])
        if not S.get("faces") or (s and (s["type"] != "video" or s.get("ai"))) or in_insert(S["t"]): continue
        for fb in S["faces"]:
            fa = (fb[2] - fb[0]) * (fb[3] - fb[1]) / (W0 * H0)
            if fb[4] >= 0.85 and fa > 0.04: find("O2", S["t"], f"close-up face ({fa:.0%} of frame) in source footage - stranger?", sev="warn", box=fb[:4])

# ------------------------------------------------------------------ F3 crop/upscale, F5 first shot, F6 end card, F7 card text, F8 background speech
def ocr_img(im):
    if ocr is None: return []
    osc = 1280 / max(im.shape[1], im.shape[0])
    oim = cv2.resize(im, (int(im.shape[1] * osc), int(im.shape[0] * osc)), interpolation=cv2.INTER_AREA) if osc < 1 else im
    osc = min(osc, 1.0)
    try: res, _ = ocr(oim)
    except Exception: res = None
    return [{"box": [float(min(q[0] for q in r_[0])) / osc, float(min(q[1] for q in r_[0])) / osc, float(max(q[0] for q in r_[0])) / osc, float(max(q[1] for q in r_[0])) / osc],
             "text": r_[1], "conf": float(r_[2])} for r_ in (res or [])]
def sample_ocr(S):
    if "ocr" not in S and S.get("jpg") and os.path.exists(S["jpg"]):
        im = cv2.imread(S["jpg"]); S["ocr"] = ocr_img(im) if im is not None else []
    return S.get("ocr", [])
# ---- F3 crop / upscale from the shot list's source geometry
_geo = {}
def src_dims(x):
    if x.get("src_w") and x.get("src_h"): return int(x["src_w"]), int(x["src_h"])
    pth = str(x.get("src", ""))
    if not pth or not os.path.exists(pth): return None
    if pth not in _geo:
        try:
            q = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:stream_side_data=rotation:stream_tags=rotate",
                                           "-of", "json", pth], capture_output=True, text=True).stdout)["streams"][0]
            w_, h_ = int(q["width"]), int(q["height"]); rot = int(float((q.get("tags") or {}).get("rotate", 0) or 0))
            for sd in q.get("side_data_list", []) or []:
                if "rotation" in sd: rot = int(float(sd["rotation"]))
            _geo[pth] = (h_, w_) if abs(rot) % 180 == 90 else (w_, h_)
        except Exception: _geo[pth] = None
    return _geo[pth]
F3_LIM = 1.35; f3_known = 0; f3_unknown = 0; F3_SHOT = {}
for s in SHOTS:
    t_ = s.get("type")
    if s["_a"] >= DUR: continue
    if t_ not in ("video", "photo", "multi") or s.get("_kind") in ("card", "graphic", "map"): continue
    parts = []
    if t_ == "multi":
        n_ = max(1, len(s.get("srcs", []))); ph = H0 - 28
        pw = min((W0 - 14 * (n_ + 1)) // n_, int(ph * 9 / 16) // 2 * 2)   # engine geometry: panels never wider than 9:16
        for x in s.get("srcs", []):
            dm = src_dims(x)
            if dm: cov = max(pw / dm[0], ph / dm[1]); con = min(pw / dm[0], ph / dm[1]); parts.append((dm, cov / con, cov))
    else:
        dm = src_dims(s)
        if dm:
            cov = max(W0 / dm[0], H0 / dm[1]); con = min(W0 / dm[0], H0 / dm[1])
            zm_ = float(s.get("zoom", 1.0) or 1.0)   # static framing zoom: crops away (1 - 1/zoom) of the frame
            if t_ == "video": parts.append((dm, cov / con * zm_, cov * zm_ * (1 + float(s.get("drift", 0.035) or 0))))
            elif s.get("bg", "cover") == "cover": parts.append((dm, cov / con, cov * max(float(s.get("z0", 1.0)), float(s.get("z1", 1.12)))))
            else: parts.append((dm, 1.0, con * max(float(s.get("z0", 1.0)), float(s.get("z1", 1.12)))))
    if not parts: f3_unknown += 1; continue
    f3_known += 1
    dm, crop, up = max(parts, key=lambda p_: (p_[1], p_[2]))
    F3_SHOT[s["_i"]] = (crop, up)
    tm = (s["_a"] + s["_b"]) / 2; nm = unit_name(s, s["_a"])
    portrait_in_land = dm[1] > 1.05 * dm[0] and W0 > H0 and t_ != "multi"
    msg = None; sev_ = "fail"
    if portrait_in_land and crop > F3_LIM: msg = f"vertical {dm[0]}x{dm[1]} clip cropped to 16:9: only {1 / crop:.0%} of its frame shown, upscaled {up:.2f}x ({nm})"
    elif crop > F3_LIM: msg = f"over-cropped: only {1 / crop:.0%} of the {dm[0]}x{dm[1]} source shown, upscaled {up:.2f}x ({nm})"
    elif up > F3_LIM and crop > 1.1: msg = f"crop upscaled {up:.2f}x (limit {F3_LIM}) from {dm[0]}x{dm[1]} ({nm})"
    elif up > F3_LIM: msg = f"low-res {dm[0]}x{dm[1]} source upscaled {up:.2f}x (full frame, not a crop) ({nm})"; sev_ = "warn"
    if msg: find("F3", tm, msg, sev=sev_, t_end=s["_b"], upscale=round(up, 2), crop=round(crop, 2), src=f"{dm[0]}x{dm[1]}", shot=s["_i"])
summ("F3", f"crop zoom (source frame cut away) / upscale vs {W0}x{H0} for {f3_known} planned shots with known source size ({f3_unknown} unknown); "
           f"fail: crop > {F3_LIM} or cropped+upscaled > {F3_LIM}; warn: full-frame low-res upscale, soft frames ({REP['F3'].get('soft_shots', 0)} shots)")
# ---- F5 first shot
if SEG:
    a0, b0 = SEG[0]; s0 = SHOTS[0] if SHOTS else None
    if s0 is not None: b0 = max(b0, s0["_b"]) if abs(s0["_b"] - b0) < 0.3 else b0
    why = []
    if b0 - a0 < 4.0: why.append(f"only {b0 - a0:.1f}s on screen (>= 4 s)")
    ss0 = [x for x in samples_in(a0, b0) if x["mean"] > 20]
    lap_all = [float(np.median([x["lap"] for x in samples_in(a, b_)])) for a, b_, s in MUNITS if samples_in(a, b_)]
    if ss0 and lap_all:
        l0 = float(np.median([x["lap"] for x in ss0])); lm_ = float(np.median(lap_all))
        if l0 < 0.6 * lm_: why.append(f"soft: sharpness {l0:.0f} vs episode median {lm_:.0f}")
    if s0 is not None and s0["_i"] in F3_SHOT and (F3_SHOT[s0["_i"]][0] > F3_LIM or F3_SHOT[s0["_i"]][1] > F3_LIM): why.append(f"cropped/upscaled {F3_SHOT[s0['_i']][1]:.2f}x")
    for rid_, what in (("F4", "fast camera move"), ("F1", "stutter"), ("F2", "freeze"), ("Q2", "shaky")):
        if any(f["t"] < b0 - 0.05 and f["sev"] in ("fail", "warn") for f in REP[rid_]["findings"]): why.append(what)
    if s0 is not None and not is_moving_plan(s0): why.append(f"opens on a {s0.get('_kind', s0.get('type'))}, not footage")
    if why: find("F5", min(a0 + 1.0, (a0 + b0) / 2), "first shot weak: " + "; ".join(why), sev="warn", t_end=b0)
    summ("F5", f"first shot {a0:.2f}-{b0:.2f}s ({b0 - a0:.1f}s): needs >= 4 s, sharp (>= 60 % of episode median), calm (no F4/F1/F2/Q2), not over-cropped")
else: skip("F5", "no shots detected")
# ---- F6 end card
CH_N = norm(A.channel_name.replace(" ", ""))
ws = max(0.0, DUR - 20.0)
if SHOTS and "end" in os.path.basename(str(SHOTS[-1].get("src", ""))).lower(): ws = max(ws, SHOTS[-1]["_a"])
es = [S for S in SAMPLES if ws <= S["t"] <= DUR - 0.3 and S["mean"] > 15 and S.get("jpg")]
es = [es[int(round(k))] for k in np.linspace(0, len(es) - 1, min(6, len(es)))] if es else []
LOGO = None
if A.logo and os.path.exists(A.logo):
    LOGO = cv2.imread(A.logo)
def logo_score(im):
    g_ = cv2.resize(im, (960, int(960 * H0 / W0)), interpolation=cv2.INTER_AREA); best = (-1.0, None)
    for sz in np.geomspace(50, min(g_.shape[:2]) * 0.8, 24):
        sz = int(sz); t_ = cv2.resize(LOGO, (sz, sz), interpolation=cv2.INTER_AREA); c_ = int(sz * 0.18); t_ = t_[c_:sz - c_, c_:sz - c_]
        if t_.shape[0] >= g_.shape[0] or t_.shape[1] >= g_.shape[1]: continue
        r_ = cv2.matchTemplate(g_, t_, cv2.TM_CCOEFF_NORMED); _, mx, _, loc = cv2.minMaxLoc(r_)
        if mx > best[0]: k_ = W0 / 960; best = (float(mx), [loc[0] * k_ - c_ * k_, loc[1] * k_ - c_ * k_, (loc[0] + sz - c_) * k_, (loc[1] + sz - c_) * k_])
    return best
def next_box(im, oc):
    sc_ = 960 / W0; g_ = cv2.cvtColor(cv2.resize(im, (960, int(H0 * sc_)), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    ed = cv2.dilate(cv2.Canny(g_, 30, 90), np.ones((3, 3), np.uint8))
    cs_, _ = cv2.findContours(ed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE); best = None
    for c_ in cs_:
        x, y, w_, h_ = cv2.boundingRect(c_); fa = w_ * h_ / (g_.shape[0] * g_.shape[1])
        if not (0.05 <= fa <= 0.5 and 1.3 <= w_ / max(1, h_) <= 2.2): continue
        ap_ = cv2.approxPolyDP(c_, 0.02 * cv2.arcLength(c_, True), True)
        if len(ap_) != 4 or cv2.contourArea(c_) < 0.8 * w_ * h_: continue
        if best is None or w_ * h_ > best[2] * best[3]: best = (x, y, w_, h_)
    if best is None: return None
    x, y, w_, h_ = best; ix, iy = int(w_ * 0.05) + 3, int(h_ * 0.05) + 3
    inner = g_[y + iy:y + h_ - iy, x + ix:x + w_ - ix].astype(np.float32); m_ = np.ones(inner.shape, bool); txt = []
    for o in oc:                                              # text inside the slot does not count as an image
        bx = [v * sc_ for v in o["box"]]
        if bx[0] >= x and bx[2] <= x + w_ and bx[1] >= y and bx[3] <= y + h_:
            txt.append(o["text"]); m_[max(0, int(bx[1]) - y - iy - 4):max(0, int(bx[3]) - y - iy + 4), max(0, int(bx[0]) - x - ix - 4):max(0, int(bx[2]) - x - ix + 4)] = False
    if m_.sum() < 100: return None
    eds = cv2.Canny(inner.astype(np.uint8), 30, 90) > 0
    return {"box": [x / sc_, y / sc_, (x + w_) / sc_, (y + h_) / sc_], "std": float(inner[m_].std()), "edges": float(eds[m_].mean()), "text": txt}
if not es: skip("F6", "no end-card samples")
else:
    name_hits = 0; lg = []; boxes = []
    for S in es:
        im = cv2.imread(S["jpg"])
        if im is None: continue
        oc = sample_ocr(S)
        if any(CH_N in norm(o["text"].replace(" ", "")) or (len(norm(o["text"])) >= 8 and difflib.SequenceMatcher(None, norm(o["text"].replace(" ", "")), CH_N).ratio() > 0.85) for o in oc): name_hits += 1
        if LOGO is not None: lg.append((logo_score(im), S["t"]))
        nb = next_box(im, oc)
        if nb: nb["t"] = S["t"]; boxes.append(nb)
    REP["F6"]["measured"] = {"window_s": [round(ws, 1), round(DUR, 1)], "samples": len(es), "name_hits": name_hits,
                             "logo_best": round(max((x[0][0] for x in lg), default=-1), 3) if lg else None,
                             "next_slot": [{"t": round(b["t"], 1), "std": round(b["std"], 1), "edges": round(b["edges"], 3), "text": b["text"]} for b in boxes]}
    if ocr is not None and name_hits == 0: find("F6", es[len(es) // 2]["t"], f"channel name '{A.channel_name}' not found on the end card (OCR)")
    if lg:
        (sc_, bx_), tl_ = max(lg, key=lambda x: x[0][0])
        if sc_ < 0.55: find("F6", tl_, f"owner logo not on the end card (best template match {sc_:.2f}; want >= 0.75)")
        elif sc_ < 0.75: find("F6", tl_, f"logo differs from the owner logo (template match {sc_:.2f}; want >= 0.75)", sev="warn", box=bx_)
    if not boxes: find("F6", es[len(es) // 2]["t"], "no next-video frame found on the end card", sev="warn")
    else:
        empty = [b for b in boxes if b["std"] < 12 and b["edges"] < 0.02]
        if len(empty) * 2 >= len(boxes):
            b = empty[0]; ph_ = [x for x in b["text"] if "next" in x.lower()]
            find("F6", b["t"], f"next-video slot is empty: flat box (luma std {b['std']:.1f}, edges {b['edges']:.1%})" + (f" with placeholder text '{ph_[0]}'" if ph_ else ""), box=b["box"])
    summ("F6", f"end card {ws:.1f}-{DUR:.1f}s, {len(es)} samples: name '{A.channel_name}' read in {name_hits}; logo match "
               f"{REP['F6']['measured']['logo_best']}; next slot found in {len(boxes)} (empty = luma std < 12 and edge density < 2 %)")
# ---- F7 chapter cards: name only, no 'CHAPTER ONE' numbering
NUMW = r"(?:ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN|TWENTY|FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|LAST|\d{1,2}|X{0,2}(?:IX|IV|V?I{1,3}|V))"
CHAP_RX = re.compile(r"CHAPTER\s*[-:.#]?\s*" + NUMW + r"\b")
cards = [(s["_a"], s["_b"]) for s in SHOTS if s.get("_kind") == "card" or s.get("type") == "card"] + \
        [(float(x["start"]), float(x["start"]) + float(x["dur"])) for x in TL if x.get("kind") in ("card", "title")]
cards = sorted(set((round(a, 1), round(b_, 1)) for a, b_ in cards))
f7_seen = 0; f7_hit = set()
def f7_check(S, where, key_=None):
    oc = [o for o in sample_ocr(S) if o["conf"] > 0.5]
    joined = " ".join(o["text"] for o in sorted(oc, key=lambda o: (round(o["box"][1] / 40), o["box"][0]))).upper()
    m_ = CHAP_RX.search(joined)
    if m_:
        bx = next((o["box"] for o in oc if "CHAPTER" in o["text"].upper()), None)
        key_ = key_ if key_ is not None else round(S["t"] / 3)
        if key_ not in f7_hit:
            f7_hit.add(key_); find("F7", S["t"], f"chapter numbering on {where}: '{m_.group(0)}' (chapter cards show the name only)", box=bx, text=m_.group(0))
if ocr is None: skip("F7", "OCR unavailable")
else:
    for a, b_ in cards:
        for S in samples_in(a, b_, 0.3): f7_seen += 1; f7_check(S, f"card {tc(a)}", ("card", round(a)))
    for S in SAMPLES:                                         # any other on-screen text sampled for OCR
        if "ocr" in S and not any(a - 0.3 <= S["t"] <= b_ + 0.3 for a, b_ in cards): f7_check(S, "screen text")
    summ("F7", f"{len(cards)} card/title intervals, {f7_seen} card frames OCR'd + all OCR samples; pattern CHAPTER + number word/digit/roman")
# ---- F8 people talking in the background
VADM = None
try:
    from faster_whisper.vad import get_vad_model
    VADM = get_vad_model()
except Exception as e: log("silero VAD unavailable:", e)
def load16(pth, ss=0.0, dur=None):
    cmd_ = ["ffmpeg", "-v", "error", "-ss", f"{ss:.3f}"] + (["-t", f"{dur:.3f}"] if dur else []) + ["-i", pth, "-vn", "-ac", "1", "-ar", "16000", "-af", "highpass=f=100", "-f", "s16le", "-"]
    return np.frombuffer(subprocess.run(cmd_, capture_output=True).stdout, np.int16).astype(np.float32) / 32768
def speech_prob(x):
    """per 32 ms speech probability; quiet beds are levelled per 1 s (<= +40 dB) so distant voices are not missed"""
    if len(x) < 1600: return np.zeros(0), 0.032
    y = x.copy()
    for i in range(0, len(x), 16000):
        r_ = float(np.sqrt((x[i:i + 16000] ** 2).mean()))
        if r_ > 3e-4: y[i:i + 16000] *= min(100.0, 0.1 / r_)
    y = np.clip(y, -1, 1)
    if VADM is not None:
        return np.asarray(VADM(np.pad(y, (0, 512 - len(y) % 512)))).flatten(), 0.032
    import webrtcvad
    v_ = webrtcvad.Vad(3); pcm = (y * 32767).astype(np.int16); n_ = len(pcm) // 480
    return np.array([1.0 if v_.is_speech(pcm[i * 480:(i + 1) * 480].tobytes(), 16000) else 0.0 for i in range(n_)]), 0.03
def speech_runs(pp, hop, allow=None, min_len=0.5):
    if len(pp) == 0: return []
    if allow is not None: pp = np.where(allow[:len(pp)], pp, 0.0)
    th_m, th_p = (0.2, 0.45) if VADM is not None else (0.85, 1.0)   # webrtcvad fallback fires on wind/water: strict
    w_ = np.convolve(pp, np.ones(31) / 31, "same"); on = w_ > th_m; out = []; k = 0
    while k < len(on):
        if not on[k]: k += 1; continue
        e_ = k
        while e_ < len(on) and on[e_]: e_ += 1
        if (e_ - k) * hop >= min_len and pp[k:e_].max() >= th_p: out.append((k * hop, e_ * hop, float(pp[k:e_].max())))
        k = e_
    return out
f8 = []
vad_name = "silero" if VADM is not None else "webrtcvad (fallback)"
sev8 = "fail" if VADM is not None else "warn"
try:
    if A.stems:
        for stn in ("stem_amb.wav", "stem_sfx.wav"):
            pth = os.path.join(A.stems, stn)
            if not os.path.exists(pth): continue
            pp, hop = speech_prob(load16(pth)); rr = speech_runs(pp, hop); f8.append(f"{stn}: {len(rr)} speech runs")
            for a, b_, pk in rr:
                s = shot_at((a + b_) / 2)
                find("F8", a, f"people talking in {stn} {a:.1f}-{b_:.1f}s (VAD peak {pk:.2f})" + (f" - natural sound of {unit_name(s, a)}" if s else ""), sev=sev8, t_end=b_, source=stn)
    if AS and os.path.exists(AUD):
        x16 = load16(AUD); pp, hop = speech_prob(x16)
        exp_ = np.zeros(len(pp), bool); how = ""
        if A.voice_mask and os.path.exists(A.voice_mask):
            vm = np.load(A.voice_mask).astype(bool); ti = np.clip((np.arange(len(pp)) * hop * 100).astype(int), 0, len(vm) - 1); exp_ = vm[ti]; how = "voice mask"
        elif WORDS:
            for a, b_, w in WORDS: exp_[max(0, int((a - 0.6) / hop)):int((b_ + 0.6) / hop)] = True
            how = "whisper words +-0.6 s"
        else:
            for x in TL:
                if x.get("kind") == "seg": exp_[max(0, int(float(x["start"]) / hop)):int((float(x["start"]) + float(x["dur"])) / hop)] = True
            how = "timeline narration spans (coarse)"
        for a, b_ in INSERTS: exp_[max(0, int(a / hop)):int(b_ / hop) + 1] = True
        dil = int(0.3 / hop)
        exp_ = np.convolve(exp_.astype(float), np.ones(2 * dil + 1), "same") > 0
        rr = speech_runs(pp, hop, allow=~exp_); f8.append(f"final mix outside planned voice ({how}, {float((~exp_).mean()) * len(pp) * hop:.0f}s): {len(rr)} speech runs")
        for a, b_, pk in rr: find("F8", a, f"speech in the final mix where no narration/interview is planned {a:.1f}-{b_:.1f}s (VAD peak {pk:.2f})", sev=sev8, t_end=b_, source="mix")
    nb_ = 0
    for s in SHOTS:                                          # natural sound files of own clips, when present (builder machine)
        amb = s.get("amb")
        if not amb or not os.path.exists(str(amb)) or s["_a"] >= DUR: continue
        nb_ += 1; d_ = (s["_b"] - s["_a"]) * float(s.get("speed", 1) or 1)
        pp, hop = speech_prob(load16(amb, 0.0, d_ + 0.1))
        for a, b_, pk in speech_runs(pp, hop, min_len=0.4):
            find("F8", s["_a"] + a, f"people talking in the natural sound of {unit_name(s, s['_a'])} (+{a:.1f}-{b_:.1f}s, VAD peak {pk:.2f}, gain {s.get('amb_g', 0)} dB)",
                 sev=sev8, t_end=s["_a"] + b_, source=os.path.basename(str(amb)))
    if nb_: f8.append(f"{nb_} shot ambience files")
    summ("F8", f"{vad_name} VAD (levelled, 1 s mean > 0.2, peak > 0.45, >= 0.5 s): " + "; ".join(f8) + ("" if A.stems else "; no --stems: speech under narration is not detectable in the mix"))
except Exception as e:
    skip("F8", f"failed: {e}")

# ------------------------------------------------------------------ CLIP: P2, A4, O2 objects
if clip is not None and any("emb" in S for S in SAMPLES):
    torch, model, prep, tok = clip
    def tenc(txts):
        with torch.no_grad():
            e_ = model.encode_text(tok(txts)); return (e_ / e_.norm(dim=-1, keepdim=True)).numpy()
    # P2
    if EN and not VERT:
        rows = []
        for a, b_, s in UNITS:
            if s and s["type"] in ("card", "map"): continue
            ss = [x for x in samples_in(a, b_) if "emb" in x and x["mean"] > 25]
            txt = narration_at(a, b_)
            if not ss or not txt: continue
            S = ss[len(ss) // 2]; rows.append((S["t"], a, b_, txt, S["emb"], s))
        if rows:
            te = tenc([r_[3][:300] for r_ in rows]); sims = np.array([float(r_[4] @ te[k_]) for k_, r_ in enumerate(rows)])
            floor = float(np.percentile(sims, 5)); REP["P2"]["measured"] = {"shots": len(rows), "median": round(float(np.median(sims)), 3), "p5": round(floor, 3)}
            for k_ in np.argsort(sims)[: max(1, int(math.ceil(len(rows) * 0.05)))]:
                t, a, b_, txt, _, s = rows[k_]
                find("P2", t, f"sim {sims[k_]:.3f}: \"{txt[:90]}\"" + (f" | {os.path.basename(s.get('src', ''))}" if s else ""), sev="warn", t_end=b_, sim=round(float(sims[k_]), 3))
            summ("P2", f"CLIP ViT-B/32 frame-vs-narration, median {np.median(sims):.3f}; lowest 5 % (<= {floor:.3f}) listed for review")
    elif VERT and WORDS:
        rows = []
        for a, b_ in SEG:
            ss = [x for x in samples_in(a, b_) if "emb" in x]
            txt = " ".join(w for x, y, w in WORDS if y > a and x < b_)
            if ss and txt: rows.append((ss[len(ss) // 2]["t"], a, b_, txt, ss[len(ss) // 2]["emb"]))
        if rows:
            te = tenc([r_[3][:300] for r_ in rows]); sims = np.array([float(r_[4] @ te[k_]) for k_, r_ in enumerate(rows)])
            for k_ in np.argsort(sims)[: max(1, int(math.ceil(len(rows) * 0.05)))]:
                find("P2", rows[k_][0], f"sim {sims[k_]:.3f}: \"{rows[k_][3][:90]}\"", sev="warn", t_end=rows[k_][2], sim=round(float(sims[k_]), 3))
            REP["P2"]["measured"] = {"shots": len(rows), "median": round(float(np.median(sims)), 3)}
            summ("P2", f"CLIP frame-vs-spoken words per shot, median {np.median(sims):.3f}; lowest 5 % listed")
    else: skip("P2", "no narration text (SRT/transcript)")
    # A4
    ART = ["an AI image with garbled unreadable text", "a person with deformed hands", "a hand with extra fingers", "a distorted melted face",
           "a person with extra limbs", "a glitchy morphing AI artifact"]
    OK = ["a photo of a person", "a person's hands", "a face", "a landscape", "a horse", "a cowboy", "a historical photograph", "an illustration of a person",
          "a building", "text on a sign", "a mountain", "a soldier", "a group of people", "a night scene", "a campfire", "a forest", "rocks"]
    te = tenc(ART + OK); scores = []
    for S in SAMPLES:
        if "emb" not in S: continue
        s = shot_at(S["t"])
        if (SHOTS and not (s and s.get("ai"))) or S["mean"] < 25: continue
        lg = 100 * (te @ S["emb"]); pr_ = np.exp(lg - lg.max()); pr_ /= pr_.sum(); pa_ = float(pr_[: len(ART)].sum())
        scores.append((pa_, S["t"], ART[int(np.argmax(pr_[: len(ART)]))]))
    scores.sort(reverse=True)
    for pa_, t, what in [x for x in scores if x[0] > 0.8][:10]: find("A4", t, f"{what} (p {pa_:.2f})", sev="warn", p=round(pa_, 2))
    summ("A4", f"CLIP zero-shot on {len(scores)} {'AI-shot ' if SHOTS else ''}frames (text boxes blurred out); p(artifact) > 0.8 listed (max 10)")
    # O2 objects
    PO = ["a photo of an ID card", "a driver's license", "a passport page", "a car license plate", "a computer screen showing a website", "a smartphone screen", "a paper document with printed text", "a house number and street sign"]
    NO = ["a landscape", "mountains", "a desert", "a historical photograph", "a person", "rock formations", "a forest", "a map", "a title card with text", "a old newspaper page", "a cowboy", "a horse", "a sky", "a gravestone", "a sign on an old wooden building", "a historic town street"]
    te = tenc(PO + NO); hits = 0
    for S in SAMPLES:
        if "emb" not in S: continue
        s = shot_at(S["t"])
        if s and (s["type"] in ("card", "map", "photo") or s.get("ai")): continue   # archive stills / our AI scenes are not privacy risks
        lg = 100 * (te @ S["emb"]); pr_ = np.exp(lg - lg.max()); pr_ /= pr_.sum(); k_ = int(np.argmax(pr_))
        if k_ < len(PO) and pr_[k_] > 0.5: hits += 1; find("O2", S["t"], f"{PO[k_]}? (CLIP p {pr_[k_]:.2f})", sev="warn")
    summ("O2", f"OCR patterns (phone/e-mail/address/ID/plate) + CLIP object scan ({hits} hits) + close-up faces in source footage")
else:
    skip("P2", "CLIP unavailable"); skip("A4", "CLIP unavailable")
    REP["O2"]["summary"] = "OCR patterns + faces only (CLIP unavailable)"

# ------------------------------------------------------------------ dedupe noisy findings, statuses
for rid, r in REP.items():
    last = {}; out = []
    for f in sorted(r["findings"], key=lambda f: f["t"]):
        k_ = (re.sub(r"[\d.,%]+", "#", f["msg"]), f["sev"])
        if rid not in ("R7", "Q1", "P2", "F1", "F3", "F4", "F5", "F6", "F7") and k_ in last and f["t"] - last[k_][1] <= 1.6:
            kept = last[k_][0]; kept["t_end"] = max(kept.get("t_end", kept["t"]), f.get("t_end", f["t"])); kept["n"] = kept.get("n", 1) + 1
            last[k_] = (kept, f["t"]); continue
        last[k_] = (f, f["t"]); out.append(f)
    r["findings"] = out
    if r["status"] == "skipped": continue
    sev = set(f["sev"] for f in out)
    if "fail" in sev: r["status"] = "fail" if r["check"] == "auto" else "warn"
    elif "warn" in sev: r["status"] = "warn"
    else: r["status"] = "pass"

# ------------------------------------------------------------------ contact sheets
from PIL import ImageDraw, ImageFont
def grab(t):
    t = min(max(0.0, t), DUR - 0.05)
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", A.video, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    if len(r) < W0 * H0 * 3: return Image.new("RGB", (W0, H0))
    return Image.fromarray(np.frombuffer(r[: W0 * H0 * 3], np.uint8).reshape(H0, W0, 3))
try: FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15); FONT_S = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
except Exception: FONT = FONT_S = ImageFont.load_default()
TW = 270 if VERT else 480; TH = int(TW * H0 / W0)
def tile(f, rid, t, note=""):
    im = grab(t); sx = TW / W0
    d = ImageDraw.Draw(im)
    if f.get("box"):
        x0, y0, x1, y1 = f["box"]; d.rectangle([x0, y0, x1, y1], outline=(255, 40, 40), width=max(3, W0 // 300))
    if VERT and rid in ("V1", "V3", "V2"): d.rectangle(SAFE, outline=(40, 255, 80), width=3)
    im = im.resize((TW, TH)); c = Image.new("RGB", (TW, TH + 40), (20, 20, 20)); c.paste(im, (0, 0)); d = ImageDraw.Draw(c)
    col = (255, 80, 80) if f["sev"] == "fail" else (255, 200, 60) if f["sev"] == "warn" else (150, 200, 255)
    d.text((4, TH + 2), f"{rid} {tc(t)} {note}", fill=col, font=FONT); d.text((4, TH + 21), f["msg"][:70 if not VERT else 40], fill=(230, 230, 230), font=FONT_S)
    return c
SHEETS = []
for rid, r in REP.items():
    fl = [f for f in r["findings"] if f["sev"] in ("fail", "warn")]
    if not fl: continue
    tiles = []
    for f in fl[:32]:
        if rid in ("Q1",):
            tiles += [tile(f, rid, f["t"] - 0.1, "before"), tile(f, rid, f["t"] + 0.07, "after")]
        elif rid == "R7":
            tiles.append(tile(f, rid, (f["t"] + f.get("t_end", f["t"])) / 2, f"{f.get('dur', '')}s"))
        elif rid == "Q3":
            tiles += [tile(f, rid, f["t"] - 0.4, "moving"), tile(f, rid, f["t"] + 0.2, "frozen")]
        elif rid == "F2" and f.get("kind") != "held_open":
            tiles += [tile(f, rid, f["t"] - 0.4, "moving"), tile(f, rid, f["t"] + 0.2, "frozen")]
        elif rid == "F4":
            tiles.append(tile(f, rid, f.get("t_peak", f["t"]), f"{f.get('peak_px_s', '')} px/s"))
        elif rid == "F1":
            tiles.append(tile(f, rid, f["t"], f"{f.get('ratio', 0):.0%} repeated"))
        elif rid == "F3" and f.get("kind") != "soft":
            tiles.append(tile(f, rid, f["t"], f"{f.get('upscale', '')}x"))
        elif rid == "Q9":
            tiles += [tile(f, rid, f["other"] + 0.5, "first"), tile(f, rid, f["t"] + 0.5, "again")]
        elif rid in ("U1", "U2", "U3", "U5", "T1", "Q5") and f["t"] == 0: continue
        else: tiles.append(tile(f, rid, f["t"] + (0.0 if f.get("box") else 0.3)))
    if not tiles: continue
    cols = 6 if VERT else 4; per = cols * 4
    for n in range(0, len(tiles), per):
        chunk = tiles[n:n + per]; rows_ = math.ceil(len(chunk) / cols)
        sh = Image.new("RGB", (cols * (TW + 4), rows_ * (TH + 44)), (0, 0, 0))
        for k_, tl_ in enumerate(chunk): sh.paste(tl_, ((k_ % cols) * (TW + 4), (k_ // cols) * (TH + 44)))
        fn = f"sheet_{rid}_{n // per + 1}.jpg"; sh.save(os.path.join(A.out, fn), quality=82); SHEETS.append(fn)
log("sheets", len(SHEETS))

rep = {"video": os.path.basename(A.video), "mode": MODE, "width": W0, "height": H0, "fps": round(FPS, 3), "duration_s": round(DUR, 2), "frames": N,
       "cuts_detected": len(CUTS), "shots_planned": len(SHOTS), "shot_offset_s": round(OFFSET, 3), "whisper_words": len(WORDS),
       "tools": {"ocr": ocr is not None, "clip": clip is not None, "faces": (face is not None) and ("haar" if isinstance(face, tuple) else "yunet"), "whisper": bool(WORDS)},
       "elapsed_s": round(time.time() - T0, 1),
       "totals": {k_: sum(1 for r in REP.values() if r["status"] == k_) for k_ in ("pass", "warn", "fail", "skipped")},
       "rules": REP, "sheets": SHEETS, "cuts": [round(c, 2) for c in CUTS]}
json.dump(rep, open(os.path.join(A.out, "report.json"), "w"), indent=1, default=float)
try:
    os.remove(AUD)
    import shutil; shutil.rmtree(JDIR)
except Exception: pass
print("\n== RECIPE AUDIT", rep["video"], MODE, f"{DUR:.1f}s", "in", rep["elapsed_s"], "s ==")
for rid, r in REP.items():
    nf = sum(1 for f in r["findings"] if f["sev"] == "fail"); nw = sum(1 for f in r["findings"] if f["sev"] == "warn")
    print(f"{rid:3} {r['status']:8} fail {nf:3} warn {nw:3}  {r['summary'][:110]}")
