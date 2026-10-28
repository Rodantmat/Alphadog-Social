#!/usr/bin/env python3
"""Spotify promo (vertical 1080x1920, phone-safe) cut from the published Episode 1 (release artifact of chiricahua-v5).
Window = the Bascom tent story, located by subtitle text so it follows the final timing.
Usage: spotify_promo.py EPISODE_MP4 EPISODE_EN_SRT OUT_DIR"""
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
# title overlay (text only inside x 170..910, y 400..1220)
img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
for y in range(0, 760): gd.line([(0, y), (W, y)], fill=(0, 0, 0, int(170 * max(0, 1 - y / 760))))
for y in range(1000, H): gd.line([(0, y), (W, y)], fill=(0, 0, 0, int(190 * min(1, (y - 1000) / 420))))
img.alpha_composite(g)
pf = font(M, 34); txt = "NOW ON SPOTIFY"; tw = d.textlength(txt, font=pf); x0 = (W - tw - 60) // 2
d.rounded_rectangle((x0, 415, x0 + tw + 60, 475), radius=30, fill=(30, 215, 96, 255)); d.text((W // 2, 445), txt, font=pf, fill=(0, 0, 0), anchor="mm")
for i, (l, c) in enumerate([("THE WAR THAT", (255, 255, 255)), ("STARTED IN A TENT", (255, 205, 60))]):
    f = font(B, 76)
    while f.getlength(l) > 740: f = font(B, f.size - 2)
    d.text((W // 2, 545 + i * 88), l, font=f, fill=c, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
img.save("title.png")
# end card
bg = Image.open("spires.png").convert("RGB"); s = max(W / bg.width, H / bg.height); bg = bg.resize((int(bg.width * s) + 1, int(bg.height * s) + 1))
bg = bg.crop(((bg.width - W) // 2, 0, (bg.width - W) // 2 + W, H)).filter(ImageFilter.GaussianBlur(30))
bg = Image.blend(bg, Image.new("RGB", (W, H), (10, 10, 16)), 0.55); bg.paste(cover(620), ((W - 620) // 2, 420)); d = ImageDraw.Draw(bg)
d.text((W // 2, 1100), "What happened next", font=font(M, 44), fill=(255, 255, 255), anchor="mm")
d.text((W // 2, 1155), "started 11 years of war.", font=font(M, 44), fill=(255, 255, 255), anchor="mm")
f = font(B, 48); t = "FULL EPISODE ON SPOTIFY"; tw = f.getlength(t)
d.rounded_rectangle(((W - tw) // 2 - 40, 1200, (W + tw) // 2 + 40, 1290), radius=45, fill=(30, 215, 96)); d.text((W // 2, 1246), t, font=f, fill=(0, 0, 0), anchor="mm")
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
for a, e, p in cues:
    if a < ENDC: ass.append(f"Dialogue: 0,{at(a)},{at(min(e, ENDC))},Cap,,0,0,0,,{{\\fad(60,60)}}{p.upper()}")
open("cap.ass", "w").write("\n".join(ass) + "\n")
fc = (f"[0:v]scale=-2:1920,crop=1080:1920,setsar=1,fps=30,eq=brightness=-0.03[bg];"
      f"[0:a]atrim=0:{T1-T0:.3f},asetpts=PTS-STARTPTS,apad=pad_dur={TAIL},afade=t=out:st={T1-T0-0.4:.2f}:d=1.2,loudnorm=I=-14:TP=-1.5,asplit[a][aw];"
      f"[aw]showwaves=s=740x110:mode=cline:colors=0x1ED760:scale=sqrt:rate=30,format=rgba,colorchannelmixer=aa=0.9[wv];"
      f"[bg][1:v]overlay=0:0[t1];[t1][wv]overlay=170:1250[t2];[t2]ass=cap.ass:fontsdir={FD}[t3];"
      f"[2:v]format=rgba,fade=t=in:st=0:d=0.5:alpha=1[ec];[t3][ec]overlay=0:0:enable='gte(t,{ENDC:.2f})'[t4];"
      f"[t4]fade=t=in:st=0:d=0.4,fade=t=out:st={DUR-0.6:.2f}:d=0.6,format=yuv420p[v]")
run("ffmpeg", "-v", "error", "-y", "-ss", f"{T0:.3f}", "-t", f"{DUR:.3f}", "-i", SRC, "-loop", "1", "-t", f"{DUR:.3f}", "-i", "title.png",
    "-loop", "1", "-t", f"{DUR:.3f}", "-i", "endcard.png", "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
    "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-maxrate", "8M", "-bufsize", "16M", "-c:a", "aac", "-b:a", "192k",
    "-t", f"{DUR:.3f}", "-movflags", "+faststart", "spotify_promo_ep1.mp4")
d_ = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", "spotify_promo_ep1.mp4"], capture_output=True, text=True).stdout)
assert 30 < d_ < 59.5, d_
run("ffmpeg", "-v", "error", "-y", "-i", "spotify_promo_ep1.mp4", "-vf", "fps=1,scale=216:-2,tile=10x6", "-frames:v", "1", "-q:v", "5", "qa_sheet.jpg")
print("PROMO_OK", round(d_, 2))
