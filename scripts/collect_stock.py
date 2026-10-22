#!/usr/bin/env python3
"""Collect free-license stock videos (Pixabay / Mixkit / Coverr) by search query.
Usage: collect_stock.py OUTDIR MAX_PER_QUERY "query one|query two|..."
Writes OUTDIR/<site>_<id>.mp4 (720p-ish, h264) + index.json with source page/search and resolution."""
import json, os, re, subprocess, sys, urllib.parse, hashlib
from curl_cffi import requests as cr

OUT = sys.argv[1]; MAXQ = int(sys.argv[2]); QUERIES = [q.strip() for q in sys.argv[3].split("|") if q.strip()]
os.makedirs(OUT, exist_ok=True)
S = cr.Session(impersonate="chrome")
log = {"queries": QUERIES, "pages": {}, "clips": []}
done = set()

def page(url):
    try:
        r = S.get(url, timeout=40); return r.status_code, r.text
    except Exception as e:
        return 0, str(e)

def mp4s(html):
    urls = set(re.findall(r'https?:\\?/\\?/[^"\'\s<>]+?\.mp4', html))
    return [u.replace("\\/", "/") for u in urls]

def pick(urls, site):
    groups = {}
    for u in urls:
        if site == "pixabay":
            m = re.search(r"/video/\d+/\d+/\d+/(\d+)-(\d+)_(tiny|small|medium|large)\.mp4", u)
            if not m: continue
            key, q = m.group(1) + "-" + m.group(2), ["tiny", "small", "medium", "large"].index(m.group(3))
        elif site == "mixkit":
            m = re.search(r"/videos/(?:preview/)?(?:mixkit-)?([\w-]+?)-(\d+)?-?(small|medium|large|360|720|1080)?\.mp4", u)
            if not m: continue
            key, q = m.group(1), {"small": 0, "360": 0, "medium": 1, "720": 1, "large": 2, "1080": 2}.get(m.group(3) or "", 1)
        else:
            key = hashlib.md5(re.sub(r"[?#].*", "", u).encode()).hexdigest()[:10]
            q = 2 if re.search(r"1080|hd", u) else 1 if re.search(r"720", u) else 0
        if key not in groups or q > groups[key][1]: groups[key] = (u, q)
    return [(k, v[0]) for k, v in groups.items()]

for q in QUERIES:
    qs = urllib.parse.quote(q)
    for site, url in [("pixabay", f"https://pixabay.com/videos/search/{qs}/"),
                      ("mixkit", f"https://mixkit.co/free-stock-video/{q.replace(' ', '-')}/"),
                      ("coverr", f"https://coverr.co/s?q={qs}")]:
        st, html = page(url)
        cands = pick(mp4s(html), site) if st == 200 else []
        log["pages"][f"{site}:{q}"] = {"status": st, "cands": len(cands)}
        n = 0
        for key, u in cands:
            if n >= MAXQ: break
            fid = f"{site}_{re.sub(r'[^A-Za-z0-9_-]', '_', key)[:60]}"
            if fid in done: continue
            raw = f"/tmp/{fid}.raw"; dst = f"{OUT}/{fid}.mp4"
            try:
                r = S.get(u, timeout=120)
                if r.status_code != 200 or len(r.content) < 50_000: continue
                open(raw, "wb").write(r.content)
                p = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-t", "60",
                                    "-vf", "scale='if(gt(iw,ih),-2,min(1080,iw))':'if(gt(iw,ih),min(1080,ih),-2)'",
                                    "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", dst], capture_output=True, text=True)
                os.remove(raw)
                if p.returncode: continue
                pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height:format=duration", "-of", "json", dst],
                                    capture_output=True, text=True)
                info = json.loads(pr.stdout)
                vs = [s for s in info.get("streams", []) if s.get("width")]
                log["clips"].append({"file": f"{fid}.mp4", "site": site, "query": q, "src": u,
                                     "w": vs[0]["width"] if vs else None, "h": vs[0]["height"] if vs else None,
                                     "dur": float(info.get("format", {}).get("duration", 0))})
                done.add(fid); n += 1
            except Exception as e:
                log["pages"][f"{site}:{q}"].setdefault("errs", []).append(str(e)[:120])

json.dump(log, open(f"{OUT}/index.json", "w"), indent=1)
print(json.dumps(log["pages"], indent=1)); print("clips", len(log["clips"]))
