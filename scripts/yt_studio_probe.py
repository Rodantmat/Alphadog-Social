#!/usr/bin/env python3
"""Read-only YouTube Studio probe. Loads the saved session, opens Studio, confirms the channel, opens a video's Languages
page, and saves (blurred) screenshots + redacted text dumps + a structural map of buttons/rows to $QA_DIR.
With PROBE_MENU=1 it also opens the 'Add language' menu (lists entries) and presses Escape - nothing is changed.
Stops at once on any Google sign-in / 'Verify it's you' page. Saves refreshed cookies on success."""
import json, os, re, sys
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(__file__))
import yt_studio_session as S
VID = os.environ.get("VIDEO_ID", "LfoM0KAi8Yo"); OUT = os.environ.get("QA_DIR", "/tmp/ytqa"); os.makedirs(OUT, exist_ok=True)
STRUCT_JS = r"""() => {
  const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const lab = e => ((e.getAttribute('aria-label') || '') + ' | ' + (e.innerText || '').trim().replace(/\s+/g, ' ')).slice(0, 120);
  const btns = [...document.querySelectorAll('button, ytcp-button, ytcp-icon-button, tp-yt-paper-icon-button, [role=button], a[role=link]')]
     .filter(vis).map(e => ({tag: e.tagName.toLowerCase(), id: e.id || '', cls: (e.className && e.className.baseVal === undefined ? e.className : '').toString().slice(0, 80), label: lab(e)}));
  const rows = [...document.querySelectorAll('[role=row], tr, ytgn-video-translations-row, ytcp-video-translations-row, .row, [class*=row]')]
     .filter(vis).slice(0, 40).map(e => ({tag: e.tagName.toLowerCase(), id: e.id || '', cls: (e.className || '').toString().slice(0, 100),
        text: (e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 200),
        kids: [...e.children].map(c => c.tagName.toLowerCase() + (c.id ? '#' + c.id : '') + (c.className ? '.' + c.className.toString().split(' ').slice(0,2).join('.') : '')).slice(0, 12)}));
  const tags = {}; document.querySelectorAll('*').forEach(e => { const t = e.tagName.toLowerCase(); if (t.includes('-')) tags[t] = (tags[t] || 0) + 1; });
  const files = [...document.querySelectorAll('input[type=file]')].map(e => ({id: e.id, name: e.name, accept: e.accept}));
  return {buttons: btns, rows, custom_tags: tags, file_inputs: files}; }"""
def struct(pg, name):
    try: d = pg.evaluate(STRUCT_JS)
    except Exception as e: d = {"error": str(e)[:200]}
    open(f"{OUT}/{name}_struct.json", "w").write(S.redact(json.dumps(d, indent=1, ensure_ascii=False)))
def snap(pg, name): S.shot(pg, f"{OUT}/{name}.png"); S.dump(pg, f"{OUT}/{name}.txt"); struct(pg, name)
def stop(pg, ctx, b, st, name):
    snap(pg, name); print(f"STOP: {st} at {S.mask_url(pg.url)} - nothing retried"); b.close(); sys.exit(3)
with sync_playwright() as p:
    b, ctx, pg = S.open_browser(p)
    S.goto(pg, S.STUDIO)
    st = S.status(pg); print("[studio] status:", st, "| landed:", S.mask_url(pg.url))
    if st != "ok": stop(pg, ctx, b, st, "00_stop_studio")  # dashboard is not saved on success (shows subscriber names)
    S.pause(3, 6)
    S.goto(pg, f"https://studio.youtube.com/video/{VID}/translations", settle=8000)
    for _ in range(6):  # Studio renders the table lazily
        try: body = pg.inner_text("body", timeout=10000)
        except Exception: body = ""
        if pg.locator("ytgn-video-translation-row, #add-translations-button").count(): break
        pg.wait_for_timeout(5000)
    st = S.status(pg); print("[languages] status:", st, "| landed:", S.mask_url(pg.url))
    if st in ("challenge", "login"): stop(pg, ctx, b, st, "02_languages_stop")
    snap(pg, "02_languages")
    t = open(f"{OUT}/02_languages.txt").read()
    for w in ["Add language", "ADD LANGUAGE", "Spanish", "Portuguese", "Audio", "Dubbing", "Subtitles", "Title & description", "Published", "Draft"]:
        pass
    if os.environ.get("PROBE_MENU") == "1":
        try:
            S.pause()
            pg.locator("#add-translations-button").first.click(timeout=15000)
            pg.wait_for_timeout(3000); snap(pg, "03_add_language_menu")
            pg.keyboard.press("Escape"); pg.wait_for_timeout(2000)
        except Exception as e: print("add-language menu:", str(e)[:150])
        try:  # hover the Spanish row so per-cell action buttons show
            for i, r in enumerate(pg.locator("ytgn-video-translation-row").all()):
                n = r.locator("button.language-display-name").first.inner_text().strip()
                if n not in ("Spanish", "Espanhol", "Portuguese", "Português"): continue
                c = r.locator("ytgn-video-translation-cell-audio").first; c.hover(timeout=10000); pg.wait_for_timeout(2000)
                snap(pg, f"04_hover_audio_{i}")
                open(f"{OUT}/04_hover_audio_{i}_cell.html", "w").write(S.redact(c.evaluate("e => e.outerHTML"))[:30000])
        except Exception as e: print("spanish hover:", str(e)[:150])
    if os.environ.get("PROBE_LANG_CLICK") == "1":  # open each language's own editor (read-only), then close it
        for want in ("Espanhol", "Spanish", "Português", "Portuguese"):
            try:
                btn = pg.locator("button.language-display-name").filter(has_text=re.compile(rf"^\s*{want}\s*$"))
                if not btn.count(): continue
                S.pause(); btn.first.click(timeout=10000); pg.wait_for_timeout(5000)
                snap(pg, f"05_lang_{want}")
                for d in pg.locator("tp-yt-paper-dialog[opened], [role=dialog]").all():
                    try: open(f"{OUT}/05_lang_{want}_dialog.html", "a").write(S.redact(d.evaluate("e => e.outerHTML"))[:60000] + "\n\n")
                    except Exception: pass
                closed = False
                for nm in ["Fechar", "Close", "Cancelar", "Cancel"]:
                    c = pg.get_by_role("button", name=nm)
                    if c.count():
                        try: c.last.click(timeout=4000); closed = True; break
                        except Exception: pass
                if not closed: pg.keyboard.press("Escape")
                pg.wait_for_timeout(2500)
                if "/translations" not in pg.url: S.goto(pg, f"https://studio.youtube.com/video/{VID}/translations", settle=6000)
            except Exception as e: print("lang click", want, str(e)[:150])
    S.pause(2, 4); S.save(ctx); b.close()
print("PROBE_DONE")
