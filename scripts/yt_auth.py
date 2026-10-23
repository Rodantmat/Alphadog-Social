#!/usr/bin/env python3
"""YouTube OAuth for a Desktop-app client.
  yt_auth.py url                  -> prints the consent URL (uses YT_CLIENT_ID)
  yt_auth.py exchange CODE_OR_URL -> exchanges the one-time code for a refresh token and stores it as repo secret YT_REFRESH_TOKEN
  yt_auth.py check                -> uses stored YT_REFRESH_TOKEN to print channel info
Secrets come from env: YT_CLIENT_ID, YT_CLIENT_SECRET, SECRETS_WRITER_TOKEN, YT_REFRESH_TOKEN, GITHUB_REPOSITORY. The refresh token is never printed."""
import base64, json, os, sys, urllib.parse, urllib.request, urllib.error

CID = os.environ.get("YT_CLIENT_ID", "").strip(); CSEC = os.environ.get("YT_CLIENT_SECRET", "").strip()
REDIRECT = "http://localhost"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube",
          "https://www.googleapis.com/auth/youtube.force-ssl"]

def call(url, data=None, headers=None, method=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method or ("POST" if data else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        return e.code, {"_error": body[:2000]}

def channel_check(access_token):
    st, ch = call("https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics,status&mine=true",
                  headers={"Authorization": "Bearer " + access_token})
    if st != 200:
        print("CHANNEL_CHECK_FAILED", st, ch.get("_error")); return False
    if not ch.get("items"): print("CHANNEL_CHECK: no channel on this account"); return False
    for it in ch["items"]:
        print("CHANNEL:", it["id"], "|", it["snippet"]["title"], "| subs:", it["statistics"].get("subscriberCount"),
              "| videos:", it["statistics"].get("videoCount"), "| longUploads:", it.get("status", {}).get("longUploadsStatus"))
    return True

mode = sys.argv[1]
if mode == "url":
    if not CID: sys.exit("YT_CLIENT_ID secret missing")
    q = {"client_id": CID, "redirect_uri": REDIRECT, "response_type": "code", "scope": " ".join(SCOPES),
         "access_type": "offline", "prompt": "consent", "include_granted_scopes": "true"}
    print("AUTH_URL=" + "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(q))
    sys.exit(0)

if mode == "exchange":
    raw = sys.argv[2].strip()
    code = urllib.parse.parse_qs(urllib.parse.urlparse(raw).query).get("code", [raw])[0] if "code=" in raw else raw
    st, tok = call("https://oauth2.googleapis.com/token", urllib.parse.urlencode({
        "code": code, "client_id": CID, "client_secret": CSEC, "redirect_uri": REDIRECT, "grant_type": "authorization_code"}).encode(),
        {"Content-Type": "application/x-www-form-urlencoded"})
    if st != 200: sys.exit(f"TOKEN_EXCHANGE_FAILED {st} {tok.get('_error')}")
    rt = tok.get("refresh_token")
    if not rt: sys.exit("No refresh_token returned: " + json.dumps({k: v for k, v in tok.items() if k != "access_token"}))
    print("TOKEN_OK scopes:", tok.get("scope"))
    # 1) store as encrypted repo secret FIRST so the token is never lost
    from nacl import encoding, public
    repo = os.environ["GITHUB_REPOSITORY"]; gh = os.environ["SECRETS_WRITER_TOKEN"].strip()
    H = {"Authorization": f"Bearer {gh}", "Accept": "application/vnd.github+json"}
    st, pk = call(f"https://api.github.com/repos/{repo}/actions/secrets/public-key", headers=H)
    if st != 200: sys.exit(f"PUBLIC_KEY_FAILED {st} {pk.get('_error')}")
    box = public.SealedBox(public.PublicKey(pk["key"].encode(), encoding.Base64Encoder()))
    enc = base64.b64encode(box.encrypt(rt.encode())).decode()
    st, _ = call(f"https://api.github.com/repos/{repo}/actions/secrets/YT_REFRESH_TOKEN",
                 data=json.dumps({"encrypted_value": enc, "key_id": pk["key_id"]}).encode(),
                 headers={**H, "Content-Type": "application/json"}, method="PUT")
    print("SECRET_SAVED status", st)
    if st not in (201, 204): sys.exit(1)
    # 2) sanity check (non-fatal)
    channel_check(tok["access_token"])
    sys.exit(0)

if mode == "check":
    rt = os.environ.get("YT_REFRESH_TOKEN", "").strip()
    if not rt: sys.exit("YT_REFRESH_TOKEN secret missing")
    st, tok = call("https://oauth2.googleapis.com/token", urllib.parse.urlencode({
        "refresh_token": rt, "client_id": CID, "client_secret": CSEC, "grant_type": "refresh_token"}).encode(),
        {"Content-Type": "application/x-www-form-urlencoded"})
    if st != 200: sys.exit(f"REFRESH_FAILED {st} {tok.get('_error')}")
    sys.exit(0 if channel_check(tok["access_token"]) else 1)
