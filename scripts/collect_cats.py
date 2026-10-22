#!/usr/bin/env python3
"""Collect freely licensed sleepy-cat videos (Wikimedia Commons) + probe Pexels/Pixabay reachability.
Usage: collect_cats.py OUTDIR MAX_DL"""
import json, os, subprocess, sys, urllib.parse, urllib.request

OUT = sys.argv[1]; MAX_DL = int(sys.argv[2]) if len(sys.argv) > 2 else 30
os.makedirs(OUT, exist_ok=True)
UA = "AlphaDogSocialBot/1.0 (https://github.com/Rodantmat/Alphadog-Social; contact via repo)"
log = {"probes": {}, "found": [], "downloaded": []}

def get(url, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()

# --- reachability probes for stock sites (curl_cffi impersonation) ---
try:
    from curl_cffi import requests as cr
    for name, u in [("pexels", "https://www.pexels.com/search/videos/sleepy%20cat/"),
                    ("pixabay", "https://pixabay.com/videos/search/sleeping%20cat/"),
                    ("mixkit", "https://mixkit.co/free-stock-video/cat/"),
                    ("coverr", "https://coverr.co/s?q=cat")]:
        try:
            r = cr.get(u, impersonate="chrome", timeout=30)
            log["probes"][name] = {"status": r.status_code, "len": len(r.text), "mp4_links": r.text.count(".mp4")}
        except Exception as e:
            log["probes"][name] = {"error": str(e)[:200]}
except Exception as e:
    log["probes"]["curl_cffi"] = str(e)[:200]

# --- Wikimedia Commons search ---
seen = {}
queries = ["sleeping cat", "cat sleeping", "sleepy cat", "kitten sleeping", "cat falling asleep",
           "cat yawning", "cat yawn", "kitten yawning", "cat nap", "cat dozing", "sleeping kitten", "cat snoring"]
for q in queries:
    params = {"action": "query", "format": "json", "generator": "search",
              "gsrsearch": f"{q} filetype:video", "gsrnamespace": "6", "gsrlimit": "50",
              "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata|metadata"}
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    try:
        st, body = get(url)
        pages = json.loads(body).get("query", {}).get("pages", {})
    except Exception as e:
        log["probes"][f"commons:{q}"] = str(e)[:200]; continue
    log["probes"][f"commons:{q}"] = len(pages)
    for p in pages.values():
        t = p["title"]
        if t in seen: continue
        ii = (p.get("imageinfo") or [{}])[0]
        md = {m["name"]: m["value"] for m in (ii.get("metadata") or []) if isinstance(m, dict) and "name" in m}
        em = ii.get("extmetadata") or {}
        dur = md.get("playtime_seconds") or md.get("length")
        seen[t] = {"title": t, "url": ii.get("url"), "w": ii.get("width"), "h": ii.get("height"),
                   "mime": ii.get("mime"), "size": ii.get("size"), "dur": dur,
                   "license": (em.get("LicenseShortName") or {}).get("value"),
                   "artist": (em.get("Artist") or {}).get("value", "")[:200],
                   "desc": (em.get("ImageDescription") or {}).get("value", "")[:300], "q": q}
log["found"] = list(seen.values())

def ok(c):
    t = c["title"].lower()
    if not any(k in t for k in ("cat", "kitten", "kitty", "katze", "gato", "chat", "neko")): return False
    try:
        d = float(c["dur"] or 0)
    except Exception:
        d = 0
    return (c["size"] or 0) < 400_000_000 and (d == 0 or 3 <= d <= 600) and (c["w"] or 0) >= 480

cands = [c for c in seen.values() if ok(c)]
cands.sort(key=lambda c: -(c["w"] or 0) * (c["h"] or 0))
n = 0
for c in cands:
    if n >= MAX_DL: break
    safe = "".join(ch if ch.isalnum() else "_" for ch in c["title"][5:])[:70]
    raw = os.path.join("/tmp", "raw_" + safe)
    dst = os.path.join(OUT, safe + ".mp4")
    try:
        st, body = get(c["url"], timeout=180)
        open(raw, "wb").write(body)
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-t", "90",
                            "-vf", "scale='if(gt(iw,ih),-2,720)':'if(gt(iw,ih),720,-2)'",
                            "-c:v", "libx264", "-crf", "22", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", dst],
                           capture_output=True, text=True, timeout=600)
        os.remove(raw)
        if r.returncode == 0:
            c["file"] = os.path.basename(dst); log["downloaded"].append(c); n += 1
        else:
            c["ffmpeg_err"] = r.stderr[-300:]
    except Exception as e:
        c["dl_err"] = str(e)[:200]

json.dump(log, open(os.path.join(OUT, "index.json"), "w"), indent=1)
print(json.dumps(log["probes"], indent=1))
print("found", len(seen), "cands", len(cands), "downloaded", n)
for c in log["downloaded"]:
    print(c["file"], c["w"], c["h"], c["dur"], c["license"])
