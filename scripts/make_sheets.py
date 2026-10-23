#!/usr/bin/env python3
"""Review sheets for any scan.json (stock_scan / pd_scan schema).
usage: make_sheets.py SCAN_JSON OUT_DIR [frames_per_clip=4]
For each clip: N frames sampled across the clip (ffmpeg seeks straight from the URL, using 'preview' if present),
one labeled row per clip (key, duration, source); rows grouped by query into OUT_DIR/<query-slug>.jpg (max 10 rows per page).
Also writes OUT_DIR/probe.json with real duration/size per key (and drops keys that fail)."""
import json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont

scan = json.load(open(sys.argv[1])); OUT = sys.argv[2]; N = int(sys.argv[3]) if len(sys.argv) > 3 else 4
os.makedirs(OUT, exist_ok=True); TW, TH = 320, 180
try: FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
except OSError: FONT = ImageFont.load_default()

def probe(url):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height", "-of", "json", url],
                       capture_output=True, text=True, timeout=120)
    try:
        j = json.loads(p.stdout); vs = [s for s in j.get("streams", []) if s.get("width")]
        return float(j["format"]["duration"]), (vs[0]["width"], vs[0]["height"]) if vs else (None, None)
    except Exception: return None, (None, None)

def row(r):
    url = r.get("preview") or r["full"]
    d, (w, h) = probe(url)
    if not d: return r["key"], None, None
    im = Image.new("RGB", (TW * N, TH), (0, 0, 0))
    for i in range(N):
        t = d * (i + 0.5) / N; f = f"/tmp/sh_{r['key']}_{i}.jpg"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", url, "-frames:v", "1", "-vf",
                        f"scale={TW}:{TH}:force_original_aspect_ratio=decrease,pad={TW}:{TH}:(ow-iw)/2:(oh-ih)/2", f],
                       capture_output=True, timeout=180)
        if os.path.exists(f):
            im.paste(Image.open(f).convert("RGB"), (i * TW, 0)); os.remove(f)
    d2 = ImageDraw.Draw(im); lab = f"{r['key']}  {d:.0f}s  {r.get('source','')}"
    d2.rectangle([0, 0, d2.textlength(lab, font=FONT) + 10, 24], fill=(0, 0, 0)); d2.text((5, 2), lab, font=FONT, fill=(255, 220, 0))
    return r["key"], im, {"duration": round(d, 2), "pw": w, "ph": h}

with ThreadPoolExecutor(8) as ex: res = list(ex.map(row, scan))
probe_out = {k: m for k, im, m in res if m}
rows = {k: im for k, im, m in res if im is not None}
groups = {}
for r in scan:
    if r["key"] in rows: groups.setdefault(r.get("q", "misc"), []).append(rows[r["key"]])
for q, ims in groups.items():
    slug = re.sub(r"[^a-z0-9]+", "_", q.lower()).strip("_")[:40] or "misc"
    for p in range(0, len(ims), 10):
        page = ims[p:p + 10]; sheet = Image.new("RGB", (TW * N, TH * len(page)), (0, 0, 0))
        for i, im in enumerate(page): sheet.paste(im, (0, i * TH))
        sheet.save(f"{OUT}/{slug}{'_' + str(p // 10 + 1) if p else ''}.jpg", quality=80)
json.dump(probe_out, open(f"{OUT}/probe.json", "w"), indent=1)
print("SHEETS", len(groups), "rows", len(rows), "of", len(scan))
