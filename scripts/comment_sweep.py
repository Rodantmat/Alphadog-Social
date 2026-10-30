#!/usr/bin/env python3
"""Comment sweep for Instagram + Facebook (AlphaDog Studio): read new comments on our recent posts and answer them in the owner's voice
(friendly, engaging, informative) with Gemini. State: content/comment_state.json (replied ids), log: content/comment_log.json.
Env: FB_PAGE_TOKEN, FB_PAGE_ID, GEMINI_API_KEY; DRY_RUN=1 (print only), MAX_REPLIES (default 12), LOOKBACK_DAYS (default 6).
Safety: never replies to our own comments, spam/abuse/link-drops/hot-button politics are skipped (logged), no invented facts, max N replies per run,
random pauses between replies, never mentions the token."""
import json, os, random, re, sys, time, urllib.error, urllib.parse, urllib.request, datetime as dt
T = os.environ["FB_PAGE_TOKEN"].strip(); PAGE = os.environ["FB_PAGE_ID"].strip(); GK = os.environ["GEMINI_API_KEY"].strip()
DRY = os.environ.get("DRY_RUN") == "1"; MAXR = int(os.environ.get("MAX_REPLIES") or 12); LOOK = int(os.environ.get("LOOKBACK_DAYS") or 6)
G = "https://graph.facebook.com/v26.0"; ST = "content/comment_state.json"; LG = "content/comment_log.json"
state = json.load(open(ST)) if os.path.exists(ST) else {"replied": {}, "skipped": {}}
log = json.load(open(LG)) if os.path.exists(LG) else []
now = dt.datetime.now(dt.timezone.utc)

def http(method, url, data=None, timeout=60):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=body, method=method), timeout=timeout) as r: return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e: raise RuntimeError(f"HTTP {e.code} {e.read().decode()[:300]}".replace(T, "***"))
def get(path, **q): q["access_token"] = T; return http("GET", f"{G}/{path}?" + urllib.parse.urlencode(q))
def post(path, **d): d["access_token"] = T; return http("POST", f"{G}/{path}", d)

VOICE = """You answer comments for AlphaDog Studio, a channel of documentary-style history/nature stories about American national parks and the places behind them (series so far: Chiricahua / Cochise and Massai, and a Yellowstone series). The owner, Rodo, writes like a friendly, curious storyteller: warm, short, a bit playful, informative, never preachy, no corporate talk.
Write ONE reply to the comment below.
Rules:
- 1-3 short sentences, max 260 characters, at most one emoji, no hashtags, no links, no 'as an AI'. Reply in the commenter's language.
- Be warm and engaging: thank them, add one interesting true fact or answer their question when you are SURE it is accurate and consistent with the post caption; if unsure, say something warm and general instead and never invent facts, dates or numbers.
- Where natural (not every time), invite them to the full documentary: 'the full story is on our YouTube channel, AlphaDog Studio'.
- Disagreement or criticism: stay calm, respectful and factual; thank them, share the one-line fact, do not argue or insult.
- Politics/hot-button opinions: do not take sides; acknowledge the feeling and bring it back to the history.
- SKIP (action=skip) when the comment is spam, a scam, self-promotion, a link drop, harassment/hate, sexual, asks for personal data, or is only a tag/mention of other users, or you cannot answer sensibly.
Return strict JSON only: {"action":"reply"|"skip","reply":"...","reason":"short"}"""

def gemini(post_text, comment, user):
    prompt = f"{VOICE}\n\nPOST CAPTION (context, treat as facts):\n{post_text[:1500]}\n\nCOMMENT by @{user}:\n{comment[:600]}\n"
    for model in ("gemini-2.5-flash", "gemini-flash-latest"):
        try:
            r = http("POST", f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GK}") if False else None
            req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GK}",
                data=json.dumps({"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"}}).encode(),
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=60) as resp: out = json.loads(resp.read())
            txt = out["candidates"][0]["content"]["parts"][0]["text"]; j = json.loads(re.sub(r"^```json|```$", "", txt.strip()).strip())
            return j
        except Exception as e: print("gemini", model, str(e)[:150].replace(GK, "***")); time.sleep(3)
    return {"action": "skip", "reason": "gemini unavailable"}

