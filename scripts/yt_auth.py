#!/usr/bin/env python3
"""YouTube OAuth for a Desktop-app client.
  yt_auth.py url                 -> prints the consent URL (uses YT_CLIENT_ID)
  yt_auth.py exchange CODE_OR_URL -> exchanges the one-time code for a refresh token and stores it as repo secret YT_REFRESH_TOKEN
Secrets come from env: YT_CLIENT_ID, YT_CLIENT_SECRET, SECRETS_WRITER_TOKEN, GITHUB_REPOSITORY. The refresh token is never printed."""
import base64, json, os, sys, urllib.parse, urllib.request

CID = os.environ.get("YT_CLIENT_ID", "").strip(); CSEC = os.environ.get("YT_CLIENT_SECRET", "").strip()
REDIRECT = "http://localhost"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube",
          "https://www.googleapis.com/auth/youtube.force-ssl"]

def post(url, data, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read() or b"{}")

if sys.argv[1] == "url":
    if not CID: sys.exit("YT_CLIENT_ID secret missing")
    q = {"client_id": CID, "redirect_uri": REDIRECT, "response_type": "code", "scope": " ".join(SCOPES),
         "access_type": "offline", "prompt": "consent", "include_granted_scopes": "true"}
    print("AUTH_URL=" + "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(q))
    sys.exit(0)

if sys.argv[1] == "exchange":
    raw = sys.argv[2].strip()
    code = urllib.parse.parse_qs(urllib.parse.urlparse(raw).query).get("code", [raw])[0] if "code=" in raw else raw
    tok = post("https://oauth2.googleapis.com/token", urllib.parse.urlencode({
        "code": code, "client_id": CID, "client_secret": CSEC, "redirect_uri": REDIRECT, "grant_type": "authorization_code"}).encode(),
        {"Content-Type": "application/x-www-form-urlencoded"})
    rt = tok.get("refresh_token")
    if not rt: sys.exit("No refresh_token returned: " + json.dumps({k: v for k, v in tok.items() if k != "access_token"}))
    # quick sanity check: which channel did we get?
    req = urllib.request.Request("https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics,status&mine=true",
                                 headers={"Authorization": "Bearer " + tok["access_token"]})
    with urllib.request.urlopen(req, timeout=30) as r: ch = json.loads(r.read())
    for it in ch.get("items", []):
        print("CHANNEL:", it["id"], "|", it["snippet"]["title"], "| subs:", it["statistics"].get("subscriberCount"),
              "| videos:", it["statistics"].get("videoCount"), "| longUploads:", it.get("status", {}).get("longUploadsStatus"))
    # store as encrypted repo secret
    from nacl import encoding, public
    repo = os.environ["GITHUB_REPOSITORY"]; gh = os.environ["SECRETS_WRITER_TOKEN"].strip()
    H = {"Authorization": f"Bearer {gh}", "Accept": "application/vnd.github+json"}
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/actions/secrets/public-key", headers=H)
    with urllib.request.urlopen(req, timeout=30) as r: pk = json.loads(r.read())
    box = public.SealedBox(public.PublicKey(pk["key"].encode(), encoding.Base64Encoder()))
    enc = base64.b64encode(box.encrypt(rt.encode())).decode()
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/actions/secrets/YT_REFRESH_TOKEN",
                                 data=json.dumps({"encrypted_value": enc, "key_id": pk["key_id"]}).encode(),
                                 headers={**H, "Content-Type": "application/json"}, method="PUT")
    with urllib.request.urlopen(req, timeout=30) as r: print("SECRET_SAVED status", r.status)
