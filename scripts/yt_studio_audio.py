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
THUMB = os.environ.get("THUMB", "")  # optional per-language thumbnail (JPG/PNG 1280x720, < 2 MB)
OUT = os.environ.get("QA_DIR", "/tmp/ytqa"); os.makedirs(OUT, exist_ok=True)
RES = os.environ.get("RESULT_JSON", f"{OUT}/result.json")
# UI names per language. The account UI is English (US) since 2026-10-28; Portuguese labels are kept as a fallback.
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
    """The language editor dialog (or topmost open Studio dialog)."""
    for sel in ["tp-yt-paper-dialog:has(#language-details-source-label-audio)", "tp-yt-paper-dialog[opened]", "[role=dialog]:visible"]:
        loc = pg.locator(sel)
        try:
            if loc.count() and loc.last.is_visible(): return loc.last
        except Exception: pass
    return None
def dialog_text(pg):
    d = dialog(pg)
    try: return S.redact(d.inner_text(timeout=3000)) if d else ""
    except Exception: return ""
def _vis_text(pg, sel):
    """Studio keeps many hidden copies of the editor in the DOM - read only the visible one(s)."""
    out = ""
    for e in pg.locator(sel).all():
        try:
            if e.evaluate("e => !!(e.offsetParent || e.getClientRects().length) && getComputedStyle(e).visibility !== 'hidden' && !!e.closest('tp-yt-paper-dialog') && getComputedStyle(e.closest('tp-yt-paper-dialog')).display !== 'none'"):
                out = (e.inner_text(timeout=2000) or "").strip() or out
        except Exception: pass
    return out
def audio_state(pg):
    return _vis_text(pg, "#language-details-source-label-audio"), _vis_text(pg, "#language-details-status-label-audio")
def click_named(scope, names, timeout=5000):
    for nm in names:
        b = scope.get_by_role("button", name=nm, exact=True)
        if b.count():
            try: b.last.click(timeout=timeout); return nm
            except Exception: pass
    return None
def close_dialog(pg):
    for _ in range(3):
        if not dialog(pg): return
        if not click_named(pg, ["Close", "Cancel", "Fechar", "Cancelar"]): pg.keyboard.press("Escape")
        pg.wait_for_timeout(2000)
        click_named(pg, ["Discard", "Leave", "Discard changes", "Descartar", "Sair", "Descartar alterações"], 3000); pg.wait_for_timeout(1500)

def add_language(pg):
    print("language row missing - adding it via 'Add language'")
    pg.locator("#add-translations-button").first.click(timeout=15000); pg.wait_for_timeout(2500)
    snap(pg, "10_add_language_menu")
    items = pg.locator("tp-yt-paper-item:visible, [role=option]:visible, [role=menuitem]:visible")
    for name in WANT:
        it = items.filter(has_text=re.compile(rf"^\s*{re.escape(name)}\s*$"))
        if it.count():
            it.first.scroll_into_view_if_needed(); S.pause(0.8, 1.6); it.first.click(timeout=8000); pg.wait_for_timeout(5000)
            snap(pg, "10b_after_add_language"); return True
    pg.keyboard.press("Escape"); return False

def open_editor(pg, row):
    """Clicking the language name opens that language's editor dialog (title/description, thumbnail, AUDIO, subtitles)."""
    if not dialog(pg):
        S.pause(0.8, 1.8); row.locator("button.language-display-name").first.click(timeout=10000)
    pg.locator("#language-details-text-button-audio:visible, #language-details-more-options-button-audio:visible").first.wait_for(timeout=30000)
    pg.wait_for_timeout(2500)
