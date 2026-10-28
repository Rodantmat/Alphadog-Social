#!/usr/bin/env python3
"""Collect public-domain / openly licensed media from a curated list.
Usage: collect_list_media.py LIST_JSON OUTDIR
LIST_JSON: {"chapter": "ch1", "items": [ {...}, ... ]}
Item kinds (all record license, credit, source page and the page's own rights text):
  direct        url                          -> one file (video/image by extension)
  usgs_video    page                         -> original mp4 from the USGS media page
  usgs_image    page                         -> 'Original' image from the USGS media page
  usgs_listing  page(s), filter, max_n, sub  -> USGS listing pages, follow /media/<sub>/ links whose title matches filter
  nps_clips     page, max_n                  -> NPS Video Library clip page (embed ids -> view page -> mp4)
  nps_videos    page, filter, max_n          -> NPS page with view.htm?id= links; only NPS-credited (PD) items
  nps_view      page                         -> one NPS view.htm?id= video
  slidefile     page, filter, max_n          -> NPS Yellowstone photo collection page (+pagination)
  loc           page                         -> loc.gov item (JSON API, rights_advisory recorded)
  commons       title | search, max_n        -> Wikimedia Commons file(s); only PD / CC0 / CC BY / CC BY-SA kept
Common item fields: name, shows, license, credit, status, max_sec (video, default 600), filter (regex, case-insens.)
Rights rules enforced: USGS pages must say 'Public Domain'; 'used with permission' -> status EXCLUDE-pending;
NPS videos must be credited to NPS/National Park Service without (c); Commons licence whitelist."""
import json, os, re, subprocess, sys, urllib.parse, hashlib, html as H
from curl_cffi import requests as cr

LIST = json.load(open(sys.argv[1])); OUT = sys.argv[2]
os.makedirs(f"{OUT}/video", exist_ok=True); os.makedirs(f"{OUT}/img", exist_ok=True)
S = cr.Session(impersonate="chrome")
BUA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
entries, fails, probes = [], [], {}
seen_urls = set()
PREV = json.load(open(sys.argv[3])) if len(sys.argv) > 3 and os.path.exists(sys.argv[3]) else {"files": []}
prev_names = {e["name"] for e in PREV.get("files", [])}
seen_urls.update(e["src_url"] for e in PREV.get("files", []))
def already(it):
    n = it.get("name", "")
    return not it.get("redo") and (n in prev_names or any(x.startswith(n + "_") for x in prev_names))

def page(url):
    for _ in range(3):
        try:
            r = S.get(url, timeout=60)
            if r.status_code == 200: return r.text
            last = r.status_code
        except Exception as e:
            last = str(e)[:100]
    probes.setdefault("page_fail", []).append([url, last]); return ""

def text(h): return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style).*?</\1>", " ", h)))).strip()
def og(h, prop):
    m = re.search(r'<meta[^>]+(?:property|name)="%s"[^>]+content="([^"]*)"' % re.escape(prop), h) or \
        re.search(r'<meta[^>]+content="([^"]*)"[^>]+(?:property|name)="%s"' % re.escape(prop), h)
    return H.unescape(m.group(1)) if m else ""
def after(t, label, n=220):
    m = re.search(re.escape(label) + r"\s*:?\s*(.{0,%d})" % n, t)
    return m.group(1).strip() if m else ""
def slug(s): return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:60]
def fid(s): return hashlib.md5(s.encode()).hexdigest()[:6]

def curl(url, dst):
    p = subprocess.run(["curl", "-fsSL", "--retry", "4", "--retry-delay", "3", "--connect-timeout", "30", "-m", "900",
                        "-A", BUA, "-o", dst, url], capture_output=True, text=True)
    return p.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 10_000

def head_ok(url):
    p = subprocess.run(["curl", "-sIL", "-A", BUA, "-o", "/dev/null", "-w", "%{http_code}", "-m", "40", url], capture_output=True, text=True)
    return p.stdout.strip().endswith("200")

