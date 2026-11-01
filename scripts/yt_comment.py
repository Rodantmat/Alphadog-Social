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
    text = open(q["text_file"]).read()
    # long credits: first part as the top-level comment, the rest as replies under it (each chunk <= 8500 bytes, split on line breaks)
    chunks, cur = [], ""
    for ln in text.splitlines(keepends=True):
        if cur and len((cur + ln).encode()) > 8500: chunks.append(cur.rstrip()); cur = ""
        cur += ln
    if cur.strip(): chunks.append(cur.rstrip())
    def post(url, body):
        req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                     headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"})
        with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read())
    try:
        th = post("https://www.googleapis.com/youtube/v3/commentThreads?part=snippet",
                  {"snippet": {"videoId": q["video_id"], "topLevelComment": {"snippet": {"textOriginal": chunks[0]}}}})
        print("comment posted", q["video_id"], len(chunks[0]), "chars")
        for extra in chunks[1:]:
            post("https://www.googleapis.com/youtube/v3/comments?part=snippet", {"snippet": {"parentId": th["id"], "textOriginal": extra}})
            print("reply posted", q["video_id"], len(extra), "chars")
        os.remove(f)
    except urllib.error.HTTPError as e: print("comment failed", q["video_id"], e.code, e.read()[:600])