SELECT = re.compile(r"^(Select file|Choose file|Selecionar arquivo|Escolher arquivo)$", re.I)
PUBLISH = re.compile(r"^(Publish|Publicar)$", re.I)
BUSY = re.compile(r"(enviando|uploading|carregando|processando|processing|verificando|checking|\d+ ?%)", re.I)
BAD = re.compile(r"(n[aã]o (foi|é) poss[ií]vel enviar|must (match|be)|precisa (ter|corresponder)|n[aã]o corresponde|doesn.t match|"
                 r"too (long|short)|muito (longo|curto)|couldn.t|failed|falhou|falha|erro|error|inv[aá]lid|unsupported|n[aã]o compat[ií]vel)", re.I)
def audio_dialog(pg):
    """The 'Audio in <language>' sub-dialog (has Cancel + Publish, is not the editor)."""
    for d in pg.locator("tp-yt-paper-dialog, [role=dialog], ytcp-dialog").all():
        try:
            if not d.is_visible() or d.locator("#language-details-source-label-audio").count(): continue
            if d.get_by_role("button", name=PUBLISH).count(): return d
        except Exception: pass
    return None
def upload(pg):
    """Editor > Audio 'Add' -> sub-dialog 'Audio in X' -> 'Select file' -> wait -> 'Publish'."""
    btn = pg.locator("#language-details-text-button-audio:visible").first
    S.pause(1, 2.5); btn.click(timeout=10000)
    for _ in range(15):
        sd = audio_dialog(pg)
        if sd: break
        pg.wait_for_timeout(1000)
    if not sd: snap(pg, "12_no_audio_dialog"); return "error", "audio sub-dialog did not open"
    base = set(l.strip() for l in sd.inner_text().splitlines())
    print("audio dialog:", S.redact(sd.inner_text())[:400].replace("\n", " | "))
    snap(pg, "12_audio_dialog")
    sel = sd.get_by_role("button", name=SELECT)
    S.pause(1, 2.5)
    with pg.expect_file_chooser(timeout=15000) as fc: sel.first.click(timeout=10000)
    print("file chooser opened")
    if DRY:
        return "dry", "audio dialog + file chooser OK"
    fc.value.set_files(AUDIO); print("file handed to Studio")
    t0 = time.time(); last = None; txt = ""
    while time.time() - t0 < 2400:
        pg.wait_for_timeout(10000)
        sd = audio_dialog(pg)
        toast = " ".join(t.inner_text().strip() for t in pg.locator("tp-yt-paper-toast:visible, ytcp-toast:visible").all() if t.inner_text().strip())
        if not sd: return "closed", "TOAST: " + S.redact(toast)
        full = S.redact(sd.inner_text())
        txt = "\n".join(l for l in full.splitlines() if l.strip() and l.strip() not in base) + ("\nTOAST: " + S.redact(toast) if toast else "")
        if txt != last: print(f"[{int(time.time()-t0)}s] {txt[-400:]!r}"); last = txt
        if BAD.search(txt) and not BUSY.search(txt): snap(pg, "14_rejected"); return "rejected", full
        pb = sd.get_by_role("button", name=PUBLISH).first
        enabled = pb.is_visible() and not pb.is_disabled() and pb.get_attribute("aria-disabled") != "true"
        if enabled and not re.search(r"(enviando|uploading|\d+ ?%)", txt, re.I):
            snap(pg, "14_ready"); S.pause(1.5, 3); pb.click(timeout=10000); print("clicked Publish")
            pg.wait_for_timeout(8000)
            sd = audio_dialog(pg)
            if sd: print("audio dialog still open:", S.redact(sd.inner_text())[:400].replace("\n", " | ")); snap(pg, "15_after_publish_click")
            return "published", txt
    return "timeout", txt

THUMB_BTN = "#language-details-text-button-localized-thumbnail"
def thumb_state(pg):
    """'' = no language thumbnail yet (button says Add), else the button label (e.g. Excluir/Delete) = already set."""
    t = _vis_text(pg, THUMB_BTN)
    return "" if re.match(r"^(Add|Upload|Adicionar|Enviar)$", t or "", re.I) else (t or "?")
