#!/usr/bin/env python3
"""AlphaDog Studio - shared shot/cut/flash detector (the one scripts/recipe/analyze.py uses).

Importable by builders:
    from shots import detect_shots, find_flashes
    segs = detect_shots("video.mp4")                 # [(start_s, end_s), ...] on-screen shots
    fl = find_flashes(segs, min_dur=1.2)             # [(start_s, end_s), ...] shorter than min_dur
    fl = find_flashes(segs, min_dur=0.5, as_frames=True, fps=30)   # frame ranges [(a, b), ...] to hold/repair
    segs, cuts = detect_shots("video.mp4", return_cuts=True)       # cuts: [(t, kind)], kind in hard/dip/motion/dissolve/jump

Cut model (v1, calibrated on Chiricahua Ep1 + Shorts + promo):
  * hard cuts: normalized 64x36 luma correlation drop vs the neighbourhood OR hue/sat histogram drop
    (both required in dim scenes); fade/dip aware (cuts across dark runs, dips that never reach black).
v2 additions:
  * fast motion: a motion-compensated correlation (previous frame warped by the LK/RANSAC global motion) - a cut
    inside fast AI/drone motion shows as a drop of the compensated correlation while its neighbours stay high
    (the old builder spike detector missed a 0.35 s flash there); a pure luma-correlation drop that the
    compensated correlation explains (pan/whip) is vetoed.
  * jumps: a luma-layout jump with an unchanged colour palette (AI clip glitch, held-frame jump) is kind 'jump' -
    reported, but not a shot boundary (no false 'flash' between a dip and the glitch).
  * dissolves: frame j looks like the blend of frames j-K and j+K (normalized 64x36 vectors), the two ends are
    unrelated and no hard cut sits inside the window -> one boundary at the dissolve centre (kind 'dissolve').
CLI:  python3 shots.py VIDEO [--min 1.2] [--json]
"""
import json, subprocess, sys
import numpy as np, cv2


def probe(path):
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                    "stream=width,height,r_frame_rate:format=duration", "-of", "json", path],
                                   capture_output=True, text=True).stdout)
    s = pr["streams"][0]; n, d = map(int, s["r_frame_rate"].split("/"))
    return int(s["width"]), int(s["height"]), n / d, float(pr["format"]["duration"])


