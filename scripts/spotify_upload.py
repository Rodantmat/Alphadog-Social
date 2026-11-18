#!/usr/bin/env python3
"""Upload a FULL documentary as a Spotify for Creators (English show) video episode.
Usage: spotify_upload.py MODE VIDEO.mp4 TITLE DESC_FILE      MODE = probe (upload + report Details/Review UI, publish nothing) | publish
Env: SPOTIFY_CREATORS_SESSION. Prints only masked URLs / UI labels. Screenshots in /tmp/spx."""
import os, re, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import spotify_session as S
from playwright.sync_api import sync_playwright
MODE, VIDEO, TITLE, DESC = sys.argv[1:5]
DESC = open(DESC, encoding="utf-8").read().strip()
SHOW = "5K5ZytGhBYz2xJ8Iwvf8ss"; OUT = "/tmp/spx"; os.makedirs(OUT, exist_ok=True)
def ui(pg, tag):
    pg.screenshot(path=f"{OUT}/{tag}.png", full_page=True)
    print(f"[{tag}] url={pg.url.split('?')[0].replace(SHOW,'<id>')}")
    print("  inputs:", pg.eval_on_selector_all("input,textarea,[contenteditable=true],select", "e=>e.map(x=>({t:x.tagName,type:x.type||'',id:x.id,name:x.name||'',ph:x.placeholder||x.getAttribute('aria-label')||'',v:(x.value||x.innerText||'').slice(0,40)}))"))
    print("  buttons:", [t.strip()[:50] for t in pg.eval_on_selector_all("button,[role=button],[role=radio],label", "e=>e.map(x=>x.innerText)") if t.strip()][:40])
    print("  text:", pg.inner_text("body")[:1400].replace("\n", " | "))
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1366, "height": 1000}, locale="en-US", timezone_id="America/Los_Angeles",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
    ctx.add_cookies(S.load()); pg = ctx.new_page(); pg.set_default_timeout(120000)
    pg.goto(f"https://creators.spotify.com/pod/show/{SHOW}/episode/wizard", wait_until="domcontentloaded")
    pg.wait_for_selector("#uploadAreaInput", state="attached", timeout=90000)
    print("uploading", os.path.getsize(VIDEO) // 1000000, "MB")
    pg.set_input_files("#uploadAreaInput", VIDEO)
    t0 = time.time()
    while time.time() - t0 < 25 * 60:               # wait until the Details step is reachable
        txt = pg.inner_text("body")
        if re.search(r"Episode title|Episode description|Title", txt) and pg.query_selector("input[name=title], input[id*=title], textarea, [contenteditable=true]"): break
        time.sleep(15)
    print("upload step finished after", int(time.time() - t0), "s")
    pg.wait_for_timeout(5000); ui(pg, "details")
    if MODE == "probe":
        S.save(ctx); b.close(); sys.exit(0)
    S.save(ctx); b.close()
