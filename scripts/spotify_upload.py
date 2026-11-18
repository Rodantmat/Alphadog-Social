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
SHOW = os.environ.get("SHOW_ID", "5K5ZytGhBYz2xJ8Iwvf8ss"); OUT = "/tmp/spx"; os.makedirs(OUT, exist_ok=True)
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
    pg.wait_for_selector("#title-input", timeout=180000)
    pg.fill("#title-input", TITLE[:200])
    ed = pg.query_selector("[contenteditable=true]")
    ed.click(); pg.keyboard.press("Control+A"); pg.keyboard.press("Delete")
    ed.fill(DESC[:4000]) if hasattr(ed, "fill") else pg.keyboard.insert_text(DESC[:4000])
    thumb = os.environ.get("THUMB")
    if thumb and os.path.exists(thumb):
        fis = [f for f in pg.query_selector_all("input[type=file]") if f.get_attribute("id") != "uploadAreaInput"]
        if fis: fis[0].set_input_files(thumb); print("thumbnail set")
    pg.wait_for_timeout(8000)
    for dlg in pg.query_selector_all("[role=dialog],[class*=dialog]"):
        try:
            print("dialog text:", dlg.inner_text()[:500].replace("\n", " | "))
            print("dialog buttons:", [x.inner_text().strip()[:30] for x in dlg.query_selector_all("button") if x.inner_text().strip()])
        except Exception: pass
    pg.screenshot(path=f"{OUT}/after_thumb.png")
    for rx in (r"^(Done|Save|Apply|Confirm|Crop|Use|Select|Continue|OK)", ):
        for bt in pg.query_selector_all("[role=dialog] button, [class*=dialog] button"):
            try:
                if re.match(rx, bt.inner_text().strip(), re.I) and bt.is_visible(): print("clicking dialog button:", bt.inner_text().strip()); bt.click(); pg.wait_for_timeout(4000); break
            except Exception: pass
    print("title ok:", pg.input_value("#title-input")[:60], "| desc chars:", len(pg.inner_text("[contenteditable=true]")))
    # wait for the media upload to finish: Next enabled and no progress text
    nxt = pg.get_by_role("button", name="Next")
    while time.time() - t0 < 40 * 60:
        busy = re.search(r"Uploading|Processing|\d+\s?%", pg.inner_text("body")[:3000])
        if nxt.is_enabled() and not busy: break
        time.sleep(15)
    print("media upload ready after", int(time.time() - t0), "s")
    ui(pg, "details_filled")
    nxt.click(); pg.wait_for_timeout(8000)
    ui(pg, "review")
    if MODE == "publish":
        print("radios:", pg.eval_on_selector_all("input[type=radio]", "e=>e.map(x=>({id:x.id,name:x.name,v:x.value,c:x.checked}))"))
        done = False
        for fn in (lambda: pg.locator("input[type=radio][value=now]").first.check(force=True),
                   lambda: pg.locator("label:has-text('Now')").first.click(timeout=8000),
                   lambda: pg.get_by_text("Now", exact=True).first.click(timeout=8000, force=True),
                   lambda: pg.get_by_role("radio", name=re.compile("Now", re.I)).first.check(force=True)):
            try: fn(); done = True; print("selected Now"); break
            except Exception as e: print("now try failed:", str(e)[:90])
        pg.wait_for_timeout(1500)
        print("radios after:", pg.eval_on_selector_all("input[type=radio]", "e=>e.map(x=>({id:x.id,v:x.value,c:x.checked}))"))
        btn = pg.get_by_role("button", name=re.compile(r"^(Publish|Publish now|Publish episode)$", re.I))
        print("publish buttons:", btn.count())
        if btn.count() == 1:
            btn.first.click(); pg.wait_for_timeout(20000); ui(pg, "after_publish")
    S.save(ctx); b.close()
