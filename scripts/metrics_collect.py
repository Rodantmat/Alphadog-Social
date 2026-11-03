#!/usr/bin/env python3
"""Daily read-only metrics snapshot for every platform -> content/metrics/<date>.json (+ latest.json).
YouTube: Data API per-video views/likes/comments (+ YouTube Analytics impressions/CTR/avg view duration/retention when the
token has yt-analytics.readonly and the API is enabled). Instagram: per-media views/reach/likes/comments/saves/shares.
Facebook: page followers + per-post reactions/comments/shares + reel plays. TikTok: public profile via yt-dlp.
Each source fails independently (its error is recorded); nothing is ever posted or changed."""
import datetime as dt, json, os, subprocess, urllib.error, urllib.parse, urllib.request
NOW = dt.datetime.now(dt.timezone.utc); OUT = {"at": NOW.strftime("%Y-%m-%dT%H:%M:%SZ")}
def http(url, data=None, headers=None):
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers or {}), timeout=40) as r: return json.loads(r.read())
def safe(name, fn):
    try: OUT[name] = fn()
    except urllib.error.HTTPError as e: OUT[name] = {"error": f"{e.code} {e.read().decode()[:300]}"}
    except Exception as e: OUT[name] = {"error": str(e)[:300]}

def youtube():
    d = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                                "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    t = http("https://oauth2.googleapis.com/token", data=d); H = {"Authorization": "Bearer " + t["access_token"]}
    g = lambda u: http(u, headers=H)
    ch = g("https://www.googleapis.com/youtube/v3/channels?part=statistics,contentDetails&mine=true")["items"][0]
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]; ids, tok = [], ""
    while True:
        r = g(f"https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults=50&playlistId={up}" + (f"&pageToken={tok}" if tok else ""))
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]; tok = r.get("nextPageToken")
        if not tok: break
    vids = []
    for i in range(0, len(ids), 50):
        for v in g("https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,status,contentDetails&id=" + ",".join(ids[i:i + 50]))["items"]:
            if v["snippet"]["publishedAt"] < "2026-01-01": continue          # old personal uploads
            s = v["statistics"]
            vids.append({"id": v["id"], "title": v["snippet"]["title"], "published": v["snippet"]["publishedAt"], "privacy": v["status"]["privacyStatus"],
                         "duration": v["contentDetails"]["duration"], "views": int(s.get("viewCount", 0)), "likes": int(s.get("likeCount", 0)),
                         "comments": int(s.get("commentCount", 0))})
    res = {"channel": ch["statistics"], "videos": vids, "scopes": t.get("scope", "")}
    if "yt-analytics" in t.get("scope", ""):
        start = "2026-10-01"; end = NOW.date().isoformat()
        try:
            a = g("https://youtubeanalytics.googleapis.com/v2/reports?" + urllib.parse.urlencode({
                "ids": "channel==MINE", "startDate": start, "endDate": end, "dimensions": "video", "sort": "-views", "maxResults": "200",
                "metrics": "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained"}))
            res["analytics_by_video"] = {"columns": [c["name"] for c in a.get("columnHeaders", [])], "rows": a.get("rows", [])}
            a = g("https://youtubeanalytics.googleapis.com/v2/reports?" + urllib.parse.urlencode({
                "ids": "channel==MINE", "startDate": start, "endDate": end, "dimensions": "insightTrafficSourceType", "metrics": "views,estimatedMinutesWatched"}))
            res["traffic_sources"] = a.get("rows", [])
        except urllib.error.HTTPError as e: res["analytics_error"] = f"{e.code} {e.read().decode()[:300]}"
        # Reporting API: impressions + impressions CTR per video (daily CSV reports; the job is created once, first data ~2 days later)
        try:
            R = "https://youtubereporting.googleapis.com/v1"
            jobs = g(f"{R}/jobs").get("jobs", [])
            job = next((j for j in jobs if j["reportTypeId"] == "channel_reach_basic_a1"), None)
            if not job:
                job = http(f"{R}/jobs", data=json.dumps({"reportTypeId": "channel_reach_basic_a1", "name": "alphadog reach"}).encode(),
                           headers={**H, "Content-Type": "application/json"}); res["reach_job"] = "created"
            reps = sorted(g(f"{R}/jobs/{job['id']}/reports").get("reports", []), key=lambda r: r["startTime"])[-14:]
            agg = {}
            for rp in reps:
                with urllib.request.urlopen(urllib.request.Request(rp["downloadUrl"], headers=H), timeout=60) as r: rows = r.read().decode().splitlines()
                hd = rows[0].split(",")
                for ln in rows[1:]:
                    d = dict(zip(hd, ln.split(","))); v = d.get("video_id")
                    if not v: continue
                    a_ = agg.setdefault(v, {"impressions": 0, "ctr_x_impr": 0.0})
                    im = int(float(d.get("video_thumbnail_impressions") or 0)); a_["impressions"] += im
                    a_["ctr_x_impr"] += im * float(d.get("video_thumbnail_impressions_ctr") or 0)
            for v, a_ in agg.items(): a_["ctr"] = round(a_["ctr_x_impr"] / a_["impressions"], 4) if a_["impressions"] else None; a_.pop("ctr_x_impr")
            res["reach_14d"] = {"reports": len(reps), "by_video": agg}
        except urllib.error.HTTPError as e: res["reach_error"] = f"{e.code} {e.read().decode()[:300]}"
        except Exception as e: res["reach_error"] = str(e)[:300]
    return res

