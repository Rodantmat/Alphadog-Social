#!/usr/bin/env python3
"""Cross-post queued Reels to Instagram and Facebook with the never-expiring Page token, and TikTok drafts.
Queue: content/social_queue.json  [{id, platform: instagram|facebook|tiktok_draft, file, at (UTC ISO), caption, comment?, done?: {...}}]
Videos come from a GitHub Actions artifact (downloaded by the workflow into ./media).
Env: FB_PAGE_TOKEN, FB_PAGE_ID, STUDIO_TIKTOK_* (tiktok), DRY_RUN=1 (upload + process but never publish), ONLY=<id> (force one item now).
Instagram: resumable upload (no public URL needed) -> container -> FINISHED -> media_publish.
Facebook: /video_reels start -> rupload -> finish (PUBLISHED), then the link as the first comment (Meta warns links in captions cut reach).
TikTok (until the app passes TikTok's audit): the clip goes to the creator's TikTok inbox as a draft to finish in the app.
Every result is written back to the queue (post log)."""
import json, os, sys, time, subprocess, datetime as dt, urllib.request, urllib.error, urllib.parse
G = "https://graph.facebook.com/v26.0"; T = os.environ["FB_PAGE_TOKEN"].strip(); PAGE = os.environ["FB_PAGE_ID"].strip()
DRY = os.environ.get("DRY_RUN") == "1"; ONLY = os.environ.get("ONLY", "").strip()
Q = "content/social_queue.json"; MEDIA = "media"

def call(method, url, data=None, headers=None, raw=None, timeout=300):
    h = dict(headers or {}); body = raw
    if data is not None:
        data = dict(data); data.setdefault("access_token", T); body = urllib.parse.urlencode(data).encode()
        h["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} {url.split('?')[0]}: {e.read().decode()[:500].replace(T, '***')}")
def get(path, **q): q["access_token"] = T; return call("GET", f"{G}/{path}?" + urllib.parse.urlencode(q))

def ig_reel(item, path):
    ig = get(PAGE, fields="instagram_business_account")["instagram_business_account"]["id"]
    c = call("POST", f"{G}/{ig}/media", data={"media_type": "REELS", "upload_type": "resumable", "caption": item["caption"],
                                             "share_to_feed": "true", "thumb_offset": str(item.get("thumb_ms", 1200))})
    cid, uri = c["id"], c["uri"]; n = os.path.getsize(path)
    up = call("POST", uri, raw=open(path, "rb").read(), headers={"Authorization": f"OAuth {T}", "offset": "0", "file_size": str(n)}, timeout=900)
    print("ig upload", up)
    for _ in range(80):
        st = get(cid, fields="status_code,status")
        if st.get("status_code") == "FINISHED": break
        if st.get("status_code") in ("ERROR", "EXPIRED"): raise RuntimeError(f"ig container {st}")
        time.sleep(10)
    else: raise RuntimeError("ig container not ready after ~13 min")
    if DRY: return {"dry_run": True, "container": cid, "status": "FINISHED (not published)"}
    m = call("POST", f"{G}/{ig}/media_publish", data={"creation_id": cid})
    info = get(m["id"], fields="permalink,timestamp")
    if item.get("comment"):
        try: print("ig comment", call("POST", f"{G}/{m['id']}/comments", data={"message": item["comment"]}))
        except Exception as e: print("ig comment failed", e)
    return {"media_id": m["id"], "permalink": info.get("permalink"), "posted": info.get("timestamp")}