class Features:
    """Per-frame low-res features. add() takes a BGR frame at low res (LWxLH) and returns (gray uint8, gray f32)."""

    def __init__(self, lw, lh, vert=False, motion=True):
        self.LW, self.LH, self.VERT, self.motion = lw, lh, vert, motion
        self.sz64 = (36, 64) if vert else (64, 36)
        self.han = cv2.createHanningWindow((lw, lh), cv2.CV_32F)
        self.prev = None; self.last_nd = None; self.prev_g8 = None; self.prev_pts = None
        k = ["Ym", "Ys", "Y99", "CORR", "HOV", "DX", "DY", "RESP", "DIFF", "P50", "P90", "MCC", "TX", "TY", "ROT", "SCL",
             "INL", "NPT", "RES", "SKEW", "EDGE", "GAIN", "Lm", "Am", "Bm", "BL", "BR", "BT", "BB"]
        self.a = {x: [] for x in k}; self.D16 = []; self.HS = []; self.G64 = []

    def _motion(self, g8):
        """global similarity motion prev->cur (LK + RANSAC) + residual structure"""
        out = dict(TX=0.0, TY=0.0, ROT=0.0, SCL=1.0, INL=0.0, NPT=0, RES=0.0, SKEW=0.0, EDGE=0.0, M=None)
        if self.prev_g8 is None: return out
        p0 = cv2.goodFeaturesToTrack(self.prev_g8, 140, 0.01, 7, blockSize=5)
        if p0 is None or len(p0) < 12: return out
        p1, st, _ = cv2.calcOpticalFlowPyrLK(self.prev_g8, g8, p0, None, winSize=(15, 15), maxLevel=2,
                                             criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 20, 0.03))
        ok = st.ravel() == 1
        out["NPT"] = int(len(p0))
        if ok.sum() < 10: return out
        a0 = p0[ok].reshape(-1, 2); a1 = p1[ok].reshape(-1, 2)
        M, inl = cv2.estimateAffinePartial2D(a0, a1, method=cv2.RANSAC, ransacReprojThreshold=1.5, maxIters=500)
        if M is None: return out
        inl = inl.ravel().astype(bool)
        cx, cy = self.LW / 2, self.LH / 2                       # displacement of the frame centre (zoom does not leak into pan)
        out.update(TX=float(M[0, 0] * cx + M[0, 1] * cy + M[0, 2] - cx), TY=float(M[1, 0] * cx + M[1, 1] * cy + M[1, 2] - cy), ROT=float(np.degrees(np.arctan2(M[1, 0], M[0, 0]))),
                   SCL=float(np.hypot(M[0, 0], M[1, 0])), INL=float(inl.sum()) / len(p0), M=M)
        pr = a0 @ M[:, :2].T + M[:, 2]; r = a1 - pr; rn = np.hypot(r[:, 0], r[:, 1])
        good = rn < 4.0
        if good.sum() >= 10:
            out["RES"] = float(np.median(rn[good]))
            y = a0[good, 1]; dxr = r[good, 0]
            if y.std() > 5: out["SKEW"] = float(np.polyfit((y - self.LH / 2) / self.LH, dxr, 1)[0])   # px of horizontal shear top->bottom
            x = a0[good, 0]; ed = (x < 0.12 * self.LW) | (x > 0.88 * self.LW) | (y < 0.12 * self.LH) | (y > 0.88 * self.LH)
            if ed.sum() >= 4 and (~ed).sum() >= 4: out["EDGE"] = float(np.median(rn[good][ed]) / (np.median(rn[good][~ed]) + 0.05))
        return out

    def add(self, im):
        a = self.a
        g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); gf = g.astype(np.float32)
        q = np.percentile(g, (50, 90, 99)); m, sd = float(g.mean()), float(g.std())
        a["Ym"].append(m); a["Ys"].append(sd); a["Y99"].append(float(q[2])); a["P50"].append(float(q[0])); a["P90"].append(float(q[1]))
        sm = cv2.resize(gf, self.sz64, interpolation=cv2.INTER_AREA)
        gn = (sm - sm.mean()) / (sm.std() + 1e-3)
        small = cv2.resize(im, self.sz64, interpolation=cv2.INTER_AREA)
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        h = cv2.calcHist([hsv], [0, 1], None, [16, 4], [0, 180, 0, 256]).flatten(); h /= (h.sum() + 1e-6)
        lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32).mean(0)
        a["Lm"].append(float(lab[0])); a["Am"].append(float(lab[1]) - 128); a["Bm"].append(float(lab[2]) - 128)
        p50, p90 = q[0], q[1]
        dark = p50 < 18 and p90 < 45                       # median-based: burned-in captions do not hide a fade
        s16 = cv2.resize(gf, (9, 16) if self.VERT else (16, 9), interpolation=cv2.INTER_AREA).flatten()
        self.D16.append(((s16 - s16.mean()) / (s16.std() + 1e-3)).astype(np.float16))
        self.HS.append(h.astype(np.float16)); self.G64.append(gn.astype(np.float16).flatten())
        # black stabilization borders: outermost line black while 2 lines in is picture
        def bfrac(o, i_): return float(((o < 10) & (i_ > 30)).mean())
        a["BL"].append(bfrac(g[:, 0], g[:, 2])); a["BR"].append(bfrac(g[:, -1], g[:, -3]))
        a["BT"].append(bfrac(g[0], g[2])); a["BB"].append(bfrac(g[-1], g[-3]))
        mo = self._motion(g) if self.motion else dict(TX=0.0, TY=0.0, ROT=0.0, SCL=1.0, INL=0.0, NPT=0, RES=0.0, SKEW=0.0, EDGE=0.0, M=None)
        for k in ("TX", "TY", "ROT", "SCL", "INL", "NPT", "RES", "SKEW", "EDGE"): a[k].append(mo[k])
        prev = self.prev
        if prev is not None:
            ref = self.last_nd if (dark or prev[3]) and self.last_nd is not None else prev
            a["CORR"].append(float((gn * ref[0]).mean())); a["HOV"].append(float(np.minimum(h, ref[1]).sum()))
            (dx, dy), resp = cv2.phaseCorrelate(prev[2], gf, self.han); a["DX"].append(dx); a["DY"].append(dy); a["RESP"].append(resp)
            a["DIFF"].append(float(np.abs(sm - prev[4]).mean()))
            mid = (prev[4] > 30) & (prev[4] < 220) & (sm > 20)            # robust global gain (overlays/captions barely move the median)
            a["GAIN"].append(float(np.median(np.log(sm[mid] / prev[4][mid]))) if mid.sum() > 200 else 0.0)
            # motion-compensated correlation (central 80 %)
            if mo["M"] is not None:
                wp = cv2.warpAffine(prev[2], mo["M"], (self.LW, self.LH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
                y0, y1, x0, x1 = int(self.LH * .1), int(self.LH * .9), int(self.LW * .1), int(self.LW * .9)
                u = cv2.resize(wp[y0:y1, x0:x1], (64, 36) if not self.VERT else (36, 64), interpolation=cv2.INTER_AREA)
                v = cv2.resize(gf[y0:y1, x0:x1], (64, 36) if not self.VERT else (36, 64), interpolation=cv2.INTER_AREA)
                u = (u - u.mean()) / (u.std() + 1e-3); v = (v - v.mean()) / (v.std() + 1e-3)
                a["MCC"].append(float((u * v).mean()))
            else: a["MCC"].append(0.0)
        else:
            a["CORR"].append(1.0); a["HOV"].append(1.0); a["DX"].append(0.0); a["DY"].append(0.0); a["RESP"].append(1.0); a["DIFF"].append(0.0); a["MCC"].append(1.0); a["GAIN"].append(0.0)
        self.prev = (gn, h, gf, dark, sm)
        if not dark: self.last_nd = self.prev
        self.prev_g8 = g
        return g, gf

    def arrays(self):
        F = {k: np.array(v, np.float32) for k, v in self.a.items()}
        F["D16"] = np.array(self.D16, np.float32); F["HS"] = np.array(self.HS, np.float32); F["G64"] = np.array(self.G64, np.float16)
        F["N"] = len(F["Ym"])
        F["DARK"] = (F["P50"] < 18) & (F["P90"] < 45); F["BLACK"] = (F["P50"] < 10) & (F["P90"] < 18)
        return F


def detect_cuts(F, fps, robust=True):
    """-> sorted list of (frame_index (float, centre for dips/dissolves), kind) ; kinds: hard, dip, motion, dissolve, jump (not a boundary)"""
    N = F["N"]; DARK = F["DARK"]; CORR, HOV, Ys, P50, D16, HS = F["CORR"], F["HOV"], F["Ys"], F["P50"], F["D16"], F["HS"]
    MCC = F.get("MCC"); INL = F.get("INL")
    cuts = []; j = 1
    while j < N:
        if DARK[j]:                                           # a dark run: one boundary at its centre if content changes across it
            k = j
            while k < N and DARK[k]: k += 1
            if j < fps * 0.3 or k > N - fps * 0.3: pass
            elif k < N and (CORR[k] < 0.6 or HOV[k] < 0.6) and k - j < fps * 3: cuts.append(((j + k) / 2, "dip"))
            elif k < N and k - j >= fps * 3: cuts.append((j, "dip")); cuts.append((k, "dip"))
            j = k + 1; continue
        lo, hi = max(1, j - 6), min(N, j + 7)
        nb = [x for x in range(lo, hi) if x != j and not DARK[x]]
        mc = np.median(CORR[nb]) if nb else 1.0; mh = np.median(HOV[nb]) if nb else 1.0
        flat = Ys[j] < 5
        if P50[j] < 25 or P50[j - 1] < 25 or j < fps * 0.3 or j > N - fps * 0.3: j += 1; continue     # dim frames: fades/cards (handled as dips)
        c_cut = (not flat) and CORR[j] < 0.55 and mc - CORR[j] > 0.3
        h_cut = HOV[j] < 0.5 and mh - HOV[j] > 0.3
        dim = P50[j] < 45 or P50[j - 1] < 45                 # low-light scenes: noise/flicker - require both signals
        hit = (c_cut and h_cut) if dim else (c_cut or h_cut)
        if robust and MCC is not None and not dim:
            mm = np.median(MCC[nb]) if nb else 1.0
            if hit and c_cut and not h_cut and MCC[j] > 0.85 and INL[j] > 0.5: hit = False          # pan/whip explained by global motion
            # fast motion: luma correlation is low everywhere, but compensated correlation stays high except at the cut
            if not hit and (not flat) and MCC[j] < 0.35 and mm > 0.75 and mm - MCC[j] > 0.45 and INL[j] < 0.35 and CORR[j] < 0.75 and HOV[j] < 0.85:
                cuts.append((j, "motion")); j += 1; continue
        if hit:
            # same palette, only the luma layout jumps (AI clip glitch / jump inside one shot): kind 'jump' - not a shot boundary
            cuts.append((j, "jump" if (robust and c_cut and not h_cut and HOV[j] >= 0.85 and mh - HOV[j] < 0.12) else "hard"))
        j += 1
    # fade dips that never reach black (captions/vignette on top): local luma minimum at < 50 % of both sides + content change
    for j in range(10, N - 10):
        if DARK[j] or P50[j] > min(P50[j - 3:j + 4]): continue
        pre, post = P50[j - 10:j - 2].max(), P50[j + 3:j + 11].max()
        if min(pre, post) < 30 or P50[j] > 0.5 * min(pre, post): continue
        a, b2 = j - 6, j + 6
        c = float(D16[a] @ D16[b2]) / D16.shape[1]; hh = float(np.minimum(HS[a], HS[b2]).sum())
        if c < 0.5 or hh < 0.6: cuts.append((j, "dip"))
    if robust and "G64" in F: cuts += _dissolves(F, fps, cuts)
    cuts.sort(); out = []
    for c in cuts:                                            # merge cuts closer than 6 frames
        if out and c[0] - out[-1][0] < 6: continue
        out.append(c)
    return out


def _dissolves(F, fps, cuts):
    G = F["G64"]; N = F["N"]; DARK = F["DARK"]; Ys = F["Ys"]; CORR = F["CORR"]
    taken = np.zeros(N, bool)
    for c, _ in cuts: taken[max(0, int(c) - 30): int(c) + 31] = True
    D = G.shape[1]; out = []
    for K in (6, 10, 16):
        j = K + 2
        while j < N - K - 2:
            if taken[j] or DARK[j - K:j + K + 1].any() or j < fps * 0.5 or j > N - fps * 0.5: j += 1; continue
            A = G[j - K].astype(np.float32); B = G[j + K].astype(np.float32); X = G[j].astype(np.float32)
            ab = float(A @ B) / D
            if ab > 0.25: j += 1; continue
            s = A + B; cs = float(X @ s) / (D * np.sqrt(max(1e-6, (2 + 2 * ab))))
            ca, cb = float(X @ A) / D, float(X @ B) / D
            if cs > 0.93 and 0.35 < ca < 0.88 and 0.35 < cb < 0.88 and CORR[j - K + 1:j + K + 1].min() > 0.6 and Ys[j] < 0.95 * 0.5 * (Ys[j - K] + Ys[j + K]):
                # monotone transition: correlation with A decreases, with B increases across the window
                ra = [float(G[q].astype(np.float32) @ A) / D for q in range(j - K, j + K + 1, max(1, K // 3))]
                if ra[0] > ra[len(ra) // 2] > ra[-1]:
                    out.append((float(j), "dissolve")); taken[max(0, j - 30): j + 31] = True; j += K; continue
            j += 1
    return out


def segments(cuts, N, fps, with_jumps=False):
    b = [0.0] + [c[0] / fps for c in cuts if with_jumps or c[1] != "jump"] + [N / fps]
    return [(b[i], b[i + 1]) for i in range(len(b) - 1) if b[i + 1] - b[i] > 0.02]


def find_flashes(segs, min_dur=1.2, as_frames=False, fps=30.0, skip_edges=0.6, dur_total=None):
    """segments shorter than min_dur (start/end remnants < skip_edges ignored). as_frames -> integer frame ranges"""
    end = dur_total if dur_total is not None else (segs[-1][1] if segs else 0)
    out = []
    for a, b in segs:
        if b - a >= min_dur: continue
        if (a < 0.05 or b > end - 0.05) and b - a < skip_edges: continue
        out.append((int(round(a * fps)), int(round(b * fps))) if as_frames else (round(a, 3), round(b, 3)))
    return out


def scan(path, max_dur=0.0, motion=True, keep=False):
    """decode every frame at low res -> (Features arrays, fps, duration, (W, H))"""
    W, H, fps, dur = probe(path)
    vert = H > W; LW, LH = (180, 320) if vert else (320, 180)
    cmd = ["ffmpeg", "-v", "error"] + (["-t", str(max_dur)] if max_dur else []) + ["-i", path, "-an", "-sn", "-vf", f"scale={LW}:{LH}:flags=area",
                                                                                 "-pix_fmt", "bgr24", "-f", "rawvideo", "pipe:1"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10 ** 7); fb = LW * LH * 3
    Fe = Features(LW, LH, vert, motion)
    while True:
        buf = p.stdout.read(fb)
        if len(buf) < fb: break
        Fe.add(np.frombuffer(buf, np.uint8).reshape(LH, LW, 3))
    p.wait()
    return Fe.arrays(), fps, dur, (W, H)


def detect_shots(path, max_dur=0.0, return_cuts=False):
    F, fps, dur, _ = scan(path, max_dur)
    cuts = detect_cuts(F, fps)
    segs = segments(cuts, F["N"], fps)
    return (segs, [(round(c / fps, 3), k) for c, k in cuts]) if return_cuts else segs


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("--min", type=float, default=1.2)
    ap.add_argument("--max-dur", type=float, default=0.0); ap.add_argument("--json", action="store_true")
    A = ap.parse_args()
    segs, cuts = detect_shots(A.video, A.max_dur, return_cuts=True)
    fl = find_flashes(segs, A.min)
    if A.json: print(json.dumps({"shots": segs, "cuts": cuts, "flashes": fl}))
    else:
        print(len(segs), "shots;", len(cuts), "cuts:", " ".join(f"{t:.2f}{k[0] if k != 'hard' else ''}" for t, k in cuts))
        print("flashes <", A.min, "s:", fl)
