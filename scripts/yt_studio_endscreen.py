#!/usr/bin/env python3
"""Add end-screen elements (Subscribe + a Video element) to a video through YouTube Studio's end-screen editor.
env: VIDEO_ID, NEXT_VIDEO (video id for the 'Video' element; empty = skip), MODE=explore|apply, QA_DIR.
explore: open the editor and screenshot/dump each step, change nothing. Uses the saved Studio session (yt_studio_session)."""
import json, os, re, sys, time
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(__file__))
import yt_studio_session as S
VID = os.environ["VIDEO_ID"]; NEXT = os.environ.get("NEXT_VIDEO", ""); MODE = os.environ.get("MODE", "explore")
OUT = os.environ.get("QA_DIR", "/tmp/ytqa"); os.makedirs(OUT, exist_ok=True)
def snap(pg, n): S.shot(pg, f"{OUT}/{n}.png"); S.dump(pg, f"{OUT}/{n}.txt")
def click_text(pg, names, timeout=4000):
    for n in names:
        for loc in (pg.get_by_role("button", name=n), pg.get_by_text(n, exact=True)):
            try:
                if loc.count() and loc.first.is_visible():
                    loc.first.click(timeout=timeout); print("clicked", n); return n
            except Exception: pass
    return None
with sync_playwright() as p:
    b, ctx, pg = S.open_browser(p)
    S.goto(pg, f"https://studio.youtube.com/video/{VID}/edit", settle=8000)
    st = S.status(pg); print("STATUS", st)
    if st != "ok": snap(pg, "00_status_" + st); b.close(); sys.exit(2)
    pg.mouse.wheel(0, 6000); pg.wait_for_timeout(1500); snap(pg, "01_details_bottom")
    got = click_text(pg, ["End screen", "Add an end screen", "Tela final"])
    pg.wait_for_timeout(8000); snap(pg, "02_endscreen_open")
    if not got: print("no end screen entry found"); b.close(); sys.exit(4)
    # list every button/menu label visible, to learn the UI
    labels = pg.evaluate("() => [...document.querySelectorAll('button, [role=button], [role=menuitem], tp-yt-paper-item')].map(e => (e.innerText||e.getAttribute('aria-label')||'').trim()).filter(Boolean).slice(0,120)")
    print("LABELS", json.dumps(labels, ensure_ascii=False))
    if MODE == "explore2":
        pg.get_by_role("button", name="Adicionar elemento").first.click(); pg.wait_for_timeout(2500); snap(pg, "03_menu")
        items = pg.evaluate("() => [...document.querySelectorAll('[role=menuitem], tp-yt-paper-item, ytcp-text-menu *')].map(e => (e.innerText||'').trim()).filter(Boolean).slice(0,40)")
        print("MENU", json.dumps(items, ensure_ascii=False))
        for nm in ["Inscrever-se", "Inscrição"]:
            it = pg.get_by_text(nm, exact=True)
            if it.count():
                it.first.click(); print("added", nm); pg.wait_for_timeout(3000); break
        snap(pg, "04_after_subscribe")
        # report geometry of the preview player and any element boxes
        geo = pg.evaluate("""() => { const r=[]; document.querySelectorAll('[class*=endscreen], [class*=element], ytve-endscreen-element, ytve-endscreen-editor *').forEach(e=>{const b=e.getBoundingClientRect(); if(b.width>20&&b.height>20&&b.width<900) r.push([e.tagName, (e.className||'').toString().slice(0,60), Math.round(b.x),Math.round(b.y),Math.round(b.width),Math.round(b.height)])}); return r.slice(0,60);}""")
        print("GEO", json.dumps(geo))
        tl = pg.evaluate("() => [...document.querySelectorAll('[class*=timeline] *')].map(e=>(e.innerText||'').trim()).filter(t=>/\d+:\d+/.test(t)).slice(0,20)")
        print("TIMES", json.dumps(tl))
        # do not save
        click = pg.get_by_role("button", name="Descartar alterações")
        if click.count(): click.first.click(); pg.wait_for_timeout(1500)
    b.close()
