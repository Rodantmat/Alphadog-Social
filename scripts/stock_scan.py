#!/usr/bin/env python3
"""Stock video scan/fetch for Pexels + Pixabay (API keys in env PEXELS_API_KEY / PIXABAY_API_KEY); fetch also works for any
scan.json with a "full" URL (archive.org, LoC, Commons, Coverr).
scan:  stock_scan.py scan OUT_DIR PER_QUERY @queries.txt
       -> OUT_DIR/scan.json (every candidate with id, source, url, credit, duration, size) and
          OUT_DIR/sheets/<query-slug>.jpg (one row per clip: 4 frames from the smallest rendition, labeled with clip key)
fetch: stock_scan.py fetch OUT_DIR picks.json      (env SCAN_FILES=comma-separated scan.json paths)
       picks.json = [{"key": "px_123", "ss": 0, "dur": 12, "tag": "...", "audio": false}, ...]  (key from scan.json)
       -> OUT_DIR/<key>_<ss>.mp4 (1080p max, trimmed; audio only if asked) and OUT_DIR/index.json with credits"""
import json, os, re, subprocess, sys, time, urllib.parse, urllib.request

PX = os.environ.get("PEXELS_API_KEY", "").strip(); PB = os.environ.get("PIXABAY_API_KEY", "").strip()
UA = {"User-Agent": "AlphaDogStudio/1.0 (documentary research)"}

def jget(url, headers=None):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read())

def dl(url, path):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=300) as r, open(path, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b: break
            f.write(b)

def sh(cmd, timeout=900):
    try: return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).returncode
    except subprocess.TimeoutExpired: return 124

def pexels(q, n):
    if not PX: return []
    j = jget("https://api.pexels.com/videos/search?" + urllib.parse.urlencode({"query": q, "per_page": n, "orientation": "landscape"}),
             {"Authorization": PX})
    out = []
    for v in j.get("videos", []):
        files = sorted([f for f in v.get("video_files", []) if f.get("width")], key=lambda f: f["width"])
        if not files: continue
        hd = [f for f in files if f["width"] <= 1920] or files
        out.append({"key": f"px_{v['id']}", "source": "pexels", "page": v.get("url"), "duration": v.get("duration"),
                    "w": v.get("width"), "h": v.get("height"), "preview": files[0]["link"], "full": hd[-1]["link"],
                    "credit": f"{v.get('user', {}).get('name')} / Pexels", "q": q})
    return out

def pixabay(q, n):
    if not PB: return []
    j = jget("https://pixabay.com/api/videos/?" + urllib.parse.urlencode({"key": PB, "q": q, "per_page": max(3, n), "safesearch": "true"}))
    out = []
    for v in j.get("hits", []):
        vs = v.get("videos", {})
        full = (vs.get("large") or {}).get("url") or (vs.get("medium") or {}).get("url")
        prev = (vs.get("tiny") or {}).get("url") or (vs.get("small") or {}).get("url") or full
        if not full: continue
        out.append({"key": f"pb_{v['id']}", "source": "pixabay", "page": v.get("pageURL"), "duration": v.get("duration"),
                    "w": (vs.get("large") or vs.get("medium") or {}).get("width"), "h": (vs.get("large") or vs.get("medium") or {}).get("height"),
                    "preview": prev, "full": full, "credit": f"{v.get('user')} / Pixabay", "q": q})
    return out

mode, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
if mode == "scan":
    per = int(sys.argv[3]); qf = sys.argv[4]
    queries = [l.strip() for l in open(qf[1:]) if l.strip() and not l.startswith("#")] if qf.startswith("@") else sys.argv[4:]
    os.makedirs(f"{out}/sheets", exist_ok=True); allc = {}
    print("KEYS pexels:", bool(PX), "pixabay:", bool(PB), flush=True)
    for q in queries:
        rows = []
        for fn in (pexels, pixabay):
            try: rows += fn(q, per)
            except Exception as e: print("API_FAIL", fn.__name__, q, str(e)[:200], flush=True)
        rows = [r for r in rows if r["key"] not in allc]
        for r in rows: allc[r["key"]] = r
        print("QUERY", q, "->", len(rows), flush=True)
        strips = []
        for r in rows:
            p = f"/tmp/{r['key']}.mp4"
            try: dl(r["preview"], p)
            except Exception as e: print("PREV_FAIL", r["key"], str(e)[:120]); continue
            d = float(r.get("duration") or 8); s = f"/tmp/{r['key']}_strip.jpg"
            sh(["ffmpeg", "-y", "-v", "error", "-i", p, "-vf",
                f"fps=4/{max(d,1):.2f},scale=240:-2,pad=240:135:(ow-iw)/2:(oh-ih)/2,tile=4x1,"
                f"drawtext=text='{r['key']} {int(d)}s':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.7", "-frames:v", "1", s])
            if os.path.exists(s): strips.append(s)
            os.remove(p)
        if strips:
            slug = re.sub(r"[^a-z0-9]+", "_", q.lower()).strip("_")[:40]
            inputs = sum([["-i", s] for s in strips], [])
            sh(["ffmpeg", "-y", "-v", "error"] + inputs + ["-filter_complex", f"vstack=inputs={len(strips)}" if len(strips) > 1 else "null",
                f"{out}/sheets/{slug}.jpg"])
        time.sleep(1)
    json.dump(list(allc.values()), open(f"{out}/scan.json", "w"), indent=1)
    print("SCAN_TOTAL", len(allc))
elif mode == "fetch":
    picks = json.load(open(sys.argv[3])); scan = {}
    for sf in [l for l in os.environ.get("SCAN_FILES", "").split(",") if l]:
        for r in json.load(open(sf)): scan[r["key"]] = r
    idx = []
    for p in picks:
        r = scan.get(p["key"])
        if not r: print("NO_KEY", p["key"]); continue
        raw = f"/tmp/{r['key']}_full.mp4"
        if not os.path.exists(raw):
            try: dl(r["full"], raw)
            except Exception as e: print("DL_FAIL", r["key"], str(e)[:150]); continue
        name = f"{r['key']}_{int(p.get('ss', 0))}.mp4"
        cmd = ["ffmpeg", "-y", "-v", "error", "-ss", str(p.get("ss", 0)), "-i", raw]
        if p.get("dur"): cmd += ["-t", str(p["dur"])]
        cmd += (["-c:a", "aac", "-b:a", "160k"] if p.get("audio") else ["-an"]) + ["-vf", "scale='min(1920,iw)':-2,fps=30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                "-map_metadata", "-1", "-movflags", "+faststart", f"{out}/{name}"]
        sh(cmd)
        if os.path.exists(f"{out}/{name}"):
            idx.append({**r, **p, "file": name}); print("SAVED", name, flush=True)
    json.dump(idx, open(f"{out}/index.json", "w"), indent=1)
    print("FETCH_TOTAL", len(idx))
