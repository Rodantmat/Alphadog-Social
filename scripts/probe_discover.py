"""Round 3: can the runner discover the newest official TikTok posts by itself, and download several in a row?
Writes clips/probe3/report.json."""
import json, os, re, subprocess, time

OUT = "clips/probe3"; os.makedirs(OUT, exist_ok=True)
ACCOUNTS = ["nba", "spurs", "detroitpistons", "nyknicks", "okcthunder", "sixers"]
report = {"discovery": [], "downloads": []}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"

def sh(cmd, timeout=180):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr[-800:]
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"

def via_ytdlp(acct):
    rc, out, err = sh(["yt-dlp", "--flat-playlist", "--playlist-items", "1:8", "--impersonate", "chrome",
                       "--print", "%(id)s|%(timestamp)s|%(title).80s", f"https://www.tiktok.com/@{acct}"])
    rows = [l.split("|", 2) for l in out.splitlines() if l.count("|") >= 2]
    return [{"url": f"https://www.tiktok.com/@{acct}/video/{r[0]}", "ts": r[1], "title": r[2]} for r in rows], err

def via_browser(acct):
    from playwright.sync_api import sync_playwright
    found = []
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(user_agent=UA, viewport={"width": 1280, "height": 900})
        pg.goto(f"https://www.tiktok.com/@{acct}", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(8000)
        for _ in range(3): pg.mouse.wheel(0, 2500); pg.wait_for_timeout(1500)
        html = pg.content(); title = pg.title(); b.close()
    for vid in dict.fromkeys(re.findall(rf"/@{acct}/video/(\d{{15,22}})", html)):
        found.append({"url": f"https://www.tiktok.com/@{acct}/video/{vid}"})
    return found[:8], title

for acct in ACCOUNTS:
    rec = {"account": acct}
    try:
        items, err = via_ytdlp(acct); rec["ytdlp_count"] = len(items); rec["ytdlp_sample"] = items[:3]
        if not items: rec["ytdlp_err"] = err[-300:]
    except Exception as e:
        items = []; rec["ytdlp_err"] = repr(e)[:300]
    if not items:
        try:
            items, title = via_browser(acct); rec["browser_count"] = len(items); rec["browser_title"] = title; rec["browser_sample"] = items[:3]
        except Exception as e:
            rec["browser_err"] = repr(e)[:300]
    rec["urls"] = [i["url"] for i in items]
    report["discovery"].append(rec); print(json.dumps(rec)[:900], flush=True)

# batch: download newest 2 per account, 2-4 s apart, to test rate limits
for rec in report["discovery"]:
    for url in rec["urls"][:2]:
        tag = f"{rec['account']}_{url.rsplit('/', 1)[-1]}"
        t0 = time.time()
        rc, out, err = sh(["yt-dlp", "--no-warnings", "-f", "best[ext=mp4]/best", "-o", f"/tmp/{tag}.mp4",
                           "--print-json", "--no-simulate", url])
        d = {"url": url, "ok": rc == 0 and os.path.exists(f"/tmp/{tag}.mp4"), "secs": round(time.time() - t0, 1)}
        if d["ok"]:
            try:
                j = json.loads(out.strip().splitlines()[-1])
                d.update(title=(j.get("title") or "")[:90], duration=j.get("duration"), width=j.get("width"), height=j.get("height"),
                         uploaded=j.get("timestamp"), views=j.get("view_count"))
            except Exception:
                pass
            sh(["ffmpeg", "-y", "-ss", "1", "-t", "4", "-i", f"/tmp/{tag}.mp4", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-map_metadata", "-1", f"{OUT}/{tag}.mp4"])
        else:
            d["error"] = err[-300:]
        report["downloads"].append(d); print(json.dumps(d)[:500], flush=True)
        time.sleep(3)

ok = sum(d["ok"] for d in report["downloads"])
report["summary"] = {"accounts_discovered": sum(1 for r in report["discovery"] if r["urls"]),
                     "downloads_ok": ok, "downloads_total": len(report["downloads"])}
json.dump(report, open(f"{OUT}/report.json", "w"), indent=2)
print("SUMMARY", report["summary"])
