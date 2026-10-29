#!/usr/bin/env python3
"""Clip preparation with automatic quality gates (owner critique 2026-10-28). Used by every episode.
For every moving-picture source referenced by the plan (own phone clips, public-domain video, AI clips):
  Q-FPS    true 30 fps cadence: sources whose average frame rate is < 29.5 (iPhone VFR, low light, 24 fps AI clips) or that
           contain repeated frames are motion-interpolated to 30 fps (no duplicated frames = no micro-stutter).
  Q-CALM   camera motion is measured (phase correlation, 10 fps); the window used is the calmest one of the needed length
           near the requested in-point; whip pans (> PAN_MAX px/frame at 1080p) are never inside a used window.
  Q-LEN    the real usable length is recorded; build_shots never lets a shot outlast its footage (no frozen tail frames).
  Q-STAB   own handheld clips are stabilized (vidstab, tripod-like smoothing).
  Q-VOICE  own-clip natural sound is kept as ambience only if no human speech is detected (WebRTC VAD); otherwise none.
Writes prep/<key>.mp4 (+ .wav ambience) and prep/index.json {key: {src, ss_req, ss, len, fps_fix, pan_max, speech, w, h}}.
usage: prep2.py requests.json   (list of {key, src, ss, need, kind})"""
import json, os, subprocess, sys, numpy as np, cv2
D = os.path.dirname(os.path.abspath(__file__)); OUT = f"{D}/prep"; os.makedirs(OUT, exist_ok=True)
IDX = f"{OUT}/index.json"; idx = json.load(open(IDX)) if os.path.exists(IDX) else {}
PAN_MAX = 9.0        # px per frame at 1080p height (~270 px/s): faster = whip pan
def probe(p):
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", p], capture_output=True, text=True).stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd: rot = int(sd["rotation"])
    a, b = (v.get("avg_frame_rate", "30/1") + "/1").split("/")[:2]
    fps = float(a) / float(b) if float(b) else 30.0
    w, h = v["width"], v["height"]
    if abs(rot) == 90: w, h = h, w
    return float(j["format"]["duration"]), fps, w, h, any(s["codec_type"] == "audio" for s in j["streams"])
def motion_profile(p, t0, t1):
    """global translation speed per frame (px at 1080p) sampled at 10 fps between t0 and t1"""
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.2f}", "-t", f"{t1 - t0:.2f}", "-i", p, "-vf", "fps=10,scale=-2:180,format=gray",
                        "-f", "rawvideo", "-"], capture_output=True).stdout
    w = len(r) // 180 if False else None
    hdr = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-frames:v", "1", "-vf", "scale=-2:180", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
    W = len(hdr) // 180
    n = len(r) // (W * 180); F = np.frombuffer(r[: n * W * 180], np.uint8).reshape(n, 180, W).astype(np.float32)
    sp = [0.0]; df = [0.0]
    for a, b in zip(F[:-1], F[1:]):
        (dx, dy), _ = cv2.phaseCorrelate(a, b); sp.append(float(np.hypot(dx, dy)) * (1080 / 180) / 3.0)   # per 1/30 s
        df.append(float(np.mean(np.abs(a - b))))
    df = np.array(df); med = np.median(df) + 1e-3
    cut = (df > 18) & (df > 3.5 * med)          # edit points inside the source (never inside a used window)
    # Q-FREEZE: held/frozen frames in the source (webcam stalls, slideshow holds, near-static AI): >= 0.4 s of no change
    # relative to the clip's own motion (calm tripod shots are not "frozen"): only abrupt stalls in a moving clip count
    mdf = float(np.median(df)) if len(df) else 0.0
    still = (df < 0.15 * mdf) if mdf >= 0.8 else np.zeros(len(df), bool); frz = np.zeros(len(df), bool); run = 0
    for i, v in enumerate(still):
        run = run + 1 if v else 0
        if run >= 4: frz[i - run + 1:i + 1] = True
    return np.array(sp), cut | frz   # one value per 0.1 s; frozen runs are excluded exactly like edit points
