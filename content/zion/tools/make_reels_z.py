"""Zion reels (Part 1): standalone short scripts (shorts_p1_script.json, TTS zion-narr/shorts_p1) cut to own vertical footage,
own photos, NPS photos and the episode's AI story scenes; full-screen 1080x1920 only (V43: no side-by-side panels in reels),
burned-in captions, hook title, CTA tag, end card to the full documentary, ducked music bed.
usage: make_reels_z.py p1 id [id ...]   (spec: reels_z1.json)"""
import json, os, re, subprocess, sys, fcntl, numpy as np, soundfile as sf
D = "/home/claude/doc/zion"; SR = 48000
part = sys.argv[1]; want = sys.argv[2:]; n = part[1]
sys.path.insert(0, f"{D}/ch{n}"); import engine as E
E.W, E.H = 1080, 1920
SPEC = json.load(open(f"{D}/reels_z{n}.json")); CFG = SPEC
TXT = {x["id"]: x for x in json.load(open(f"{D}/shorts_{part}_script.json"))}
OWN = f"{D}/own"; IMG = f"{D}/media/pd_ch{n}/img"; AI = f"{D}/media/zion-ai/ch{n}"
OUT = f"{D}/shorts_{part}/out"; os.makedirs(OUT, exist_ok=True)
STORY = False
src = open("/home/claude/doc/yellowstone/make_shorts_ys.py").read()
exec(src[src.index("def rd("):src.index("for sh in CFG")].replace('ECARD = 2.5 if STORY else 3.0', 'ECARD = 3.0'))   # rd, cues_for, end_card, at, hl
class _NW(set):
    def __contains__(self, w): return any(set.__contains__(self, p) for p in w.strip(":;").split("-"))
