#!/usr/bin/env python3
"""Collect legally reusable media for a place documentary.
Usage: collect_place_media.py OUTDIR CONFIG_JSON
CONFIG: {"commons": ["Chiricahua"], "commons_cats": ["Chiricahua National Monument"],
         "archive": ["chiricahua", "apache arizona"], "nps_pages": ["https://www.nps.gov/chir/learn/photosmultimedia/videos.htm"],
         "coverr": ["arizona desert"], "loc": ["geronimo"], "max_video": 40, "max_img": 120}
Everything downloaded is logged with source URL + license in index.json."""
import json, os, re, subprocess, sys, urllib.parse, hashlib, time
from curl_cffi import requests as cr

OUT = sys.argv[1]; CFG = json.loads(sys.argv[2])
os.makedirs(f"{OUT}/video", exist_ok=True); os.makedirs(f"{OUT}/img", exist_ok=True)
S = cr.Session(impersonate="chrome")
UA = {"User-Agent": "AlphaDogSocialBot/1.0 (https://github.com/Rodantmat/Alphadog-Social)"}
log = {"probes": {}, "video": [], "img": []}
MAXV = CFG.get("max_video", 40); MAXI = CFG.get("max_img", 120)

def get(url, **kw):
    try:
        r = S.get(url, timeout=kw.pop("timeout", 60), headers=UA, **kw); return r
    except Exception as e:
        return e

def fid(s): return hashlib.md5(s.encode()).hexdigest()[:10]

def save_video(url, src, meta):
    if len(log["video"]) >= MAXV: return
    name = f"{src}_{fid(url)}.mp4"; raw = f"/tmp/{name}.raw"; dst = f"{OUT}/video/{name}"
    r = get(url, timeout=300)
    if isinstance(r, Exception) or r.status_code != 200 or len(r.content) < 100_000:
        meta["err"] = str(r)[:120] if isinstance(r, Exception) else r.status_code; log.setdefault("fail", []).append(meta); return
    open(raw, "wb").write(r.content)
    p = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-t", "240", "-vf", "scale='min(1920,iw)':-2",
                        "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", dst], capture_output=True, text=True)
    os.remove(raw)
    if p.returncode: meta["err"] = p.stderr[-200:]; log.setdefault("fail", []).append(meta); return
    pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height:format=duration", "-of", "json", dst], capture_output=True, text=True)
    info = json.loads(pr.stdout); vs = [s for s in info.get("streams", []) if s.get("width")]
    meta.update(file=f"video/{name}", src_url=url, w=vs[0]["width"] if vs else None, h=vs[0]["height"] if vs else None,
                dur=float(info.get("format", {}).get("duration", 0)))
    log["video"].append(meta)

def save_img(url, src, meta):
    if len(log["img"]) >= MAXI: return
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower() or ".jpg"
    if ext not in (".jpg", ".jpeg", ".png", ".tif", ".tiff"): ext = ".jpg"
    name = f"{src}_{fid(url)}{ext}"; r = get(url, timeout=120)
    if isinstance(r, Exception) or r.status_code != 200 or len(r.content) < 30_000: return
    open(f"{OUT}/img/{name}", "wb").write(r.content)
    if ext in (".tif", ".tiff"):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{OUT}/img/{name}", f"{OUT}/img/{name}.jpg"]); os.remove(f"{OUT}/img/{name}"); name += ".jpg"
    meta.update(file=f"img/{name}", src_url=url); log["img"].append(meta)

# ---------- Wikimedia Commons (search + categories), videos and images ----------
def commons_query(params):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({**params, "format": "json", "prop": "imageinfo",
          "iiprop": "url|size|mime|extmetadata", "iiurlwidth": "2400"})
    r = get(url)
    if isinstance(r, Exception) or r.status_code != 200: return []
    return list(r.json().get("query", {}).get("pages", {}).values())
pages = []
for q in CFG.get("commons", []):
    for ft in ("video", "bitmap"):
        pages += commons_query({"action": "query", "generator": "search", "gsrsearch": f"{q} filetype:{ft}", "gsrnamespace": "6", "gsrlimit": "50"})
for c in CFG.get("commons_cats", []):
    pages += commons_query({"action": "query", "generator": "categorymembers", "gcmtitle": f"Category:{c}", "gcmtype": "file", "gcmlimit": "200"})
log["probes"]["commons_pages"] = len(pages)
seen = set()
for p in pages:
    ii = (p.get("imageinfo") or [{}])[0]; u = ii.get("url"); 
    if not u or u in seen: continue
    seen.add(u); em = ii.get("extmetadata") or {}
    meta = {"source": "wikimedia", "title": p.get("title"), "license": (em.get("LicenseShortName") or {}).get("value"),
            "artist": re.sub("<[^>]+>", "", (em.get("Artist") or {}).get("value", ""))[:150],
            "desc": re.sub("<[^>]+>", "", (em.get("ImageDescription") or {}).get("value", ""))[:200]}
    mime = ii.get("mime", "")
    if mime.startswith("video"): save_video(u, "commons", meta)
    elif mime.startswith("image") and (ii.get("width") or 0) >= 1600: save_img(ii.get("thumburl") or u, "commons", meta)