def probe(f):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,pix_fmt,width,height:format=duration", "-of", "json", f], capture_output=True, text=True)
    try: j = json.loads(p.stdout)
    except Exception: return {}
    vs = [s for s in j.get("streams", []) if s.get("codec_type") == "video" and s.get("width")]
    au = [s for s in j.get("streams", []) if s.get("codec_type") == "audio"]
    return {"w": vs[0]["width"] if vs else None, "h": vs[0]["height"] if vs else None,
            "vcodec": vs[0].get("codec_name") if vs else None, "pix": vs[0].get("pix_fmt") if vs else None,
            "acodec": au[0].get("codec_name") if au else None,
            "dur": round(float(j.get("format", {}).get("duration") or 0), 2),
            "audio": any(s.get("codec_type") == "audio" for s in j.get("streams", []))}

SCALE_V = "scale='if(gt(iw/ih,16/9),min(1920,iw),-2)':'if(gt(iw/ih,16/9),-2,min(1080,ih))'"
SCALE_I = "scale='if(gt(iw,ih),min(3000,iw),-2)':'if(gt(iw,ih),-2,min(3000,ih))'"

def save(url, it, name, kind, extra):
    if url in seen_urls: return
    seen_urls.add(url)
    meta = {"name": name, "src_url": url, "source_page": extra.pop("source_page", it.get("page") or url),
            "shows": extra.pop("shows", None) or it.get("shows", ""), "license": it.get("license", ""), "credit": extra.pop("credit", None) or it.get("credit", ""),
            "status": extra.pop("status", None) or it.get("status", "OK"), **extra}
    tmp = f"/tmp/dl_{fid(url)}"
    if not curl(url, tmp):
        meta["err"] = "download failed"; fails.append(meta); return
    if kind == "video":
        dst = f"{OUT}/video/{name}.mp4"; info = probe(tmp)
        tlim = str(it.get("max_sec", 600))
        # already-compliant H.264 (<=1080p, yuv420p, < 95 MB) -> remux only (saves Actions minutes)
        if info.get("vcodec") == "h264" and info.get("pix") == "yuv420p" and (info.get("w") or 9999) <= 1920 and (info.get("h") or 9999) <= 1080 \
                and os.path.getsize(tmp) < 95 * 1024 * 1024:
            acodec = ["-c:a", "copy"] if info.get("acodec") == "aac" else (["-c:a", "aac", "-b:a", "160k"] if info.get("audio") else ["-an"])
            p = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-t", tlim, "-map", "0:v:0", "-map", "0:a:0?", "-c:v", "copy"] + acodec +
                               ["-movflags", "+faststart", dst], capture_output=True, text=True)
            if p.returncode == 0: meta["encode"] = "remux (source already H.264 yuv420p <=1080p)"
        for crf in ([] if meta.get("encode") else ("20", "23", "26")):
            cmd = ["ffmpeg", "-y", "-v", "error", "-i", tmp, "-t", tlim, "-vf", SCALE_V + ",format=yuv420p", "-c:v", "libx264", "-crf", crf,
                   "-preset", "veryfast", "-pix_fmt", "yuv420p"]
            cmd += (["-c:a", "aac", "-b:a", "160k"] if info.get("audio") else ["-an"])
            p = subprocess.run(cmd + ["-movflags", "+faststart", dst], capture_output=True, text=True)
            if p.returncode: meta["err"] = p.stderr[-300:]; break
            if os.path.getsize(dst) < 95 * 1024 * 1024: meta["encode"] = f"x264 crf{crf} veryfast"; break
        if not meta.get("encode") and not meta.get("err"):
            dur = min(float(tlim), info.get("dur") or float(tlim)); vb = int((88 * 8 * 1024 * 1024 / dur - 170_000) / 1000)
            cmd = ["ffmpeg", "-y", "-v", "error", "-i", tmp, "-t", tlim, "-vf", SCALE_V + ",format=yuv420p", "-c:v", "libx264", "-b:v", f"{vb}k",
                   "-maxrate", f"{vb}k", "-bufsize", f"{2*vb}k", "-preset", "veryfast", "-pix_fmt", "yuv420p"]
            cmd += (["-c:a", "aac", "-b:a", "160k"] if info.get("audio") else ["-an"])
            p = subprocess.run(cmd + ["-movflags", "+faststart", dst], capture_output=True, text=True)
            if p.returncode == 0 and os.path.getsize(dst) < 95 * 1024 * 1024: meta["encode"] = f"x264 capped {vb} kbps veryfast (CRF20-26 exceeded 95 MB)"
            else: meta["err"] = "too large after crf26 and bitrate cap"
        os.remove(tmp)
        if meta.get("err"):
            if os.path.exists(dst): os.remove(dst)
            fails.append(meta); return
        pi = probe(dst); meta.update(file=f"video/{name}.mp4", orig_dur=info.get("dur"), dur=pi.get("dur"), w=pi.get("w"), h=pi.get("h"),
                                     truncated=bool(info.get("dur") and info["dur"] > float(tlim) + 1))
    else:
        ext = ".png" if url.lower().split("?")[0].endswith(".png") else ".jpg"
        dst = f"{OUT}/img/{name}{ext}"
        p = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-vf", SCALE_I] + (["-q:v", "2"] if ext == ".jpg" else []) + ["-frames:v", "1", "-update", "1", dst],
                           capture_output=True, text=True)
        os.remove(tmp)
        if p.returncode or not os.path.exists(dst): meta["err"] = p.stderr[-300:]; fails.append(meta); return
        pi = probe(dst); meta.update(file=f"img/{name}{ext}", w=pi.get("w"), h=pi.get("h"))
    meta["bytes"] = os.path.getsize(dst); entries.append(meta); print("OK", meta["file"], meta["bytes"])

