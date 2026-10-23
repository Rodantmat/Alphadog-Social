#!/usr/bin/env python3
"""Creative Commons YouTube footage via Cloudflare WARP (runner must expose WARP SOCKS on 127.0.0.1:40000).
scan:  ytcc.py scan OUT_DIR PER_QUERY @queries.txt
       CC-filtered search -> verify license in metadata -> 360p video-only preview (native downloader, through WARP)
       -> OUT_DIR/scan.json + OUT_DIR/review/<query>.jpg (one row per video, 8 frames, timestamps)
fetch: ytcc.py fetch OUT_DIR picks.json    picks = [{"key": "yt_<id>", "ss": 12.0, "dur": 8, "tag": "...", "audio": false}]
       -> 1080p download per video (once; with audio if any pick asks for it), trimmed pieces OUT_DIR/<key>_<ss>.mp4 + index.json.
       If YouTube refuses the WARP address, the WARP registration is renewed (new address) and the download retried."""
import json, os, re, subprocess, sys, time, urllib.parse
from PIL import Image, ImageDraw, ImageFont

PROXY = os.environ.get("YT_PROXY", "socks5://127.0.0.1:40000")
YT = ["yt-dlp", "--no-warnings", "--proxy", PROXY, "--extractor-args", "youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416",
      "--downloader", "native", "--sleep-requests", "1", "--retries", "5", "--fragment-retries", "10"]
TW, TH, NF = 320, 180, 8
try: FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
except OSError: FONT = ImageFont.load_default()

def sh(cmd, timeout=900):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout); return p.returncode, p.stdout, p.stderr[-600:]
    except subprocess.TimeoutExpired: return 124, "", "timeout"

def new_warp():
    for c in (["warp-cli", "--accept-tos", "disconnect"], ["warp-cli", "--accept-tos", "registration", "delete"],
              ["warp-cli", "--accept-tos", "registration", "new"], ["warp-cli", "--accept-tos", "mode", "proxy"],
              ["warp-cli", "--accept-tos", "connect"]):
        sh(c, 60); time.sleep(2)
    time.sleep(10)
    rc, so, _ = sh(["curl", "-s", "-x", "socks5h://127.0.0.1:40000", "https://www.cloudflare.com/cdn-cgi/trace"], 30)
    print("WARP_RENEWED", " ".join(l for l in so.splitlines() if l.startswith(("ip=", "warp="))), flush=True)

def dur(path):
    rc, so, _ = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], 60)
    try: return float(so.strip())
    except ValueError: return 0

def row_image(path, label):
    d = dur(path); im = Image.new("RGB", (TW * NF, TH), (0, 0, 0))
    for i in range(NF):
        t = d * (i + 0.5) / NF; f = f"/tmp/rowf_{i}.jpg"
        sh(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1", "-vf",
            f"scale={TW}:{TH}:force_original_aspect_ratio=decrease,pad={TW}:{TH}:(ow-iw)/2:(oh-ih)/2", f], 120)
        if os.path.exists(f):
            fr = Image.open(f).convert("RGB"); dd = ImageDraw.Draw(fr)
            ts = f"{int(t // 60)}:{int(t % 60):02d}"; dd.rectangle([TW - 62, TH - 24, TW, TH], fill=(0, 0, 0)); dd.text((TW - 58, TH - 22), ts, font=FONT, fill=(255, 255, 255))
            im.paste(fr, (i * TW, 0)); os.remove(f)
    dd = ImageDraw.Draw(im); dd.rectangle([0, 0, dd.textlength(label, font=FONT) + 10, 24], fill=(0, 0, 0)); dd.text((5, 2), label, font=FONT, fill=(255, 220, 0))
    return im

mode, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)

