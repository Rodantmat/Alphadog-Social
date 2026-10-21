"""Round 2 footage probe. Fixes vs round 1: single-post URLs, real-browser capture of nba.com player streams,
full browser headers for NBA CDN/stats, alternate YouTube player clients. Writes clips/probe2/report.json."""
import json, os, subprocess, time, urllib.request

OUT = "clips/probe2"; os.makedirs(OUT, exist_ok=True)
report = []
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
H = {"User-Agent": UA, "Referer": "https://www.nba.com/", "Origin": "https://www.nba.com",
     "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US,en;q=0.9",
     "x-nba-stats-origin": "stats", "x-nba-stats-token": "true"}

def sh(cmd, timeout=240):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)[-1500:]
    except subprocess.TimeoutExpired:
        return 124, "timeout"

def trim(src, tag, start="2", headers=None):
    out = f"{OUT}/{tag}.mp4"
    cmd = ["ffmpeg", "-y"]
    if headers: cmd += ["-headers", "".join(f"{k}: {v}\r\n" for k, v in headers.items())]
    cmd += ["-ss", start, "-t", "5", "-i", src, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-movflags", "+faststart", "-map_metadata", "-1", out]
    rc, log = sh(cmd, 180)
    if rc != 0 or not os.path.exists(out) or os.path.getsize(out) < 20000: return None, log
    _, info = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=codec_type,width,height", "-of", "json", out], 30)
    return out, info

def add(rec): report.append(rec); print(json.dumps(rec)[:1400], flush=True)

def ytdlp(tag, url, extra=None):
    t0 = time.time(); raw = f"/tmp/{tag}.%(ext)s"
    cmd = ["yt-dlp", "--no-warnings", "--socket-timeout", "30", "-f", "best[height<=720][ext=mp4]/best[ext=mp4]/best",
           "-o", raw] + (extra or []) + [url]
    rc, log = sh(cmd)
    files = [f for f in os.listdir("/tmp") if f.startswith(tag + ".")]
    rec = {"source": tag, "url": url, "ok": False, "secs": round(time.time() - t0, 1)}
    if rc == 0 and files:
        out, info = trim("/tmp/" + files[0], tag); rec.update(ok=bool(out), file=out, info=(info or "")[-500:])
    else:
        rec["error"] = log[-700:]
    add(rec)

def get(url, headers, timeout=30):
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as r:
        return r.status, r.read()

# 1. TikTok single official @nba videos
ytdlp("tiktok_nba_raptors_heat", "https://www.tiktok.com/@nba/video/7692627847864749342")
ytdlp("tiktok_nba_kyrie", "https://www.tiktok.com/@nba/video/7689676638186933535", ["--impersonate", "chrome"])

# 2. YouTube with alternate clients (no cookies)
for client in ["tv", "web_safari", "mweb", "android_vr"]:
    ytdlp(f"youtube_{client}", "https://www.youtube.com/watch?v=NZmml7nxVaI",
          ["--extractor-args", f"youtube:player_client={client}"])

# 3. NBA CDN + stats with full headers
rec = {"source": "nba_cdn_stats_headers", "ok": False, "steps": []}
for name, url in [("cdn_pbp", "https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_0022600001.json"),
                  ("cdn_boxscore", "https://cdn.nba.com/static/json/liveData/boxscore/boxscore_0022600001.json"),
                  ("cdn_headshot", "https://cdn.nba.com/headshots/nba/latest/1040x760/1630595.png"),
                  ("stats_pbpv3", "https://stats.nba.com/stats/playbyplayv3?GameID=0022600001&StartPeriod=0&EndPeriod=0"),
                  ("stats_video", "https://stats.nba.com/stats/videoeventsasset?GameEventID=10&GameID=0022600001")]:
    try:
        st, body = get(url, H, 25); rec["steps"].append(f"{name}: {st} {len(body)}B {body[:160]!r}")
        if name == "stats_video" and b"videoUrls" in body:
            j = json.loads(body); urls = j["resultSets"]["Meta"]["videoUrls"]
            murl = next((u.get("lurl") or u.get("murl") for u in urls if (u.get("lurl") or u.get("murl"))), None)
            if murl:
                out, info = trim(murl, "nba_perplay", "0", {"User-Agent": UA, "Referer": "https://www.nba.com/"})
                rec.update(ok=bool(out), file=out, video_url=murl, info=(info or "")[-300:])
    except Exception as e:
        rec["steps"].append(f"{name}: FAIL {e!r}"[:220])
add(rec)

# 4. Real browser on nba.com watch pages: capture media requests the player makes
def browser_capture(tag, page_url):
    rec = {"source": tag, "url": page_url, "ok": False}
    try:
        from playwright.sync_api import sync_playwright
        media = []
        with sync_playwright() as p:
            b = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
            pg = b.new_page(user_agent=UA, viewport={"width": 1280, "height": 800})
            pg.on("request", lambda r: media.append(r.url) if any(x in r.url for x in (".m3u8", ".mp4", ".mpd")) else None)
            resp = pg.goto(page_url, wait_until="domcontentloaded", timeout=60000)
            rec["page_status"] = resp.status if resp else None
            for sel in ["button[aria-label*='Play' i]", ".vjs-big-play-button", "video"]:
                try: pg.click(sel, timeout=4000); break
                except Exception: pass
            pg.wait_for_timeout(15000)
            rec["title"] = pg.title()
            b.close()
        rec["media_seen"] = media[:8]
        src = next((u for u in media if ".m3u8" in u), None) or next((u for u in media if ".mp4" in u), None)
        if src:
            out, info = trim(src, tag, "3", {"User-Agent": UA, "Referer": "https://www.nba.com/"})
            rec.update(ok=bool(out), file=out, stream=src, info=(info or "")[-400:])
    except Exception as e:
        rec["error"] = repr(e)[:500]
    add(rec)

browser_capture("nbacom_top10_oct16", "https://www.nba.com/watch/video/top-10-plays-october-16-2026")
browser_capture("nbacom_wemby", "https://www.nba.com/watch/video/victor-wembanyamas-best-guard-like-plays-of-the-season")

json.dump(report, open(f"{OUT}/report.json", "w"), indent=2)
print("SUMMARY", [(r["source"], r["ok"]) for r in report])
