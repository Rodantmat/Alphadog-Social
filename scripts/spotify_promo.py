#!/usr/bin/env python3
"""Spotify promo (vertical 1080x1920, phone-safe) cut from the published Episode 1 (release artifact of chiricahua-v5).
Window = the Bascom tent story, located by subtitle text so it follows the final timing.
v2 (recipe-audit fixes): face-aware caption slots (V3), title only for 3.6 s, end card inside the safe area (V1),
flash shots < 0.5 s (incl. dips to black) replaced by the first frame of the next shot (R7, Q4), end card starts on a cut, true peak <= -2 dBTP (U1).
Audit feedback: env FIX_FLASH="a-b,..." (seconds) frames to hold, END_AT=seconds where the end card starts.
Usage: spotify_promo.py EPISODE_MP4 EPISODE_EN_SRT OUT_DIR   (env FACE_MODEL = YuNet onnx, default /tmp/yunet.onnx)"""
import re, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
SRC, SRT, OUT = sys.argv[1:4]; os.makedirs(OUT, exist_ok=True); os.chdir(OUT)
W, H = 1080, 1920; TAIL = 3.0
FD = "/usr/share/fonts/opentype/inter"; B = f"{FD}/InterDisplay-Black.otf"; M = f"{FD}/Inter-Bold.otf"
def run(*a): subprocess.run(list(a), check=True)
def font(p, s): return ImageFont.truetype(p, s)
def ts(x): h, m, s, ms = map(int, re.match(r"(\d+):(\d+):(\d+),(\d+)", x).groups()); return h * 3600 + m * 60 + s + ms / 1000
subs = []
for b in open(SRT, encoding="utf-8").read().strip().split("\n\n"):
    l = b.strip().split("\n"); a, e = [ts(x) for x in l[1].split(" --> ")]; subs.append((a, e, " ".join(l[2:])))
