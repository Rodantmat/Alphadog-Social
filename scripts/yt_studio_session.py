#!/usr/bin/env python3
"""YouTube Studio (web UI) session handling with auto-refresh - same model as spotify_session.py.
- Source of truth at first: GitHub secrets YT_STUDIO_SESSION (Cookie-Editor JSON export on studio.youtube.com) and
  YT_GOOGLE_SESSION (Cookie-Editor JSON export on accounts.google.com). Both are merged.
- Google rotates some cookies (e.g. __Secure-*PSIDTS) while the site is used, so after every successful run the browser's
  current youtube/google cookies are saved ENCRYPTED to content/private/yt_studio_session.enc (Fernet; key = SHA-256 of
  both secrets, which never leave GitHub secrets). The next run loads that rolling copy. A new export in either secret
  automatically wins (different key -> old file ignored).
- Never prints cookie values. Screenshots blur account avatars / email-like text; text dumps redact emails/phones.
- Google security: if a sign-in page or a "Verify it's you" challenge appears, callers must STOP (status 'challenge'/'login').
CLI: yt_studio_session.py keepalive"""
import base64, hashlib, json, os, random, re, sys, time
from cryptography.fernet import Fernet, InvalidToken
ENC = "content/private/yt_studio_session.enc"
SS = {"no_restriction": "None", "none": "None", "lax": "Lax", "strict": "Strict", "unspecified": None}
KEEP = ("youtube.com", "google.com")
CHANNEL = os.environ.get("YT_STUDIO_CHANNEL", "AlphaDog Studio")
STUDIO = "https://studio.youtube.com/"

def _secrets():
    a = os.environ.get("YT_STUDIO_SESSION", "").strip(); g = os.environ.get("YT_GOOGLE_SESSION", "").strip()
    if not a and not g: sys.exit("NO_SESSION_SECRET")
    return a, g
def _fernet(a, g): return Fernet(base64.urlsafe_b64encode(hashlib.sha256(("alphadog-ytstudio|" + a + "|" + g).encode()).digest()))
def _from_export(raw, default_domain):
    if not raw: return []
    data = json.loads(raw)
    if isinstance(data, dict) and "cookies" in data: data = data["cookies"]
    out = []
    for c in data:
        dom = c.get("domain") or default_domain
        if c.get("hostOnly") and dom.startswith("."): dom = dom[1:]
        k = {"name": c["name"], "value": c["value"], "domain": dom, "path": c.get("path") or "/",
             "secure": bool(c.get("secure", True)), "httpOnly": bool(c.get("httpOnly", False))}
        s = SS.get(str(c.get("sameSite", "")).lower())
        if s: k["sameSite"] = s
        if s == "None": k["secure"] = True
        if c["name"].startswith("__Host-"): k["path"] = "/"; k["secure"] = True; k["domain"] = k["domain"].lstrip(".")
        if c.get("expirationDate") or c.get("expires"):
            e = float(c.get("expirationDate") or c.get("expires"))
            if e > 0: k["expires"] = e
        out.append(k)
    return out
def _merge(*lists):
    m = {}
    for l in lists:
        for c in l: m[(c["name"], c["domain"], c["path"])] = c
    return list(m.values())
def load():
    a, g = _secrets()
    base = _merge(_from_export(g, ".google.com"), _from_export(a, ".youtube.com"))
    if os.path.exists(ENC) and not os.environ.get("YT_NO_ROLLING"):
        try:
            st = json.loads(_fernet(a, g).decrypt(open(ENC, "rb").read()))
            print(f"session: rolling copy from {time.strftime('%Y-%m-%d %H:%M', time.gmtime(st['saved']))} UTC ({len(st['cookies'])} cookies)")
            return st["cookies"]
        except (InvalidToken, KeyError, ValueError):
            print("session: rolling copy not usable with these secrets (new export?) - using the secrets")
    doms = sorted({c["domain"] for c in base})
    print(f"session: from the secrets ({len(base)} cookies; domains: {', '.join(doms)})")
    return base
def save(context):
    a, g = _secrets()
    ck = [c for c in context.cookies() if any(d in c.get("domain", "") for d in KEEP)]
    for c in ck:
        if c.get("expires", -1) in (-1, None): c.pop("expires", None)
    os.makedirs(os.path.dirname(ENC), exist_ok=True)
    open(ENC, "wb").write(_fernet(a, g).encrypt(json.dumps({"saved": time.time(), "cookies": ck}).encode()))
    print(f"session: saved {len(ck)} cookies (encrypted)")

