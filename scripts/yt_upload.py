#!/usr/bin/env python3
"""Upload a video to YouTube with full metadata.
Usage: yt_upload.py META_JSON
META: {"file": "ep.mp4", "title": "...", "description_file": "desc.txt", "tags": [...], "category": "27",
       "privacy": "private|unlisted|public", "publish_at": "2026-10-24T16:00:00Z" (optional, requires private),
       "thumbnail": "thumb.jpg", "made_for_kids": false, "synthetic": true, "language": "en", "playlist_id": "",
       "captions": [{"file": "ep.en.srt", "language": "en", "name": "English"}, {"file": "ep.es.srt", "language": "es", "name": "Español"}],
       "localizations": {"es": {"title": "...", "description": "..."}},   # selectable subtitle tracks (rule D1), localized metadata
       "playlist_title": "...", "comment_file": "credits.txt", "location": {"desc": "...", "lat": 0, "lng": 0}, "recording_date": "2026-10-23" }
Env: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN. Prints VIDEO_ID=...
Env RESUME_VIDEO_ID: skip the upload + thumbnail and finish the remaining steps (playlist, captions, localizations, comment) on that video."""
import json, os, sys, time, urllib.error, urllib.parse, urllib.request

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
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        print("YT_HTTP_ERROR", e.code, e.read().decode(errors="replace")[:600]); raise

M = json.load(open(sys.argv[1])); tok = access_token()
desc = open(M["description_file"]).read() if M.get("description_file") else M.get("description", "")
status = {"privacyStatus": M.get("privacy", "private"), "selfDeclaredMadeForKids": bool(M.get("made_for_kids", False)),
          "containsSyntheticMedia": bool(M.get("synthetic", True)), "embeddable": True, "license": "youtube"}
if M.get("publish_at"): status["privacyStatus"] = "private"; status["publishAt"] = M["publish_at"]
meta = {"snippet": {"title": M["title"][:100], "description": desc[:4900], "tags": M.get("tags", [])[:30],
                    "categoryId": M.get("category", "27"), "defaultLanguage": M.get("language", "en"),
                    "defaultAudioLanguage": M.get("language", "en")}, "status": status}
vid = os.environ.get("RESUME_VIDEO_ID") or None
if vid: print("RESUME on", vid); print("VIDEO_ID=" + vid)
else:
    size = os.path.getsize(M["file"])
    st, hd, _ = api("POST", "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status&notifySubscribers=true",
                    tok, body=meta, headers={"X-Upload-Content-Length": str(size), "X-Upload-Content-Type": "video/mp4"})
    loc = hd.get("Location") or hd.get("location")
    CH = 64 * 1024 * 1024; sent = 0
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
        ctype = "image/png" if M["thumbnail"].lower().endswith(".png") else "image/jpeg"
        st, _, _ = api("POST", f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}", tok,
                       raw=open(M["thumbnail"], "rb").read(), headers={"Content-Type": ctype})
        print("thumbnail", st)
if vid and M.get("playlist_title") and not M.get("playlist_id"):     # find or create the series playlist
    _, _, out = api("GET", "https://www.googleapis.com/youtube/v3/playlists?part=snippet&mine=true&maxResults=50", tok)
    hit = [p for p in json.loads(out).get("items", []) if p["snippet"]["title"] == M["playlist_title"]]
    if hit: M["playlist_id"] = hit[0]["id"]
    else:
        _, _, out = api("POST", "https://www.googleapis.com/youtube/v3/playlists?part=snippet,status", tok,
                        body={"snippet": {"title": M["playlist_title"], "description": M.get("playlist_description", ""), "defaultLanguage": "en"},
                              "status": {"privacyStatus": "public"}})
        M["playlist_id"] = json.loads(out)["id"]
    print("playlist", M["playlist_id"])
if vid and M.get("playlist_id"):          # 409 here is a known transient YouTube error: retry, never fatal
    try:
        _, _, out = api("GET", f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId={M['playlist_id']}", tok)
        already = any(i["snippet"]["resourceId"].get("videoId") == vid for i in json.loads(out).get("items", []))
    except Exception as e: already = False; print("playlist list failed", str(e)[:200])
    for attempt in range(6):
        if already: print("playlist item present"); break
        try:
            st, _, _ = api("POST", "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet", tok,
                           body={"snippet": {"playlistId": M["playlist_id"], "resourceId": {"kind": "youtube#video", "videoId": vid}}})
            print("playlist item", st); break
        except urllib.error.HTTPError as e:
            print("playlist item retry", attempt, e.code, e.read()[:300], flush=True); time.sleep(15 * (attempt + 1)); tok = access_token()
for c in (M.get("captions") or []) if vid else []:            # selectable subtitle tracks, not burned in
    if not os.path.exists(c["file"]): print("caption missing", c["file"]); continue
    b = "capboundary7f3a"; meta_c = json.dumps({"snippet": {"videoId": vid, "language": c["language"], "name": c.get("name", c["language"]), "isDraft": False}})
    body = (f"--{b}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{meta_c}\r\n--{b}\r\nContent-Type: application/octet-stream\r\n\r\n").encode() \
           + open(c["file"], "rb").read() + f"\r\n--{b}--".encode()
    for attempt in range(3):
        try:
            st, _, out = api("POST", "https://www.googleapis.com/upload/youtube/v3/captions?part=snippet&uploadType=multipart", tok,
                             raw=body, headers={"Content-Type": f"multipart/related; boundary={b}"})
            print("caption", c["language"], st); break
        except Exception as e:
            print("caption retry", c["language"], str(e)[:300]); time.sleep(5); tok = access_token()
if vid and M.get("localizations"):
    st, _, _ = api("PUT", "https://www.googleapis.com/youtube/v3/videos?part=localizations,snippet", tok,
                   body={"id": vid, "snippet": meta["snippet"], "localizations": M["localizations"]})
    print("localizations", st)
if vid and M.get("comment_file") and os.path.exists(M["comment_file"]):      # credits as the first comment (pin it in Studio)
    try:
        st, _, _ = api("POST", "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet", tok,
                       body={"snippet": {"videoId": vid, "topLevelComment": {"snippet": {"textOriginal": open(M["comment_file"]).read()[:9900]}}}})
        print("comment", st)
    except Exception as e: print("comment failed", str(e)[:300])
if vid and (M.get("location") or M.get("recording_date")):
    rd = {}
    if M.get("recording_date"): rd["recordingDate"] = M["recording_date"] + "T00:00:00Z"
    if M.get("location"): rd["locationDescription"] = M["location"]["desc"]; rd["location"] = {"latitude": M["location"]["lat"], "longitude": M["location"]["lng"]}
    try:
        st, _, _ = api("PUT", "https://www.googleapis.com/youtube/v3/videos?part=recordingDetails", tok, body={"id": vid, "recordingDetails": rd}); print("recordingDetails", st)
    except Exception as e: print("recordingDetails failed", str(e)[:300])
if vid and M.get("queue_comment"):      # posted by yt-followup once the scheduled video is public
    qc = M["queue_comment"]; ws = os.environ.get("GITHUB_WORKSPACE", ".")
    os.makedirs(f"{ws}/content/pending", exist_ok=True)
    open(f"{ws}/content/pending/ctext_{vid}.txt", "w", encoding="utf-8").write(qc["text"])
    json.dump({"video_id": vid, "after": qc["after"], "text_file": f"content/pending/ctext_{vid}.txt"}, open(f"{ws}/content/pending/comment_{vid}.json", "w"))
    print("comment queued", vid, qc["after"])
print("DONE", vid)
