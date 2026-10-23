#!/usr/bin/env python3
"""Fail fast: confirm the stored YouTube credentials work and name the channel they upload to (no secrets printed)."""
import json, os, urllib.parse, urllib.request
d = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                            "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
with urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=d), timeout=30) as r:
    t = json.loads(r.read()); tok = t["access_token"]; print("scopes:", t.get("scope"))
req = urllib.request.Request("https://www.googleapis.com/youtube/v3/channels?part=snippet,status,statistics&mine=true", headers={"Authorization": f"Bearer {tok}"})
with urllib.request.urlopen(req, timeout=30) as r:
    for c in json.loads(r.read()).get("items", []):
        print("CHANNEL", c["id"], c["snippet"]["title"], "| longUploads:", c["status"].get("longUploadsStatus"), "| videos:", c["statistics"].get("videoCount"))
# --test-upload: API projects that Google has not audited get every upload locked to private. Upload a 3 s unlisted clip,
# read back its privacy, then delete it, so we know before spending hours rendering.
import sys, subprocess
if "--test-upload" in sys.argv:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=320x240:d=3", "-pix_fmt", "yuv420p", "/tmp/t.mp4"], check=True)
    meta = {"snippet": {"title": "upload check (auto-deleted)", "categoryId": "27"}, "status": {"privacyStatus": "unlisted", "selfDeclaredMadeForKids": False}}
    sz = os.path.getsize("/tmp/t.mp4")
    r = urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status&notifySubscribers=false",
        data=json.dumps(meta).encode(), method="POST", headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json", "X-Upload-Content-Length": str(sz), "X-Upload-Content-Type": "video/mp4"}), timeout=60)
    loc = r.headers["Location"]
    with urllib.request.urlopen(urllib.request.Request(loc, data=open("/tmp/t.mp4", "rb").read(), method="PUT", headers={"Authorization": f"Bearer {tok}", "Content-Type": "video/mp4"}), timeout=120) as r2:
        v = json.loads(r2.read())
    print("TEST_UPLOAD requested=unlisted got=", v["status"].get("privacyStatus"), "| upload:", v["status"].get("uploadStatus"))
    import time; time.sleep(120)
    with urllib.request.urlopen(urllib.request.Request(f"https://www.googleapis.com/youtube/v3/videos?part=status&id={v['id']}", headers={"Authorization": f"Bearer {tok}"}), timeout=30) as r3:
        print("TEST_UPLOAD after processing:", json.dumps(json.loads(r3.read()).get("items", [{}])[0].get("status")))
    try:
        urllib.request.urlopen(urllib.request.Request(f"https://www.googleapis.com/youtube/v3/videos?id={v['id']}", method="DELETE", headers={"Authorization": f"Bearer {tok}"}), timeout=30)
        print("test video deleted")
    except Exception as e: print("delete failed (scope?)", str(e)[:200], "id", v["id"])
