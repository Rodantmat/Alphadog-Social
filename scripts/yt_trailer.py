#!/usr/bin/env python3
"""Set the channel trailer for non-subscribers (Shorts viewers who land on the channel page) via the Data API; list playlists. env YT_*, TRAILER=<video id>."""
import json, os, urllib.parse, urllib.request
d=urllib.parse.urlencode({"client_id":os.environ["YT_CLIENT_ID"],"client_secret":os.environ["YT_CLIENT_SECRET"],"refresh_token":os.environ["YT_REFRESH_TOKEN"],"grant_type":"refresh_token"}).encode()
tok=json.loads(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token",data=d)).read())["access_token"]; H={"Authorization":"Bearer "+tok}
def call(u,body=None,method=None):
    r=urllib.request.Request(u,data=json.dumps(body).encode() if body else None,headers={**H,"Content-Type":"application/json"},method=method)
    return json.loads(urllib.request.urlopen(r).read())
ch=call("https://www.googleapis.com/youtube/v3/channels?part=brandingSettings,id&mine=true")["items"][0]
bs=ch["brandingSettings"]; print("BEFORE", json.dumps(bs.get("channel",{}))[:500])
bs.setdefault("channel",{})["unsubscribedTrailer"]=os.environ["TRAILER"]
r=call("https://www.googleapis.com/youtube/v3/channels?part=brandingSettings",{"id":ch["id"],"brandingSettings":bs},"PUT")
print("AFTER", json.dumps(r["brandingSettings"].get("channel",{}))[:500])
for p in call("https://www.googleapis.com/youtube/v3/playlists?part=snippet,contentDetails&mine=true&maxResults=50")["items"]:
    print("PLAYLIST", p["id"], p["contentDetails"]["itemCount"], p["snippet"]["title"])
