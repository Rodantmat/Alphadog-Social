#!/usr/bin/env python3
"""Set a video's thumbnail. env: YT_CLIENT_ID/SECRET/REFRESH_TOKEN, VID, P (jpg path)."""
import os, json, urllib.parse, urllib.request
d = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"], "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
tok = json.loads(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=d), timeout=30).read())["access_token"]
r = urllib.request.urlopen(urllib.request.Request(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={os.environ['VID']}", data=open(os.environ["P"], "rb").read(), headers={"Authorization": f"Bearer {tok}", "Content-Type": "image/jpeg"}, method="POST"), timeout=120)
print("thumbnail", r.status)
