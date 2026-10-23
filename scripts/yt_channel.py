#!/usr/bin/env python3
"""Channel management via YouTube Data API.
  yt_channel.py inspect            -> list channel info + every upload (id, privacy, date, views, title)
  yt_channel.py privatize          -> set every currently public/unlisted upload to private (reversible)
  yt_channel.py branding CFG_JSON  -> update description/keywords/country/language (+title attempt), banner, not-made-for-kids
Env: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN."""
import json, os, sys, urllib.parse, urllib.request, urllib.error

def http(url, data=None, headers=None, method=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method or ("POST" if data is not None else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=120) as r: return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e: return e.code, {"_error": e.read().decode(errors="replace")[:1500]}

st, tok = http("https://oauth2.googleapis.com/token", urllib.parse.urlencode({
    "refresh_token": os.environ["YT_REFRESH_TOKEN"].strip(), "client_id": os.environ["YT_CLIENT_ID"].strip(),
    "client_secret": os.environ["YT_CLIENT_SECRET"].strip(), "grant_type": "refresh_token"}).encode(),
    {"Content-Type": "application/x-www-form-urlencoded"})
if st != 200: sys.exit(f"REFRESH_FAILED {st} {tok}")
AUTH = {"Authorization": "Bearer " + tok["access_token"]}
API = "https://www.googleapis.com/youtube/v3/"

def get(path, **q):
    st, r = http(API + path + "?" + urllib.parse.urlencode(q), headers=AUTH)
    if st != 200: sys.exit(f"GET {path} {st} {r}")
    return r

def channel():
    return get("channels", part="snippet,brandingSettings,contentDetails,statistics,status", mine="true")["items"][0]

def uploads(ch):
    pl = ch["contentDetails"]["relatedPlaylists"]["uploads"]; ids = []; page = None
    while True:
        q = {"part": "contentDetails", "playlistId": pl, "maxResults": 50}
        if page: q["pageToken"] = page
        r = get("playlistItems", **q); ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        page = r.get("nextPageToken")
        if not page: break
    vids = []
    for i in range(0, len(ids), 50):
        vids += get("videos", part="snippet,status,statistics,contentDetails", id=",".join(ids[i:i + 50])).get("items", [])
    return vids

mode = sys.argv[1]
ch = channel()
print("CHANNEL", ch["id"], "|", ch["snippet"]["title"], "| handle:", ch["snippet"].get("customUrl"), "| created:", ch["snippet"].get("publishedAt"),
      "| subs:", ch["statistics"].get("subscriberCount"), "| country:", ch["snippet"].get("country"), "| lang:", ch["snippet"].get("defaultLanguage"))

if mode == "inspect":
    print("DESCRIPTION:", ch["snippet"].get("description", "")[:300].replace("\n", " / "))
    print("BRANDING:", json.dumps(ch.get("brandingSettings", {}))[:800])
    for v in uploads(ch):
        print("VIDEO", v["id"], v["status"]["privacyStatus"], v["snippet"]["publishedAt"][:10], "| views:", v.get("statistics", {}).get("viewCount"),
              "| dur:", v.get("contentDetails", {}).get("duration"), "| kids:", v["status"].get("madeForKids"), "|", v["snippet"]["title"][:70])
    print("STATUS:", json.dumps(ch.get("status", {})))
    print("TOTAL_VIEWS:", ch["statistics"].get("viewCount"), "| VIDEO_COUNT:", ch["statistics"].get("videoCount"))

elif mode == "privatize":
    n = 0
    for v in uploads(ch):
        s = v["status"]
        if s["privacyStatus"] == "private": continue
        body = {"id": v["id"], "status": {"privacyStatus": "private", "embeddable": s.get("embeddable", True),
                "license": s.get("license", "youtube"), "publicStatsViewable": s.get("publicStatsViewable", True),
                "selfDeclaredMadeForKids": s.get("madeForKids", False)}}
        st, r = http(API + "videos?part=status", json.dumps(body).encode(), {**AUTH, "Content-Type": "application/json"}, "PUT")
        print("PRIVATIZE", v["id"], st, "" if st == 200 else r.get("_error", "")[:300]); n += st == 200
    print("PRIVATIZED_TOTAL", n)

elif mode == "branding":
    cfg = json.load(open(sys.argv[2]))
    bs = ch.get("brandingSettings", {}); c = bs.setdefault("channel", {})
    c["description"] = open(cfg["description_file"]).read().strip()
    c["keywords"] = cfg["keywords"]; c["country"] = cfg.get("country", "US"); c["defaultLanguage"] = cfg.get("language", "en")
    c.pop("title", None)
    if cfg.get("banner"):
        data = open(cfg["banner"], "rb").read()
        st, r = http("https://www.googleapis.com/upload/youtube/v3/channelBanners/insert?uploadType=media", data,
                     {**AUTH, "Content-Type": "image/jpeg"})
        print("BANNER_UPLOAD", st, r.get("_error", "")[:300])
        if st == 200: bs.setdefault("image", {})["bannerExternalUrl"] = r["url"]
    body = {"id": ch["id"], "brandingSettings": {k: v for k, v in bs.items() if k in ("channel", "image")}}
    st, r = http(API + "channels?part=brandingSettings", json.dumps(body).encode(), {**AUTH, "Content-Type": "application/json"}, "PUT")
    print("BRANDING_UPDATE", st, r.get("_error", "")[:600])
    if cfg.get("title") and st == 200:  # API title changes are often rejected; non-fatal
        body["brandingSettings"]["channel"]["title"] = cfg["title"]
        st2, r2 = http(API + "channels?part=brandingSettings", json.dumps(body).encode(), {**AUTH, "Content-Type": "application/json"}, "PUT")
        print("TITLE_UPDATE", st2, r2.get("_error", "")[:400] if st2 != 200 else r2.get("brandingSettings", {}).get("channel", {}).get("title"))
    st3, r3 = http(API + "channels?part=status", json.dumps({"id": ch["id"], "status": {"selfDeclaredMadeForKids": False}}).encode(),
                   {**AUTH, "Content-Type": "application/json"}, "PUT")
    print("KIDS_SETTING", st3, r3.get("_error", "")[:300] if st3 != 200 else r3.get("status"))
    now = channel()
    print("NOW:", now["snippet"]["title"], "| country:", now["snippet"].get("country"), "| lang:", now["snippet"].get("defaultLanguage"),
          "| banner:", bool(now.get("brandingSettings", {}).get("image")), "| keywords:", now["brandingSettings"]["channel"].get("keywords"))
