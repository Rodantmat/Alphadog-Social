#!/usr/bin/env python3
"""Fail fast: confirm the stored YouTube credentials work and name the channel they upload to (no secrets printed).
--test-upload: API projects Google has not audited get uploads locked to private. Upload a 3 s unlisted clip, read back its
status, then delete it (and any leftover test clips), so we know before spending hours rendering."""
import json, os, sys, subprocess, time, urllib.parse, urllib.request
d = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                            "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
with urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=d), timeout=30) as r:
    t = json.loads(r.read()); tok = t["access_token"]; print("scopes:", t.get("scope"))
H = {"Authorization": f"Bearer {tok}"}
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=30) as r: return json.loads(r.read())
ch = get("https://www.googleapis.com/youtube/v3/channels?part=snippet,status,statistics,contentDetails&mine=true")["items"][0]
print("CHANNEL", ch["id"], ch["snippet"]["title"], "| custom:", ch["snippet"].get("customUrl"), "| longUploads:", ch["status"].get("longUploadsStatus"),
      "| videos:", ch["statistics"].get("videoCount"), "| subs:", ch["statistics"].get("subscriberCount"))
uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
def delete(vid):
    try:
        urllib.request.urlopen(urllib.request.Request(f"https://www.googleapis.com/youtube/v3/videos?id={vid}", method="DELETE", headers=H), timeout=30); print("deleted", vid)
    except Exception as e: print("delete failed", vid, str(e)[:200])
def uploads_list():
    try: return get(f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,status&maxResults=50&playlistId={uploads}").get("items", [])
    except Exception as e: print("uploads list failed", str(e)[:200]); return []
for it in uploads_list():
    print("UPLOAD", it["snippet"]["resourceId"]["videoId"], "|", it["snippet"]["title"], "|", it.get("status", {}).get("privacyStatus"))
if "--test-upload" in sys.argv:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=320x240:d=3", "-pix_fmt", "yuv420p", "/tmp/t.mp4"], check=True)
    meta = {"snippet": {"title": "upload check (auto-deleted)", "categoryId": "27"}, "status": {"privacyStatus": "unlisted", "selfDeclaredMadeForKids": False}}
    sz = os.path.getsize("/tmp/t.mp4")
    r = urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status&notifySubscribers=false",
        data=json.dumps(meta).encode(), method="POST", headers={**H, "Content-Type": "application/json", "X-Upload-Content-Length": str(sz), "X-Upload-Content-Type": "video/mp4"}), timeout=60)
    with urllib.request.urlopen(urllib.request.Request(r.headers["Location"], data=open("/tmp/t.mp4", "rb").read(), method="PUT", headers={**H, "Content-Type": "video/mp4"}), timeout=120) as r2:
        v = json.loads(r2.read())
    print("TEST_UPLOAD id", v["id"], "requested=unlisted got=", v["status"].get("privacyStatus"), "| upload:", v["status"].get("uploadStatus"))
    for k in range(8):
        time.sleep(30)
        items = get(f"https://www.googleapis.com/youtube/v3/videos?part=status,processingDetails&id={v['id']}").get("items", [])
        print("TEST_UPLOAD after", (k + 1) * 30, "s:", json.dumps(items[0]["status"]) if items else "not listed", "|", json.dumps(items[0].get("processingDetails", {}).get("processingStatus")) if items else "")
        if items and items[0]["status"].get("uploadStatus") in ("processed", "rejected", "failed"): break
    for it in uploads_list():
        if it["snippet"]["title"].startswith("upload check"): delete(it["snippet"]["resourceId"]["videoId"])
    delete(v["id"])
