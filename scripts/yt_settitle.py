#!/usr/bin/env python3
"""Set the title of PRIVATE (not yet published) videos. env: PAIRS = JSON {"videoId": "new title"}; YT_CLIENT_ID/SECRET/REFRESH_TOKEN. Refuses non-private videos (already-posted items stay untouched)."""
import json, os, urllib.parse, urllib.request
d = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"], "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
tok = json.loads(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=d), timeout=30).read())["access_token"]
H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"}
for vid, title in json.loads(os.environ["PAIRS"]).items():
    it = json.loads(urllib.request.urlopen(urllib.request.Request(f"https://www.googleapis.com/youtube/v3/videos?part=snippet,status&id={vid}", headers=H), timeout=30).read())["items"]
    if not it: print("not found", vid); continue
    sn, st = it[0]["snippet"], it[0]["status"]["privacyStatus"]
    if st != "private": print("SKIP not private", vid, st); continue
    body = {"id": vid, "snippet": {"title": title[:100], "description": sn.get("description", ""), "categoryId": sn["categoryId"], **({"tags": sn["tags"]} if sn.get("tags") else {}), **({"defaultLanguage": sn["defaultLanguage"]} if sn.get("defaultLanguage") else {})}}
    try: urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?part=snippet", data=json.dumps(body).encode(), method="PUT", headers=H), timeout=60); print("retitled", vid, "->", title)
    except urllib.error.HTTPError as e: print("failed", vid, e.code, e.read()[:300])
