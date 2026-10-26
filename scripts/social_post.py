#!/usr/bin/env python3
"""Cross-post queued Reels to Instagram and Facebook with the never-expiring Page token.
Queue: content/social_queue.json  [{id, platform: instagram|facebook, file, at (UTC ISO), caption, comment?, done?: {...}}]
Videos come from a GitHub Actions artifact (downloaded by the workflow into ./media).
Env: FB_PAGE_TOKEN, FB_PAGE_ID, DRY_RUN=1 (upload + process but never publish), ONLY=<id> (force one item now).
Instagram: resumable upload (no public URL needed) -> container -> FINISHED -> media_publish.
Facebook: /video_reels start -> rupload -> finish (PUBLISHED), then the link as the first comment (Meta warns links in captions cut reach).
Every result is written back to the queue (post log)."""
import json, os, sys, time, datetime as dt, urllib.request, urllib.error, urllib.parse
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

def fb_reel(item, path):
    s = call("POST", f"{G}/{PAGE}/video_reels", data={"upload_phase": "start"})
    vid = s["video_id"]; url = s.get("upload_url") or f"https://rupload.facebook.com/video-upload/v26.0/{vid}"; n = os.path.getsize(path)
    up = call("POST", url, raw=open(path, "rb").read(), headers={"Authorization": f"OAuth {T}", "offset": "0", "file_size": str(n)}, timeout=900)
    print("fb upload", up)
    if DRY: return {"dry_run": True, "video_id": vid, "status": "uploaded (not published)"}
    f = call("POST", f"{G}/{PAGE}/video_reels", data={"upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED", "description": item["caption"]})
    st = {}
    for _ in range(60):
        st = get(vid, fields="status,permalink_url")
        s_ = st.get("status") or {}
        if s_.get("video_status") in ("ready", "published") or (s_.get("publishing_phase") or {}).get("status") == "complete": break
        if s_.get("video_status") == "error": raise RuntimeError(f"fb video {s_}")
        time.sleep(10)
    pl = st.get("permalink_url") or ""
    com = None
    if item.get("comment"):
        try: com = call("POST", f"{G}/{vid}/comments", data={"message": item["comment"]}); print("fb comment", com)
        except Exception as e: print("fb comment failed", e)
    return {"video_id": vid, "finish": f, "permalink": ("https://www.facebook.com" + pl) if pl.startswith("/") else pl, "status": st.get("status"), "comment": com}

q = json.load(open(Q)); now = dt.datetime.now(dt.timezone.utc); changed = False
for item in q:
    if item.get("done") and not item["done"].get("dry_run") and not ONLY: continue
    due = dt.datetime.fromisoformat(item["at"].replace("Z", "+00:00")) <= now
    if ONLY: due = item["id"] == ONLY and not (item.get("done") and not item["done"].get("dry_run"))
    if not due: continue
    path = os.path.join(MEDIA, item["file"]); print(f"== {item['id']} ({item['platform']}) {path} {os.path.getsize(path)} bytes", flush=True)
    try:
        res = (ig_reel if item["platform"] == "instagram" else fb_reel)(item, path)
        item["done"] = dict(res, at=now.strftime("%Y-%m-%dT%H:%M:%SZ")); print("OK", item["id"], res, flush=True)
    except Exception as e:
        item.setdefault("errors", []).append(f"{now:%Y-%m-%dT%H:%MZ} {str(e)[:300]}"); print("FAIL", item["id"], e, flush=True)
    changed = True
if changed: json.dump(q, open(Q, "w"), ensure_ascii=False, indent=1)
print("queue:", [(i["id"], "posted" if i.get("done") and not i["done"].get("dry_run") else "dry-ok" if i.get("done") else "pending") for i in q])
