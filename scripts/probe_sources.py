"""Probe which official NBA footage sources a GitHub runner can actually pull.
Each source: try to get one video, trim 5 s, strip metadata, save to clips/probe/. Writes clips/probe/report.json."""
import json, os, subprocess, time, urllib.request, urllib.error

OUT = "clips/probe"; os.makedirs(OUT, exist_ok=True)
report = []
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
STATS_H = {"User-Agent": UA, "Referer": "https://www.nba.com/", "Origin": "https://www.nba.com",
           "Accept": "application/json, text/plain, */*", "x-nba-stats-origin": "stats", "x-nba-stats-token": "true"}

def sh(cmd, timeout=240):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)[-1500:]
    except subprocess.TimeoutExpired:
        return 124, "timeout"

def trim(raw, tag, start="2"):
    out = f"{OUT}/{tag}.mp4"
    rc, log = sh(["ffmpeg", "-y", "-ss", start, "-t", "5", "-i", raw, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                  "-c:a", "aac", "-movflags", "+faststart", "-map_metadata", "-1", out], 120)
    if rc != 0 or not os.path.exists(out): return None, log
    rc2, dur = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height", "-of", "json", out], 30)
    return out, dur

def ytdlp(tag, url, playlist=False, extra=None):
    t0 = time.time(); raw = f"/tmp/{tag}.%(ext)s"
    cmd = ["yt-dlp", "--no-warnings", "--socket-timeout", "30", "-f", "best[height<=720][ext=mp4]/best[ext=mp4]/best",
           "--merge-output-format", "mp4", "-o", raw]
    if playlist: cmd += ["--playlist-items", "1"]
    cmd += (extra or []) + [url]
    rc, log = sh(cmd)
    files = [f for f in os.listdir("/tmp") if f.startswith(tag + ".")]
    rec = {"source": tag, "url": url, "ok": False, "secs": round(time.time() - t0, 1)}
    if rc == 0 and files:
        out, info = trim("/tmp/" + files[0], tag)
        rec.update(ok=bool(out), file=out, info=info[-600:])
    else:
        rec["error"] = log[-900:]
    report.append(rec); print(json.dumps(rec)[:1200], flush=True)

def get_json(url, headers, timeout=30):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def perplay():
    """NBA per-play video: live pbp (cdn) -> videoeventsasset (stats.nba.com) -> mp4 on videos.nba.com"""
    rec = {"source": "nba_perplay", "ok": False, "steps": []}
    game = "0022600001"  # BOS @ DET, Oct 20 2026
    try:
        pbp = get_json(f"https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_{game}.json", {"User-Agent": UA})
        acts = pbp["game"]["actions"]
        dunks = [a for a in acts if a.get("shotResult") == "Made" and "dunk" in (a.get("subType", "") + a.get("descriptor", "")).lower()]
        made = dunks or [a for a in acts if a.get("shotResult") == "Made"]
        rec["steps"].append(f"cdn pbp ok, {len(acts)} actions, {len(dunks)} made dunks")
    except Exception as e:
        rec["steps"].append(f"cdn pbp failed: {e!r}"); report.append(rec); print(rec); return
    for a in made[:4]:
        ev = a["actionNumber"]
        try:
            j = get_json(f"https://stats.nba.com/stats/videoeventsasset?GameEventID={ev}&GameID={game}", STATS_H, 40)
            urls = j.get("resultSets", {}).get("Meta", {}).get("videoUrls", [])
            murl = next((u.get("lurl") or u.get("murl") or u.get("surl") for u in urls if (u.get("lurl") or u.get("murl"))), None)
            rec["steps"].append(f"ev {ev} ({a.get('description','')[:60]}): {len(urls)} urls")
            if not murl: continue
            raw = f"/tmp/perplay_{ev}.mp4"
            urllib.request.urlretrieve(murl, raw)
            out, info = trim(raw, f"perplay_{ev}", "0")
            if out:
                rec.update(ok=True, file=out, video_url=murl, play=a.get("description"), info=info[-400:]); break
        except Exception as e:
            rec["steps"].append(f"ev {ev} failed: {e!r}"[:300])
    report.append(rec); print(json.dumps(rec)[:1500], flush=True)

# --- run every source
ytdlp("youtube_nba_latest", "https://www.youtube.com/@NBA/videos", playlist=True)
ytdlp("youtube_bos_det", "https://www.youtube.com/watch?v=NZmml7nxVaI")
ytdlp("tiktok_nba_latest", "https://www.tiktok.com/@nba", playlist=True)
ytdlp("instagram_nba_reels", "https://www.instagram.com/nba/reels/", playlist=True)
ytdlp("x_nba_media", "https://x.com/NBA/media", playlist=True)
ytdlp("nbacom_watch_impersonate", "https://www.nba.com/watch/video/victor-wembanyamas-best-guard-like-plays-of-the-season",
      extra=["--impersonate", "chrome"])
perplay()

json.dump(report, open(f"{OUT}/report.json", "w"), indent=2)
print("SUMMARY", [(r["source"], r["ok"]) for r in report])
