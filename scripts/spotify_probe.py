#!/usr/bin/env python3
"""Read-only probe: load the Spotify for Creators session (Cookie-Editor JSON in env SPOTIFY_CREATORS_SESSION),
open the English show's episodes page headless, and report only: logged in or not, where it landed, and the show names.
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
print("cookies loaded:", len(cookies))
SHOWS = {"en": "5K5ZytGhBYz2xJ8Iwvf8ss"}
def mask(u):
    h = re.sub(r"^https?://([^/]+).*", r"\1", u); p = re.sub(r"^https?://[^/]+", "", u).split("?")[0]
    return h + re.sub(r"/show/[A-Za-z0-9]+", "/show/<id>", re.sub(r"/episode/[A-Za-z0-9]+", "/episode/<id>", p))
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1366, "height": 900}, locale="en-US", timezone_id="America/Los_Angeles",
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
    ctx.add_cookies(cookies)
    pg = ctx.new_page()
    for name, target in [("dashboard", "https://creators.spotify.com/pod/dashboard/home"),
                         ("episodes", f"https://creators.spotify.com/pod/show/{SHOWS['en']}/episodes")]:
        try:
            pg.goto(target, wait_until="domcontentloaded", timeout=90000)
            try: pg.wait_for_load_state("networkidle", timeout=30000)
            except Exception: pass
            pg.wait_for_timeout(6000)
        except Exception as e:
            print(name, "goto error", str(e)[:120]); continue
        text = pg.inner_text("body")[:6000]
        on_login = "accounts.spotify.com" in pg.url or "/login" in pg.url
        has_app = bool(re.search(r"\b(Episodes|Analytics|Monetize|Create)\b", text)) and bool(re.search(r"Settings", text))
        challenge = re.search(r"(captcha|security check|confirm it.s you|enter the code|verify your)", text, re.I)
        shows = [s for s in ["America’s National Parks", "America's National Parks", "Parques Nacionales", "Chiricahua"] if s in text]
        print(f"[{name}] landed: {mask(pg.url)} | app_ui: {has_app} | login_page: {on_login} | challenge: {bool(challenge)} | seen: {shows}")
    b.close()