def update_enabled(pg):
    upd = pg.get_by_role("button", name=re.compile(r"^(Update|Atualizar)$"))
    return any(b.is_visible() and not b.is_disabled() and b.get_attribute("aria-disabled") != "true" for b in upd.all())
def set_thumb(pg):
    btn = pg.locator(THUMB_BTN + ":visible").first
    S.pause(1, 2.5)
    chooser = None
    try:
        with pg.expect_file_chooser(timeout=10000) as fc: btn.click(timeout=10000)
        chooser = fc.value; print("thumbnail: file chooser opened")
    except Exception:
        pg.wait_for_timeout(2500); snap(pg, "20_thumb_after_click")
        sd = None
        for d in pg.locator("tp-yt-paper-dialog, [role=dialog], ytcp-dialog").all():
            try:
                if d.is_visible() and not d.locator("#language-details-source-label-audio").count(): sd = d
            except Exception: pass
        print("thumbnail: sub-dialog:", S.redact(sd.inner_text())[:300].replace("\n", " | ") if sd else None)
        scope = sd or pg
        sel = scope.get_by_role("button", name=re.compile(r"(selecionar|select|enviar|upload|escolher|choose|adicionar|add)", re.I))
        with pg.expect_file_chooser(timeout=10000) as fc: sel.first.click(timeout=10000)
        chooser = fc.value; print("thumbnail: file chooser opened (via sub-dialog)")
    if DRY: return "dry"
    chooser.set_files(THUMB); print("thumbnail: file handed to Studio")
    for _ in range(30):
        pg.wait_for_timeout(4000)
        st = thumb_state(pg)
        for nm in ["Done", "Save", "Confirm", "Concluído", "Salvar", "Confirmar"]:  # possible crop/confirm step
            b = pg.get_by_role("button", name=nm, exact=True)
            if b.count() and b.last.is_visible():
                try: b.last.click(timeout=3000); print("thumbnail: clicked", nm); pg.wait_for_timeout(2500)
                except Exception: pass
        if st or update_enabled(pg): break
    snap(pg, "21_thumb_set")
    if update_enabled(pg):
        S.pause(1, 2); click_named(pg, ["Update", "Atualizar"]); print("thumbnail: clicked Update"); pg.wait_for_timeout(7000)
    else:
        return "error: Update never enabled"
    snap(pg, "22_thumb_saved")
    return "set"

