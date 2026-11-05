#!/usr/bin/env python3
"""Link a Short to its full documentary via YouTube Studio's 'Related video' field (not available in the Data API).
env: VIDEO_ID (the Short), RELATED_TITLE (exact title of the long video), MODE=explore|apply. Studio UI is Portuguese.
explore: open Details, expand 'Show more', dump every label/section containing 'relacion'; changes nothing."""
import sys, json, os
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(__file__))
import yt_studio_session as S
VID = os.environ["VIDEO_ID"]; MODE = os.environ.get("MODE", "explore"); TITLE = os.environ.get("RELATED_TITLE", "")
OUT = os.environ.get("QA_DIR", "/tmp/ytqa"); os.makedirs(OUT, exist_ok=True)
def snap(pg, n): S.shot(pg, f"{OUT}/{n}.png"); S.dump(pg, f"{OUT}/{n}.txt")
with sync_playwright() as p:
    b, ctx, pg = S.open_browser(p)
    S.goto(pg, f"https://studio.youtube.com/video/{VID}/edit", settle=8000)
    st = S.status(pg); print("STATUS", st)
    if st != "ok": snap(pg, "00_status_" + st); b.close(); sys.exit(2)
    pg.mouse.wheel(0, 6000); pg.wait_for_timeout(1500)
    for nm in ["Mostrar mais", "Show more"]:
        bt = pg.get_by_role("button", name=nm)
        if bt.count() and bt.first.is_visible(): bt.first.click(); pg.wait_for_timeout(2000); print("expanded", nm); break
    pg.mouse.wheel(0, 6000); pg.wait_for_timeout(1500); snap(pg, "01_details")
    txt = pg.evaluate("() => document.body.innerText")
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    print("RELATED_LINES", json.dumps([l for l in lines if "relacion" in l.lower() or "related" in l.lower()], ensure_ascii=False))
    print("ALL_LINES", json.dumps(lines[:200], ensure_ascii=False))
    labels = pg.evaluate("() => [...document.querySelectorAll('button, [role=button], ytcp-button')].map(e => (e.innerText||e.getAttribute('aria-label')||'').trim()).filter(Boolean).slice(0,120)")
    print("BUTTONS", json.dumps(labels, ensure_ascii=False))
    if MODE == "apply":
        raise SystemExit("apply not implemented until explore confirms the UI")
    b.close()
