#!/usr/bin/env python3
"""Set the AlphaDog Studio Google account's interface language to English (US) through the saved session.
STEP=youtube : Studio account menu -> Language -> English (US); then checks youtube.com (and sets it there too if needed).
STEP=google  : myaccount.google.com/language -> preferred language English (United States).
DRY_RUN=1 opens the menus/dialogs, snapshots, and backs out without choosing anything.
Stops at once (no retry) on any password / 'verify it's you' page. Changes nothing else. Saves refreshed cookies on success."""
import json, os, re, sys
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(__file__))
import yt_studio_session as S
OUT = os.environ.get("QA_DIR", "/tmp/ytqa"); os.makedirs(OUT, exist_ok=True)
STEP = os.environ.get("STEP", "youtube"); DRY = os.environ.get("DRY_RUN") == "1"
RES = {"step": STEP, "dry_run": DRY}
LANG_ITEM = re.compile(r"^\s*(Idioma|Language)\s*:", re.I)
def snap(pg, n): S.shot(pg, f"{OUT}/{n}.png"); S.dump(pg, f"{OUT}/{n}.txt")
def done(b, ctx, code, **kw):
    RES.update(kw); print("RESULT", json.dumps(RES, ensure_ascii=False)); open(f"{OUT}/result.json", "w").write(json.dumps(RES, indent=1, ensure_ascii=False))
    if code == 0: S.save(ctx)
    b.close(); sys.exit(code)
def guard(pg, b, ctx, name, need_studio=False):
    u = pg.url
    try: t = pg.inner_text("body", timeout=15000)[:4000]
    except Exception: t = ""
    bad = "accounts.google.com" in u or S.CHALLENGE.search(t) or re.search(r"(enter your password|digite sua senha|insira sua senha|confirme que é você|verifique se é você)", t, re.I)
    if bad:
        snap(pg, name + "_STOP"); print(f"STOP: Google asked to sign in / verify at {S.mask_url(u)} - nothing retried")
        done(b, ctx, 3, status="challenge", at=S.mask_url(u))
def vis_items(pg):
    out = []
    for e in pg.locator("tp-yt-paper-item, ytd-compact-link-renderer, ytcp-text-menu tp-yt-paper-item, [role=menuitem], [role=option], yt-multi-page-menu-section-renderer a").all():
        try:
            if e.is_visible(): out.append(e)
        except Exception: pass
    return out
def text(e):
    try: return re.sub(r"\s+", " ", e.inner_text(timeout=2000)).strip()
    except Exception: return ""
def open_avatar(pg, studio):
    sel = "#avatar-btn, ytcp-topbar-avatar button, button#avatar-btn" if studio else "button#avatar-btn, #avatar-btn"
    S.pause(); pg.locator(sel).first.click(timeout=15000); pg.wait_for_timeout(2500)
def current_lang_item(pg):
    for e in vis_items(pg):
        t = text(e)
        if LANG_ITEM.search(t): return e, t
    return None, ""
def pick_english(pg, name):
    e, t = current_lang_item(pg)
    print(f"{name}: menu language item: '{t}'")
    if not e: snap(pg, f"{name}_no_lang_item"); return "no_lang_item", t
    if re.search(r":\s*English\s*(\(US\)|\(United States\))?\s*$", t, re.I): pg.keyboard.press("Escape"); return "already", t
    S.pause(); e.click(timeout=10000); pg.wait_for_timeout(2500); snap(pg, f"{name}_lang_list")
    opts = [x for x in vis_items(pg) if re.fullmatch(r"English \(US\)", text(x))]
    print(f"{name}: 'English (US)' options visible: {len(opts)}")
    if not opts: return "no_english_option", t
    if DRY: pg.keyboard.press("Escape"); pg.wait_for_timeout(800); pg.keyboard.press("Escape"); return "dry_run", t
    S.pause(); opts[0].click(timeout=10000); pg.wait_for_timeout(6000)
    return "clicked", t
def studio_english(pg):
    try: body = pg.inner_text("body", timeout=15000)
    except Exception: body = ""
    return bool(re.search(r"\b(Dashboard|Content|Analytics|Comments)\b", body)) and not re.search(r"\b(Painel|Conteúdo|Comentários)\b", body)
