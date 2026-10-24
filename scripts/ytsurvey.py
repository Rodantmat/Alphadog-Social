#!/usr/bin/env python3
"""Survey whole Creative-Commons YouTube videos we already credit: 360p video-only download through WARP, then dense
contact sheets (one frame every STEP s, timestamped) so clean windows can be picked anywhere in the video, not just the
pieces cut so far. Usage: ytsurvey.py OUT_DIR STEP key1 key2 ...  (keys like yt_<id>). Writes OUT_DIR/<key>_pNN.jpg + survey.json"""
import json, os, subprocess, sys, time
from PIL import Image, ImageDraw, ImageFont

PROXY = os.environ.get("YT_PROXY", "socks5://127.0.0.1:40000")
YT = ["yt-dlp", "--no-warnings", "--proxy", PROXY, "--extractor-args", "youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416",
      "--downloader", "native", "--sleep-requests", "1", "--retries", "5", "--fragment-retries", "10"]
TW, TH, COLS, ROWS = 240, 135, 10, 10
try: FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
except OSError: FONT = ImageFont.load_default()

def sh(cmd, timeout=1800):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout); return p.returncode, p.stdout, p.stderr[-400:]
    except subprocess.TimeoutExpired: return 124, "", "timeout"

def new_warp():
    for c in (["warp-cli", "--accept-tos", "disconnect"], ["warp-cli", "--accept-tos", "registration", "delete"],
              ["warp-cli", "--accept-tos", "registration", "new"], ["warp-cli", "--accept-tos", "mode", "proxy"],
              ["warp-cli", "--accept-tos", "connect"]):
        sh(c, 60); time.sleep(2)
    time.sleep(10)

OUT, STEP, keys = sys.argv[1], float(sys.argv[2]), sys.argv[3:]
os.makedirs(OUT, exist_ok=True); summary = []
for key in keys:
    vid = key[3:]; pv = None
    for attempt in range(4):
        sh(YT + ["-f", "bv*[height<=360][ext=mp4]/bv*[height<=360]/b[height<=360]", "-o", f"/tmp/sv_{vid}.%(ext)s",
                 f"https://www.youtube.com/watch?v={vid}"])
        got = [f for f in os.listdir("/tmp") if f.startswith(f"sv_{vid}.") and not f.endswith((".part", ".ytdl"))]
        if got: pv = "/tmp/" + got[0]; break
        new_warp()
    if not pv: print("SURVEY_FAIL", key, flush=True); continue
    rc, so, _ = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", pv], 60)
    D = float(so.strip() or 0); fr = f"/tmp/fr_{vid}"; os.makedirs(fr, exist_ok=True)
    sh(["ffmpeg", "-v", "error", "-i", pv, "-vf", f"fps=1/{STEP},scale={TW}:{TH}:force_original_aspect_ratio=decrease,pad={TW}:{TH}:(ow-iw)/2:(oh-ih)/2",
        f"{fr}/%05d.jpg"], 3600)
    frames = sorted(os.listdir(fr)); per = COLS * ROWS; pages = 0
    for p in range(0, len(frames), per):
        sheet = Image.new("RGB", (TW * COLS, TH * ROWS)); dr = ImageDraw.Draw(sheet)
        for i, f in enumerate(frames[p:p + per]):
            x, y = (i % COLS) * TW, (i // COLS) * TH; sheet.paste(Image.open(f"{fr}/{f}"), (x, y))
            t = (p + i) * STEP; lab = f"{int(t // 60)}:{int(t % 60):02d}"
            dr.rectangle([x, y, x + 52, y + 19], fill=(0, 0, 0)); dr.text((x + 3, y + 1), lab, font=FONT, fill=(255, 220, 0))
        sheet.save(f"{OUT}/{key}_p{pages:02d}.jpg", quality=72); pages += 1
    summary.append({"key": key, "duration": D, "step": STEP, "pages": pages}); print("SURVEYED", key, D, pages, flush=True)
    os.remove(pv); subprocess.run(["rm", "-rf", fr])
    json.dump(summary, open(f"{OUT}/survey.json", "w"), indent=1)
