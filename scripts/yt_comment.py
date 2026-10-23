#!/usr/bin/env python3
"""Post queued comments (content/pending/comment_*.json) once their 'after' time has passed; delete the queue file on success.
Env: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN."""
import glob, json, os, sys, datetime, urllib.parse, urllib.request
def token():
    d = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                                "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    with urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=d), timeout=30) as r:
        return json.loads(r.read())["access_token"]
now = datetime.datetime.now(datetime.timezone.utc); tok = None
for f in sorted(glob.glob("content/pending/comment_*.json")):
    q = json.load(open(f))
    if now < datetime.datetime.fromisoformat(q["after"].replace("Z", "+00:00")): print("not yet", f); continue
    tok = tok or token()
    body = {"snippet": {"videoId": q["video_id"], "topLevelComment": {"snippet": {"textOriginal": open(q["text_file"]).read()[:9900]}}}}
    req = urllib.request.Request("https://www.googleapis.com/youtube/v3/commentThreads?part=snippet", data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: print("comment posted", q["video_id"], r.status)
        os.remove(f)
    except urllib.error.HTTPError as e: print("comment failed", q["video_id"], e.code, e.read()[:300])