# ---------------- resolvers ----------------
def usgs_rights(h):
    t = text(h); usage = after(t, "Sources/Usage", 160)
    usage = re.split(r"\b(Related|Top of page|Detailed Description|Image Dimensions|Location|Taken|Length)\b", usage)[0].strip()
    return t, usage

def do_usgs(it, kind, pg=None, name=None):
    pg = pg or it["page"]; h = page(pg)
    if not h: fails.append({"name": name or it.get("name"), "source_page": pg, "err": "page fetch failed"}); return
    t, usage = usgs_rights(h); title = og(h, "og:title") or pg.rsplit("/", 1)[-1]
    name = name or it.get("name") or slug(title)
    extra = {"source_page": pg, "title": title, "page_usage": usage, "page_desc": og(h, "og:description")[:400] or after(t, "Detailed Description", 400)}
    att = re.search(r"(USGS (?:photo|image|video|graphic)[^.]{0,80}|Photo(?:graph)? (?:by|courtesy of) [^.]{0,80}|(?:Video|Image) (?:by|edited by|courtesy of) [^.]{0,80})", t)
    if att: extra["page_credit"] = att.group(1).strip()
    if "public domain" not in usage.lower():
        extra["err"] = f"not PD on page: {usage!r}"; fails.append({"name": name, **extra}); return
    if "permission" in usage.lower() or "copyright" in usage.lower():
        extra["status"] = "EXCLUDE-pending (page says some content used with permission; frame-check before use)"
    if kind == "video":
        mp4 = re.findall(r'https://usgs-ocapsv2-public-(?:input|output)-media[^"\'\s<>]+?\.mp4', h)
        mp4 = sorted(set(mp4), key=lambda u: ("input" not in u, u))
        if not mp4: extra["err"] = "no mp4 found"; fails.append({"name": name, **extra}); return
        extra["length"] = after(t, "Length", 10)
        extra["credit"] = it.get("credit") or ("USGS / Yellowstone Volcano Observatory" + (f" ({extra['page_credit']})" if extra.get("page_credit") else ""))
        save(mp4[0], it, name, "video", extra)
    else:
        orig = re.findall(r'href="(https://[a-z0-9-]+-wret[^"]+)"[^>]*>\s*(?:<[^>]+>\s*)*Original', h)
        imgs = orig + re.findall(r'https://[a-z0-9-]+-wret\.s3[^"\'\s<>]+?/s3fs-public/(?!styles/)(?!geodata/)[^"\'\s<>]+?\.(?:jpe?g|png|tiff?|gif)', h, re.I)
        imgs = [H.unescape(u) for u in dict.fromkeys(imgs) if "geodata/" not in u and "/styles/" not in u]
        if not imgs: extra["err"] = "no original image found"; fails.append({"name": name, **extra}); return
        extra["credit"] = it.get("credit") or extra.get("page_credit") or "USGS"
        save(imgs[0], it, name, "image", extra)

