"""Vertical Shorts (1080x1920) from the episode's verified sources.
Rules applied: no flash shots (cut-free spans, >= 2.5 s), calm drones, matching imagery per phrase, < 60 s (Shorts with
archive/CC footage over 60 s are blocked worldwide on any claim), big burned-in captions timed to the voice, music bed under voice.
usage: python3 make_shorts.py [sh1 sh2 sh3]"""
import json, os, re, subprocess, sys, numpy as np, soundfile as sf
D = "/home/claude/doc/chiricahua"; OUT = f"{D}/shorts"; os.makedirs(OUT, exist_ok=True)
argv = sys.argv[1:]; sys.argv = sys.argv[:1]
sys.path.insert(0, D); import engine as E; import plan_v2 as P
E.W, E.H = 1080, 1920
NARR = "/home/claude/fb/chiricahua-shorts-narr2/am_michael"; SR = 48000
TEXT = {x["id"]: x["text"] for x in json.load(open("/home/claude/rs/content/chiricahua/shorts_narration.json"))}
A_CLEAN = f"{D}/media/annot/cochise_head_clean.jpg"; A_LAB = f"{D}/media/annot/cochise_head_annot.jpg"
def ph(src, **kw):
    s = {"type": "photo", "src": src, "z0": 1.0, "z1": 1.08, "x0": .5, "y0": .5, "x1": .5, "y1": .5, "bg": "fit"}; s.update(kw); return s
V = lambda d, at=None, **kw: dict(d, **({"at": at} if at else {}), **kw)
AI = lambda n, at: {"type": "video", "src": f"/home/claude/fb/ai-clips/{n}.mp4", "ss": 0, "drift": 0.02, "ai": True, "at": at}
P.SAFE["ia_ad64da0120_9"] = [(1.7, 6.05)]     # skip the SCIENCE NATION logo; the plume ends at the 6.17 s cut
LN = "hue=s=0.45,colorbalance=rm=0.05:bm=-0.06:rh=0.04:bh=-0.08,eq=contrast=1.08:brightness=-0.04"
# v5 (owner review 2026-10-25): every shot starts on the phrase it illustrates ("at"); story moments use the episode's
# animated scenes (real-time speed); no Dragoon footage as "the park"; active-volcano imagery limited to one ash cloud.
SHORTS = {
 "sh1": {"music": "tension", "title": "Who killed Johnny Ringo?", "shots": [
     P.Y("LNceEWbCiAg", "2:54", 3.3),                                                     # the oak
     AI("A08", "Revolver in"), AI("A09", "His feet wrapped"), AI("A10b", "His gun belt"),
     ph(f"{P.M2}/commons_bcf854a393.jpg", at="The jury called"),                            # historic Tombstone (coroner's jury)
     V(P.S("ia_7c0f67540d_1023", 3.5), "Ringo, one"),                                      # the Cowboys
     {"type": "video", "src": "/home/claude/fb/yt-cuts/yt_KfCNBLKYZXQ_838.mp4", "ss": 10.0, "drift": 0.03, "at": "the jury got"},   # costumed gunfight (Earp / Holliday)
     ph(f"{D}/media/img/commons_7f899d5663.jpg", at="A gambler"),                          # Tombstone saloon at night
     {"type": "video", "src": "/home/claude/fb/yt-cuts-v3/yt_LNceEWbCiAg_144.mp4", "ss": 0.0, "drift": 0.03, "vf_extra": LN, "at": "where he was"}]},   # the grave
 "sh2": {"music": "somber", "title": "He jumped from a prison train", "shots": [
     P.P(87, bg="fit"), V(P.S("pb_21555_0", 5.5, vf_extra=P.PERIOD), "every Chiricahua"), V(P.P(82, bg="fit"), "war, even"),
     V(P.S("pb_188828_0", 0.5, vf_extra=P.PERIOD), "Somewhere in Missouri"), V(P.S("pb_75635_0", 0.5), "He was alone"),
     V(P.Y("m8GhYxt-kAg", "0:56", 2), "he walked hundreds"), V(P.Y("HJlO513toNw", "5:31", 2), "mountains of the"),
     ph(f"{P.M2}/{P.WICKIUP}", at="He lived there"), V(P.F("massai_orbit", 1), "Today, the highest"), V(P.Y("cPRS8XqUNvw", "0:18", 1), "Massai Point")]},
 "sh3": {"music": "wonder", "title": "America's newest national park", "shots": [
     P.Y("pGLdAm_aQqM", "26:32", 9), V(P.S("ia_ad64da0120_9", 1.6), "Twenty-seven"), V(P.Y("pGLdAm_aQqM", "18:22", 9), "of Mount St"),
     V(P.Y("kjAGAtBYZSo", "5:53", 2), "rock, and ice"), V(P.Y("GqV7LUmlgFY", "5:05", 2), "Some boulders"),
     ph(A_CLEAN, z1=1.03, at="Look at the"), ph(A_LAB, z0=1.03, z1=1.06, at="the mountains form"),
     V(P.P(245, bg="fit"), "And a wild"), V(P.Y("pGLdAm_aQqM", "22:27", 6), "This is Chiricahua")]},
}

