import os, sys, json, urllib.request, urllib.parse
def tok():
    d = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"], "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    return json.load(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", d)))["access_token"]
T = tok()
def get(u, raw=False):
    r = urllib.request.urlopen(urllib.request.Request(u, headers={"Authorization": "Bearer " + T})).read()
    return r.decode("utf8", "replace") if raw else json.loads(r)
for v in sys.argv[1].split(","):
    j = get(f"https://www.googleapis.com/youtube/v3/captions?part=snippet&videoId={v}")
    for it in j.get("items", []):
        s = it["snippet"]; print("CAP", v, it["id"], s["language"], repr(s.get("name")), s.get("trackKind"), s.get("isDraft"), s.get("lastUpdated"))
        if os.environ.get("DL") and s["language"] in os.environ["DL"].split(","):
            try: print("  TXT", get(f"https://www.googleapis.com/youtube/v3/captions/{it['id']}?tfmt=srt", raw=True)[:160].replace("\n", " | "))
            except Exception as e: print("  dl err", e)
    vj = get(f"https://www.googleapis.com/youtube/v3/videos?part=snippet,localizations&id={v}")["items"][0]
    print("LANG", v, vj["snippet"].get("defaultLanguage"), vj["snippet"].get("defaultAudioLanguage"), list((vj.get("localizations") or {}).keys()))
