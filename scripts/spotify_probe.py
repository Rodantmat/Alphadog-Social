#!/usr/bin/env python3
"""Read-only probe: load the Spotify for Creators session (Cookie-Editor JSON in env SPOTIFY_CREATORS_SESSION),
open creators.spotify.com headless, and report only: logged in or not, where it landed, and the show names.
Never prints cookie values; takes no actions on the account. Logs are public (public repo), so output stays minimal."""
import json, os, re, sys
from playwright.sync_api import sync_playwright
raw = os.environ.get("SPOTIFY_CREATORS_SESSION", "").strip()
if not raw: sys.exit("NO_SESSION_SECRET")
try: data = json.loads(raw)
except Exception: sys.exit("SESSION_NOT_JSON (export with Cookie-Editor -> Export -> JSON)")
if isinstance(data, dict) and "cookies" in data: data = data["cookies"]
SS = {"no_restriction": "None", "none": "None", "lax": "Lax", "strict": "Strict"}
cookies = []
for c in data:
    k = {"name": c["name"], "value": c["value"], "domain": c.get("domain") or "creators.spotify.com", "path": c.get("path") or "/",
         "secure": bool(c.get("secure", True)), "httpOnly": bool(c.get("httpOnly", False))}
    s = SS.get(str(c.get("sameSite", "")).lower())
    if s: k["sameSite"] = s
    if c.get("expirationDate"): k["expires"] = float(c["expirationDate"])
    cookies.append(k)
print("cookies loaded:", len(cookies), "domains:", sorted({c["domain"] for c in cookies}))
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1366, "height": 900}, locale="en-US", timezone_id="America/Los_Angeles",
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
    ctx.add_cookies(cookies)
    pg = ctx.new_page()
    pg.goto("https://creators.spotify.com/", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(12000)
    url = pg.url; text = pg.inner_text("body")[:4000]
    host = re.sub(r"^https?://([^/]+).*", r"\1", url); path = re.sub(r"^https?://[^/]+", "", url).split("?")[0]
    print("landed:", host, re.sub(r"/show/[A-Za-z0-9]+", "/show/<id>", path))
    login_wall = "accounts.spotify.com" in host or re.search(r"\b(Log in|Sign up|Continue with)\b", text) and "Episodes" not in text
    challenge = re.search(r"(verify|verification|captcha|security check|confirm it.s you|enter the code)", text, re.I)
    shows = [s for s in ["America’s National Parks", "America's National Parks", "Parques Nacionales"] if s in text]
    print("LOGGED_IN" if not login_wall else "NOT_LOGGED_IN")
    print("CHALLENGE_SEEN" if challenge else "no challenge text")
    print("shows visible:", shows)
    b.close()
