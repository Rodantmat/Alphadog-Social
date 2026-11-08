#!/usr/bin/env python3
"""Set the Related video (Short -> full documentary) in YouTube Studio from the cloud (no public API exists for it).
env: VIDEO_IDS  comma list of Short ids, or 'auto' = every public Short in content/metrics/latest.json
     DRY=1 only reports what it would do.  Film = parsed from the Short's own description line '▶ Full documentary (… , <Title>): url'.
Uses the encrypted rolling Studio session (yt_studio_session). Stops on any login/challenge. Never touches anything but the Related video field."""
import sys, os, re, json
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(__file__))
import yt_studio_session as S
OUT = os.environ.get("QA_DIR", "/tmp/ytqa"); os.makedirs(OUT, exist_ok=True)
DRY = os.environ.get("DRY", "") in ("1", "true")
ids = os.environ.get("VIDEO_IDS", "auto").strip()
if ids == "auto":
    m = json.load(open("content/metrics/latest.json"))
    ids = [v["id"] for v in m["youtube"]["videos"] if v["privacy"] == "public" and "#Shorts" in v["title"]]
else: ids = [i.strip() for i in ids.split(",") if i.strip()]
REL = re.compile(r"^(Related video|Vídeo relacionado)", re.I)
def film_title(desc):
    m = re.search(r"Full documentary \(([^)]*)\)", desc)
    if not m: return None
    t = m.group(1)
    t = re.sub(r"^(Zion,\s*)?Part \d+[:,]\s*", "", t)   # 'Part 2, When the…' | 'Zion, Part 1: Zion's Deadliest Day'
    return t.strip()
def related_row(pg):
    return pg.locator("ytcp-video-metadata-editor-sidepanel, ytcp-video-metadata-editor").get_by_text(REL).first
done, skipped, failed = [], [], []
with sync_playwright() as p:
    b, ctx, pg = S.open_browser(p)
    S.goto(pg, S.STUDIO); st = S.status(pg, need_channel=False); print("[studio] status:", st)
    if st != "ok": S.shot(pg, f"{OUT}/status_{st}.png"); b.close(); sys.exit(2)
    for vid in ids:
        try:
            S.goto(pg, f"https://studio.youtube.com/video/{vid}/edit", settle=7000)
            if S.status(pg, need_channel=False) != "ok": failed.append((vid, "session")); break
            desc = pg.evaluate("() => (document.querySelector('#description-textarea')||{}).innerText || ''")
            title = film_title(desc)
            if not title: skipped.append((vid, "no 'Full documentary' line")); continue
            pg.mouse.wheel(0, 8000); pg.wait_for_timeout(1500)
            row = pg.get_by_text(REL).first
            row.scroll_into_view_if_needed(timeout=10000)
            box = row.locator("xpath=ancestor::*[self::ytcp-video-metadata-editor-sidepanel-item or self::div][1]")
            cur = (box.inner_text() or "").replace("\\n", " ")
            if "None" not in cur and "Nenhum" not in cur and cur.strip().lower() not in ("related video", "vídeo relacionado"):
                skipped.append((vid, "already set: " + cur[:50])); print(vid, "already set"); continue
            if DRY: skipped.append((vid, f"would link -> {title}")); print(vid, "DRY ->", title); continue
            row.click(); pg.wait_for_timeout(1500)
            sb = pg.get_by_placeholder(re.compile(r"Search your videos|Pesquis", re.I)).first
            sb.fill(title[:40]); sb.press("Enter"); pg.wait_for_timeout(2500)
            opt = pg.get_by_role("option", name=re.compile(re.escape(title[:30]), re.I))
            if opt.count() != 1: failed.append((vid, f"{opt.count()} matches for '{title[:30]}'")); pg.keyboard.press("Escape"); continue
            opt.first.click(); pg.wait_for_timeout(1500)
            pg.get_by_role("button", name=re.compile(r"^(Save|Salvar)$", re.I)).first.click(); pg.wait_for_timeout(4000)
            S.goto(pg, f"https://studio.youtube.com/video/{vid}/edit", settle=6000); pg.mouse.wheel(0, 8000); pg.wait_for_timeout(1500)
            if title[:25].lower() in pg.evaluate("() => document.body.innerText").lower(): done.append((vid, title)); print(vid, "LINKED ->", title)
            else: failed.append((vid, "did not persist")); S.shot(pg, f"{OUT}/fail_{vid}.png")
        except Exception as e: failed.append((vid, str(e)[:120])); S.shot(pg, f"{OUT}/err_{vid}.png")
        S.pause(2, 4)
    S.save(ctx); b.close()
print("RESULT", json.dumps({"linked": done, "skipped": skipped, "failed": failed}, ensure_ascii=False))
sys.exit(1 if failed else 0)
