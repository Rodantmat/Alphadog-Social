#!/usr/bin/env python3
"""Scan public-domain / openly licensed VIDEO sources and make review sheets (no full downloads).
usage: pd_scan.py OUT_DIR CONFIG_JSON_PATH
config: {"archive": ["query", ...], "loc": ["query", ...], "commons": ["query", ...], "mixkit": ["query", ...], "coverr": ["query", ...],
         "per_query": 10, "frames": 8}
Output: OUT_DIR/scan.json (same schema as stock_scan.py: key, source, page, full, duration, license, credit, title, q)
        OUT_DIR/sheets/<key>.jpg  (N frames sampled across the clip, timestamped) — read straight from the URL with ffmpeg seeks."""
import hashlib, json, os, re, subprocess, sys, time, urllib.parse
from curl_cffi import requests as cr

OUT = sys.argv[1]; CFG = json.load(open(sys.argv[2])); PER = CFG.get("per_query", 10); NF = CFG.get("frames", 8)
os.makedirs(f"{OUT}/sheets", exist_ok=True)
S = cr.Session(impersonate="chrome"); UA = {"User-Agent": "AlphaDogStudio/1.0 (documentary research; github.com/Rodantmat/Alphadog-Social)"}
cands = {}

def get(url, **kw):
    try: return S.get(url, timeout=kw.pop("timeout", 60), headers=UA, **kw)
    except Exception as e: return e

def ok(r): return not isinstance(r, Exception) and r.status_code == 200
def h(s): return hashlib.md5(s.encode()).hexdigest()[:10]

def probe_dur(url):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height", "-of", "json", url],
                       capture_output=True, text=True, timeout=120)
    try:
        j = json.loads(p.stdout); vs = [s for s in j.get("streams", []) if s.get("width")]
        return float(j["format"]["duration"]), (vs[0]["width"], vs[0]["height"]) if vs else (None, None)
    except Exception: return None, (None, None)

def sheet(r):
    d, (w, hh) = probe_dur(r["full"])
    if not d: print("NO_PROBE", r["key"]); return False
    r["duration"] = round(d, 1); r["w"], r["h"] = w, hh
    frames = []
    for i in range(NF):
        t = d * (i + 0.5) / NF; f = f"/tmp/{r['key']}_{i}.jpg"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.1f}", "-i", r["full"], "-frames:v", "1", "-vf",
                        f"scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2,"
                        f"drawtext=text='{int(t//60)}\\:{int(t%60):02d}':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.7",
                        f], capture_output=True, timeout=180)
        if os.path.exists(f): frames.append(f)
    if not frames: return False
    ins = sum([["-i", f] for f in frames], [])
    cols = 4; rows = (len(frames) + cols - 1) // cols
    subprocess.run(["ffmpeg", "-y", "-v", "error"] + ins + ["-filter_complex",
                    "".join(f"[{i}:v]" for i in range(len(frames))) + f"xstack=inputs={len(frames)}:layout=" +
                    "|".join(f"{(i%cols)*320}_{(i//cols)*180}" for i in range(len(frames))) + ":fill=black" if len(frames) > 1 else "null",
                    f"{OUT}/sheets/{r['key']}.jpg"], capture_output=True, timeout=120)
    for f in frames: os.remove(f)
    return os.path.exists(f"{OUT}/sheets/{r['key']}.jpg")

def add(r):
    if r["key"] in cands: return
    try:
        if sheet(r): cands[r["key"]] = r; print("CAND", r["key"], r["source"], r.get("duration"), r.get("w"), "|", (r.get("title") or "")[:80], flush=True)
    except Exception as e: print("SHEET_FAIL", r["key"], str(e)[:120])

# ---- Internet Archive: movies that are public domain or CC (licenseurl) or US-gov / prelinger collections ----
for q in CFG.get("archive", []):
    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode({"q": f"({q}) AND mediatype:movies",
          "fl[]": ["identifier", "title", "licenseurl", "year", "collection", "creator"], "rows": str(PER * 3), "output": "json"}, doseq=True)
    r = get(url)
    if not ok(r): print("ARCHIVE_FAIL", q); continue
    docs = r.json().get("response", {}).get("docs", []); n = 0
    for d in docs:
        if n >= PER: break
        lic = d.get("licenseurl") or ""; coll = d.get("collection") or []; coll = coll if isinstance(coll, list) else [coll]
        pd = ("publicdomain" in lic) or ("creativecommons.org/licenses/by/" in lic) or ("creativecommons.org/licenses/by-sa/" in lic) \
             or any(c in ("prelinger", "fedflix", "usgovernmentdocuments", "nasa", "national_archives") for c in coll)
        if not pd: continue
        m = get(f"https://archive.org/metadata/{d['identifier']}")
        if not ok(m): continue
        files = [f for f in m.json().get("files", []) if f.get("name", "").lower().endswith((".mp4", ".mpeg4", ".m4v"))]
        if not files: continue
        f = sorted(files, key=lambda f: -int(f.get("size", 0) or 0))[0]
        full = f"https://archive.org/download/{d['identifier']}/{urllib.parse.quote(f['name'])}"
        add({"key": f"ia_{h(d['identifier'])}", "source": "archive.org", "page": f"https://archive.org/details/{d['identifier']}", "full": full,
             "license": lic or ("collection: " + ",".join(coll)), "credit": f"{d.get('creator') or 'Internet Archive'} ({d.get('year') or 'n.d.'})",
             "title": d.get("title"), "q": q}); n += 1
    print("QUERY archive", q, n, flush=True)

