"""Collect TikTok videos from hashtag pages and/or accounts, filtered by caption regex, most-viewed first.
Usage: python collect_tiktok.py <regex> <list_per_source> <max_dl> <out_dir> src1 src2 ...
  src = "tag:NAME" (hashtag page) or "@handle" / "handle" (account)
Keeps native aspect (no padding), <=60 s, metadata stripped; index.json has credit/url/title/views."""
import json, os, re, subprocess, sys, time

rx = re.compile(sys.argv[1], re.I); per = int(sys.argv[2]); maxdl = int(sys.argv[3]); out = sys.argv[4]; srcs = sys.argv[5:]
os.makedirs(out, exist_ok=True); log = []; rows = {}

def sh(cmd, timeout=300):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout); return p.returncode, p.stdout, p.stderr[-600:]
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"

for s in srcs:
    if s.startswith("tag:") or s.startswith("#"):
        url = f"https://www.tiktok.com/tag/{s.split(':', 1)[-1].lstrip('#')}"
    else:
        url = f"https://www.tiktok.com/@{s.lstrip('@')}"
    rc, so, se = sh(["yt-dlp", "--flat-playlist", "--playlist-items", f"1:{per}", "--impersonate", "chrome",
                     "--print", "%(id)s|%(uploader)s|%(view_count)s|%(duration)s|%(webpage_url)s|%(title).250s", url], 900)
    got = [l.split("|", 5) for l in so.splitlines() if l.count("|") >= 5]
    m = 0
    for vid, up, views, dur, wurl, title in got:
        if not rx.search(title or ""): continue
        m += 1
        if vid not in rows:
            rows[vid] = {"id": vid, "uploader": up, "views": int(views) if views.isdigit() else 0, "dur": dur, "url": wurl,
                         "title": title, "src": s}
    log.append({"src": s, "url": url, "listed": len(got), "matches": m, "err": se[-300:] if not got else ""}); print(log[-1], flush=True)

cands = sorted(rows.values(), key=lambda r: -r["views"])
idx = []
for r in cands:
    if len(idx) >= maxdl: break
    try:
        if float(r["dur"] or 0) > 60: continue
    except ValueError:
        pass
    url = r["url"] if r["url"] and r["url"] != "NA" else f"https://www.tiktok.com/@{r['uploader']}/video/{r['id']}"
    raw = f"/tmp/tt_{r['id']}.mp4"
    rc, so, se = sh(["yt-dlp", "--no-warnings", "--impersonate", "chrome", "-f", "best[ext=mp4]/best", "-o", raw,
                     "--print-to-file", "%(uploader)s|%(view_count)s|%(like_count)s", f"/tmp/tt_{r['id']}.meta", url])
    if rc != 0 or not os.path.exists(raw):
        r["dl_err"] = se[-200:]; continue
    if os.path.exists(f"/tmp/tt_{r['id']}.meta"):
        p = open(f"/tmp/tt_{r['id']}.meta").read().strip().split("|")
        if len(p) == 3:
            r["uploader"] = p[0] or r["uploader"]; r["views"] = int(p[1]) if p[1].isdigit() else r["views"]
            r["likes"] = int(p[2]) if p[2].isdigit() else None
    dst = f"{out}/tt_{r['id']}.mp4"
    sh(["ffmpeg", "-y", "-i", raw, "-t", "60", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-map_metadata", "-1", "-movflags", "+faststart", dst])
    if os.path.exists(dst):
        r["file"] = os.path.basename(dst); r["credit"] = f"@{r['uploader']}"; idx.append(r)
    time.sleep(1.5)

json.dump(idx, open(f"{out}/index.json", "w"), indent=2)
json.dump({"log": log, "candidates": len(cands)}, open(f"{out}/log.json", "w"), indent=2)
print("TOTAL", len(idx), "of", len(cands))