# ---------- NPS pages: scrape mp4 / image links ----------
for page in CFG.get("nps_pages", []):
    r = get(page)
    if isinstance(r, Exception) or r.status_code != 200: log["probes"][page] = str(r)[:80] if isinstance(r, Exception) else r.status_code; continue
    html = r.text
    mp4 = set(re.findall(r'(https?://[^"\'\s>]+\.mp4|/[^"\'\s>]+\.mp4)', html))
    jpg = set(re.findall(r'(https?://www\.nps\.gov/common/uploads/[^"\'\s>]+\.(?:jpg|jpeg|png)|/common/uploads/[^"\'\s>]+\.(?:jpg|jpeg|png))', html, re.I))
    links = set(re.findall(r'href="(/chir/learn/photosmultimedia/[^"]+|/media/video/view\.htm\?id=[^"]+)"', html))
    log["probes"][page] = {"mp4": len(mp4), "img": len(jpg), "links": len(links)}
    for u in mp4: save_video(urllib.parse.urljoin(page, u), "nps", {"source": "nps", "page": page, "license": "NPS (public domain unless noted)"})
    for u in jpg: save_img(urllib.parse.urljoin(page, u), "nps", {"source": "nps", "page": page, "license": "NPS (public domain unless noted)"})
    for l in list(links)[:30]:
        sub = urllib.parse.urljoin(page, l); r2 = get(sub)
        if isinstance(r2, Exception) or r2.status_code != 200: continue
        for u in set(re.findall(r'(https?://[^"\'\s>]+\.mp4|/[^"\'\s>]+\.mp4)', r2.text)):
            save_video(urllib.parse.urljoin(sub, u), "nps", {"source": "nps", "page": sub, "license": "NPS (public domain unless noted)"})

# ---------- Internet Archive (public domain / CC films) ----------
for q in CFG.get("archive", []):
    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode({"q": f"({q}) AND mediatype:movies", "fl[]": ["identifier", "title", "licenseurl", "year"],
          "rows": "25", "output": "json"}, doseq=True)
    r = get(url)
    if isinstance(r, Exception) or r.status_code != 200: log["probes"][f"archive:{q}"] = "fail"; continue
    docs = r.json().get("response", {}).get("docs", []); log["probes"][f"archive:{q}"] = [(d.get("identifier"), d.get("title"), d.get("licenseurl"), d.get("year")) for d in docs]
    for d in docs[:CFG.get("archive_dl", 0)]:
        m = get(f"https://archive.org/metadata/{d['identifier']}")
        if isinstance(m, Exception): continue
        files = [f for f in m.json().get("files", []) if f.get("name", "").lower().endswith(".mp4")]
        if files:
            f = sorted(files, key=lambda f: int(f.get("size", 0)))[0]
            save_video(f"https://archive.org/download/{d['identifier']}/{urllib.parse.quote(f['name'])}", "archive",
                       {"source": "archive.org", "id": d["identifier"], "title": d.get("title"), "license": d.get("licenseurl"), "year": d.get("year")})

# ---------- Coverr (free license) ----------
def mp4s(html): return [u.replace("\\/", "/") for u in set(re.findall(r'https?:\\?/\\?/[^"\'\s<>]+?\.mp4', html))]
for q in CFG.get("coverr", []):
    r = get(f"https://coverr.co/s?q={urllib.parse.quote(q)}")
    if isinstance(r, Exception) or r.status_code != 200: continue
    us = [u for u in mp4s(r.text) if "1080" in u or "720" in u] or mp4s(r.text)
    log["probes"][f"coverr:{q}"] = len(us)
    for u in us[:CFG.get("coverr_per_q", 6)]:
        save_video(u, "coverr", {"source": "coverr", "query": q, "license": "Coverr license (free, commercial OK)"})

# ---------- Library of Congress ----------
for q in CFG.get("loc", []):
    r = get("https://www.loc.gov/pictures/search/?" + urllib.parse.urlencode({"q": q, "fo": "json", "c": "40"}))
    if isinstance(r, Exception) or r.status_code != 200:
        log["probes"][f"loc:{q}"] = str(r)[:80] if isinstance(r, Exception) else r.status_code; continue
    res = r.json().get("results", []); log["probes"][f"loc:{q}"] = len(res)
    for it in res[:CFG.get("loc_per_q", 10)]:
        img = (it.get("image") or {}).get("full") or (it.get("image") or {}).get("square")
        if img:
            if img.startswith("//"): img = "https:" + img
            save_img(img, "loc", {"source": "loc", "title": it.get("title"), "link": it.get("links", {}).get("item"),
                                  "license": "check item rights (LoC)", "created": it.get("created_published_date")})

json.dump(log, open(f"{OUT}/index.json", "w"), indent=1)
print(json.dumps(log["probes"], indent=1)[:6000])
print("videos", len(log["video"]), "images", len(log["img"]), "fails", len(log.get("fail", [])))
