#!/usr/bin/env python3
"""Find and download Creative Commons (CC BY) YouTube videos for documentary B-roll.
usage: collect_ytcc.py OUT_DIR PER_QUERY MAX_DL "query 1" "query 2" ...   (or a single "@queries.txt")
 - searches YouTube with the Creative Commons filter
 - verifies each candidate's license via full metadata (must say Creative Commons)
 - downloads video-only (<=1080p), strips audio, caps length, writes index.json with credit info
 - writes a contact sheet per clip (1 frame / 10 s) for review
Also usable with explicit ids: query "id:VIDEOID"."""
import json, os, subprocess, sys, time, urllib.parse

out, per, maxdl = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); queries = sys.argv[4:]
if len(queries) == 1 and queries[0].startswith("@"):
    queries = [l.strip() for l in open(queries[0][1:]) if l.strip() and not l.startswith("#")]
os.makedirs(out, exist_ok=True); os.makedirs(f"{out}/sheets", exist_ok=True)
YT = ["yt-dlp", "--no-warnings", "--impersonate", "chrome", "--extractor-args", "youtube:player_client=default,web_safari,mweb"]

def sh(cmd, timeout=600):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout); return p.returncode, p.stdout, p.stderr[-800:]
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"

seen, cands, log = set(), [], []
for q in queries:
    if q.startswith("id:"):
        ids = [q[3:]]
    else:
        url = "https://www.youtube.com/results?" + urllib.parse.urlencode({"search_query": q, "sp": "EgIwAQ=="})  # CC filter
        rc, so, se = sh(YT + ["--flat-playlist", "--playlist-items", f"1:{per}", "--print", "%(id)s", url], 300)
        ids = [l.strip() for l in so.splitlines() if l.strip()]
        log.append({"q": q, "found": len(ids), "err": se[-300:] if not ids else ""}); print("SEARCH", log[-1], flush=True)
    for vid in ids:
        if vid in seen: continue
        seen.add(vid)
        rc, so, se = sh(YT + ["-j", "--skip-download", f"https://www.youtube.com/watch?v={vid}"], 180)
        if rc != 0 or not so.strip():
            print("META_FAIL", vid, se[-200:].replace("\n", " "), flush=True); continue
        j = json.loads(so.splitlines()[0])
        lic = j.get("license") or ""
        row = {"id": vid, "title": j.get("title"), "channel": j.get("channel") or j.get("uploader"), "channel_url": j.get("channel_url"),
               "url": f"https://www.youtube.com/watch?v={vid}", "license": lic, "duration": j.get("duration"), "height": j.get("height"),
               "views": j.get("view_count"), "upload_date": j.get("upload_date"), "q": q,
               "desc": (j.get("description") or "")[:300]}
        print("CAND", vid, "|", lic[:40], "|", row["duration"], "s |", row["height"], "p |", row["views"], "v |", (row["title"] or "")[:70], "|", row["channel"], flush=True)
        if "creative commons" in lic.lower() or q.startswith("id:"):
            cands.append(row)
        time.sleep(0.5)

idx = []
for r in cands:
    if len(idx) >= maxdl: break
    if (r["duration"] or 0) > 2400 or (r["duration"] or 0) < 10: continue
    raw = f"/tmp/yt_{r['id']}"
    rc, so, se = sh(YT + ["-f", "bv*[height<=1080][ext=mp4]/bv*[height<=1080]/b[height<=1080]", "-o", raw + ".%(ext)s", r["url"]], 1200)
    got = [f for f in os.listdir("/tmp") if f.startswith(f"yt_{r['id']}.")]
    if rc != 0 or not got:
        r["dl_err"] = se[-300:]; print("DL_FAIL", r["id"], se[-300:].replace("\n", " "), flush=True); continue
    src = "/tmp/" + got[0]
    dst = f"{out}/yt_{r['id']}.mp4"
    # video only, 1080p max, keep up to 12 minutes, size-safe for git
    sh(["ffmpeg", "-y", "-v", "error", "-i", src, "-t", "720", "-an", "-vf", "scale='min(1920,iw)':-2", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "22", "-pix_fmt", "yuv420p", "-map_metadata", "-1", "-movflags", "+faststart", dst], 1800)
    if os.path.exists(dst) and os.path.getsize(dst) > 90e6:
        sh(["ffmpeg", "-y", "-v", "error", "-i", dst, "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-an", dst + ".s.mp4"], 1800)
        os.replace(dst + ".s.mp4", dst)
    if not os.path.exists(dst) or os.path.getsize(dst) > 95e6:
        print("SKIP_BIG", r["id"]); continue
    sh(["ffmpeg", "-y", "-v", "error", "-i", dst, "-vf", "fps=1/10,scale=256:-2,drawtext=text='%{pts\\:hms}':x=4:y=4:fontsize=14:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=8x9",
        "-frames:v", "1", f"{out}/sheets/{r['id']}.jpg"], 600)
    r["file"] = os.path.basename(dst); r["credit"] = f"\"{r['title']}\" by {r['channel']} ({r['url']}), CC BY"
    idx.append(r); print("SAVED", r["id"], os.path.getsize(dst) // 1e6, "MB", flush=True)
    os.remove(src)

json.dump(idx, open(f"{out}/index.json", "w"), indent=2)
json.dump({"log": log, "candidates": cands}, open(f"{out}/candidates.json", "w"), indent=2)
print("TOTAL_SAVED", len(idx), "of", len(cands), "CC candidates")