# ---- Library of Congress film & video ----
for q in CFG.get("loc", []):
    r = get("https://www.loc.gov/film-and-videos/?" + urllib.parse.urlencode({"q": q, "fo": "json", "c": str(PER * 2)}))
    if not ok(r): print("LOC_FAIL", q, getattr(r, "status_code", r)); continue
    n = 0
    for it in r.json().get("results", []):
        if n >= PER: break
        rights = " ".join(it.get("rights", []) if isinstance(it.get("rights"), list) else [str(it.get("rights", ""))])
        res = it.get("resources") or []; vids = []
        for rs in res:
            for k in ("video", "files", "url"):
                v = rs.get(k)
                if isinstance(v, str) and v.endswith(".mp4"): vids.append(v)
        if not vids:
            ir = get(it.get("id", "") + "?fo=json") if it.get("id") else None
            if ir is not None and ok(ir):
                vids = list(set(re.findall(r'https://[^"\s]+?\.mp4', ir.text)))
        if not vids: continue
        add({"key": f"loc_{h(vids[0])}", "source": "loc", "page": it.get("id"), "full": vids[0], "license": rights[:200] or "LoC: check rights",
             "credit": "Library of Congress", "title": it.get("title"), "q": q, "date": it.get("date")}); n += 1
    print("QUERY loc", q, n, flush=True)

# ---- Wikimedia Commons videos ----
for q in CFG.get("commons", []):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search",
          "gsrsearch": f"{q} filetype:video", "gsrnamespace": "6", "gsrlimit": str(PER), "prop": "imageinfo",
          "iiprop": "url|mime|extmetadata"})
    r = get(url); n = 0
    if not ok(r): print("COMMONS_FAIL", q); continue
    for p in r.json().get("query", {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [{}])[0]; em = ii.get("extmetadata") or {}
        if not ii.get("url"): continue
        lic = (em.get("LicenseShortName") or {}).get("value", "")
        if "NC" in lic or "ND" in lic: continue
        add({"key": f"wc_{h(ii['url'])}", "source": "wikimedia", "page": ii.get("descriptionurl"), "full": ii["url"], "license": lic,
             "credit": re.sub("<[^>]+>", "", (em.get("Artist") or {}).get("value", ""))[:120], "title": p.get("title"), "q": q}); n += 1
    print("QUERY commons", q, n, flush=True)

# ---- Mixkit (free license) ----
for q in CFG.get("mixkit", []):
    r = get(f"https://mixkit.co/free-stock-video/{urllib.parse.quote(q.replace(' ', '-'))}/")
    if not ok(r): print("MIXKIT_FAIL", q); continue
    groups = {}
    for u in set(x.replace("\\/", "/") for x in re.findall(r'https?:\\?/\\?/[^"\'\s<>]+?\.mp4', r.text)):
        m = re.search(r"/videos/(?:preview/)?(?:mixkit-)?([\w-]+?)-(\d+)?-?(small|medium|large|360|720|1080)?\.mp4", u)
        if not m: continue
        k, qq = m.group(1), {"small": 0, "360": 0, "medium": 1, "720": 1, "large": 2, "1080": 2}.get(m.group(3) or "", 1)
        if k not in groups or qq > groups[k][1]: groups[k] = (u, qq)
    urls = [v[0] for v in groups.values()][:PER]
    for full in urls:
        add({"key": f"mk_{h(full)}", "source": "mixkit", "page": f"https://mixkit.co/free-stock-video/{q.replace(' ', '-')}/", "full": full,
             "license": "Mixkit Stock Video Free License", "credit": "Mixkit", "title": full.rsplit('/', 1)[-1], "q": q})
    print("QUERY mixkit", q, len(urls), flush=True)

# ---- Coverr (free license) ----
for q in CFG.get("coverr", []):
    r = get(f"https://coverr.co/s?q={urllib.parse.quote(q)}")
    if not ok(r): print("COVERR_FAIL", q); continue
    us = [u.replace("\\/", "/") for u in dict.fromkeys(re.findall(r'https?:\\?/\\?/[^"\'\s<>]+?\.mp4', r.text))]
    us = ([u for u in us if "1080" in u] or us)[:PER]
    for u in us:
        add({"key": f"cv_{h(u)}", "source": "coverr", "page": f"https://coverr.co/s?q={q}", "full": u, "license": "Coverr license",
             "credit": "Coverr", "title": u.rsplit('/', 1)[-1][:80], "q": q})
    print("QUERY coverr", q, len(us), flush=True)

json.dump(list(cands.values()), open(f"{OUT}/scan.json", "w"), indent=1)
print("SCAN_TOTAL", len(cands))
