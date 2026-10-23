#!/usr/bin/env python3
"""Collect public-domain / CC sound effects + ambiences.
 - NPS sound gallery pages (public domain)
 - Wikimedia Commons audio search (excludes NC/ND)
usage: sfx_collect.py OUT_DIR CONFIG_JSON  config: {"nps": ["sounds-stream", ...], "commons": {"wind": "wind ambience", ...}, "per": 3}
-> OUT_DIR/<name>.wav (48k stereo, max 90 s) + OUT_DIR/index.json (title, source page, license, credit)"""
import hashlib, json, os, re, subprocess, sys, urllib.parse
from curl_cffi import requests as cr
OUT = sys.argv[1]; CFG = json.load(open(sys.argv[2])); PER = CFG.get("per", 3); os.makedirs(OUT, exist_ok=True)
S = cr.Session(impersonate="chrome"); UA = {"User-Agent": "AlphaDogStudio/1.0 (documentary research; https://github.com/Rodantmat/Alphadog-Social)"}
idx = []
def get(u, **kw):
    try: return S.get(u, headers=UA, timeout=kw.pop("timeout", 60), **kw)
    except Exception as e: return None
def save(url, name, meta):
    r = get(url, timeout=180)
    if r is None or r.status_code != 200 or len(r.content) < 5000: print("DL_FAIL", name, url); return
    raw = f"/tmp/{name}.raw"; open(raw, "wb").write(r.content)
    p = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-t", "90", "-ac", "2", "-ar", "48000", f"{OUT}/{name}.wav"], capture_output=True, text=True)
    if p.returncode: print("CONV_FAIL", name, p.stderr[-200:]); return
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{OUT}/{name}.wav"], capture_output=True, text=True).stdout or 0)
    idx.append({**meta, "file": f"{name}.wav", "src_url": url, "dur": round(d, 1)}); print("SAVED", name, round(d, 1), "s", flush=True)
for page in CFG.get("nps", []):
    u = f"https://www.nps.gov/subjects/sound/{page}.htm"; r = get(u)
    if r is None or r.status_code != 200: print("PAGE_FAIL", u); continue
    links = list(dict.fromkeys(re.findall(r'(?:https?://www\.nps\.gov)?/[^"\'\s>]+?\.(?:mp3|wav)', r.text, re.I)))
    title = re.search(r"<title>(.*?)</title>", r.text, re.S); title = (title.group(1).strip() if title else page)[:80]
    for i, l in enumerate(links[:2]):
        save(urllib.parse.urljoin(u, l), f"nps_{page.replace('sounds-', '')}_{i}", {"source": "NPS Natural Sounds", "page": u, "title": title, "license": "Public domain (NPS)", "credit": "National Park Service"})
for name, q in CFG.get("commons", {}).items():
    api = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search",
          "gsrsearch": f"{q} filetype:audio", "gsrnamespace": "6", "gsrlimit": "20", "prop": "imageinfo", "iiprop": "url|extmetadata|size"})
    r = get(api)
    if r is None or r.status_code != 200: print("COMMONS_FAIL", q); continue
    n = 0
    for p in r.json().get("query", {}).get("pages", {}).values():
        if n >= PER: break
        ii = (p.get("imageinfo") or [{}])[0]; em = ii.get("extmetadata") or {}
        lic = (em.get("LicenseShortName") or {}).get("value", "")
        if not ii.get("url") or "NC" in lic or "ND" in lic or not lic: continue
        artist = re.sub("<[^>]+>", "", (em.get("Artist") or {}).get("value", ""))[:100]
        save(ii["url"], f"wc_{name}_{n}", {"source": "Wikimedia Commons", "page": ii.get("descriptionurl"), "title": p.get("title"), "license": lic,
                                          "credit": f"{p.get('title','')[5:]} by {artist} ({lic})", "q": q}); n += 1
json.dump(idx, open(f"{OUT}/index.json", "w"), indent=1)
print("TOTAL", len(idx))
