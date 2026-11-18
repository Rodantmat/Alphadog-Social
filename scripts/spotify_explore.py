#!/usr/bin/env python3
"""Read-only: open Spotify for Creators 'new episode' wizard, report file inputs/buttons, take screenshots (artifact). Uploads nothing."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import spotify_session as S
from playwright.sync_api import sync_playwright
SHOW = "5K5ZytGhBYz2xJ8Iwvf8ss"; OUT = "/tmp/spx"; os.makedirs(OUT, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1366, "height": 900}, locale="en-US", timezone_id="America/Los_Angeles",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
    ctx.add_cookies(S.load()); pg = ctx.new_page()
    for i, u in enumerate([f"https://creators.spotify.com/pod/show/{SHOW}/episodes",
                           f"https://creators.spotify.com/pod/show/{SHOW}/episode/wizard"]):
        pg.goto(u, wait_until="domcontentloaded", timeout=90000)
        try: pg.wait_for_load_state("networkidle", timeout=30000)
        except Exception: pass
        pg.wait_for_timeout(6000)
        pg.screenshot(path=f"{OUT}/s{i}.png", full_page=True)
        print(f"[{i}] url={pg.url.split('?')[0].replace(SHOW,'<id>')}")
        print("  file inputs:", pg.eval_on_selector_all("input[type=file]", "e=>e.map(x=>({accept:x.accept,multiple:x.multiple,name:x.name,id:x.id}))"))
        print("  buttons:", [t.strip()[:40] for t in pg.eval_on_selector_all("button,a[role=button],[role=button]", "e=>e.map(x=>x.innerText)") if t.strip()][:30])
        print("  text:", pg.inner_text("body")[:900].replace("\n", " | "))
    S.save(ctx); b.close()
