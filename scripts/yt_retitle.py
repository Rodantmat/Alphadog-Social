#!/usr/bin/env python3
"""Prefix the title of videos (used to tell superseded private uploads apart from the live ones in Studio pickers).
env: IDS (comma list), PREFIX; YT_CLIENT_ID/SECRET/REFRESH_TOKEN. Costs ~50 quota units per video."""
import json, os, urllib.parse, urllib.request
def token():
    d = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                                "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    with urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=d), timeout=30) as r:
        return json.loads(r.read())["access_token"]
tok = token(); H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"}
PREFIX = os.environ.get("PREFIX", "[OLD private] ")
for vid in [x.strip() for x in os.environ["IDS"].split(",") if x.strip()]:
    r = urllib.request.urlopen(urllib.request.Request(f"https://www.googleapis.com/youtube/v3/videos?part=snippet,status&id={vid}", headers=H), timeout=30)
    items = json.loads(r.read())["items"]
    if not items: print("not found", vid); continue
    sn = items[0]["snippet"]; st = items[0]["status"]["privacyStatus"]
    if sn["title"].startswith(PREFIX): print("already", vid); continue
    if st != "private": print("SKIP: not private", vid, st); continue
    sn["title"] = PREFIX + sn["title"]
    body = {"id": vid, "snippet": {"title": sn["title"][:100], "description": sn.get("description", ""), "categoryId": sn["categoryId"],
                                   **({"tags": sn["tags"]} if sn.get("tags") else {}), **({"defaultLanguage": sn["defaultLanguage"]} if sn.get("defaultLanguage") else {})}}
    try:
        urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?part=snippet", data=json.dumps(body).encode(), method="PUT", headers=H), timeout=60)
        print("retitled", vid, "->", body["snippet"]["title"])
    except urllib.error.HTTPError as e: print("failed", vid, e.code, e.read()[:300])
