#!/usr/bin/env python3
"""Conflict-proof post-log save: re-apply this run's done/errors/hold onto the newest origin queue (never lose a 'done', which is what lets a later run double-post)."""
import json, subprocess, sys
Q = "content/social_queue.json"
mine = {i["id"]: i for i in json.load(open(Q))}
subprocess.run(["git", "fetch", "-q", "origin", "main"], check=True)
theirs = json.loads(subprocess.run(["git", "show", f"origin/main:{Q}"], capture_output=True, text=True, check=True).stdout)
for t in theirs:
    m = mine.get(t["id"])
    if not m: continue
    if m.get("done") and not t.get("done"): t["done"] = m["done"]
    if m.get("errors") and m["errors"] != t.get("errors"): t["errors"] = m["errors"]
    if m.get("hold") and not t.get("hold") and not t.get("done"): t["hold"] = m["hold"]
json.dump(theirs, open(Q, "w"), ensure_ascii=False, indent=1)