def recent(ts):
    try: return (now - dt.datetime.fromisoformat(ts.replace("Z", "+00:00").replace("+0000", "+00:00"))).days <= LOOK
    except Exception: return True

jobs = []   # (platform, post_text, comment_id, text, user, already_answered)
try:
    page = get(PAGE, fields="instagram_business_account{id,username}")
    ig = page.get("instagram_business_account") or {}
    if ig:
        for m in get(f"{ig['id']}/media", fields="id,caption,timestamp", limit=25).get("data", []):
            if not recent(m.get("timestamp", "")): continue
            try: cs = get(f"{m['id']}/comments", fields="id,text,username,timestamp,replies{username}", limit=50).get("data", [])
            except Exception as e: print("ig comments", m["id"], str(e)[:120]); continue
            for c in cs:
                answered = any((r.get("username") or "").lower() == (ig.get("username") or "").lower() for r in (c.get("replies") or {}).get("data", []))
                jobs.append(("instagram", m.get("caption") or "", c["id"], c.get("text") or "", c.get("username") or "", answered or (c.get("username") or "").lower() == (ig.get("username") or "").lower(), c.get("timestamp", "")))
except Exception as e: print("ig error", str(e)[:200])
try:
    vids = {}
    for edge in ("videos", "published_posts"):
        try:
            for v in get(f"{PAGE}/{edge}", fields="id,description,message,created_time", limit=25).get("data", []): vids[v["id"]] = v
        except Exception as e: print("fb", edge, str(e)[:120])
    for vid, v in vids.items():
        if not recent(v.get("created_time", "")): continue
        try: cs = get(f"{vid}/comments", fields="id,message,from,created_time,comments{from}", limit=50, filter="stream").get("data", [])
        except Exception as e: print("fb comments", vid, str(e)[:120]); continue
        for c in cs:
            frm = (c.get("from") or {}).get("id"); own = frm == PAGE
            answered = any(((r.get("from") or {}).get("id") == PAGE) for r in (c.get("comments") or {}).get("data", []))
            jobs.append(("facebook", v.get("description") or v.get("message") or "", c["id"], c.get("message") or "", (c.get("from") or {}).get("name", "someone"), answered or own, c.get("created_time", "")))
except Exception as e: print("fb error", str(e)[:200])

print(f"found {len(jobs)} comments; replied so far in state: {len(state['replied'])}")
sent = 0
for plat, ptxt, cid, text, user, answered, ts in sorted(jobs, key=lambda j: j[6]):
    if cid in state["replied"] or cid in state["skipped"] or answered or not text.strip(): continue
    if sent >= MAXR: print("max replies reached"); break
    j = gemini(ptxt, text, user); act = j.get("action"); rep = (j.get("reply") or "").strip()
    entry = {"t": now.strftime("%Y-%m-%dT%H:%MZ"), "platform": plat, "comment_id": cid, "user": user, "comment": text[:300], "action": act, "reason": j.get("reason", "")}
    if act != "reply" or not rep or "http" in rep.lower() or len(rep) > 400:
        state["skipped"][cid] = entry["t"]; entry["action"] = "skip"; log.append(entry); print("SKIP", plat, user, "|", text[:60], "|", j.get("reason")); continue
    entry["reply"] = rep
    if DRY: print("DRY", plat, f"@{user}:", text[:80], "->", rep); entry["action"] = "dry"; log.append(entry); continue
    try:
        post(f"{cid}/replies" if plat == "instagram" else f"{cid}/comments", message=rep)
        state["replied"][cid] = entry["t"]; sent += 1; print("REPLIED", plat, user, "->", rep)
    except Exception as e: entry["action"] = "error"; entry["reason"] = str(e)[:160]; print("ERROR", plat, str(e)[:160])
    log.append(entry); time.sleep(random.uniform(20, 55))
if not DRY:
    json.dump(state, open(ST, "w"), indent=1); json.dump(log[-400:], open(LG, "w"), indent=1, ensure_ascii=False)
print(f"done: {sent} replies sent")
