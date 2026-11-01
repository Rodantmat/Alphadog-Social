#!/usr/bin/env python3
"""Add end-screen elements (Subscribe + a Video element) to a video through YouTube Studio's end-screen editor.
env: VIDEO_ID, NEXT_VIDEO (video id for the 'Video' element; empty = skip), MODE=explore|apply, QA_DIR.
explore: open the editor and screenshot/dump each step, change nothing. Uses the saved Studio session (yt_studio_session)."""
import sys, json, os, re, sys, time
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(__file__))
import yt_studio_session as S
VID = os.environ["VIDEO_ID"]; NEXT = os.environ.get("NEXT_VIDEO", ""); MODE = os.environ.get("MODE", "explore")
OUT = os.environ.get("QA_DIR", "/tmp/ytqa"); os.makedirs(OUT, exist_ok=True)
def dump(pg, label):
    """print a small JPEG of the page as base64 lines so it can be read back from the run log"""
    import base64
    try:
        raw = pg.screenshot(type="jpeg", quality=35)
        b = base64.b64encode(raw).decode()
        print("IMGSTART", label, len(b))
        for k in range(0, len(b), 3000): print("IMG", b[k:k+3000])
        print("IMGEND", label)
    except Exception as e: print("dump failed", e)

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
    if MODE == "explore3":
        pg.get_by_role("button", name="Adicionar elemento").first.click(); pg.wait_for_timeout(2000)
        pg.get_by_text("Vídeo", exact=True).first.click(); pg.wait_for_timeout(3000); snap(pg, "05_video_dialog")
        txt = pg.evaluate("() => (document.querySelector('ytve-endscreen-editor-options-panel')||document.body).innerText.slice(0,1500)")
        print("PANEL", json.dumps(txt, ensure_ascii=False))
        dl = pg.evaluate("() => [...document.querySelectorAll('tp-yt-paper-dialog, ytcp-dialog, [role=dialog]')].map(d=>(d.innerText||'').slice(0,800))")
        print("DIALOG", json.dumps(dl, ensure_ascii=False))
        for n in ["Escolher vídeo específico","Escolha um vídeo"]:
            print("has", n, pg.get_by_text(n).count())
    if MODE == "explore4":
        pg.get_by_role("button", name="Adicionar elemento").first.click(); pg.wait_for_timeout(2000)
        pg.get_by_text("Vídeo", exact=True).first.click(); pg.wait_for_timeout(2500)
        pg.get_by_text("Escolher um vídeo específico").first.click(); pg.wait_for_timeout(4000); snap(pg, "06_picker")
        dl = pg.evaluate("() => [...document.querySelectorAll('ytcp-video-pick-dialog, ytcp-dialog, tp-yt-paper-dialog, [role=dialog]')].map(d=>(d.tagName+': '+(d.innerText||'')).replace(/\\s+/g,' ').slice(0,1500)).filter(t=>t.length>40)")
        print("PICKER", json.dumps(dl, ensure_ascii=False))
        inp = pg.evaluate("() => [...document.querySelectorAll('input')].map(i=>[i.placeholder,i.type,i.getAttribute('aria-label')])")
        print("INPUTS", json.dumps(inp, ensure_ascii=False))
    if MODE in ("apply", "inspect"):
        TITLE = os.environ.get("NEXT_TITLE") or ""
        if NEXT and not TITLE: raise SystemExit("NEXT_TITLE is required when NEXT_VIDEO is set (picker matches by title)")
        def add(kind):
            # a menu left open by a previous (possibly disabled) menu item intercepts the next click: close it first
            for _ in range(3):
                if pg.locator("ytcp-text-menu tp-yt-paper-item").first.is_visible():
                    pg.keyboard.press("Escape"); pg.wait_for_timeout(600)
                else: break
            pg.get_by_role("button", name="Adicionar elemento").first.click(timeout=15000); pg.wait_for_timeout(1500)
            it = pg.get_by_text(kind, exact=True).first
            dis = it.evaluate("e => { const p = e.closest('tp-yt-paper-item'); return !!p && (p.getAttribute('aria-disabled')==='true' || p.hasAttribute('disabled')); }")
            if dis:
                print("menu item disabled (element of this kind already exists):", kind); pg.keyboard.press("Escape"); pg.wait_for_timeout(800); return False
            it.click(); pg.wait_for_timeout(2500); return True
        def boxes():
            return pg.evaluate("() => [...document.querySelectorAll('.ytp-ce-element')].map(e=>{const b=e.getBoundingClientRect(); return [e.className.toString().slice(0,50), Math.round(b.x),Math.round(b.y),Math.round(b.width),Math.round(b.height)]})")
        def drag(box, tx, ty):
            cx, cy = box[1]+box[3]/2, box[2]+box[4]/2
            pg.mouse.move(cx, cy); pg.mouse.down(); pg.mouse.move(cx+(tx-cx)/2, cy+(ty-cy)/2, steps=8); pg.mouse.move(tx, ty, steps=8); pg.mouse.up(); pg.wait_for_timeout(800)
        def boxes0():
            return pg.evaluate("() => [...document.querySelectorAll('.ytp-ce-element')].map(e=>{const b=e.getBoundingClientRect(); return [e.className.toString().slice(0,50), Math.round(b.x),Math.round(b.y),Math.round(b.width),Math.round(b.height)]})")
        # remove video elements that already exist (they may point at a superseded video); keep exactly the one we add below
        if NEXT:
            for _ in range(4):
                vids = [b_ for b_ in boxes0() if "ytp-ce-video" in b_[0]]
                if not vids: break
                v = vids[0]; pg.mouse.click(v[1] + v[3] / 2, v[2] + v[4] / 2); pg.wait_for_timeout(1200)
                pg.get_by_role("button", name="Excluir elemento").first.click(); pg.wait_for_timeout(1500)
                dlg_txt = pg.evaluate("() => [...document.querySelectorAll('tp-yt-paper-dialog, ytcp-dialog, [role=dialog]')].filter(d=>d.offsetParent!==null).map(d=>(d.innerText||'').replace(/\\s+/g,' ').slice(0,300))")
                print("DELETE_DIALOG", json.dumps(dlg_txt, ensure_ascii=False))
                for lab in ["Excluir", "Confirmar", "OK", "Sim"]:
                    cb = pg.locator("tp-yt-paper-dialog, ytcp-dialog, [role=dialog]").get_by_role("button", name=lab)
                    if cb.count() and cb.first.is_visible(): cb.first.click(); pg.wait_for_timeout(1500); print("confirmed delete via", lab); break
            print("VIDEO_BOXES_AFTER_PREDELETE", json.dumps([b_ for b_ in boxes0() if "ytp-ce-video" in b_[0]]))
        if "Inscreva-se:" in pg.evaluate("() => document.body.innerText"): print("subscribe element already present, not adding another")
        else: add("Inscrever-se")
        snap(pg, "10_sub")
        if NEXT:
            add("Vídeo")
            pg.get_by_text("Escolher um vídeo específico").first.click(); pg.wait_for_timeout(3000)
            dlg = pg.locator("ytcp-video-pick-dialog")
            try: dlg.get_by_placeholder("Pesquise nos seus vídeos").fill(TITLE[:25]); pg.wait_for_timeout(2000)
            except Exception as e: print("search skip", e)
            print("DLGTXT", json.dumps(dlg.inner_text()[:500], ensure_ascii=False))
            dlg.get_by_text(TITLE, exact=False).first.click(); pg.wait_for_timeout(2500)
            print("DLGBTN", json.dumps(pg.evaluate("() => [...document.querySelectorAll('ytcp-video-pick-dialog button, ytcp-video-pick-dialog ytcp-button')].map(b=>[(b.innerText||b.getAttribute('aria-label')||'').trim(), b.disabled||b.getAttribute('aria-disabled')])"), ensure_ascii=False))
            for lab in ["Selecionar", "Concluído", "Escolher", "OK"]:
                bt = dlg.get_by_role("button", name=lab)
                if bt.count() and bt.first.is_visible(): bt.first.click(); print("picked via", lab); pg.wait_for_timeout(1500); break
        snap(pg, "11_added"); bx = boxes(); print("BOXES", json.dumps(bx))
        # preview 721,264 480x270 (scale .25): logo circle ~ (828,398); video slot centre ~ (1059,398)
        for b_ in bx:
            if "channel" in b_[0]: drag(b_, 828, 398)
        bx = boxes()
        for b_ in bx:
            if "video" in b_[0] or "playlist" in b_[0]: drag(b_, 1059, 398)
        snap(pg, "12_placed"); print("BOXES2", json.dumps(boxes()))
        print("PANELAFTER", json.dumps(pg.evaluate("() => (document.querySelector('ytve-endscreen-editor-options-panel')||document.body).innerText.slice(0,600)"), ensure_ascii=False))
        print("TOPTXT", json.dumps(pg.evaluate("() => [...document.querySelectorAll('ytve-endscreen-editor-preview-overlay .ytp-ce-element')].map(e=>e.innerText.slice(0,80))"), ensure_ascii=False))
        if MODE == "inspect":
            b.close(); sys.exit(0)
        sv = pg.get_by_role("button", name="Salvar").last
        for _ in range(15):
            if sv.get_attribute("aria-disabled") != "true": break
            pg.wait_for_timeout(1000)
        print("SAVEDIS", sv.get_attribute("aria-disabled"))
        print("ERRTXT", json.dumps(pg.evaluate("() => (document.body.innerText.match(/[^\\n]*(erro|inválid|sobrepo|não é possível|Não foi)[^\\n]*/gi)||[]).slice(0,10)"), ensure_ascii=False))
        print("TLTXT", json.dumps(pg.evaluate("() => (document.querySelector('ytve-endscreen-editor-timeline')||document.body).innerText.slice(0,300)"), ensure_ascii=False))
        sv.click(timeout=8000); pg.wait_for_timeout(5000); snap(pg, "13_saved")
        print("SAVED")
    b.close()
