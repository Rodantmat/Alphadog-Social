#!/usr/bin/env python3
"""Read-only: list the Spotify for Creators shows on the account and print followers/plays + episode rows."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import spotify_session as S
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1366, "height": 1000}, locale="en-US", timezone_id="America/Los_Angeles",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
    ctx.add_cookies(S.load()); pg = ctx.new_page(); pg.set_default_timeout(90000)
    pg.goto("https://creators.spotify.com/pod/dashboard/home", wait_until="domcontentloaded"); pg.wait_for_timeout(10000)
    print("URL", pg.url.split("?")[0])
    print("TEXT", pg.inner_text("body")[:800].replace("\n", " | "))
    ids = []
    for h in pg.eval_on_selector_all("a[href*='/pod/show/']", "e=>e.map(x=>x.href)"):
        m = re.search(r"/pod/show/([A-Za-z0-9]+)", h)
        if m and m.group(1) not in ids: ids.append(m.group(1))
    print("SHOW_IDS", ids)
    for sid in ["0Ylyy2y3qBkG0AUpAgGT7Q","2KocfjPnhOYoSesUmFICRb"]:
        for path in ("", "/episodes"):
            pg.goto(f"https://creators.spotify.com/pod/show/{sid}{path}", wait_until="domcontentloaded"); pg.wait_for_timeout(9000)
            print(f"== {sid} {path or '/home'}:", pg.inner_text("body")[:1500].replace("\n", " | ").replace("\t", ""))
    S.save(ctx)