def dup_ratio(p, ss, ln):
    out = subprocess.run(["ffmpeg", "-nostats", "-ss", f"{ss:.2f}", "-t", f"{ln:.2f}", "-i", p, "-vf", "scale=320:-2,mpdecimate=hi=64*2:lo=64:frac=0.33,showinfo",
                          "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
    kept = out.count("pts_time:"); return 1 - kept / max(1, int(ln * 30))
def speech(p, ss, ln):
    import webrtcvad
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{ss:.2f}", "-t", f"{ln:.2f}", "-i", p, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    v = webrtcvad.Vad(3); fr = 480 * 2; n = len(raw) // fr
    if n == 0: return 0.0
    return sum(v.is_speech(raw[i * fr:(i + 1) * fr], 16000) for i in range(n)) / n
def f1_ratio(src, ss, ln, rel=0.2):
    """share of repeated frames (native-res centre crop, same rule as analyze.py F1) in the source window as it would play at 30 fps"""
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-select_streams", "v", src], capture_output=True, text=True).stdout)["streams"][0]
    W, H = j["width"], j["height"]
    if any(abs(int(sd.get("rotation", 0))) == 90 for sd in j.get("side_data_list", []) or []): W, H = H, W
    sc = 1080 / H if H > 1080 else 1.0; W, H = int(W * sc) // 2 * 2, int(H * sc) // 2 * 2
    cw, ch = (W // 4) // 2 * 2, (H // 4) // 2 * 2
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{ss:.2f}", "-t", f"{min(ln, 6):.2f}", "-i", src, "-an", "-vf", f"scale={W}:{H},fps=30,crop={cw}:{ch}:{(W - cw) // 2}:{(H - ch) // 2},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    n = len(r) // (cw * ch)
    if n < 12: return 0.0
    F = np.frombuffer(r[: n * cw * ch], np.uint8).reshape(n, ch, cw).astype(np.float32); d = np.abs(np.diff(F, axis=0)).mean((1, 2))
    nl = np.array([d[max(0, k - 3):k].max() if k > 0 else 0 for k in range(len(d))]); nr = np.array([d[k + 1:k + 4].max() if k + 1 < len(d) else 0 for k in range(len(d))])
    nb = np.minimum(nl, nr); v = nb >= 0.6; v[:3] = False; v[-3:] = False
    return float(((d < rel * nb) & v).sum() / max(1, v.sum()))
def hard_cuts(p):
    """times (s) of hard scene cuts inside a prepared clip (30 fps scan, gray 160 px)"""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-an", "-vf", "scale=160:90,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    n = len(r) // (160 * 90)
    if n < 3: return []
    F = np.frombuffer(r[: n * 160 * 90], np.uint8).reshape(n, 90, 160).astype(np.float32)
    d = np.abs(np.diff(F, axis=0)).mean((1, 2)); med = np.median(d) + 0.3
    return [round((i + 1) / 30, 3) for i in np.where((d > 18) & (d > 6 * med))[0]]
def prep(req):
    k = req["key"] + ("" if req["kind"] in ("own", "ai") else "")  # (keys unchanged)
    k = req["key"]; src = req["src"]; need = float(req["need"]); ss_req = float(req.get("ss", 0)); kind = req["kind"]
    dst = f"{OUT}/{k}.mp4"
    if k in idx and (idx[k].get("v", 0) >= (7 if kind == "own" and (idx[k].get("fps_fix") or idx[k].get("v",0) >= 6) else 3) or kind == "pd") and os.path.exists(dst) and (idx[k]["len"] >= need - 0.2 or idx[k]["len"] >= idx[k].get("avail_max", 1e9) - 0.3): return idx[k]
    dur, fps, w, h, has_a = probe(src)
    if ss_req > dur - min(need, dur) - 0.1: ss_req = max(0.0, dur - min(need, dur) - 0.1)   # in-point past the end of the clip: use its last usable stretch
    # calm window search within [ss_req - 2, ss_req + 10]
    lo = max(0.0, ss_req - 2.0); hi = min(dur, ss_req + max(need, 4) + 10.0)
    prof, cut = motion_profile(src, lo, hi)
    win = max(1, int(round(need * 10))); best = None
    for i in range(0, max(1, len(prof) - win + 1)):
        seg = prof[i:i + win]; m = float(np.percentile(seg, 98)) if len(seg) else 0
        if cut[i + 1:i + win].any(): continue
        cost = max(m, 4.0) + 0.6 * abs((lo + i / 10) - ss_req)   # calm enough -> stay at the requested in-point
        if best is None or cost < best[0]: best = (cost, lo + i / 10, m)
    if best is None:   # every window touches a cut/freeze: take the one with the fewest bad samples (build2 then adds a gentle push-in)
        bad = [int(cut[i + 1:i + win].sum()) for i in range(0, max(1, len(prof) - win + 1))]
        i = int(np.argmin(bad)) if bad else 0
        best = (0, lo + i / 10, float(np.percentile(prof[i:i + win], 98)) if len(prof) else 0)
    _, ss, pan = best
    avail = max(0.0, dur - ss - 0.15)
    ln = min(avail, need + 1.0)
    dr = dup_ratio(src, ss, ln)
    # true repeated frames (native-res detail test, same rule as the audit) decide whether motion interpolation is needed:
    # the old 320 px mpdecimate ratio flagged clean clips, and interpolating them *created* a pulse (F1, ch1 v4/v5)
    fr = f1_ratio(src, ss, ln) if fps >= 29.5 and fps < 50 else 0.0
    fix = fps < 29.5 or (fr > 0.03 and fps < 50)
    vf = []
    pre = "scale=-2:1080," if (h > w and h > 1080) else ""   # portrait clips only ever fill a 9:16 panel of a 1080p frame
    if pre: vf.append(pre.rstrip(","))
    if kind == "own":
        trf = f"{OUT}/{k}.trf"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss:.2f}", "-t", f"{ln:.2f}", "-i", src, "-vf", f"{pre}vidstabdetect=shakiness=6:accuracy=12:result={trf}", "-f", "null", "-"])
        vf.append(f"vidstabtransform=input={trf}:smoothing=24:optzoom=1:zoomspeed=0.2:interpol=bicubic")
    if fix:   # remove duplicated frames, then synthesise true in-between frames up to 30 fps
        # drop duplicated frames but KEEP their timestamps (no setpts reset): minterpolate then synthesises true in-betweens
        # across the gaps. Resetting pts (v3) made the stream gap-free at 30 fps, minterpolate had nothing to do -> micro-stutter (F1, ch1 v4)
        if kind == "own" or (kind == "ai" and dr > 0.15):
            vf += ["mpdecimate=hi=64*2:lo=64:frac=0.33"]
        vf += ["minterpolate=fps=30:mi_mode=mci:mc_mode=obmc:me_mode=bidir"]
    else:
        vf.append("fps=30")
    if kind == "own": vf.append("unsharp=5:5:0.35")
    vf.append("format=yuv420p")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss:.2f}", "-t", f"{ln:.2f}", "-i", src, "-vf", ",".join(vf), "-an", "-r", "30",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", dst], capture_output=True, text=True)
    if r.returncode and kind == "own":   # stabiliser failed (bad transform file): use the clip as filmed
        vf = [x for x in vf if "vidstab" not in x]
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss:.2f}", "-t", f"{ln:.2f}", "-i", src, "-vf", ",".join(vf), "-an", "-r", "30",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", dst], capture_output=True, text=True)
        print("NO-STAB (vidstab failed)", k, flush=True)
    if r.returncode: raise RuntimeError(k + " " + r.stderr[-400:])
    if kind == "own" and not fix and f1_ratio(dst, 0, ln, 0.25) > 0.02:   # stabilising added repeated frames (low-light / noisy clips): use the clip as filmed
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss:.2f}", "-t", f"{ln:.2f}", "-i", src, "-vf", ",".join([x for x in vf if "vidstab" not in x]), "-an", "-r", "30",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", dst], capture_output=True, text=True)
        if r.returncode: raise RuntimeError(k + " " + r.stderr[-400:])
        print("NO-STAB", k, flush=True)
    real = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", dst], capture_output=True, text=True).stdout or 0)
    # Q-CUT: hard cut left inside the prepared clip (edit point of the source the 10 fps scan missed): keep the longer clean side
    cuts_ = hard_cuts(dst)
    if cuts_:
        tc = cuts_[0]; keep = (0.0, tc - 0.04) if tc >= real - tc else (tc + 0.04, real)
        if len(cuts_) > 1: keep = max(zip([0.0] + [c + 0.04 for c in cuts_], [c - 0.04 for c in cuts_] + [real]), key=lambda a: a[1] - a[0])
        tmp = dst[:-4] + "_t.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{keep[0]:.3f}", "-t", f"{keep[1] - keep[0]:.3f}", "-i", dst, "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-an", "-r", "30", tmp], capture_output=True)
        os.replace(tmp, dst); ss += keep[0]; real = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", dst], capture_output=True, text=True).stdout or 0)
        print("CUT-TRIM", k, [round(c, 2) for c in cuts_], "->", round(real, 2), flush=True)
    sp_ = 0.0; amb = None
    if kind == "own" and has_a:
        sp_ = speech(src, ss, ln)
        if sp_ < 0.02:      # any hint of a human voice -> no natural sound from this clip
            amb = dst[:-4] + ".wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss:.2f}", "-t", f"{ln:.2f}", "-i", src, "-vn", "-ac", "2", "-ar", "48000",
                            "-af", "highpass=f=120,lowpass=f=9000", amb], capture_output=True)
    if os.path.exists(f"{OUT}/{k}.trf"): os.remove(f"{OUT}/{k}.trf")
    rec = {"v": 7, "avail_max": round(avail, 2), "src": src, "ss_req": ss_req, "ss": round(ss, 2), "len": round(real, 2), "need": need, "fps": round(fps, 2), "dup": round(dr, 3), "f1": round(fr, 3),
           "fps_fix": fix, "pan_max": round(pan, 1), "pan_ok": pan <= PAN_MAX, "speech": round(sp_, 2), "amb": amb, "w": w, "h": h, "kind": kind}
    import fcntl
    with open(IDX + ".lock", "w") as lk:          # several prep workers may run in parallel
        fcntl.flock(lk, fcntl.LOCK_EX)
        cur = json.load(open(IDX)) if os.path.exists(IDX) else {}
        cur[k] = rec; idx.update(cur); json.dump(cur, open(IDX + ".tmp", "w"), indent=1); os.replace(IDX + ".tmp", IDX)
    print(k, kind, f"ss {ss_req}->{ss:.1f} len {real:.1f}/{need:.1f} fps {fps:.1f} dup {dr:.2f} fix {fix} pan {pan:.1f} speech {sp_:.2f}", flush=True)
    return rec
if __name__ == "__main__":
    for req in json.load(open(sys.argv[1])):
        try: prep(req)
        except Exception as e: print("FAIL", req["key"], str(e)[-300:], flush=True)
