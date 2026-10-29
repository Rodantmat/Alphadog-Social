#!/usr/bin/env python3
"""AlphaDog Studio <-> TikTok (Login Kit + Content Posting API).
Actions (argv[1]):
  connect_page  write docs/studio/connect.html (Connect-with-TikTok button; the client key is public by design in OAuth URLs)
  exchange      trade STUDIO_TIKTOK_AUTH_CODE for tokens; store them encrypted (AES-256, key = client secret) in content/tiktok_studio_token.enc
  videos        list the account's latest public videos (video.list; read only)
  info          refresh the token, print the connected profile + creator info (read only)
  post FILE     direct-post FILE (env PRIVACY, default SELF_ONLY; CAPTION) and poll until published (needs audit, or a private account)
  draft FILE    send FILE to the creator's TikTok inbox/drafts (video.upload) to finish and post in the app
Env: STUDIO_TIKTOK_CLIENT_KEY, STUDIO_TIKTOK_CLIENT_SECRET, STUDIO_TIKTOK_AUTH_CODE (exchange only). Never prints tokens."""
import json, os, sys, time, subprocess, urllib.request, urllib.error, urllib.parse, datetime as dt
KEY = os.environ["STUDIO_TIKTOK_CLIENT_KEY"].strip(); SECRET = os.environ["STUDIO_TIKTOK_CLIENT_SECRET"].strip()
REDIRECT = "https://rodantmat.github.io/Alphadog-Social/studio/callback.html"
SCOPES = "user.info.basic,user.info.profile,user.info.stats,video.list,video.publish,video.upload"
API = "https://open.tiktokapis.com/v2"; STORE = "content/tiktok_studio_token.enc"
HIDE = [SECRET]

def scrub(s):
    for h in HIDE:
        if h: s = s.replace(h, "***")
    return s
def http(method, url, form=None, js=None, token=None, raw=None, headers=None, timeout=300):
    h = dict(headers or {}); body = raw
    if form is not None: body = urllib.parse.urlencode(form).encode(); h["Content-Type"] = "application/x-www-form-urlencoded"
    if js is not None: body = json.dumps(js).encode(); h["Content-Type"] = "application/json; charset=UTF-8"
    if token: h["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: b = r.read(); return r.status, (json.loads(b) if b else {})
    except urllib.error.HTTPError as e: return e.code, scrub(e.read().decode()[:600])
def save(tok):
    HIDE.extend([tok.get("access_token", ""), tok.get("refresh_token", "")])
    p = subprocess.run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-salt", "-a", "-A", "-pass", "env:STUDIO_TIKTOK_CLIENT_SECRET"],
                       input=json.dumps(tok).encode(), capture_output=True, check=True)
    os.makedirs("content", exist_ok=True); open(STORE, "w").write(p.stdout.decode() + "\n")
def load():
    p = subprocess.run(["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-a", "-A", "-pass", "env:STUDIO_TIKTOK_CLIENT_SECRET"],
                       input=open(STORE).read().strip().encode(), capture_output=True, check=True)
    t = json.loads(p.stdout); HIDE.extend([t.get("access_token", ""), t.get("refresh_token", "")]); return t
def fresh():
    t = load()
    if time.time() < t.get("access_expires_at", 0) - 600: return t
    st, r = http("POST", f"{API}/oauth/token/", form={"client_key": KEY, "client_secret": SECRET, "grant_type": "refresh_token", "refresh_token": t["refresh_token"]})
    if st != 200 or "access_token" not in r: sys.exit(f"refresh failed: HTTP {st} {scrub(str(r))[:300]}")
    t.update(r); now = time.time(); t["access_expires_at"] = now + r.get("expires_in", 86400); t["refresh_expires_at"] = now + r.get("refresh_expires_in", 31536000)
    save(t); print("token refreshed; refresh token valid until", dt.datetime.fromtimestamp(t["refresh_expires_at"], dt.timezone.utc).date()); return t

act = sys.argv[1]
if act == "connect_page":
    url = "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode({"client_key": KEY, "scope": SCOPES, "response_type": "code", "redirect_uri": REDIRECT, "state": "alphadog-studio"})
    html = open("docs/studio/connect.template.html").read().replace("{{AUTH_URL}}", url)
    open("docs/studio/connect.html", "w").write(html); print("connect page written")
