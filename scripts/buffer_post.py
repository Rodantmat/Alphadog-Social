#!/usr/bin/env python3
"""Buffer GraphQL API helper (https://api.buffer.com, Bearer key in BUFFER_API_KEY).
Usage:
  buffer_post.py channels
  buffer_post.py post SERVICE VIDEO_URL DUE_AT_UTC TEXT_FILE [THUMB_MS]   (DUE_AT empty = add to queue)
  buffer_post.py posts SERVICE            (list recent/scheduled posts on that channel)"""
import json, os, sys, urllib.request, urllib.error
KEY = os.environ["BUFFER_API_KEY"].strip()
def gql(query, variables=None):
    req = urllib.request.Request("https://api.buffer.com", data=json.dumps({"query": query, "variables": variables or {}}).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r: out = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code}: {e.read().decode()[:800]}")
    if out.get("errors"): print("GRAPHQL_ERRORS", json.dumps(out["errors"])[:1500])
    return out.get("data") or {}
def channels():
    orgs = gql("query { account { organizations { id name } } }")["account"]["organizations"]
    res = []
    for o in orgs:
        for c in gql('query($o: OrganizationId!) { channels(input: { organizationId: $o }) { id name service } }', {"o": o["id"]}).get("channels") or []:
            res.append(c)
    return res
def chan(service):
    m = [c for c in channels() if c["service"].lower() == service.lower()]
    if not m: raise SystemExit(f"no {service} channel connected")
    return m[0]["id"]
cmd = sys.argv[1]
if cmd == "channels":
    print(json.dumps(channels(), indent=1))
elif cmd == "post":
    service, url, due, textf = sys.argv[2:6]; thumb = int(sys.argv[6]) if len(sys.argv) > 6 else 1200
    inp = {"text": open(textf, encoding="utf-8").read().strip(), "channelId": chan(service), "schedulingType": "automatic",
           "assets": [{"video": {"url": url, "metadata": {"thumbnailOffset": thumb}}}]}
    if due: inp.update(mode="customScheduled", dueAt=due)
    else: inp["mode"] = "addToQueue"
    q = """mutation($input: CreatePostInput!) { createPost(input: $input) {
      ... on PostActionSuccess { post { id text dueAt status assets { source } } }
      ... on MutationError { message } } }"""
    d = gql(q, {"input": inp}); print("RESULT", json.dumps(d))
    r = (d.get("createPost") or {})
    if not r.get("post"): raise SystemExit("BUFFER_POST_FAILED " + json.dumps(r))
    print("BUFFER_POST_ID=" + r["post"]["id"])
elif cmd == "posts":
    cid = chan(sys.argv[2]); org = gql("query { account { organizations { id } } }")["account"]["organizations"][0]["id"]
    q = """query($o: OrganizationId!, $c: ChannelId!) { posts(input: { organizationId: $o, filter: { channelIds: [$c] } }, first: 100) { edges { node { id status dueAt text assets { source } } } } }"""
    d = gql(q, {"o": org, "c": cid})
    for e in ((d.get("posts") or {}).get("edges") or []):
        n = e["node"]; print("POST", n["id"], n["status"], n["dueAt"], repr((n["text"] or "")[:70]), [a.get("source", "")[-40:] for a in n.get("assets") or []])
elif cmd == "edit":
    inp = {"id": sys.argv[2]}
    if len(sys.argv) > 3 and sys.argv[3]: inp["dueAt"] = sys.argv[3]; inp["mode"] = "customScheduled"
    if len(sys.argv) > 4: inp["text"] = open(sys.argv[4], encoding="utf-8").read().strip()
    d = gql("mutation($i: EditPostInput!) { editPost(input: $i) { ... on PostActionSuccess { post { id dueAt status } } ... on MutationError { message } } }", {"i": inp})
    print("EDIT", json.dumps(d))
elif cmd == "delete":
    d = gql("mutation($i: DeletePostInput!) { deletePost(input: $i) { ... on PostActionSuccess { post { id } } ... on MutationError { message } } }", {"i": {"id": sys.argv[2]}})
    print("DELETE", json.dumps(d))
elif cmd == "types":
    for n in (sys.argv[2:] or ["Mutation"]):
        d = gql('query($n:String!){ __type(name:$n){ fields{ name args{ name type{ name kind ofType{ name kind } } } } inputFields{ name type{ name kind ofType{ name kind ofType{name kind} } } } } }', {"n": n}); print("TYPE", n, json.dumps(d))