def main():
    if not DRY and not (AUDIO and os.path.exists(AUDIO)) and not (THUMB and os.path.exists(THUMB)):
        result("error", error=f"no input file (audio: {AUDIO}, thumb: {THUMB})"); sys.exit(4)
    do_audio = DRY or (AUDIO and os.path.exists(AUDIO)); do_thumb = bool(THUMB) and (DRY or os.path.exists(THUMB))
    with sync_playwright() as p:
        b, ctx, pg = S.open_browser(p)
        out = {}
        def finish(code, status, **kw):
            result(status, **out, **kw); S.save(ctx); b.close(); sys.exit(code)
        S.goto(pg, S.STUDIO)
        st = S.status(pg); print("[studio] status:", st)
        if st == "login" and not os.environ.get("YT_NO_ROLLING"):   # rolling copy went stale: retry once from the secrets
            print("[studio] rolling copy rejected - retrying from the secrets"); b.close(); os.environ["YT_NO_ROLLING"] = "1"
            b, ctx, pg = S.open_browser(p); S.goto(pg, S.STUDIO); st = S.status(pg); print("[studio] status (secrets):", st)
        if st != "ok":
            S.dump(pg, f"{OUT}/00_stop.txt")
            if st == "challenge": S.shot(pg, f"{OUT}/00_challenge.png")
            result(st); b.close(); sys.exit(3 if st == "challenge" else 2)
        S.pause(2, 5); open_languages(pg)
        st = S.status(pg, need_channel=False)
        if st in ("challenge", "login"): S.dump(pg, f"{OUT}/00_stop.txt"); result(st); b.close(); sys.exit(3 if st == "challenge" else 2)
        snap(pg, "01_before")
        f = find_row(pg)
        if not f:
            if DRY: print("DRY_RUN: would add the language", WANT[0]); finish(0, "dry_run", note="language row missing")
            if not add_language(pg): snap(pg, "90_fail"); finish(4, "error", error="could not add language")
            if not dialog(pg):
                open_languages(pg); f = find_row(pg)
                if not f: snap(pg, "90_fail"); finish(4, "error", error="row not visible after add")
        name = f[0] if f else WANT[0]; out["row"] = name
        def editor():
            if not dialog(pg):
                r = find_row(pg)
                open_editor(pg, r[2] if r else None)
            else: open_editor(pg, None)
        # ---- 1) per-language thumbnail ----
        if do_thumb:
            try:
                editor(); ts = thumb_state(pg); print(f"thumbnail state: '{ts}'"); snap(pg, "11_editor")
                if ts: out["thumb"] = "already"
                else:
                    r = set_thumb(pg); out["thumb"] = "dry_run" if r == "dry" else r
                    if r == "set":
                        close_dialog(pg); open_languages(pg); editor()
                        ts2 = thumb_state(pg); print(f"thumbnail state after: '{ts2}'"); out["thumb"] = "set" if ts2 else "unverified"
            except Exception as e: snap(pg, "90_thumb_fail"); out["thumb"] = "error: " + str(e)[:160]
            close_dialog(pg); S.pause(2, 4)
        # ---- 2) dubbed audio track ----
        if not do_audio:
            finish(0 if not str(out.get("thumb", "")).startswith("error") else 4, "thumb_only")
        f = find_row(pg)
        if f and f[1] not in EMPTY:
            print(f"'{f[0]}' already has audio: {f[1]} - nothing to do"); finish(0, "already", ui=f[1])
        try: editor()
        except Exception as e: snap(pg, "90_fail"); finish(4, "error", error="open language editor: " + str(e)[:200])
        src, stt = audio_state(pg); print(f"editor: {name} | audio source='{src}' status='{stt}'")
        if src or stt: close_dialog(pg); finish(0, "already", ui=stt or src)
        try: state, txt = upload(pg)
        except Exception as e: snap(pg, "90_fail"); close_dialog(pg); finish(4, "error", error="upload step: " + str(e)[:200])
        if state == "dry":
            pg.wait_for_timeout(1500)
            sd = audio_dialog(pg)
            if sd: click_named(sd, ["Cancel", "Cancelar"]); pg.wait_for_timeout(2000)
            close_dialog(pg); snap(pg, "13_after_cancel"); finish(0, "dry_run", saw=txt)
        if state == "rejected":
            sd = audio_dialog(pg)
            if sd: click_named(sd, ["Cancel", "Cancelar"])
            close_dialog(pg); finish(5, "rejected", message=txt[:800])
        if state not in ("published", "closed"):
            sd = audio_dialog(pg)
            if sd: click_named(sd, ["Cancel", "Cancelar"])
            close_dialog(pg); finish(4, "error", error=f"upload {state}", message=txt[:800])
        src, stt = audio_state(pg); print(f"editor after publish: audio source='{src}' status='{stt}'"); snap(pg, "15_editor_after")
        if update_enabled(pg):
            S.pause(1, 2); click_named(pg, ["Update", "Atualizar"]); print("clicked Update"); pg.wait_for_timeout(6000)
        close_dialog(pg)
        S.pause(3, 6); open_languages(pg); snap(pg, "16_after")
        f = find_row(pg); ui = f[1] if f else ""
        ok = bool(f) and ui not in EMPTY
        finish(0 if ok else 4, "published" if ok else "unverified", ui=ui)
if __name__ == "__main__":
    main()