NUMW = _NW("one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million billion percent tons".split())
def end_card(path, thumb, line1, line2):
    """V1 phone-safe end card (owner: nothing may be cut on the phone): every element inside x 170..910, y 400..1220."""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    F = lambda n, sz: ImageFont.truetype(f"/usr/share/fonts/opentype/inter/{n}.otf", sz)
    t = Image.open(thumb).convert("RGB")
    bg = t.resize((1080, 1920), Image.LANCZOS).filter(ImageFilter.GaussianBlur(40)); bg = Image.eval(bg, lambda v: int(v * 0.35))
    w = 720; h = int(t.height * w / t.width); x0 = (1080 - w) // 2; y = 540
    bg.paste(t.resize((w, h), Image.LANCZOS), (x0, y)); d = ImageDraw.Draw(bg)
    def ctr(txt, yy, f, col=(255, 255, 255)):
        b = d.textbbox((0, 0), txt, font=f); d.text(((1080 - (b[2] - b[0])) // 2, yy), txt, font=f, fill=col, stroke_width=4, stroke_fill=(0, 0, 0))
    ctr("THE FULL STORY", 430, F("InterDisplay-Black", 76), (255, 200, 60))
    ctr(line1, y + h + 40, F("InterDisplay-Black", 52)); ctr(line2, y + h + 120, F("InterDisplay-Black", 42), (255, 200, 60))
    cx, cy = x0 + w - 60, y + h - 60; d.ellipse((cx - 40, cy - 40, cx + 40, cy + 40), fill=(255, 0, 0)); d.polygon([(cx - 12, cy - 24), (cx - 12, cy + 24), (cx + 26, cy)], fill=(255, 255, 255))
    assert y + h + 120 + 60 <= 1220, "end card text below the phone-safe area"
    bg.save(path)
def norm(t): return re.sub(r"[^a-z0-9 ]", "", t.lower())
for sh in SPEC["reels"]:
    if want and sh["id"] not in want: continue
    assert sh["shots"][0]["src"].startswith("own:"), ("first shot must be own footage (cover)", sh["id"])
    narr = rd(f"{D}/shorts_{part}/narr/{sh['id']}.m4a"); a1 = len(narr) / SR
    dur = round(a1 + 0.5, 3); a0 = 0.0
    assert dur + ECARD < 59.6, (sh["id"], dur)
    work = f"{OUT}/{sh['id']}"; os.makedirs(work, exist_ok=True)
    lk = open(f"{work}/.lock", "w"); fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
    cues = cues_for(TXT[sh["id"]]["text"], narr, 0.0)
    # shot start times from their anchor phrase
    T = []
    for k, x in enumerate(sh["shots"]):
        if k == 0: T.append(0.0); continue
        c = next((c for c in cues if norm(c[2]).startswith(norm(x["at"]))), None)
        assert c, ("anchor not found", sh["id"], x["at"], [c[2] for c in cues])
        T.append(max(T[-1] + 1.5, c[0] - 0.08))
    T.append(dur)
    files = []
    for k, x in enumerate(sh["shots"]):
        d = round(T[k + 1] - T[k], 3); assert d >= 1.4, ("shot too short", sh["id"], k, d)
        if x["src"].startswith("own:"):
            cid = x["src"][4:]; s = {"type": "video", "src": f"{OWN}/{cid}.mov", "ss": x.get("ss", 0), "dur": d, "drift": 0.0, "fx": x.get("fx", 0.5), "fy": 0.5}
        elif x["src"].startswith("ai:"):   # episode AI story scene (1280x704), cover-cropped around its subject
            s = {"type": "video", "src": f"{AI}/{x['src'][3:]}.mp4", "ss": x.get("ss", 0), "dur": d, "drift": 0.0, "fx": x.get("fx", 0.5), "fy": 0.5}
        else:
            p = f"{IMG}/{x['src']}.jpg"; s = {"type": "photo", "src": p, "dur": d, "bg": "cover",
                  "z0": x.get("z0", 1.0), "z1": x.get("z1", 1.06), "x0": x.get("x0", .5), "x1": x.get("x1", .5), "y0": x.get("y0", .5), "y1": x.get("y1", .5), "bg": x.get("bg", "cover")}
        if s["type"] == "video":   # never let a shot outrun its source (a short source silently shortens the track and desyncs every later cut)
            sd = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", s["src"]], capture_output=True, text=True).stdout)
            avail = sd - s["ss"] - 0.1
            if avail < d:
                assert avail >= d * 0.75, ("shot longer than its source - split it", sh["id"], k, x["src"], round(avail, 2), d)
                s["speed"] = round(avail / d, 3)
        f = f"{work}/{k:02d}_{E.key(s)}.mp4"
        if not os.path.exists(f): E.render_shot(s, f)
        files.append(f)
    vd = sum(float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout) for f in files)
    assert abs(vd - dur) < 0.25, ("video track length != narration", sh["id"], round(vd, 2), round(dur, 2))
    open(f"{work}/concat.txt", "w").write("".join(f"file '{f}'\n" for f in files))
    # audio: episode narration + fresh music bed (ducked under voice)
    TOT = dur + ECARD; N = int(TOT * SR); narr = narr[: int(dur * SR)]
    voice = np.zeros(N, np.float32); voice[: len(narr)] = narr
    m = rd(f"{D}/{sh['music']}"); m = np.roll(m, -int(sh.get('music_off', 0) * SR))
    m = np.tile(m, N // len(m) + 1)[:N].copy()
    vm = np.convolve((np.abs(voice) > 0.01).astype(np.float32), np.ones(SR // 4) / (SR // 4), "same")
    m *= (0.20 - 0.14 * np.clip(vm * 4, 0, 1))
    fade = np.ones(N, np.float32); fade[:SR] = np.linspace(0, 1, SR); fade[-SR:] = np.linspace(1, 0, SR)
    sf.write(f"{work}/mix0.wav", np.stack([voice + m * fade] * 2, 1), SR)
    _j = subprocess.run(["ffmpeg", "-nostats", "-i", f"{work}/mix0.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    _j = json.loads(_j[_j.rindex("{"):])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{work}/mix0.wav", "-af", f"loudnorm=I=-14:TP=-2.5:LRA=11:measured_I={_j['input_i']}:measured_TP={_j['input_tp']}:measured_LRA={_j['input_lra']}:measured_thresh={_j['input_thresh']}:offset={_j['target_offset']}:linear=true,alimiter=limit=0.75:level=false", "-ar", "48000", f"{work}/mix.wav"], check=True)
    # captions inside the phone safe zone (x 170..910, y 400..1220)
    ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV",
           "Style: Cap,Inter Display Black,76,&H00FFFFFF,&H00000000,&H64000000,1,1,6,2,2,170,170,700",
           "Style: Tag,Inter Display Black,40,&H0052A0D6,&H00000000,&H64000000,1,1,4,2,8,170,170,410",
           "Style: Top,Inter Display Black,58,&H00FFFFFF,&H00000000,&H64000000,1,1,5,2,8,160,160,400", "", "[Events]",
           "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
           f"Dialogue: 0,{at(0)},{at(3.2)},Top,,0,0,0,,{{\\fad(150,300)}}{sh['title'].upper()}",
           f"Dialogue: 0,{at(3.2)},{at(dur)},Tag,,0,0,0,,{{\\fad(300,200)}}▶ FULL DOCUMENTARY ON YOUTUBE"]
    names = set(sh.get("names", []))
    for x, y, p in cues:
        ws = []
        for w in p.split():
            gold = re.search(r"\d", w) or w.lower().strip(",.?!") in NUMW or w.strip(",.?!") in names
            ws.append(("{\\c&H52A0D6&}" + w + "{\\c&HFFFFFF&}") if gold else w)
        ass.append(f"Dialogue: 0,{at(x)},{at(y)},Cap,,0,0,0,,{{\\fad(60,60)}}{' '.join(ws)}")
    open(f"{work}/cap.ass", "w").write("\n".join(ass) + "\n")
    end_card(f"{work}/endcard.png", os.path.join(D, sh.get("thumb", CFG["thumb"])), sh.get("line1", CFG["line1"]), sh.get("line2", CFG["line2"]))
    out = f"{OUT}/zion_{part}_{sh['id']}.mp4"
    fc = (f"[0:v]fps=30,ass={work}/cap.ass:fontsdir=/usr/share/fonts/opentype/inter,tpad=stop_mode=clone:stop_duration={ECARD}[m];"
          f"[2:v]format=rgba,fade=t=in:st={dur:.2f}:d=0.4:alpha=1[ec];[m][ec]overlay=0:0:enable='gte(t,{dur:.2f})'[v];[1:a]anull[a]")
    if sh.get("audio_from"):   # same narration slice + music bed as the already-scheduled Short of this id (identical timing)
        fc = fc.replace("[1:a]loudnorm=I=-14:TP=-1.5[a]", "[1:a]anull[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{work}/concat.txt", "-i", sh.get("audio_from") or f"{work}/mix.wav",
                    "-loop", "1", "-framerate", "30", "-i", f"{work}/endcard.png", "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
                    "-t", f"{TOT:.2f}", "-movflags", "+faststart", out], check=True)
    # U1 guard (2026-11-03, z5 came out -15.3 LUFS after the limiter): re-level the finished file if it misses -14 +-0.8
    _m = subprocess.run(["ffmpeg", "-nostats", "-i", out, "-af", "loudnorm=I=-14:TP=-2:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    _m = json.loads(_m[_m.rindex("{"):])
    if abs(float(_m["input_i"]) + 14) > 0.8 or float(_m["input_tp"]) > -1.5:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-c:v", "copy", "-af", f"loudnorm=I=-14:TP=-2:LRA=11:measured_I={_m['input_i']}:measured_TP={_m['input_tp']}:measured_LRA={_m['input_lra']}:measured_thresh={_m['input_thresh']}:offset={_m['target_offset']}",
                        "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out + ".lv.mp4"], check=True); os.replace(out + ".lv.mp4", out)
    errs = subprocess.run(["ffmpeg", "-v", "error", "-i", out, "-f", "null", "-"], capture_output=True, text=True).stderr.strip()
    assert not errs, ("output does not decode cleanly", sh["id"], errs[:300])
    print(sh["id"], round(TOT, 1), "s,", len(files), "shots ->", out, flush=True)
