#!/usr/bin/env python3
"""Read-only: find every show reachable by this Spotify creators session (switcher / hrefs)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import spotify_session as S
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1366, "height": 1000}, locale="en-US",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
    ctx.add_cookies(S.load()); pg = ctx.new_page(); pg.set_default_timeout(60000)
    for u in ("https://creators.spotify.com/home", "https://creators.spotify.com/pod/dashboard/shows"):
        pg.goto(u, wait_until="domcontentloaded"); pg.wait_for_timeout(9000)
        print("PAGE", pg.url.split("?")[0], "|", pg.inner_text("body")[:300].replace("\n", " | "))
        print("HREFS", sorted(set(re.findall(r"/(?:pod/)?(?:home/)?show/[A-Za-z0-9]+", " ".join(pg.eval_on_selector_all("a", "e=>e.map(x=>x.href)"))))))
        for t in ("button[aria-haspopup]", "[data-testid*=show]", "header button", "nav button"):
            for el in pg.query_selector_all(t)[:3]:
                try: el.click(timeout=3000); pg.wait_for_timeout(2000)
                except Exception: pass
        print("AFTER_CLICK", pg.inner_text("body")[:600].replace("\n", " | "))
        print("HREFS2", sorted(set(re.findall(r"show/[A-Za-z0-9]+", " ".join(pg.eval_on_selector_all("a", "e=>e.map(x=>x.href)"))))))
    S.save(ctx)
