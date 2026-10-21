"""Collect official NBA / team TikTok posts inside a time window.
Usage: python collect_footage.py <since_unix> <until_unix> <out_dir> acct1 acct2 ...
Saves 720x1280 re-encodes (metadata stripped) + index.json with credit, url, title, timestamp, duration."""
import json, os, subprocess, sys, time

since, until, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
accounts = sys.argv[4:]
os.makedirs(out, exist_ok=True)
idx_path = f"{out}/index.json"
index = json.load(open(idx_path)) if os.path.exists(idx_path) else []
have = {i["id"] for i in index}
MAX_DUR = 150

def sh(cmd, timeout=240):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr[-600:]
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"

log = []
for acct in accounts:
    rc, so, se = sh(["yt-dlp", "--flat-playlist", "--playlist-items", "1:20", "--impersonate", "chrome",
                     "--print", "%(id)s|%(timestamp)s|%(duration)s", f"https://www.tiktok.com/@{acct}"])
    rows = [l.split("|") for l in so.splitlines() if l.count("|") == 2]
    picked = 0
    for vid, ts, dur in rows:
        ts = int(ts) if ts.isdigit() else 0
        if vid in have or not (since <= ts <= until): continue
        url = f"https://www.tiktok.com/@{acct}/video/{vid}"
        raw = f"/tmp/{acct}_{vid}.mp4"
        rc, js, err = sh(["yt-dlp", "--no-warnings", "-f", "best[ext=mp4]/best", "-o", raw, "--print-json", "--no-simulate", url])
        if rc != 0 or not os.path.exists(raw):
            log.append({"acct": acct, "id": vid, "error": err[-200:]}); continue
        meta = json.loads(js.strip().splitlines()[-1])
        if (meta.get("duration") or 0) > MAX_DUR:
            log.append({"acct": acct, "id": vid, "skip": "too long"}); continue
        dst = f"{out}/{acct}_{vid}.mp4"
        sh(["ffmpeg", "-y", "-i", raw, "-vf", "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
            "-map_metadata", "-1", "-movflags", "+faststart", dst], 300)
        if not os.path.exists(dst): continue
        index.append({"id": vid, "account": acct, "credit": f"@{acct}", "url": url, "file": os.path.basename(dst),
                      "title": (meta.get("title") or meta.get("description") or "")[:200], "timestamp": ts,
                      "duration": meta.get("duration"), "src_w": meta.get("width"), "src_h": meta.get("height"),
                      "views": meta.get("view_count"), "likes": meta.get("like_count")})
        have.add(vid); picked += 1
        time.sleep(2)
    log.append({"acct": acct, "listed": len(rows), "new_in_window": picked})
    print(log[-1], flush=True)

index.sort(key=lambda i: -(i.get("views") or 0))
json.dump(index, open(idx_path, "w"), indent=2)
json.dump(log, open(f"{out}/collect_log.json", "w"), indent=2)
print("TOTAL", len(index))
