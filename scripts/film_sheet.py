#!/usr/bin/env python3
"""Dense timestamped contact sheet(s) for long films, read straight from URL.
usage: film_sheet.py OUT_DIR N_FRAMES KEY=URL [KEY=URL ...]   -> OUT_DIR/<KEY>_pN.jpg (6 cols x 6 rows per page)"""
import os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont
OUT, N = sys.argv[1], int(sys.argv[2]); os.makedirs(OUT, exist_ok=True); TW, TH, C, R = 320, 180, 6, 6
try: FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
except OSError: FONT = ImageFont.load_default()
UA = ["-user_agent", "AlphaDogStudio/1.0 (documentary research; github.com/Rodantmat/Alphadog-Social)"]
def frame(args):
    key, url, i, t = args; f = f"/tmp/fs_{key}_{i}.jpg"
    subprocess.run(["ffmpeg", "-y", "-v", "error"] + (UA if url.startswith("http") else []) + ["-ss", f"{t:.1f}", "-i", url, "-frames:v", "1", "-vf",
                    f"scale={TW}:{TH}:force_original_aspect_ratio=decrease,pad={TW}:{TH}:(ow-iw)/2:(oh-ih)/2", f], capture_output=True, timeout=240)
    return i, t, f
for kv in sys.argv[3:]:
    key, url = kv.split("=", 1)
    p = subprocess.run(["ffprobe", "-v", "error"] + (UA if url.startswith("http") else []) + ["-show_entries", "format=duration", "-of", "csv=p=0", url], capture_output=True, text=True, timeout=180)
    try: d = float(p.stdout.strip())
    except ValueError: print("NO_PROBE", key); continue
    jobs = [(key, url, i, d * (i + 0.5) / N) for i in range(N)]
    with ThreadPoolExecutor(6) as ex: res = sorted(ex.map(frame, jobs))
    per = C * R
    for pg in range(0, len(res), per):
        sheet = Image.new("RGB", (TW * C, TH * R)); dd = ImageDraw.Draw(sheet)
        for j, (i, t, f) in enumerate(res[pg:pg + per]):
            x, y = (j % C) * TW, (j // C) * TH
            if os.path.exists(f): sheet.paste(Image.open(f).convert("RGB"), (x, y)); os.remove(f)
            lab = f"{int(t // 60)}:{int(t % 60):02d}"; dd.rectangle([x, y, x + 62, y + 22], fill=(0, 0, 0)); dd.text((x + 3, y + 1), lab, font=FONT, fill=(255, 220, 0))
        sheet.save(f"{OUT}/{key}_p{pg // per + 1}.jpg", quality=80)
    print("SHEET", key, round(d), "s")
