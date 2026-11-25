#!/usr/bin/env python3
"""Read-only: print status/contentDetails/processingDetails/topic for given video ids (1 quota unit per call)."""
import json, os, urllib.parse, urllib.request
d = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                            "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
tok = json.loads(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=d), timeout=30).read())["access_token"]
ids = os.environ["IDS"].replace(" ", "")
u = "https://www.googleapis.com/youtube/v3/videos?part=status,contentDetails,processingDetails,snippet,statistics&id=" + ids
for it in json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"Authorization": f"Bearer {tok}"}), timeout=30).read())["items"]:
    print("VIDEO", it["id"], it["snippet"]["title"][:50], "| published", it["snippet"]["publishedAt"])
    print("  status", json.dumps(it["status"]))
    print("  details", json.dumps({k: it["contentDetails"].get(k) for k in ("duration", "definition", "licensedContent", "regionRestriction", "contentRating")}))
    print("  processing", json.dumps(it.get("processingDetails")))
    print("  stats", json.dumps(it["statistics"]), "| tags", len(it["snippet"].get("tags", [])), "| cat", it["snippet"].get("categoryId"), "| defaultLang", it["snippet"].get("defaultAudioLanguage"))
