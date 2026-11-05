#!/usr/bin/env python3
"""Deep read-only analytics pull -> content/metrics/deep.json. YouTube Analytics (daily trend, content type, geo, device, age/gender,
subscribed status, traffic by video, search terms, external/related sources, sharing, retention curves, subs by video),
Instagram account insights + demographics, Facebook page insights. Each query fails independently; nothing is posted or changed."""
import datetime as dt, json, os, urllib.error, urllib.parse, urllib.request
NOW = dt.datetime.now(dt.timezone.utc); TODAY = NOW.date().isoformat(); S28 = (NOW - dt.timedelta(days=28)).date().isoformat(); S0 = "2026-10-01"
OUT = {"at": NOW.strftime("%Y-%m-%dT%H:%M:%SZ")}
def http(url, data=None, headers=None):
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers or {}), timeout=60) as r: return json.loads(r.read())
def tryq(fn):
    try: return fn()
    except urllib.error.HTTPError as e: return {"error": f"{e.code} {e.read().decode()[:220]}"}
    except Exception as e: return {"error": str(e)[:220]}
def yt():
    d = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                                "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    t = http("https://oauth2.googleapis.com/token", data=d); H = {"Authorization": "Bearer " + t["access_token"]}
    def rep(metrics, dims=None, start=S0, filters=None, sort=None, mx=None):
        p = {"ids": "channel==MINE", "startDate": start, "endDate": TODAY, "metrics": metrics}
        if dims: p["dimensions"] = dims
        if filters: p["filters"] = filters
        if sort: p["sort"] = sort
        if mx: p["maxResults"] = str(mx)
        a = http("https://youtubeanalytics.googleapis.com/v2/reports?" + urllib.parse.urlencode(p), headers=H)
        return {"cols": [c["name"] for c in a.get("columnHeaders", [])], "rows": a.get("rows", [])}
    R = {}
    R["scopes"] = t.get("scope", "")
    R["totals"] = tryq(lambda: rep("views,estimatedMinutesWatched,averageViewDuration,likes,comments,shares,subscribersGained,subscribersLost"))
    R["daily"] = tryq(lambda: rep("views,estimatedMinutesWatched,subscribersGained,subscribersLost", "day", sort="day"))
    R["content_type"] = tryq(lambda: rep("views,estimatedMinutesWatched,averageViewDuration,subscribersGained", "creatorContentType"))
    R["daily_by_type"] = tryq(lambda: rep("views", "day,creatorContentType", sort="day"))
    R["country"] = tryq(lambda: rep("views,estimatedMinutesWatched,subscribersGained", "country", sort="-views", mx=15))
    R["device"] = tryq(lambda: rep("views,estimatedMinutesWatched", "deviceType"))
    R["os"] = tryq(lambda: rep("views", "operatingSystem"))
    R["age_gender"] = tryq(lambda: rep("viewerPercentage", "ageGroup,gender"))
    R["subscribed_status"] = tryq(lambda: rep("views,estimatedMinutesWatched,averageViewDuration", "subscribedStatus"))
    R["sharing"] = tryq(lambda: rep("shares", "sharingService", sort="-shares"))
    R["playback_location"] = tryq(lambda: rep("views,estimatedMinutesWatched", "insightPlaybackLocationType"))
    R["subs_by_video"] = tryq(lambda: rep("subscribersGained,subscribersLost,views", "video", sort="-subscribersGained", mx=15))
    for st in ("YT_SEARCH", "RELATED_VIDEO", "EXT_URL", "YT_CHANNEL", "YT_OTHER_PAGE", "SHORTS", "NOTIFICATION", "SUBSCRIBER", "PLAYLIST", "END_SCREEN", "HASHTAGS"):
        R["tsd_" + st] = tryq(lambda st=st: rep("views,estimatedMinutesWatched", "insightTrafficSourceDetail", filters=f"insightTrafficSourceType=={st}", sort="-views", mx=12))
    vids = tryq(lambda: rep("views", "video", sort="-views", mx=60))
    R["videos_ranked"] = vids
    top = [r[0] for r in vids.get("rows", [])][:60]
    R["by_video_traffic"] = {}; R["retention"] = {}; R["video_detail"] = {}
    for v in top:
        R["by_video_traffic"][v] = tryq(lambda v=v: rep("views", "insightTrafficSourceType", filters=f"video=={v}"))
        R["video_detail"][v] = tryq(lambda v=v: rep("views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained,annotationClickThroughRate,cardClickRate,cardTeaserClickRate", filters=f"video=={v}"))
        R["retention"][v] = tryq(lambda v=v: rep("audienceWatchRatio,relativeRetentionPerformance", "elapsedVideoTimeRatio", filters=f"video=={v}"))
    return R
def ig():
    T = os.environ["IG_TOKEN"].strip(); B = "https://graph.instagram.com"
    q = lambda p, **k: http(f"{B}/{p}?" + urllib.parse.urlencode({**k, "access_token": T}))
    R = {}
    since = int((NOW - dt.timedelta(days=28)).timestamp()); until = int(NOW.timestamp())
    for name, kw in {"account_totals": dict(metric="reach,views,profile_views,website_clicks,total_interactions,likes,comments,shares,saves,follows_and_unfollows,profile_links_taps", period="day", metric_type="total_value", since=since, until=until),
                     "reach_by_follow_type": dict(metric="reach", period="day", metric_type="total_value", breakdown="follow_type", since=since, until=until),
                     "reach_by_product": dict(metric="reach", period="day", metric_type="total_value", breakdown="media_product_type", since=since, until=until),
                     "views_by_follow_type": dict(metric="views", period="day", metric_type="total_value", breakdown="follow_type", since=since, until=until),
                     "followers_country": dict(metric="follower_demographics", period="lifetime", metric_type="total_value", breakdown="country"),
                     "followers_age": dict(metric="follower_demographics", period="lifetime", metric_type="total_value", breakdown="age"),
                     "followers_gender": dict(metric="follower_demographics", period="lifetime", metric_type="total_value", breakdown="gender"),
                     "engaged_country": dict(metric="engaged_audience_demographics", period="lifetime", metric_type="total_value", breakdown="country"),
                     "follower_count_daily": dict(metric="follower_count", period="day", since=since, until=until)}.items():
        R[name] = tryq(lambda kw=kw: q("me/insights", **kw))
    return R
def fb():
    T = os.environ["FB_TOKEN"].strip(); P = os.environ["FB_PAGE"].strip(); B = "https://graph.facebook.com/v26.0"
    q = lambda p, **k: http(f"{B}/{p}?" + urllib.parse.urlencode({**k, "access_token": T}))
    R = {}
    for m in ("page_media_view", "page_total_media_view_unique", "page_views_total", "page_follows", "page_daily_follows_unique", "page_daily_unfollows_unique",
              "page_post_engagements", "page_video_views", "page_impressions", "page_impressions_unique", "page_fans", "page_actions_post_reactions_total"):
        R[m] = tryq(lambda m=m: q(f"{P}/insights", metric=m, period="day", since=int((NOW - dt.timedelta(days=28)).timestamp()), until=int(NOW.timestamp())))
    return R
OUT["youtube"] = tryq(yt); OUT["instagram"] = tryq(ig); OUT["facebook"] = tryq(fb)
os.makedirs("content/metrics", exist_ok=True); json.dump(OUT, open("content/metrics/deep.json", "w"), indent=1)
print("ok", {k: (len(json.dumps(v))) for k, v in OUT.items() if k != "at"})
