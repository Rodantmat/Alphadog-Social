#!/usr/bin/env python3
"""Feed content/tiktok_backlog.json into Buffer (TikTok) as Buffer's 10-post queue frees up.
Each item: {file, due (UTC ISO), service, text, mode, artifact}. Items due within the next 4 days that are not yet scheduled are
hosted on release media-public (same file name as on IG/FB/YT - one post = one file) and created on Buffer at their due time.
An item whose due time already passed is scheduled 20 minutes from now and marked late. Stops at the first Buffer refusal
(queue full) and retries on the next run. Files come from the footage clone in FBS (default /tmp/fbs/yellowstone-shorts)."""
import datetime as dt, glob, json, os, subprocess, sys
P = "content/tiktok_backlog.json"; FBS = os.environ.get("FBS", "/tmp/fbs/yellowstone-shorts"); REPO = os.environ["GITHUB_REPOSITORY"]
now = dt.datetime.now(dt.timezone.utc); B = json.load(open(P)); changed = False
for it in sorted(B, key=lambda x: x["due"]):
    if it.get("scheduled"): continue
    due = dt.datetime.fromisoformat(it["due"].replace("Z", "+00:00"))
    if due - now > dt.timedelta(days=4): continue
    when = due
    if due - now < dt.timedelta(minutes=15): when = now + dt.timedelta(minutes=20); it["late"] = True
    src = (glob.glob(f"{FBS}/*/{it['file']}") or [None])[0]
    if not src: print("MISSING", it["file"]); it["error"] = "file missing on footage"; changed = True; continue
    up = subprocess.run(["gh", "release", "upload", "media-public", src, "--clobber", "-R", REPO], capture_output=True, text=True)
    if up.returncode: print("UPLOAD FAILED", it["file"], up.stderr[-300:]); break
    url = f"https://github.com/{REPO}/releases/download/media-public/{it['file']}"
    open("/tmp/tt_text.txt", "w", encoding="utf-8").write(it["text"].replace("\\n", "\n"))
    r = subprocess.run(["python3", "scripts/buffer_post.py", "post", it.get("service", "tiktok"), url, when.strftime("%Y-%m-%dT%H:%M:%SZ"), "/tmp/tt_text.txt"],
                       capture_output=True, text=True)
    out = r.stdout + r.stderr; print(it["file"], it["due"], out[-600:])
    pid = next((l.split("=", 1)[1].strip() for l in out.splitlines() if l.startswith("BUFFER_POST_ID=")), None)
    if not pid: print("Buffer refused (queue full?) - stopping, will retry next run"); break
    it["scheduled"] = {"buffer_id": pid, "at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "due": when.strftime("%Y-%m-%dT%H:%M:%SZ")}; changed = True
if changed: json.dump(B, open(P, "w"), indent=1, ensure_ascii=False)
print("pending:", sum(1 for x in B if not x.get("scheduled")))
