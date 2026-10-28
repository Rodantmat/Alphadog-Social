#!/usr/bin/env python3
"""Add a dubbed AUDIO TRACK to an existing YouTube video through YouTube Studio's Languages page (the Data API can't).
env: VIDEO_ID, AUDIO_LANG (code like es / pt / pt-BR, or a UI label like "Portuguese (Brazil)"), AUDIO (local file path),
     DRY_RUN=1 (open the add-audio dialog, screenshot, cancel - nothing uploaded), QA_DIR, YT_STUDIO_SESSION, YT_GOOGLE_SESSION.
Idempotent: if that language row already shows an audio track, nothing is done.
Stops at once (no retries) on a Google sign-in / verification page.
Exit codes: 0 done/skipped/dry-run ok, 2 session dead, 3 Google challenge, 4 UI flow failed, 5 Studio rejected the file.
Writes the outcome to $RESULT_JSON (default /tmp/ytqa/result.json)."""
import json, os, re, sys, time
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(__file__))
import yt_studio_session as S

VID = os.environ["VIDEO_ID"]; LANG = os.environ.get("AUDIO_LANG") or "pt"
AUDIO = os.environ.get("AUDIO", ""); DRY = os.environ.get("DRY_RUN") == "1"
OUT = os.environ.get("QA_DIR", "/tmp/ytqa"); os.makedirs(OUT, exist_ok=True)
RES = os.environ.get("RESULT_JSON", f"{OUT}/result.json")
# UI names per language, in the UI languages Studio may be shown in (account is in Portuguese; English kept as fallback).
NAMES = {
    "es": ["Spanish", "Espanhol", "Español"], "es-419": ["Spanish (Latin America)", "Espanhol (América Latina)"],
    "es-ES": ["Spanish (Spain)", "Espanhol (Espanha)"], "es-MX": ["Spanish (Mexico)", "Espanhol (México)"],
    "pt": ["Portuguese", "Português"], "pt-BR": ["Portuguese (Brazil)", "Português (Brasil)"], "pt-PT": ["Portuguese (Portugal)", "Português (Portugal)"],
    "fr": ["French", "Francês"], "de": ["German", "Alemão"], "it": ["Italian", "Italiano"], "ja": ["Japanese", "Japonês"],
    "hi": ["Hindi", "Híndi"], "id": ["Indonesian", "Indonésio"], "ko": ["Korean", "Coreano"], "zh": ["Chinese", "Chinês"],
    "ru": ["Russian", "Russo"], "nl": ["Dutch", "Holandês"], "pl": ["Polish", "Polonês"], "tr": ["Turkish", "Turco"],
}
def lang_key(x):
    for k, v in NAMES.items():
        if x.lower() == k.lower() or x.lower() in [n.lower() for n in v]: return k
    return x
KEY = lang_key(LANG)
BASE = KEY.split("-")[0]
WANT = NAMES.get(KEY, [LANG])                       # exact names
ALT = NAMES.get(BASE, []) if BASE != KEY else []    # e.g. pt-BR may live in an existing plain "Portuguese" row
EMPTY = {"", "–", "-", "—"}
PUBLISH = re.compile(r"^\s*(Publish|Publicar)\s*$", re.I)
ADD = re.compile(r"^\s*(Add|Adicionar|Upload|Enviar)\s*$", re.I)
DONE_WORDS = re.compile(r"(Published|Publicado|Processing|Processando|Em processamento|Draft|Rascunho)", re.I)