def do_usgs_listing(it):
    sub = it.get("sub", "images"); flt = re.compile(it.get("filter", "."), re.I); n = 0; found = []
    for pg in it.get("pages", [it.get("page")]):
        h = page(pg)
        for href, inner in re.findall(r'href="((?:https://www\.usgs\.gov)?/media/%s/[^"#?]+)"[^>]*>(.*?)</a>' % sub, h, re.S):
            href = urllib.parse.urljoin("https://www.usgs.gov", href); title = text(inner) or href.rsplit("/", 1)[-1].replace("-", " ")
            found.append([title[:90], href])
    found = list({u: t for t, u in found}.items())
    probes[f"listing:{it.get('name')}"] = [[t, u] for u, t in found if flt.search(t + " " + u)]
    for u, t in found:
        if n >= it.get("max_n", 10): break
        if flt.search(t + " " + u):
            n += 1; do_usgs(it, "video" if sub == "videos" else "image", pg=u, name=f"{it.get('name', 'usgs')}_{slug(u.rsplit('/', 1)[-1])}"[:80])

def nps_mp4_variants(u):
    base = re.sub(r"(\d{3,4}p)?\.mp4$", "", u)
    return [base + ".mp4", base + "1080p.mp4", u]

def nps_view(it, vid, name=None, require_pd=True, extra=None, flt=None):
    pg = f"https://www.nps.gov/media/video/view.htm?id={vid}"; h = page(pg)
    if not h: fails.append({"name": name, "source_page": pg, "err": "view page failed"}); return False
    t = text(h); title = og(h, "og:title")
    if flt and not flt.search(title): return False
    credit = re.split(r"\s(?:Date|Duration|Copyright|Description|Tags|Release|Audio Description|Open Captions|Transcript)\b", after(t, "Credit", 160))[0].strip()
    mp4 = og(h, "og:video") or og(h, "og:video:secure_url")
    ex = {"source_page": pg, "title": title, "page_credit": credit, "page_duration": after(t, "Duration", 30), **(extra or {})}
    ok_pd = bool(re.search(r"\b(NPS|National Park Service)\b", credit)) and "©" not in credit and "copyright" not in credit.lower()
    if require_pd and not ok_pd:
        fails.append({"name": name or slug(title), **ex, "err": "credit not NPS-only -> not presumed PD"}); return False
    if not mp4: fails.append({"name": name, **ex, "err": "no og:video"}); return False
    url = next((v for v in nps_mp4_variants(mp4) if head_ok(v)), mp4)
    ex["credit"] = it.get("credit") or "National Park Service"
    save(url, it, name or f"{it.get('name', 'nps')}_{slug(title)}"[:80], "video", ex); return True