# ---------- browser ----------
def pause(lo=1.2, hi=3.5): time.sleep(random.uniform(lo, hi))
def open_browser(p):
    """Real Google Chrome when present (ubuntu runners have it), headed if a display exists (xvfb-run), else headless."""
    args = ["--disable-blink-features=AutomationControlled", "--lang=en-US"]
    headless = not os.environ.get("DISPLAY")
    try: b = p.chromium.launch(channel="chrome", headless=headless, args=args)
    except Exception: b = p.chromium.launch(headless=headless, args=args)
    major = (b.version or "141.0").split(".")[0]
    ua = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major}.0.0.0 Safari/537.36"
    ctx = b.new_context(viewport={"width": 1440, "height": 1000}, locale="en-US", timezone_id="America/Los_Angeles",
                        user_agent=ua, extra_http_headers={"Accept-Language": "en-US,en;q=0.9"})
    ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
                        "Object.defineProperty(navigator,'platform',{get:()=>'Win32'});")
    ctx.add_cookies(load())
    pg = ctx.new_page()
    try:  # keep client hints consistent with the Windows UA
        cdp = ctx.new_cdp_session(pg)
        brands = [{"brand": "Google Chrome", "version": major}, {"brand": "Chromium", "version": major}, {"brand": "Not=A?Brand", "version": "24"}]
        cdp.send("Emulation.setUserAgentOverride", {"userAgent": ua, "acceptLanguage": "en-US,en;q=0.9", "platform": "Win32",
                 "userAgentMetadata": {"brands": brands, "fullVersion": f"{major}.0.0.0", "platform": "Windows", "platformVersion": "15.0.0",
                                       "architecture": "x86", "model": "", "mobile": False, "bitness": "64"}})
    except Exception as e: print("ua-metadata override skipped:", str(e)[:80])
    print(f"browser: {'headless' if headless else 'headed'} {b.version}")
    return b, ctx, pg

def goto(pg, url, settle=6000):
    pg.goto(url, wait_until="domcontentloaded", timeout=90000)
    try: pg.wait_for_load_state("networkidle", timeout=30000)
    except Exception: pass
    pg.wait_for_timeout(settle + random.randint(0, 2500))

CHALLENGE = re.compile(r"(verify it.s you|confirm it.s you|this extra step shows|unusual activity|couldn.t sign you in|"
                       r"2-step verification|enter the code|captcha|try another way|suspicious)", re.I)
def mask_url(u): return re.sub(r"[?#].*$", "", u)
def status(pg, need_channel=True):
    """'ok' | 'login' | 'challenge' | 'wrong_channel' | 'unknown'"""
    u = pg.url
    try: t = pg.inner_text("body", timeout=15000)[:20000]
    except Exception: t = ""
    if "accounts.google.com" in u:
        return "challenge" if ("challenge" in u or CHALLENGE.search(t)) else "login"
    if CHALLENGE.search(t[:3000]): return "challenge"
    if "studio.youtube.com" not in u: return "unknown"
    if not need_channel: return "ok"
    if CHANNEL.lower() in t.lower(): return "ok"
    try:  # channel name is in the left drawer; give it a moment
        pg.wait_for_selector(f"text={CHANNEL}", timeout=15000); return "ok"
    except Exception: return "wrong_channel" if re.search(r"Dashboard|Content|Analytics", t) else "unknown"

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"\+?\d[\d ()-]{8,}\d")
def redact(s): return PHONE.sub("<phone>", EMAIL.sub("<email>", s))
_BLUR_JS = r"""() => {
  const re = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/;
  const els = [];
  document.querySelectorAll('img').forEach(i => { const s = i.src || ''; if (/googleusercontent|ggpht|gstatic.com\/.*avatar/.test(s)) els.push(i); });
  document.querySelectorAll('#avatar-btn, ytcp-topbar-avatar, [aria-label*="Account"], [data-email], [data-identifier]').forEach(e => els.push(e));
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n; while ((n = w.nextNode())) { if (re.test(n.nodeValue) && n.parentElement) els.push(n.parentElement); }
  els.forEach(e => { e.setAttribute('data-adblur', e.style.filter || ''); e.style.filter = 'blur(14px)'; });
  return els.length; }"""
_UNBLUR_JS = "() => document.querySelectorAll('[data-adblur]').forEach(e => { e.style.filter = e.getAttribute('data-adblur'); e.removeAttribute('data-adblur'); })"
def shot(pg, path):
    """Screenshot with account avatars and any email-like text blurred (safe for the public release)."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    try:
        pg.evaluate(_BLUR_JS); pg.screenshot(path=path, full_page=True); pg.evaluate(_UNBLUR_JS)
    except Exception as e: print("screenshot failed:", path, str(e)[:100])
def dump(pg, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    try: t = pg.inner_text("body", timeout=15000)
    except Exception as e: t = f"<inner_text failed: {e}>"
    open(path, "w").write(f"URL: {mask_url(pg.url)}\n\n" + redact(t))

if __name__ == "__main__" and sys.argv[1:] == ["keepalive"]:
    from playwright.sync_api import sync_playwright
    out = os.environ.get("QA_DIR", "/tmp/ytqa")
    with sync_playwright() as p:
        b, ctx, pg = open_browser(p)
        goto(pg, STUDIO)
        st = status(pg); print("STATUS", st, "| landed:", mask_url(pg.url))
        if st == "ok":
            pause(4, 9); save(ctx)
        else:
            shot(pg, f"{out}/keepalive_{st}.png"); dump(pg, f"{out}/keepalive_{st}.txt")
        b.close()
        sys.exit(0 if st == "ok" else 2)
