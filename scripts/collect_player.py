"""Collect official TikTok posts that mention a player.
Usage: python collect_player.py <regex> <max_items_per_account> <out_dir> acct1 acct2 ...
Downloads matching posts (<= 90 s), re-encodes 720x1280 (metadata stripped), writes index.json."""
import json, os, re, subprocess, sys, time

rx = re.compile(sys.argv[1], re.I); maxn = int(sys.argv[2]); out = sys.argv[3]; accounts = sys.argv[4:]
os.makedirs(out, exist_ok=True); index = []; log = []

def sh(cmd, timeout=300):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout); return p.returncode, p.stdout, p.stderr[-500:]
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"

for acct in accounts:
    rc, so, se = sh(["yt-dlp", "--flat-playlist", "--playlist-items", f"1:{maxn}", "--impersonate", "chrome",
                     "--print", "%(id)s|%(timestamp)s|%(duration)s|%(title).200s", f"https://www.tiktok.com/@{acct}"], 600)
    rows = [l.split("|", 3) for l in so.splitlines() if l.count("|") >= 3]
    hits = [r for r in rows if rx.search(r[3])]
    log.append({"acct": acct, "listed": len(rows), "matches": len(hits), "err": se[-200:] if not rows else ""}); print(log[-1], flush=True)
    for vid, ts, dur, title in hits:
        try:
            if float(dur or 0) > 90: continue
        except ValueError:
            pass
        url = f"https://www.tiktok.com/@{acct}/video/{vid}"; raw = f"/tmp/{acct}_{vid}.mp4"
        rc, js, err = sh(["yt-dlp", "--no-warnings", "-f", "best[ext=mp4]/best", "-o", raw, url])
        if rc != 0 or not os.path.exists(raw): continue
        dst = f"{out}/{acct}_{vid}.mp4"
        sh(["ffmpeg", "-y", "-i", raw, "-vf", "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
            "-map_metadata", "-1", "-movflags", "+faststart", dst])
        if os.path.exists(dst):
            index.append({"account": acct, "credit": f"@{acct}", "url": url, "file": os.path.basename(dst), "title": title,
                          "timestamp": int(ts) if ts.isdigit() else None, "duration": dur})
        time.sleep(2)

json.dump(index, open(f"{out}/index.json", "w"), indent=2); json.dump(log, open(f"{out}/log.json", "w"), indent=2)
print("TOTAL", len(index))
