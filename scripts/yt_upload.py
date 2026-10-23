#!/usr/bin/env python3
"""Upload a video to YouTube with full metadata.
Usage: yt_upload.py META_JSON
META: {"file": "ep.mp4", "title": "...", "description_file": "desc.txt", "tags": [...], "category": "27",
       "privacy": "private|unlisted|public", "publish_at": "2026-10-24T16:00:00Z" (optional, requires private),
       "thumbnail": "thumb.jpg", "made_for_kids": false, "synthetic": true, "language": "en", "playlist_id": "" }
Env: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN. Prints VIDEO_ID=..."""
import json, os, sys, time, urllib.parse, urllib.request

def access_token():
    d = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                                "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    with urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=d), timeout=30) as r:
        return json.loads(r.read())["access_token"]

def api(method, url, tok, body=None, headers=None, raw=None):
    h = {"Authorization": f"Bearer {tok}"}; h.update(headers or {})
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    if body is not None and raw is None: h["Content-Type"] = "application/json; charset=UTF-8"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=600) as r:
        return r.status, dict(r.headers), r.read()

M = json.load(open(sys.argv[1])); tok = access_token()
desc = open(M["description_file"]).read() if M.get("description_file") else M.get("description", "")
status = {"privacyStatus": M.get("privacy", "private"), "selfDeclaredMadeForKids": bool(M.get("made_for_kids", False)),
          "containsSyntheticMedia": bool(M.get("synthetic", True)), "embeddable": True, "license": "youtube"}
if M.get("publish_at"): status["privacyStatus"] = "private"; status["publishAt"] = M["publish_at"]
meta = {"snippet": {"title": M["title"][:100], "description": desc[:4900], "tags": M.get("tags", [])[:30],
                    "categoryId": M.get("category", "27"), "defaultLanguage": M.get("language", "en"),
                    "defaultAudioLanguage": M.get("language", "en")}, "status": status}
size = os.path.getsize(M["file"])
st, hd, _ = api("POST", "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status&notifySubscribers=true",
                tok, body=meta, headers={"X-Upload-Content-Length": str(size), "X-Upload-Content-Type": "video/mp4"})
loc = hd.get("Location") or hd.get("location")
CH = 64 * 1024 * 1024; sent = 0; vid = None
with open(M["file"], "rb") as f:
    while sent < size:
        chunk = f.read(CH); end = sent + len(chunk) - 1
        for attempt in range(5):
            try:
                req = urllib.request.Request(loc, data=chunk, method="PUT", headers={"Authorization": f"Bearer {tok}",
                      "Content-Length": str(len(chunk)), "Content-Range": f"bytes {sent}-{end}/{size}"})
                try:
                    with urllib.request.urlopen(req, timeout=900) as r:
                        vid = json.loads(r.read())["id"]
                except urllib.error.HTTPError as e:
                    if e.code != 308: raise
                break
            except Exception as e:
                print("retry", attempt, str(e)[:200], flush=True); time.sleep(5 * (attempt + 1)); tok = access_token()
        sent = end + 1; print(f"uploaded {sent/size:.0%}", flush=True)
print("VIDEO_ID=" + str(vid))
if vid and M.get("thumbnail") and os.path.exists(M["thumbnail"]):
    st, _, _ = api("POST", f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}", tok,
                   raw=open(M["thumbnail"], "rb").read(), headers={"Content-Type": "image/jpeg"})
    print("thumbnail", st)
if vid and M.get("playlist_id"):
    api("POST", "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet", tok,
        body={"snippet": {"playlistId": M["playlist_id"], "resourceId": {"kind": "youtube#video", "videoId": vid}}})