def load(p):
    a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout, np.float32)
    idx = np.where(np.abs(a) > 0.003)[0]; return a[max(0, idx[0] - 2400): idx[-1] + 4800]

def caption_cues(text, a, t0):
    """phrases of <= 4 words, sentence starts anchored to real pauses"""
    hop = SR // 100; env = np.sqrt(np.mean(a[: len(a) // hop * hop].reshape(-1, hop) ** 2, 1)); thr = 10 ** (-40 / 20)
    sil = env < thr; P_ = []; n = 0
    for k, s in enumerate(sil):
        if s: n += 1
        else:
            if n >= 14: P_.append((k - n / 2) / 100)
            n = 0
    sents = [x for x in re.split(r"(?<=[.?!])\s+", text.strip()) if x]
    L = np.cumsum([len(x) for x in sents]); tot = L[-1]; s0 = 0.0; s1 = len(a) / SR; cuts = []
    for k in range(len(sents) - 1):
        g = s1 * L[k] / tot; c = [p for p in P_ if (not cuts or p > cuts[-1] + 0.3)]
        b = min(c, key=lambda p: abs(p - g)) if c else g; cuts.append(b if abs(b - g) < 1.8 else g)
    T = [s0] + cuts + [s1]; cues = []
    for k, s in enumerate(sents):
        w = s.split(); ph_ = []; cur = []
        for x in w:
            cur.append(x)
            if len(cur) >= 4 or (len(cur) >= 2 and x[-1] in ",.?!:"): ph_.append(" ".join(cur)); cur = []
        if cur: ph_.append(" ".join(cur))
        a_, b_ = T[k] + 0.05, T[k + 1] - 0.05; tt = sum(len(p) for p in ph_); t = a_
        for p in ph_:
            d = (b_ - a_) * len(p) / tt; cues.append((t0 + t, t0 + t + d, p)); t += d
    return cues

def ass_time(x): h, r = divmod(x, 3600); m, s = divmod(r, 60); return f"{int(h)}:{int(m):02d}:{s:05.2f}"
def hl(p):   # highlight numbers and names in gold
    return " ".join(("{\\c&H52A0D6&}" + w + "{\\c&HFFFFFF&}") if (re.search(r"\d", w) or (w[:1].isupper() and w.lower() not in ("in", "the", "his", "and", "a", "he", "it", "which", "today", "some", "look", "twenty-seven", "revolver", "boots", "almost", "somewhere", "traveling", "america"))) else w for w in p.split())

