#!/usr/bin/env python3
"""Spotify for Creators session handling with auto-refresh.
- Source of truth at first: GitHub secret SPOTIFY_CREATORS_SESSION (Cookie-Editor JSON export).
- After every run the browser's current cookies (Spotify refreshes them while we use the site) are saved ENCRYPTED to
  content/private/spotify_session.enc (Fernet; key = SHA-256 of the secret, which never leaves GitHub secrets).
- Next run loads the newest of the two. A new export in the secret automatically wins (different key -> old file ignored).
Usage as module: cookies = load(); ...; save(context)   |   CLI: spotify_session.py keepalive"""
import base64, hashlib, json, os, re, sys, time
from cryptography.fernet import Fernet, InvalidToken
ENC = "content/private/spotify_session.enc"
SS = {"no_restriction": "None", "none": "None", "lax": "Lax", "strict": "Strict", "unspecified": None}
def _secret():
    raw = os.environ.get("SPOTIFY_CREATORS_SESSION", "").strip()
    if not raw: sys.exit("NO_SESSION_SECRET")
    return raw
def _fernet(raw): return Fernet(base64.urlsafe_b64encode(hashlib.sha256(("alphadog-spotify|" + raw).encode()).digest()))
def _from_export(raw):
    data = json.loads(raw)
    if isinstance(data, dict) and "cookies" in data: data = data["cookies"]
    out = []
    for c in data:
        k = {"name": c["name"], "value": c["value"], "domain": c.get("domain") or "creators.spotify.com", "path": c.get("path") or "/",
             "secure": bool(c.get("secure", True)), "httpOnly": bool(c.get("httpOnly", False))}
        s = SS.get(str(c.get("sameSite", "")).lower())
        if s: k["sameSite"] = s
        if c.get("expirationDate") or c.get("expires"):
            e = float(c.get("expirationDate") or c.get("expires"))
            if e > 0: k["expires"] = e
        out.append(k)
    return out
def load():
    raw = _secret(); base = _from_export(raw)
    if os.path.exists(ENC):
        try:
            st = json.loads(_fernet(raw).decrypt(open(ENC, "rb").read()))
            print(f"session: rolling copy from {time.strftime('%Y-%m-%d %H:%M', time.gmtime(st['saved']))} UTC ({len(st['cookies'])} cookies)")
            return st["cookies"]
        except (InvalidToken, KeyError, ValueError):
            print("session: rolling copy not usable with this secret (new export?) - using the secret")
    print(f"session: from the secret ({len(base)} cookies)")
    return base
def save(context):
    raw = _secret()
    ck = [c for c in context.cookies() if "spotify" in c.get("domain", "")]
    for c in ck:
        if c.get("expires", -1) in (-1, None): c.pop("expires", None)
    os.makedirs(os.path.dirname(ENC), exist_ok=True)
    open(ENC, "wb").write(_fernet(raw).encrypt(json.dumps({"saved": time.time(), "cookies": ck}).encode()))
    soon = min([c["expires"] for c in ck if c.get("expires")] or [0])
    print(f"session: saved {len(ck)} cookies (encrypted); earliest expiry {time.strftime('%Y-%m-%d', time.gmtime(soon)) if soon else 'session-only'}")
def logged_in(page):
    t = page.inner_text("body")[:6000]
    return not ("accounts.spotify.com" in page.url or "/login" in page.url) and bool(re.search(r"Episodes|Analytics|Chiricahua", t))
if __name__ == "__main__" and sys.argv[1:] == ["keepalive"]:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1366, "height": 900}, locale="en-US", timezone_id="America/Los_Angeles",
                            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
        ctx.add_cookies(load()); pg = ctx.new_page()
        pg.goto("https://creators.spotify.com/pod/dashboard/home", wait_until="domcontentloaded", timeout=90000)
        try: pg.wait_for_load_state("networkidle", timeout=30000)
        except Exception: pass
        pg.wait_for_timeout(5000)
        ok = logged_in(pg); print("LOGGED_IN" if ok else "NOT_LOGGED_IN")
        if ok: save(ctx)
        b.close()
        sys.exit(0 if ok else 2)