with sync_playwright() as p:
    b, ctx, pg = S.open_browser(p)
    if STEP == "youtube":
        S.goto(pg, S.STUDIO); guard(pg, b, ctx, "00_studio")
        st = S.status(pg); print("[studio] status:", st)
        if st != "ok": done(b, ctx, 3 if st == "challenge" else 2, status=st)
        try: open_avatar(pg, True)
        except Exception as e: snap(pg, "01_avatar_fail"); done(b, ctx, 4, status="error", error="studio avatar: " + str(e)[:150])
        r, before = pick_english(pg, "02_studio"); RES["studio"] = r; RES["studio_before"] = before
        guard(pg, b, ctx, "03_studio_after_pick")
        if r in ("no_lang_item", "no_english_option"): done(b, ctx, 4, status="error")
        if r == "clicked":
            S.goto(pg, S.STUDIO); guard(pg, b, ctx, "04_studio_reload")
        RES["studio_english"] = studio_english(pg); print("studio shows English labels:", RES["studio_english"])
        # YouTube main site
        S.pause(3, 6); S.goto(pg, "https://www.youtube.com/"); guard(pg, b, ctx, "05_youtube")
        try: open_avatar(pg, False)
        except Exception as e: snap(pg, "05_yt_avatar_fail"); done(b, ctx, 4, status="error", error="youtube avatar: " + str(e)[:150])
        r2, before2 = pick_english(pg, "06_youtube"); RES["youtube"] = r2; RES["youtube_before"] = before2
        guard(pg, b, ctx, "07_youtube_after_pick")
        if r2 == "clicked": S.goto(pg, "https://www.youtube.com/"); guard(pg, b, ctx, "08_youtube_reload")
        if not DRY:
            try: open_avatar(pg, False); _, now = current_lang_item(pg); RES["youtube_now"] = now; pg.keyboard.press("Escape")
            except Exception: pass
            S.goto(pg, S.STUDIO); guard(pg, b, ctx, "09_studio_final"); RES["studio_english"] = studio_english(pg)  # no dashboard snapshot (subscriber names)
        ok = DRY or (RES["studio_english"] and re.search(r"English", RES.get("youtube_now", "") or "English"))
        done(b, ctx, 0 if ok else 4, status="ok" if ok else "unverified")
    elif STEP == "google":
        S.goto(pg, "https://myaccount.google.com/language", settle=7000); guard(pg, b, ctx, "10_google_lang")
        snap(pg, "10_google_lang")
        body = pg.inner_text("body", timeout=15000)
        m = re.search(r"(Preferred language|Idioma preferido)\s*\n+\s*([^\n]+)", body); RES["before"] = m.group(2).strip() if m else "?"
        print("preferred language now:", RES["before"])
        if re.match(r"English", RES["before"]): done(b, ctx, 0, status="already")
        edit = pg.locator("[aria-label*='Edit'], [aria-label*='Editar'], [aria-label*='Alterar']").filter(has_not_text=re.compile("xyz"))
        cands = [e for e in edit.all() if e.is_visible()]
        print("edit buttons:", [e.get_attribute("aria-label") for e in cands][:6])
        if not cands: done(b, ctx, 4, status="error", error="no edit button")
        S.pause(); cands[0].click(timeout=10000); pg.wait_for_timeout(3500); guard(pg, b, ctx, "11_google_edit")
        snap(pg, "11_google_edit")
        box = pg.locator("[role=dialog] input[type=text], [role=dialog] input:not([type]), [role=dialog] [role=combobox] input, [role=dialog] input").first
        try: S.pause(); box.click(timeout=8000); box.type("English", delay=120); pg.wait_for_timeout(2500)
        except Exception as e: snap(pg, "12_google_nobox"); done(b, ctx, 4, status="error", error="search box: " + str(e)[:150])
        snap(pg, "12_google_search")
        opt = pg.locator("[role=option], [role=listbox] li, li[role=option]").filter(has_text=re.compile(r"^\s*English\s*$|English \(United States\)"))
        o = [x for x in opt.all() if x.is_visible()]
        print("english options:", [text(x) for x in o][:5])
        if not o: done(b, ctx, 4, status="error", error="no English option")
        S.pause(); o[0].click(timeout=8000); pg.wait_for_timeout(2500); snap(pg, "13_google_after_english")
        # a region step may follow (United States)
        reg = [x for x in pg.locator("[role=dialog] [role=radio], [role=dialog] [role=option], [role=dialog] li, [role=dialog] label").all()
               if x.is_visible() and re.search(r"United States|Estados Unidos", text(x))]
        if reg: S.pause(); reg[0].click(timeout=8000); pg.wait_for_timeout(1500); print("region: United States")
        snap(pg, "14_google_region")
        if DRY:
            c = pg.get_by_role("button", name=re.compile(r"^(Cancel|Cancelar)$"))
            (c.last.click() if c.count() else pg.keyboard.press("Escape")); pg.wait_for_timeout(1500); done(b, ctx, 0, status="dry_run")
        sv = pg.get_by_role("button", name=re.compile(r"^(Select|Selecionar|Save|Salvar|Done|Concluído|Confirm|Confirmar)$"))
        s_ = [x for x in sv.all() if x.is_visible()]
        if not s_: snap(pg, "15_google_nosave"); done(b, ctx, 4, status="error", error="no save button")
        S.pause(); s_[-1].click(timeout=8000); pg.wait_for_timeout(5000); guard(pg, b, ctx, "15_google_saved")
        S.goto(pg, "https://myaccount.google.com/language", settle=6000); guard(pg, b, ctx, "16_google_verify"); snap(pg, "16_google_verify")
        body = pg.inner_text("body", timeout=15000)
        m = re.search(r"(Preferred language|Idioma preferido)\s*\n+\s*([^\n]+)", body); RES["after"] = m.group(2).strip() if m else "?"
        ok = RES["after"].startswith("English"); done(b, ctx, 0 if ok else 4, status="set" if ok else "unverified")