elif act == "exchange":
    code = os.environ["STUDIO_TIKTOK_AUTH_CODE"].strip()
    code = urllib.parse.unquote(code.split("code=")[-1].split("&")[0]) if "code=" in code else code
    st, r = http("POST", f"{API}/oauth/token/", form={"client_key": KEY, "client_secret": SECRET, "code": code, "grant_type": "authorization_code", "redirect_uri": REDIRECT})
    if st != 200 or "access_token" not in r: sys.exit(f"exchange failed: HTTP {st} {scrub(str(r))[:400]}")
    now = time.time(); r["access_expires_at"] = now + r.get("expires_in", 86400); r["refresh_expires_at"] = now + r.get("refresh_expires_in", 31536000)
    save(r); print("connected; scopes:", r.get("scope"), "| refresh valid until", dt.datetime.fromtimestamp(r["refresh_expires_at"], dt.timezone.utc).date())
elif act == "info":
    t = fresh(); tok = t["access_token"]
    st, r = http("GET", f"{API}/user/info/?fields=open_id,avatar_url,display_name,username,bio_description,is_verified,follower_count,following_count,likes_count,video_count", token=tok)
    print("== user info: HTTP", st); print(json.dumps(r.get("data", r) if isinstance(r, dict) else r, indent=1)[:1200])
    st, r = http("POST", f"{API}/post/publish/creator_info/query/", js={}, token=tok)
    print("== creator info: HTTP", st); print(json.dumps(r.get("data", r) if isinstance(r, dict) else r, indent=1)[:1200])
elif act == "videos":
    t = fresh(); tok = t["access_token"]
    st, r = http("POST", f"{API}/video/list/?fields=id,title,create_time,share_url,duration", js={"max_count": 20}, token=tok)
    print("== video list: HTTP", st)
    for v in ((r.get("data") or {}).get("videos") or []) if isinstance(r, dict) else []:
        print(dt.datetime.utcfromtimestamp(v.get("create_time", 0)).isoformat() + "Z", v.get("share_url"), (v.get("title") or "")[:90].replace("\n", " "))
    if isinstance(r, dict) and r.get("error", {}).get("code") not in (None, "ok"): print(r["error"])
elif act in ("post", "draft"):
    t = fresh(); tok = t["access_token"]; f = sys.argv[2]; n = os.path.getsize(f)
    st, ci = http("POST", f"{API}/post/publish/creator_info/query/", js={}, token=tok); print("creator info", st, json.dumps(ci.get("data", {}) if isinstance(ci, dict) else ci)[:600])
    priv = os.environ.get("PRIVACY", "SELF_ONLY")
    body = {"post_info": {"title": os.environ.get("CAPTION", "")[:2200], "privacy_level": priv, "disable_duet": False, "disable_comment": False,
                          "disable_stitch": False, "video_cover_timestamp_ms": 1200},
            "source_info": {"source": "FILE_UPLOAD", "video_size": n, "chunk_size": n, "total_chunk_count": 1}}
    if act == "draft": body = {"source_info": body["source_info"]}
    ep = "video/init" if act == "post" else "inbox/video/init"
    st, r = http("POST", f"{API}/post/publish/{ep}/", js=body, token=tok); print("init", st, scrub(json.dumps(r) if isinstance(r, dict) else r)[:500])
    if not (isinstance(r, dict) and r.get("data", {}).get("upload_url")): sys.exit(f"{act} init failed")
    d = r["data"]; up = d["upload_url"]; pid = d["publish_id"]
    st, r2 = http("PUT", up, raw=open(f, "rb").read(), headers={"Content-Type": "video/mp4", "Content-Range": f"bytes 0-{n - 1}/{n}", "Content-Length": str(n)}, timeout=900)
    print("upload", st, str(r2)[:300])
    for _ in range(60):
        st, s = http("POST", f"{API}/post/publish/status/fetch/", js={"publish_id": pid}, token=tok)
        stat = (s.get("data") or {}).get("status") if isinstance(s, dict) else None; print("status", stat)
        if stat in ("PUBLISH_COMPLETE", "FAILED", "SEND_TO_USER_INBOX"): print(json.dumps(s.get("data"), indent=1)); break
        time.sleep(10)