def instagram():
    T = os.environ["IG_TOKEN"].strip(); B = "https://graph.instagram.com"
    q = lambda p, **k: http(f"{B}/{p}?" + urllib.parse.urlencode({**k, "access_token": T}))
    me = q("me", fields="username,followers_count,media_count"); items = []
    for x in q("me/media", fields="id,media_product_type,timestamp,like_count,comments_count,caption,permalink", limit="50").get("data", []):
        if x["timestamp"] < "2026-01-01": continue
        try: ins = {d["name"]: d["values"][0]["value"] for d in q(f"{x['id']}/insights", metric="views,reach,saved,shares,total_interactions,ig_reels_avg_watch_time").get("data", [])}
        except Exception: ins = {d["name"]: d["values"][0]["value"] for d in q(f"{x['id']}/insights", metric="views,reach,saved,shares,total_interactions").get("data", [])}
        items.append({"id": x["id"], "at": x["timestamp"], "caption": (x.get("caption") or "")[:80], "likes": x.get("like_count", 0),
                      "comments": x.get("comments_count", 0), **ins})
    return {"profile": me, "media": items}

def facebook():
    T = os.environ["FB_TOKEN"].strip(); P = os.environ["FB_PAGE"].strip(); B = "https://graph.facebook.com/v26.0"
    q = lambda p, **k: http(f"{B}/{p}?" + urllib.parse.urlencode({**k, "access_token": T}))
    res = {"page": q(P, fields="followers_count,fan_count"), "posts": [], "reels": []}
    for x in q(f"{P}/posts", fields="id,created_time,message,shares,reactions.summary(true),comments.summary(true)", limit="50").get("data", []):
        res["posts"].append({"id": x["id"], "at": x["created_time"], "text": (x.get("message") or "")[:80],
                             "reactions": x.get("reactions", {}).get("summary", {}).get("total_count", 0),
                             "comments": x.get("comments", {}).get("summary", {}).get("total_count", 0), "shares": x.get("shares", {}).get("count", 0)})
    try:
        for x in q(f"{P}/video_reels", fields="id,created_time,description", limit="50").get("data", []):
            v = {}
            for met in ("fb_reels_total_plays", "blue_reels_play_count", "post_impressions_unique", "post_video_avg_time_watched", "post_video_followers"):
                try: v.update({d["name"]: d["values"][0]["value"] for d in q(f"{x['id']}/video_insights", metric=met).get("data", [])})
                except Exception: pass
            if not v:
                try: v = {d["name"]: d["values"][0]["value"] for d in q(f"{x['id']}/video_insights").get("data", []) if d.get("values")}
                except urllib.error.HTTPError as e: v = {"error": e.read().decode()[:160]}
            res["reels"].append({"id": x["id"], "at": x["created_time"], "text": (x.get("description") or "")[:80], **v})
    except Exception as e: res["reels_error"] = str(e)[:200]
    return res

def tiktok():
    h = os.environ.get("TT_HANDLE", "alphadogstudio")
    r = subprocess.run(["yt-dlp", "--impersonate", "chrome", "-J", "--flat-playlist", f"https://www.tiktok.com/@{h}"], capture_output=True, text=True, timeout=300)
    ents = (json.loads(r.stdout).get("entries") or []) if r.stdout.strip() else []; vids = []
    for e in ents[:60]:
        v = e
        if v.get("view_count") is None:
            rr = subprocess.run(["yt-dlp", "--impersonate", "chrome", "-J", "--skip-download", e.get("url")], capture_output=True, text=True, timeout=120)
            try: v = json.loads(rr.stdout)
            except Exception: continue
        ts = v.get("timestamp") or 0
        if ts and ts < 1767225600: continue                                   # 2026-01-01: skip the 2022 travel posts
        vids.append({"id": v.get("id"), "at": dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if ts else None,
                     "title": (v.get("title") or v.get("description") or "")[:80], "duration": v.get("duration"),
                     "views": v.get("view_count") or 0, "likes": v.get("like_count") or 0, "comments": v.get("comment_count") or 0,
                     "shares": v.get("repost_count") or 0})
    return {"handle": h, "videos": vids, "listed": len(ents)}

for n, f in (("youtube", youtube), ("instagram", instagram), ("facebook", facebook), ("tiktok", tiktok)): safe(n, f)
os.makedirs("content/metrics", exist_ok=True)
for p in (f"content/metrics/{NOW.date().isoformat()}.json", "content/metrics/latest.json"):
    json.dump(OUT, open(p, "w"), ensure_ascii=False, indent=1)
for n in ("youtube", "instagram", "facebook", "tiktok"):
    v = OUT[n]; print(n, "ERROR " + v["error"] if "error" in v else "ok", {k: len(x) for k, x in v.items() if isinstance(x, list)})