def do_nps_clips(it):
    h = page(it["page"]); ids = list(dict.fromkeys(re.findall(r'(?:embed|view)\.htm\?id=([0-9A-Fa-f-]{20,})', h)))
    t = text(h); cr_ = after(t, "Copyright Info", 30)
    probes[f"clips:{it['name']}"] = {"ids": ids, "copyright": cr_}
    for i, vid in enumerate(ids[: it.get("max_n", 3)]):
        nps_view(it, vid, name=f"{it['name']}_{i+1}", require_pd=False,
                 extra={"page_usage": "NPS Yellowstone Video Library: 'recorded in the park and are in the public domain... may be downloaded and used without limitation' / clip page: Copyright Info: " + (cr_ or "?")})

def do_nps_videos(it):
    h = page(it["page"]); ids = list(dict.fromkeys(re.findall(r'(?:embed|view)\.htm\?id=([0-9A-Fa-f-]{20,})', h)))
    probes[f"npsvideos:{it['name']}"] = ids; n = 0; flt = re.compile(it["filter"], re.I) if it.get("filter") else None
    for vid in ids:
        if n >= it.get("max_n", 6): break
        if nps_view(it, vid, flt=flt): n += 1

def do_slidefile(it):
    base = it["page"].rsplit("/", 1)[0] + "/"; h0 = page(it["page"])
    pages = [it["page"]] + sorted({urllib.parse.urljoin(base, p) for p in re.findall(r'href="([^"]*Page-\d+\.htm)"', h0, re.I)}) if h0 else []
    flt = re.compile(it.get("filter", "."), re.I); n = 0; listing = []
    for pg in dict.fromkeys(pages):
        h = h0 if pg == it["page"] else page(pg)
        parts = re.split(r'(?=<a[^>]+href="[^"]*Images/\d+\.(?:jpg|jpeg)")', h, flags=re.I)
        for part in parts[1:]:
            m = re.search(r'href="([^"]*Images/(\d+)\.(?:jpg|jpeg))"', part, re.I)
            cap = text(part)[:300]
            listing.append([m.group(2), cap[:140]])
            if n >= it.get("max_n", 40) or not flt.search(cap): continue
            n += 1; url = urllib.parse.urljoin(pg, m.group(1))
            ph = re.search(r"Photographer\s*:?\s*([^;|]{0,60}?)(?:\s+Date|\s*$)", cap)
            save(url, it, f"{it['name']}_{m.group(2)}", "image",
                 {"source_page": pg, "shows": cap, "credit": "NPS Yellowstone photo collection" + (f"; photographer: {ph.group(1).strip()}" if ph else ""),
                  "page_usage": "NPS Yellowstone Photo Collection: 'These images are in the public domain and may be reproduced, free of charge with the proper credit line.'"})
    probes[f"slidefile:{it['name']}"] = listing

def do_loc(it):
    pg = it["page"].split("?")[0].rstrip("/") + "/"; r = page(pg + "?fo=json")
    try: j = json.loads(r)
    except Exception: fails.append({"name": it["name"], "source_page": pg, "err": "loc json failed"}); return
    item = j.get("item", {}); rights = " | ".join(item.get("rights_advisory", []) if isinstance(item.get("rights_advisory"), list) else [str(item.get("rights_advisory", ""))])
    rights = rights or " ".join(item.get("rights", []) if isinstance(item.get("rights"), list) else [str(item.get("rights", ""))])
    files = [f for res in j.get("resources", []) for grp in res.get("files", []) for f in grp]
    jpg = [f for f in files if f.get("mimetype") == "image/jpeg"]
    best = max(jpg, key=lambda f: (f.get("width") or 0)) if jpg else None
    ex = {"source_page": pg, "title": item.get("title"), "page_usage": rights[:400], "date": item.get("date"),
          "page_credit": ", ".join(item.get("contributor_names", []) or item.get("creators", []) if isinstance(item.get("contributor_names", []), list) else [])[:200]}
    if not re.search(r"no known restrictions", rights, re.I):
        ex["status"] = "EXCLUDE-pending (LoC rights statement is not 'No known restrictions')"
    if not best: fails.append({"name": it["name"], **ex, "err": "no jpeg resource"}); return
    ex["credit"] = it.get("credit") or f"Library of Congress, Prints & Photographs Division ({ex['page_credit'] or 'photographer unknown'})"
    save(best["url"], it, it["name"], "image", ex)