norm = lambda t: re.sub(r"[^a-z ]", "", t.lower())
T0 = next(a for a, e, t in subs if norm(t).startswith("the army assumed cochise")) - 0.3
T1 = next(e for a, e, t in subs if "spiraled out of control" in norm(t)) + 0.02
DUR = T1 - T0 + TAIL; ENDC = T1 - T0 - 1.6
print(f"window {T0:.2f}-{T1:.2f} dur {DUR:.2f}")
# cover frame (spires) for the end card
run("ffmpeg", "-v", "error", "-y", "-ss", "760", "-i", SRC, "-frames:v", "1", "spires.png")
def cover(size):
    im = Image.open("spires.png").convert("RGB"); w, h = im.size; x0 = (w - h) // 2 + 80
    sq = ImageEnhance.Contrast(im.crop((x0, 0, x0 + h, h)).resize((3000, 3000), Image.LANCZOS)).enhance(1.06)
    g = Image.new("L", (3000, 3000), 0); d = ImageDraw.Draw(g)
    for y in range(3000): d.line([(0, y), (3000, y)], fill=int(200 * max(0, 1 - y / 1300)) if y < 1300 else int(170 * max(0, (y - 2200) / 800)))
    sq = Image.composite(Image.new("RGB", (3000, 3000), (8, 10, 20)), sq, g); d = ImageDraw.Draw(sq)
    def fit(t, maxw, s):
        while font(B, s).getlength(t) > maxw: s -= 5
        return font(B, s)
    def ct(y, t, f, c): d.text((1500, y), t, font=f, fill=c, anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
    ct(330, "AMERICA'S", font(M, 130), (255, 255, 255)); f = fit("NATIONAL PARKS", 2500, 330); ct(600, "NATIONAL PARKS", f, (255, 255, 255))
    ct(600 + f.size + 20, "THE HIDDEN HISTORY", fit("THE HIDDEN HISTORY", 2500, 330), (255, 205, 60)); ct(2800, "ALPHADOG STUDIO", font(M, 120), (255, 255, 255))
    return sq.resize((size, size), Image.LANCZOS)
# overlays (text only inside x 170..910, y 400..1220): gradient (always), pill (always), title (first 3.6 s)
g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
for y in range(0, 760): gd.line([(0, y), (W, y)], fill=(0, 0, 0, int(150 * max(0, 1 - y / 760))))
for y in range(1000, H): gd.line([(0, y), (W, y)], fill=(0, 0, 0, int(190 * min(1, (y - 1000) / 420))))
g.save("grad.png")
pill = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pdr = ImageDraw.Draw(pill)
pf = font(B, 58); txt = "NOW ON SPOTIFY"; tw = pdr.textlength(txt, font=pf); x0 = (W - tw - 70) // 2
pdr.rounded_rectangle((x0, 405, x0 + tw + 70, 495), radius=45, fill=(30, 215, 96, 255)); pdr.text((W // 2, 450), txt, font=pf, fill=(0, 0, 0), anchor="mm")
pill.save("pill.png")
img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
for i, (l, c) in enumerate([("THE WAR THAT", (255, 255, 255)), ("STARTED IN A TENT", (255, 205, 60))]):
    f = font(B, 76)
    while f.getlength(l) > 740: f = font(B, f.size - 2)
    d.text((W // 2, 575 + i * 88), l, font=f, fill=c, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
img.save("title.png")
# end card
bg = Image.open("spires.png").convert("RGB"); s = max(W / bg.width, H / bg.height); bg = bg.resize((int(bg.width * s) + 1, int(bg.height * s) + 1))
bg = bg.crop(((bg.width - W) // 2, 0, (bg.width - W) // 2 + W, H)).filter(ImageFilter.GaussianBlur(30))
bg = Image.blend(bg, Image.new("RGB", (W, H), (10, 10, 16)), 0.55); bg.paste(cover(540), ((W - 540) // 2, 410)); d = ImageDraw.Draw(bg)
d.text((W // 2, 1000), "What happened next", font=font(M, 44), fill=(255, 255, 255), anchor="mm")
d.text((W // 2, 1052), "started 11 years of war.", font=font(M, 44), fill=(255, 255, 255), anchor="mm")
f = font(B, 48); t = "FULL EPISODE ON SPOTIFY"; tw = f.getlength(t)
d.rounded_rectangle(((W - tw) // 2 - 40, 1100, (W + tw) // 2 + 40, 1190), radius=45, fill=(30, 215, 96)); d.text((W // 2, 1145), t, font=f, fill=(0, 0, 0), anchor="mm")
bg.save("endcard.png")
# captions: subtitle cues re-split into phrases of <= 4 words
cues = []
for a, e, text in subs:
    if e <= T0 or a >= T1: continue
    ph, cur = [], []
    for w in text.split():
        cur.append(w)
        if len(cur) >= 4 or (len(cur) >= 2 and w[-1] in ",.?!:"): ph.append(" ".join(cur)); cur = []
    if cur: ph.append(" ".join(cur))
    tot = sum(len(p) for p in ph); t = a
    for p in ph: dd = (e - a) * len(p) / tot; cues.append((t - T0, t - T0 + dd, p)); t += dd
def at(x): x = max(0, x); h, r = divmod(x, 3600); m, s_ = divmod(r, 60); return f"{int(h)}:{int(m):02d}:{s_:05.2f}"
ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Cap,Inter Display Black,72,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,5,2,2,170,170,720,1", "", "[Events]",
       "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
# --- base picture (vertical crop), flash repair, face-aware caption placement
import cv2, numpy as np
run("ffmpeg", "-v", "error", "-y", "-ss", f"{T0:.3f}", "-t", f"{T1 - T0:.3f}", "-i", SRC, "-an", "-vf",
    "scale=-2:1920,crop=1080:1920,setsar=1,fps=30,eq=brightness=-0.03", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "base.mp4")
cap = cv2.VideoCapture("base.mp4"); prev = None; mad = []
while True:
    ok, fr = cap.read()
    if not ok: break
    g_ = cv2.resize(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY), (90, 160)).astype(np.float32)
    mad.append(float(np.mean(np.abs(g_ - prev))) if prev is not None else 0.0); prev = g_
mad = np.array(mad)
# hard cut = a one-frame spike well above its neighbourhood (dissolves change gradually and are not counted)
cuts = [i for i in range(1, len(mad)) if mad[i] > 18 and mad[i] > 3 * np.median(mad[max(0, i - 6):i + 7])]
flashes = [(a, b) for a, b in zip(cuts, cuts[1:]) if 2 < b - a < 15] if os.environ.get("AUTO_FLASH") == "1" else []   # own detector is weak on fast AI motion: off by default, audit feeds FIX_FLASH
# fixes fed back from recipe-audit (R7): FIX_FLASH="32.82-33.17,..." seconds into the promo; END_AT = cut where the end card starts
for rng_ in filter(None, os.environ.get("FIX_FLASH", "").split(",")):
    a_, b_ = [float(x) for x in rng_.split("-")]; flashes.append((max(1, round(a_ * 30)), round(b_ * 30)))
flashes = sorted(set(flashes))
print("hard cuts at", [round(c / 30, 2) for c in cuts], "flash repairs (frames):", flashes)
if flashes:
    fg, last = [], "[0:v]"
    for n_, (a, b) in enumerate(flashes):
        fg.append(f"{last}split[m{n_}][r{n_}];[m{n_}][r{n_}]freezeframes=first={a}:last={b - 1}:replace={b}[f{n_}]"); last = f"[f{n_}]"
    run("ffmpeg", "-v", "error", "-y", "-i", "base.mp4", "-filter_complex", ";".join(fg), "-map", last,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "base_fixed.mp4")
else:
    os.replace("base.mp4", "base_fixed.mp4")
det = None; mp = os.environ.get("FACE_MODEL", "/tmp/yunet.onnx")
if os.path.exists(mp): det = cv2.FaceDetectorYN.create(mp, "", (W // 2, H // 2), 0.6)
try: haar = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
except Exception: haar = None
print("face detector:", "yunet" if det is not None else ("haar" if haar is not None else "none"))
def faces_at(t):
    c2 = cv2.VideoCapture("base_fixed.mp4"); c2.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, fr = c2.read(); c2.release()
    if not ok: return []
    sm = cv2.resize(fr, (W // 2, H // 2))
    if det is not None:
        _, f = det.detect(sm); f = [] if f is None else f
        return [(x * 2, y * 2, w * 2, h * 2) for x, y, w, h in [r[:4] for r in f]]
    if haar is None: return []
    return [(x * 2, y * 2, w * 2, h * 2) for x, y, w, h in haar.detectMultiScale(cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY), 1.1, 5, minSize=(30, 30))]
SLOTS = [("bottom", 700, (1050, 1225)), ("middle", 960, (790, 965)), ("top", 1240, (520, 690))]   # MarginV, caption box y-range
def overlap(box, fs):
    y0, y1 = box; tot = 0
    for x, y, w, h in fs:
        if x + w < 170 or x > 910: continue
        tot += max(0, min(y1, y + h) - max(y0, y))
    return tot
late = [c / 30 for c in cuts if ENDC - 1.2 < c / 30 < ENDC]
if os.environ.get("END_AT"): late = [float(os.environ["END_AT"])]
if late: ENDC = late[-1]; print("end card moved to the last cut at", round(ENDC, 2))
placed = []
for a, e, p in cues:
    if a >= ENDC: continue
    fs = [f for t in (a + 0.05, (a + e) / 2, e - 0.05) for f in faces_at(t)]
    if a < 3.7: fs += [(170, 405, 740, 330)]            # keep clear of the title while it shows
    best = min(SLOTS, key=lambda sl: (overlap(sl[2], fs), SLOTS.index(sl)))
    placed.append(best[0])
    ass.append(f"Dialogue: 0,{at(a)},{at(min(e, ENDC))},Cap,,0,0,{best[1]},,{{\\fad(60,60)}}{p.upper()}")
print("caption slots:", {k: placed.count(k) for k in set(placed)})
open("cap.ass", "w").write("\n".join(ass) + "\n")
fc = (f"[0:v]null[bg];"
      f"[1:a]atrim=0:{T1-T0:.3f},asetpts=PTS-STARTPTS,apad=pad_dur={TAIL},afade=t=out:st={T1-T0-0.4:.2f}:d=1.2,loudnorm=I=-14:TP=-2.0,alimiter=limit=0.78:level=disabled,asplit[a][aw];"
      f"[aw]showwaves=s=740x110:mode=cline:colors=0x1ED760:scale=sqrt:rate=30,format=rgba,colorchannelmixer=aa=0.9[wv];"
      f"[bg][2:v]overlay=0:0[g1];[g1][3:v]overlay=0:0[g2];[4:v]format=rgba,fade=t=out:st=3.0:d=0.6:alpha=1[tt];[g2][tt]overlay=0:0:enable='lt(t,3.7)'[t1];"
      f"[t1][wv]overlay=170:1250[t2];[t2]ass=cap.ass:fontsdir={FD}[t3];"
      f"[5:v]format=rgba,fade=t=in:st=0:d=0.5:alpha=1[ec];[t3][ec]overlay=0:0:enable='gte(t,{ENDC:.2f})'[t4];"
      f"[t4]fade=t=in:st=0:d=0.4,fade=t=out:st={DUR-0.6:.2f}:d=0.6,format=yuv420p[v]")
run("ffmpeg", "-v", "error", "-y", "-i", "base_fixed.mp4", "-ss", f"{T0:.3f}", "-t", f"{T1 - T0:.3f}", "-i", SRC,
    "-loop", "1", "-t", f"{DUR:.3f}", "-i", "grad.png", "-loop", "1", "-t", f"{DUR:.3f}", "-i", "pill.png",
    "-loop", "1", "-t", f"{DUR:.3f}", "-i", "title.png", "-loop", "1", "-t", f"{DUR:.3f}", "-i", "endcard.png",
    "-filter_complex", "[0:v]tpad=stop_mode=clone:stop_duration=" + f"{TAIL:.2f}" + "[pv];" + fc.replace("[0:v]null[bg]", "[pv]null[bg]"),
    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-maxrate", "8M", "-bufsize", "16M", "-c:a", "aac", "-b:a", "192k",
    "-t", f"{DUR:.3f}", "-movflags", "+faststart", "spotify_promo_ep1.mp4")
d_ = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", "spotify_promo_ep1.mp4"], capture_output=True, text=True).stdout)
assert 30 < d_ < 59.5, d_
run("ffmpeg", "-v", "error", "-y", "-i", "spotify_promo_ep1.mp4", "-vf", "fps=1,scale=216:-2,tile=10x6", "-frames:v", "1", "-q:v", "5", "qa_sheet.jpg")
print("PROMO_OK", round(d_, 2))