if mode == "scan":
    per = int(sys.argv[3]); qa = sys.argv[4]
    queries = [l.strip() for l in open(qa[1:]) if l.strip() and not l.startswith("#")] if qa.startswith("@") else sys.argv[4:]
    os.makedirs(f"{OUT}/review", exist_ok=True); cands = {}
    for q in queries:
        url = "https://www.youtube.com/results?" + urllib.parse.urlencode({"search_query": q, "sp": "EgIwAQ=="})
        rc, so, se = sh(YT + ["--flat-playlist", "--playlist-items", f"1:{per}", "--print", "%(id)s", url], 300)
        ids = [l.strip() for l in so.splitlines() if l.strip()]; rows = []
        print("SEARCH", q, len(ids), se[-150:].replace("\n", " ") if not ids else "", flush=True)
        for vid in ids:
            key = f"yt_{vid}"
            if key in cands: continue
            rc, so, se = sh(YT + ["-j", "--skip-download", f"https://www.youtube.com/watch?v={vid}"], 180)
            if rc or not so.strip(): print("META_FAIL", vid, se[-150:].replace("\n", " "), flush=True); continue
            j = json.loads(so.splitlines()[0]); lic = j.get("license") or ""
            if "creative commons" not in lic.lower(): print("NOT_CC", vid, lic); continue
            if (j.get("duration") or 0) > 3600 or (j.get("duration") or 0) < 8: continue
            r = {"key": key, "id": vid, "source": "youtube-cc", "page": f"https://www.youtube.com/watch?v={vid}", "title": j.get("title"),
                 "channel": j.get("channel") or j.get("uploader"), "channel_url": j.get("channel_url"), "license": lic,
                 "duration": j.get("duration"), "height": j.get("height"), "views": j.get("view_count"), "upload_date": j.get("upload_date"),
                 "credit": f"\"{j.get('title')}\" by {j.get('channel') or j.get('uploader')} (youtube.com/watch?v={vid}), licensed CC BY",
                 "desc": (j.get("description") or "")[:400], "q": q}
            pv = f"/tmp/pv_{vid}.mp4"
            rc, so, se = sh(YT + ["-f", "bv*[height<=360][ext=mp4]/bv*[height<=360]/b[height<=360]", "-o", pv, r["page"]], 900)
            if not os.path.exists(pv):
                cand = [f for f in os.listdir("/tmp") if f.startswith(f"pv_{vid}")]
                pv = "/tmp/" + cand[0] if cand else None
            if not pv: print("PREVIEW_FAIL", vid, se[-200:].replace("\n", " "), flush=True); continue
            rows.append(row_image(pv, f"{key}  {int(r['duration'] or 0)}s  {(r['title'] or '')[:50]}")); os.remove(pv)
            cands[key] = r; print("CAND", key, r["duration"], r["height"], "|", (r["title"] or "")[:70], "|", r["channel"], flush=True)
        if rows:
            slug = re.sub(r"[^a-z0-9]+", "_", q.lower()).strip("_")[:40]
            for p in range(0, len(rows), 8):
                page = rows[p:p + 8]; sheet = Image.new("RGB", (TW * NF, TH * len(page)))
                for i, im in enumerate(page): sheet.paste(im, (0, i * TH))
                sheet.save(f"{OUT}/review/{slug}{'_' + str(p // 8 + 1) if p else ''}.jpg", quality=78)
        json.dump(list(cands.values()), open(f"{OUT}/scan.json", "w"), indent=1)
    print("SCAN_TOTAL", len(cands))

elif mode == "fetch":
    picks = json.load(open(sys.argv[3])); scan = {}
    for sf in [l for l in os.environ.get("SCAN_FILES", "").split(",") if l]:
        for r in json.load(open(sf)): scan[r["key"]] = r
    idx, have = [], {}
    audio_vids = {p["key"][3:] for p in picks if p.get("audio")}
    def download(vid, page):
        raw = f"/tmp/full_{vid}"
        fmt = "bv*[height<=1080]+ba/b[height<=1080]" if vid in audio_vids else "bv*[height<=1080][ext=mp4]/bv*[height<=1080]/b[height<=1080]"
        for attempt in range(4):
            rc, so, se = sh(YT + ["-f", fmt, "--merge-output-format", "mp4", "-o", raw + ".%(ext)s", page], 2400)
            got = [f for f in os.listdir("/tmp") if f.startswith(f"full_{vid}.") and not f.endswith((".part", ".ytdl"))]
            if got: return "/tmp/" + got[0]
            print("DL_RETRY", vid, attempt, se[-160:].replace("\n", " "), flush=True)
            if "Sign in" in se or "bot" in se or "403" in se: new_warp()
            else: time.sleep(15)
        return None
    for p in picks:
        r = scan.get(p["key"]) or {"key": p["key"], "id": p["key"][3:], "page": f"https://www.youtube.com/watch?v={p['key'][3:]}"}
        vid = r["id"]
        if vid not in have:
            have[vid] = download(vid, r["page"])
        src = have[vid]
        if not src: print("DL_FAIL", vid, flush=True); continue
        name = f"{p['key']}_{int(float(p.get('ss', 0)))}.mp4"
        cmd = ["ffmpeg", "-y", "-v", "error", "-ss", str(p.get("ss", 0)), "-i", src]
        if p.get("dur"): cmd += ["-t", str(p["dur"])]
        cmd += (["-c:a", "aac", "-b:a", "160k"] if p.get("audio") else ["-an"]) + ["-vf", "scale='min(1920,iw)':-2,fps=30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
                "-map_metadata", "-1", "-movflags", "+faststart", f"{OUT}/{name}"]
        sh(cmd)
        if os.path.exists(f"{OUT}/{name}"):
            idx.append({**r, **p, "file": name}); print("SAVED", name, flush=True)
    json.dump(idx, open(f"{OUT}/index.json", "w"), indent=1)
    print("FETCH_TOTAL", len(idx))