OKLIC = re.compile(r"^(public domain|pd\b|pd-|cc0|cc by(-sa)? ?\d|cc-by(-sa)?-\d|no restrictions)", re.I)
def do_commons(it):
    base = {"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": "3000"}
    if it.get("title"): base["titles"] = it["title"]
    else: base.update(generator="search", gsrsearch=it["search"] + " filetype:bitmap", gsrnamespace="6", gsrlimit="20")
    r = page("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(base))
    try: pages_ = list(json.loads(r).get("query", {}).get("pages", {}).values())
    except Exception: pages_ = []
    pages_.sort(key=lambda p: p.get("index", 0)); n = 0; flt = re.compile(it.get("filter", "."), re.I); seen = []
    for p in pages_:
        ii = (p.get("imageinfo") or [{}])[0]; em = ii.get("extmetadata") or {}
        lic = (em.get("LicenseShortName") or {}).get("value", ""); title = p.get("title", "")
        artist = text((em.get("Artist") or {}).get("value", ""))[:150]; desc = text((em.get("ImageDescription") or {}).get("value", ""))[:300]
        date = text((em.get("DateTimeOriginal") or {}).get("value", ""))[:60]
        seen.append([title, lic, artist, date])
        if n >= it.get("max_n", 1) or not flt.search(title + " " + desc): continue
        if not OKLIC.search(lic.strip()): continue
        n += 1
        save(ii.get("thumburl") or ii.get("url"), it, f"{it['name']}_{n}" if not it.get("title") else it["name"], "image",
             {"source_page": ii.get("descriptionurl"), "title": title, "page_usage": f"Wikimedia Commons licence: {lic}", "license": lic,
              "credit": it.get("credit") or f"{artist} ({date}) via Wikimedia Commons, {lic}", "shows": it.get("shows") or desc, "date": date})
    probes[f"commons:{it['name']}"] = seen

for it in LIST["items"]:
    k = it["kind"]; print("==", k, it.get("name"), flush=True)
    if already(it): print("   already collected, skip"); continue
    try:
        if k == "direct": save(it["url"], it, it["name"], "video" if it["url"].lower().split("?")[0].endswith((".mp4", ".mov", ".m4v")) else "image", {k: it[k] for k in ("page_usage", "title") if k in it})
        elif k == "usgs_video": do_usgs(it, "video")
        elif k == "usgs_image": do_usgs(it, "image")
        elif k == "usgs_listing": do_usgs_listing(it)
        elif k == "nps_clips": do_nps_clips(it)
        elif k == "nps_videos": do_nps_videos(it)
        elif k == "nps_view": nps_view(it, it["page"].split("id=")[-1], name=it["name"], require_pd=not it.get("pd_known"))
        elif k == "slidefile": do_slidefile(it)
        elif k == "loc": do_loc(it)
        elif k == "commons": do_commons(it)
    except Exception as e:
        fails.append({"name": it.get("name"), "err": f"exception {e!r}"[:300]})
    json.dump({"chapter": LIST.get("chapter"), "files": entries, "not_obtained": fails, "probes": probes, "partial": True}, open(f"{OUT}/index.json", "w"), indent=1)

json.dump({"chapter": LIST.get("chapter"), "files": entries, "not_obtained": fails, "probes": probes}, open(f"{OUT}/index.json", "w"), indent=1)
print(json.dumps({"ok": len(entries), "fail": len(fails)}))
for f in fails: print("FAIL", f.get("name"), f.get("err"), f.get("source_page"))