def result(status, **kw):
    d = {"video_id": VID, "lang": KEY, "status": status, "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **kw}
    os.makedirs(os.path.dirname(RES) or ".", exist_ok=True); json.dump(d, open(RES, "w"), ensure_ascii=False, indent=1)
    print("RESULT", json.dumps(d, ensure_ascii=False))
def snap(pg, name): S.shot(pg, f"{OUT}/{name}.png"); S.dump(pg, f"{OUT}/{name}.txt")
def rows(pg):
    out = []
    for r in pg.locator("ytgn-video-translation-row").all():
        try:
            name = r.locator("button.language-display-name").first.inner_text(timeout=3000).strip()
            audio = r.locator("ytgn-video-translation-cell-audio").first.inner_text(timeout=3000).strip()
            out.append((name, audio, r))
        except Exception: pass
    return out
def find_row(pg):
    rs = rows(pg)
    print("rows:", [(n, a) for n, a, _ in rs])
    for names in (WANT, ALT):
        for n, a, r in rs:
            if n.lower() in [x.lower() for x in names]: return n, a, r
    return None
def open_languages(pg):
    S.goto(pg, f"https://studio.youtube.com/video/{VID}/translations", settle=7000)
    for _ in range(8):
        if pg.locator("ytgn-video-translation-row, #add-translations-button").count(): break
        pg.wait_for_timeout(4000)
    pg.wait_for_timeout(2500)
def dialog(pg):
    """The topmost open Studio dialog."""
    for sel in ["tp-yt-paper-dialog[opened]", "ytcp-dialog[opened] tp-yt-paper-dialog", "[role=dialog]:visible", "tp-yt-paper-dialog:visible"]:
        loc = pg.locator(sel)
        if loc.count(): return loc.last
    return None
def dialog_text(pg):
    d = dialog(pg)
    try: return S.redact(d.inner_text(timeout=3000)) if d else ""
    except Exception: return ""
def close_dialog(pg):
    d = dialog(pg)
    if d:
        for name in ["Cancel", "Cancelar", "Close", "Fechar", "Discard", "Descartar"]:
            b = d.get_by_role("button", name=name)
            if b.count():
                try: b.first.click(timeout=4000); pg.wait_for_timeout(2000); break
                except Exception: pass
        else:
            pg.keyboard.press("Escape"); pg.wait_for_timeout(2000)
    # a "discard changes?" confirmation may follow
    d = dialog(pg)
    if d:
        for name in ["Discard", "Descartar", "Close", "Fechar", "Sair"]:
            b = d.get_by_role("button", name=name)
            if b.count():
                try: b.first.click(timeout=4000); pg.wait_for_timeout(1500); break
                except Exception: pass

def add_language(pg):
    print("language row missing - adding it via 'Add language'")
    pg.locator("#add-translations-button").first.click(timeout=15000); pg.wait_for_timeout(2500)
    snap(pg, "10_add_language_menu")
    for name in WANT:
        it = pg.locator("tp-yt-paper-item, ytcp-text-menu tp-yt-paper-item, [role=option], [role=menuitem]").filter(has_text=re.compile(rf"^\s*{re.escape(name)}\s*$"))
        if it.count():
            it.first.scroll_into_view_if_needed(); S.pause(0.8, 1.6); it.first.click(timeout=8000); pg.wait_for_timeout(4000); return True
    # menu may have a search box
    sb = pg.locator("input[type=text]:visible, input:not([type]):visible")
    if sb.count():
        sb.first.type(WANT[-1] if len(WANT) > 1 else WANT[0], delay=120); pg.wait_for_timeout(2000)
        it = pg.locator("tp-yt-paper-item:visible, [role=option]:visible").first
        if it.count(): it.click(timeout=8000); pg.wait_for_timeout(4000); return True
    pg.keyboard.press("Escape"); return False

def open_add_audio(pg, row):
    cell = row.locator("ytgn-video-translation-cell-audio").first
    cell.scroll_into_view_if_needed(); cell.hover(); pg.wait_for_timeout(1800)
    snap(pg, "11_audio_cell_hover")
    btns = cell.locator("button, ytcp-button, [role=button]")
    print("audio cell buttons:", [S.redact((b.get_attribute("aria-label") or "") + "|" + (b.inner_text() or "").strip()) for b in btns.all()][:8])
    target = None
    for b in btns.all():
        t = (b.inner_text() or "").strip(); a = b.get_attribute("aria-label") or ""
        if ADD.match(t) or ADD.match(a) or re.search(r"(add|adicionar)", a, re.I): target = b; break
    if target is None and btns.count(): target = btns.first
    if target is None: target = cell
    S.pause(0.8, 1.8); target.click(timeout=10000); pg.wait_for_timeout(3500)
    # the click may open a small menu (e.g. "Upload file" / "Enviar arquivo")
    menu = pg.locator("tp-yt-paper-item:visible, [role=menuitem]:visible")
    if menu.count() and not dialog(pg):
        print("audio menu:", [m.inner_text().strip()[:40] for m in menu.all()][:8])
        pick = menu.filter(has_text=re.compile(r"(upload|enviar|arquivo|file)", re.I))
        (pick.first if pick.count() else menu.first).click(timeout=8000); pg.wait_for_timeout(3500)
    snap(pg, "12_add_audio_dialog"); print("dialog text:", dialog_text(pg)[:800].replace("\n", " | "))

def upload(pg):
    d = dialog(pg) or pg
    inp = d.locator("input[type=file]")
    if not inp.count(): inp = pg.locator("input[type=file]:not(#captions-file-loader)")
    if inp.count():
        inp.last.set_input_files(AUDIO); print("file set via input")
    else:
        btn = d.get_by_role("button", name=re.compile(r"(select|selecionar|upload|enviar|choose|escolher)", re.I))
        with pg.expect_file_chooser(timeout=15000) as fc: btn.first.click()
        fc.value.set_files(AUDIO); print("file set via chooser")
    # wait for the upload to go through and Publish to become enabled, or an error
    t0 = time.time(); last = ""
    while time.time() - t0 < 1500:
        pg.wait_for_timeout(10000)
        txt = dialog_text(pg);
        if txt != last: print(f"[{int(time.time()-t0)}s] dialog:", txt[:400].replace("\n", " | ")); last = txt
        if re.search(r"(error|erro|n[aã]o (foi|é) poss|must match|precisa|duration|dura[cç][aã]o|too (long|short)|muito (longo|curto)|couldn.t|failed|falh)", txt, re.I) \
           and not re.search(r"(enviando|uploading|\d+ ?%)", txt, re.I):
            return "rejected", txt
        d = dialog(pg)
        if d:
            pb = d.get_by_role("button", name=PUBLISH)
            if pb.count() and pb.first.is_enabled() and (pb.first.get_attribute("aria-disabled") or "false") != "true":
                if not re.search(r"(uploading|enviando|\d+ ?%)", txt, re.I): return "ready", txt
        else:
            return "closed", txt
    return "timeout", last

def main():
    if not DRY and not (AUDIO and os.path.exists(AUDIO)): result("error", error=f"audio file missing: {AUDIO}"); sys.exit(4)
    with sync_playwright() as p:
        b, ctx, pg = S.open_browser(p)
        S.goto(pg, S.STUDIO)
        st = S.status(pg); print("[studio] status:", st)
        if st != "ok":
            S.dump(pg, f"{OUT}/00_stop.txt")
            if st == "challenge": S.shot(pg, f"{OUT}/00_challenge.png")
            result(st); b.close(); sys.exit(3 if st == "challenge" else 2)
        S.pause(2, 5); open_languages(pg)
        st = S.status(pg, need_channel=False)
        if st in ("challenge", "login"): S.dump(pg, f"{OUT}/00_stop.txt"); result(st); b.close(); sys.exit(3 if st == "challenge" else 2)
        snap(pg, "01_before")
        f = find_row(pg)
        if f and f[1] not in EMPTY:
            print(f"'{f[0]}' already has audio: {f[1]} - nothing to do"); result("already", ui=f[1], row=f[0]); S.save(ctx); b.close(); return
        if not f:
            if DRY: print("DRY_RUN: would add the language row", WANT[0]); result("dry_run", note="language row missing"); S.save(ctx); b.close(); return
            if not add_language(pg): snap(pg, "90_fail"); result("error", error="could not add language"); S.save(ctx); b.close(); sys.exit(4)
            f = find_row(pg)
            if not f: snap(pg, "90_fail"); result("error", error="row not visible after add"); S.save(ctx); b.close(); sys.exit(4)
        name, audio, row = f; print(f"row: {name} | audio: {audio or '-'}")
        try: open_add_audio(pg, row)
        except Exception as e: snap(pg, "90_fail"); result("error", error="open add-audio: " + str(e)[:200]); S.save(ctx); b.close(); sys.exit(4)
        if DRY:
            close_dialog(pg); snap(pg, "13_after_cancel"); result("dry_run", row=name, dialog=dialog_text(pg)[:300]); S.save(ctx); b.close(); return
        S.pause(1.5, 3)
        state, txt = upload(pg); snap(pg, "14_after_upload")
        if state == "rejected": result("rejected", message=txt[:600], row=name); close_dialog(pg); S.save(ctx); b.close(); sys.exit(5)
        if state not in ("ready", "closed"): result("error", error=f"upload {state}", message=txt[:600]); close_dialog(pg); S.save(ctx); b.close(); sys.exit(4)
        if state == "ready":
            S.pause(1.5, 3); dialog(pg).get_by_role("button", name=PUBLISH).first.click(timeout=10000); pg.wait_for_timeout(8000)
            snap(pg, "15_after_publish")
            if dialog(pg): print("dialog still open:", dialog_text(pg)[:400].replace("\n", " | "))
        S.pause(3, 6); open_languages(pg); snap(pg, "16_after")
        f = find_row(pg); ui = f[1] if f else ""
        ok = bool(f) and ui not in EMPTY
        result("published" if ok else "unverified", ui=ui, row=f[0] if f else None)
        S.save(ctx); b.close(); sys.exit(0 if ok else 4)
main()