def ig_reel_url(item, path):
    """Fallback when the resumable upload keeps failing: host the file on the public media-public release and let Instagram fetch it."""
    ig = get(PAGE, fields="instagram_business_account")["instagram_business_account"]["id"]
    name = os.path.basename(path); repo = os.environ.get("GITHUB_REPOSITORY", "Rodantmat/Alphadog-Social")
    subprocess.run(["gh", "release", "view", "media-public"], capture_output=True) .returncode or None
    up = subprocess.run(["gh", "release", "upload", "media-public", path, "--clobber"], capture_output=True, text=True); print("release upload", up.returncode, up.stderr[-200:])
    url = f"https://github.com/{repo}/releases/download/media-public/{name}"
    c = call("POST", f"{G}/{ig}/media", data={"media_type": "REELS", "video_url": url, "caption": item["caption"], "share_to_feed": "true", "thumb_offset": str(item.get("thumb_ms", 1200))})
    cid = c["id"]
    for _ in range(80):
        st = get(cid, fields="status_code,status")
        if st.get("status_code") == "FINISHED": break
        if st.get("status_code") in ("ERROR", "EXPIRED"): raise RuntimeError(f"ig url container {st}")
        time.sleep(10)
    else: raise RuntimeError("ig url container not ready")
    if DRY: return {"dry_run": True, "container": cid, "status": "FINISHED (not published)"}
    m = call("POST", f"{G}/{ig}/media_publish", data={"creation_id": cid}); info = get(m["id"], fields="permalink,timestamp")
    if item.get("comment"):
        try: print("ig comment", call("POST", f"{G}/{m['id']}/comments", data={"message": item["comment"]}))
        except Exception as e: print("ig comment failed", e)
    return {"media_id": m["id"], "permalink": info.get("permalink"), "posted": info.get("timestamp"), "via": "video_url"}

def fb_reel(item, path):
    s = call("POST", f"{G}/{PAGE}/video_reels", data={"upload_phase": "start"})
    vid = s["video_id"]; url = s.get("upload_url") or f"https://rupload.facebook.com/video-upload/v26.0/{vid}"; n = os.path.getsize(path)
    up = call("POST", url, raw=open(path, "rb").read(), headers={"Authorization": f"OAuth {T}", "offset": "0", "file_size": str(n)}, timeout=900)
    print("fb upload", up)
    if DRY: return {"dry_run": True, "video_id": vid, "status": "uploaded (not published)"}
    f = call("POST", f"{G}/{PAGE}/video_reels", data={"upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED", "description": item["caption"]})
    # From here on the reel is published: never raise (a raise would leave the item pending and re-post it next run).
    st = {}; errs = []
    for _ in range(60):
        try: st = get(vid, fields="status,permalink_url")
        except Exception as e: errs.append(str(e)[:200]); time.sleep(10); continue
        s_ = st.get("status") or {}
        if s_.get("video_status") in ("ready", "published") or (s_.get("publishing_phase") or {}).get("status") == "complete": break
        if s_.get("video_status") == "error": errs.append(f"fb video {s_}"); break
        time.sleep(10)
    pl = st.get("permalink_url") or f"/reel/{vid}/"
    com = None
    if item.get("comment"):
        try: com = call("POST", f"{G}/{vid}/comments", data={"message": item["comment"]}); print("fb comment", com)
        except Exception as e: print("fb comment failed", e)
    return {"video_id": vid, "finish": f, "permalink": ("https://www.facebook.com" + pl) if pl.startswith("/") else pl, "status": st.get("status"),
            "comment": com, "status_errors": errs[-3:] or None}

def ig_story(item, path):
    ig = get(PAGE, fields="instagram_business_account")["instagram_business_account"]["id"]
    c = call("POST", f"{G}/{ig}/media", data={"media_type": "STORIES", "upload_type": "resumable"})
    cid, uri = c["id"], c["uri"]; n = os.path.getsize(path)
    up = call("POST", uri, raw=open(path, "rb").read(), headers={"Authorization": f"OAuth {T}", "offset": "0", "file_size": str(n)}, timeout=900)
    print("ig story upload", up)
    for _ in range(80):
        st = get(cid, fields="status_code,status")
        if st.get("status_code") == "FINISHED": break
        if st.get("status_code") in ("ERROR", "EXPIRED"): raise RuntimeError(f"ig story container {st}")
        time.sleep(10)
    else: raise RuntimeError("ig story container not ready after ~13 min")
    if DRY: return {"dry_run": True, "container": cid, "status": "FINISHED (not published)"}
    m = call("POST", f"{G}/{ig}/media_publish", data={"creation_id": cid})
    return {"media_id": m["id"], "story": True}