def build(sid):
    cfg = SHORTS[sid]; a = load(f"{NARR}/{sid}.m4a"); lead = 0.35; dur = lead + len(a) / SR + 1.2
    assert dur < 59.5, (sid, dur)
    shots = [dict(s) for s in cfg["shots"]]
    for s in shots:
        for k in ("label", "date", "amb", "amb_g", "sfx", "rep_ok"): s.pop(k, None)
        s["fx"] = 0.5
    cues = caption_cues(TEXT[sid], a, lead)
    if any("at" in x for x in shots):                       # v5: every shot starts on the phrase it illustrates
        norm = lambda t: re.sub(r"[^a-z0-9 ]", "", t.lower())
        T = []
        for k, x in enumerate(shots):
            at = x.pop("at", None)
            if k == 0: T.append(0.0); continue
            c = next(c for c in cues if norm(c[2]).startswith(norm(at)))
            T.append(c[0] - 0.08)
        T.append(dur); used = set()
        for k, x in enumerate(shots):
            want = round(T[k + 1] - T[k], 3); x["dur"] = want
            if x["type"] == "video":
                got = P.place_video(x, want, used)
                if got + 0.05 < want: print("SHORT_CAPACITY", sid, k, os.path.basename(x["src"]), round(got, 2), "<", want, flush=True)
                x["dur"] = want
    else:
        P.allocate(shots, dur, 2.5)
    work = f"{OUT}/{sid}"; os.makedirs(work, exist_ok=True); files = []
    for i, s in enumerate(shots):
        f = f"{work}/{i:02d}_{E.key(s)}.mp4"
        if not os.path.exists(f): E.render_shot(s, f)
        files.append(f)
    open(f"{work}/concat.txt", "w").write("".join(f"file '{f}'\n" for f in files))
    # captions - phone safe zone (owner 2026-10-26: text was getting cut on phones). Keep all text inside x 170..910
    # (tall phones crop ~100 px per side, right-rail buttons) and y 400..1220 (IG 4:5 feed crop top 285 / bottom 1635,
    # TikTok top tabs, caption + username block at the bottom).
    ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV",
           "Style: Cap,Inter Display Black,76,&H00FFFFFF,&H00000000,&H64000000,1,1,6,2,2,170,170,700",
           "Style: Top,Inter Display Black,58,&H00FFFFFF,&H00000000,&H64000000,1,1,5,2,8,160,160,400", "", "[Events]",
           "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
           f"Dialogue: 0,{ass_time(0)},{ass_time(3.2)},Top,,0,0,0,,{{\\fad(150,300)}}{cfg['title'].upper()}",
           f"Dialogue: 0,{ass_time(dur - 1.3)},{ass_time(dur)},Top,,0,0,0,,{{\\fad(200,0)}}FULL STORY ON THE CHANNEL"]
    for x, y, p in cues: ass.append(f"Dialogue: 0,{ass_time(x)},{ass_time(y)},Cap,,0,0,0,,{{\\fad(60,60)}}{hl(p)}")
    open(f"{work}/cap.ass", "w").write("\n".join(ass) + "\n")
    # audio: narration + music bed (-22 dB under voice), whoosh on first cut
    N = int(dur * SR); voice = np.zeros(N, np.float32); s0 = int(lead * SR); voice[s0:s0 + len(a)] = a[: N - s0]
    m, _ = sf.read(f"{D}/music/{cfg['music']}.wav", dtype="float32", always_2d=True); m = m.mean(1)
    m = np.tile(m, N // len(m) + 1)[:N]
    vm = np.convolve((np.abs(voice) > 0.01).astype(np.float32), np.ones(SR // 4) / (SR // 4), "same")
    g = (0.22 - 0.16 * np.clip(vm * 4, 0, 1)); m *= g
    fade = np.ones(N, np.float32); k = int(1.0 * SR); fade[:k] = np.linspace(0, 1, k); fade[-k:] = np.linspace(1, 0, k)
    mix = voice + m * fade
    sf.write(f"{work}/mix.wav", np.stack([mix, mix], 1), SR)
    out = f"{OUT}/chiricahua_{sid}.mp4"
    E.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{work}/concat.txt", "-i", f"{work}/mix.wav",
           "-filter_complex", f"[0:v]ass={work}/cap.ass:fontsdir=/usr/share/fonts/opentype/inter[v];[1:a]loudnorm=I=-14:TP=-1.5[a]",
           "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-t", f"{dur:.2f}", "-movflags", "+faststart", out])
    print(sid, round(dur, 1), "s,", len(shots), "shots,", len(cues), "caption cues ->", out, flush=True)

for sid in (argv or list(SHORTS)): build(sid)