def fb_story(item, path):
    s = call("POST", f"{G}/{PAGE}/video_stories", data={"upload_phase": "start"})
    vid = s["video_id"]; url = s.get("upload_url") or f"https://rupload.facebook.com/video-upload/v26.0/{vid}"; n = os.path.getsize(path)
    up = call("POST", url, raw=open(path, "rb").read(), headers={"Authorization": f"OAuth {T}", "offset": "0", "file_size": str(n)}, timeout=900)
    print("fb story upload", up)
    if DRY: return {"dry_run": True, "video_id": vid, "status": "uploaded (not published)"}
    f = call("POST", f"{G}/{PAGE}/video_stories", data={"upload_phase": "finish", "video_id": vid})
    return {"video_id": vid, "finish": f, "story": True}

def tt_draft(item, path):
    if DRY: return {"dry_run": True, "status": "not sent"}
    r = subprocess.run(["python3", "scripts/tiktok_studio.py", "draft", path], capture_output=True, text=True)
    print(r.stdout[-1500:], r.stderr[-500:])
    if r.returncode != 0 or "SEND_TO_USER_INBOX" not in r.stdout: raise RuntimeError("tiktok draft failed: " + (r.stdout + r.stderr)[-300:])
    return {"status": "SEND_TO_USER_INBOX"}

q = json.load(open(Q)); now = dt.datetime.now(dt.timezone.utc); changed = False
for item in q:
    if item.get("done") and not item["done"].get("dry_run") and not ONLY: continue
    due = dt.datetime.fromisoformat(item["at"].replace("Z", "+00:00")) <= now
    if ONLY: due = item["id"] == ONLY and not (item.get("done") and not item["done"].get("dry_run"))
    if not due: continue
    if "{LINK}" in json.dumps(item): print(f"== {item['id']} SKIPPED: link placeholder not filled yet", flush=True); continue
    path = os.path.join(MEDIA, item["file"]); print(f"== {item['id']} ({item['platform']}) {path} {os.path.getsize(path)} bytes", flush=True)
    try:
        fn = {"instagram": ig_reel, "facebook": fb_reel, "instagram_story": ig_story, "facebook_story": fb_story, "tiktok_draft": tt_draft}[item["platform"]]
        # Instagram's upload endpoint fails intermittently with 'ProcessingFailedError' (2026-10-30: same file failed 4x, then posted untouched).
        # The failure always happens BEFORE media_publish, so retrying with a fresh container is safe.
        for attempt in range(1, 5 if item["platform"].startswith("instagram") else 2):
            try: res = fn(item, path); break
            except Exception as e:
                if "ProcessingFailedError" not in str(e): raise
                print(f"{item['id']}: ProcessingFailedError (attempt {attempt})", flush=True)
                if attempt >= 2 and item["platform"] == "instagram":
                    print("falling back to Instagram video_url (public release) upload", flush=True); res = ig_reel_url(item, path); break
                if attempt >= 4: raise
                time.sleep(45 * attempt)
        item["done"] = dict(res, at=now.strftime("%Y-%m-%dT%H:%M:%SZ")); print("OK", item["id"], res, flush=True)
    except Exception as e:
        item.setdefault("errors", []).append(f"{now:%Y-%m-%dT%H:%MZ} {str(e)[:300]}"); print("FAIL", item["id"], e, flush=True)
    changed = True
if changed: json.dump(q, open(Q, "w"), ensure_ascii=False, indent=1)
print("queue:", [(i["id"], "posted" if i.get("done") and not i["done"].get("dry_run") else "dry-ok" if i.get("done") else "pending") for i in q])
