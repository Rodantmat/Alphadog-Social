#!/usr/bin/env python3
"""Private memorial generation on GitHub Actions (public repo, so everything private is encrypted).
modes:
  keys    make the workflow's RSA keypair; private half encrypted with GEMINI_API_KEY -> content/private/memorial_wf.{pub,key.enc}
  gen     decrypt content/private/memorial_in.{tar.enc,key.enc}; run plan.json stage (STAGE=list|images|videos|omni);
          encrypt ./out for Claude's public key (content/private/claude_out.pub) -> /tmp/enc/out.{tar.enc,key.enc}
Never prints the API key."""
import base64, json, os, subprocess, sys, time, urllib.request, urllib.error
K = os.environ["GEMINI_API_KEY"].strip(); B = "https://generativelanguage.googleapis.com/v1beta"
P = "content/private"
def sh(*a, inp=None): return subprocess.run(list(a), input=inp, capture_output=True, check=True).stdout
def req(method, url, body=None, timeout=600):
    r = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, method=method,
                               headers={"x-goog-api-key": K, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=timeout) as x: return x.status, json.loads(x.read() or b"{}")
    except urllib.error.HTTPError as e: return e.code, e.read().decode()[:1500].replace(K, "***")
def b64(p): return base64.b64encode(open(p, "rb").read()).decode()
def mime(p): return "image/png" if p.endswith(".png") else "image/jpeg"

mode = sys.argv[1]
if mode == "keys":
    os.makedirs(P, exist_ok=True)
    sh("openssl", "genrsa", "-out", "/tmp/wf.key", "3072")
    open(f"{P}/memorial_wf.pub", "wb").write(sh("openssl", "rsa", "-in", "/tmp/wf.key", "-pubout"))
    open(f"{P}/memorial_wf.key.enc", "wb").write(sh("openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-salt", "-a",
                                                    "-pass", "env:GEMINI_API_KEY", "-in", "/tmp/wf.key"))
    os.remove("/tmp/wf.key"); print("keys ok"); sys.exit()

# ---- gen: decrypt inputs (bundle may arrive as base64 parts memorial_in.b64.NN + memorial_in.key.b64, checked against memorial_in.sha)
import glob, hashlib
parts = sorted(glob.glob(f"{P}/memorial_in.b64.*"))
if parts:
    bad = []
    want = dict(l.split() for l in open(f"{P}/memorial_in.sha").read().split("\n") if l.strip())
    for p in parts:
        h = hashlib.sha256(open(p, "rb").read().strip()).hexdigest()[:12]
        if want.get(os.path.basename(p)) != h: bad.append(os.path.basename(p))
    print("parts", len(parts), "bad", bad)
    if bad: sys.exit("corrupt parts: " + ",".join(bad))
    open(f"{P}/memorial_in.tar.enc", "wb").write(base64.b64decode("".join(open(p).read().strip() for p in parts)))
    open(f"{P}/memorial_in.key.bin", "wb").write(base64.b64decode(open(f"{P}/memorial_in.key.b64").read().strip()))
sh("openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-a", "-pass", "env:GEMINI_API_KEY", "-in", f"{P}/memorial_wf.key.enc", "-out", "/tmp/wf.key")
akey = sh("openssl", "pkeyutl", "-decrypt", "-inkey", "/tmp/wf.key", "-pkeyopt", "rsa_padding_mode:oaep", "-in", f"{P}/memorial_in.key.bin")
os.makedirs("in", exist_ok=True)
sh("openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "10000", "-pass", "stdin", "-in", f"{P}/memorial_in.tar.enc", "-out", "/tmp/in.tar", inp=akey)
sh("tar", "-xf", "/tmp/in.tar", "-C", "in"); os.remove("/tmp/in.tar"); os.remove("/tmp/wf.key")
plan = json.load(open("in/plan.json"))
if os.path.exists(f"{P}/memorial_videos.json"):
    vp = json.load(open(f"{P}/memorial_videos.json")); plan["videos"] = vp["videos"]; plan["video_models"] = vp.get("video_models", [plan["video_model"]])
    plan["negative"] = vp.get("negative", plan.get("negative", "")); plan["resolution"] = vp.get("resolution", plan.get("resolution"))
    for k in ("omni_model", "omni_res"):
        if k in vp: plan[k] = vp[k]
PREV = os.environ.get("PREV", "").strip()
if PREV:  # keyframes from an earlier images run (symmetric, GEMINI_API_KEY)
    u = f"https://raw.githubusercontent.com/{os.environ.get('GITHUB_REPOSITORY','Rodantmat/Alphadog-Social')}/footage/private/memorial/{PREV}/wf_out.tar.enc"
    open("/tmp/prev.enc", "wb").write(urllib.request.urlopen(u, timeout=300).read())
    sh("openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-pass", "env:GEMINI_API_KEY", "-in", "/tmp/prev.enc", "-out", "/tmp/prev.tar")
    sh("tar", "-xf", "/tmp/prev.tar", "-C", "in"); print("prev keyframes:", sorted(f for f in os.listdir("in") if f.endswith(".png")))
STAGE = os.environ.get("STAGE", "list"); ONLY = [x for x in os.environ.get("ONLY", "").split(",") if x]
os.makedirs("out", exist_ok=True); log = []
def note(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.append(s)

if STAGE == "list":
    tok = ""
    while True:
        st, r = req("GET", f"{B}/models?pageSize=1000" + (f"&pageToken={tok}" if tok else ""))
        if not isinstance(r, dict): note("list failed", st, r); break
        for m in r.get("models", []): note(m["name"], m.get("supportedGenerationMethods"))
        tok = r.get("nextPageToken")
        if not tok: break

if STAGE == "images":
    for j in plan["images"]:
        if ONLY and j["id"] not in ONLY: continue
        parts = [{"text": j["prompt"]}] + [{"inline_data": {"mime_type": mime(f"in/{p}"), "data": b64(f"in/{p}")}} for p in j["refs"]]
        for n in range(j.get("n", 2)):
            body = {"contents": [{"role": "user", "parts": parts}],
                    "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "9:16", "imageSize": "2K"}}}
            st, r = req("POST", f"{B}/models/{plan['image_model']}:generateContent", body)
            if st == 400 and "imageSize" in str(r):
                body["generationConfig"]["imageConfig"].pop("imageSize"); st, r = req("POST", f"{B}/models/{plan['image_model']}:generateContent", body)
            ok = False
            if isinstance(r, dict):
                for c in r.get("candidates", []):
                    for p in (c.get("content") or {}).get("parts", []):
                        d = p.get("inlineData") or p.get("inline_data")
                        if d: open(f"out/{j['id']}_{n}.png", "wb").write(base64.b64decode(d["data"])); ok = True
            note(j["id"], n, "OK" if ok else f"FAIL {st} {str(r)[:400]}")

if STAGE == "videos":
    ops = []
    for v in plan["videos"]:
        if ONLY and v["id"] not in ONLY: continue
        inst = {"prompt": v["prompt"], "image": {"bytesBase64Encoded": b64(f"in/{v['first']}"), "mimeType": mime(v["first"])}}
        if v.get("last"): inst["lastFrame"] = {"bytesBase64Encoded": b64(f"in/{v['last']}"), "mimeType": mime(v["last"])}
        params = {"aspectRatio": "9:16", "durationSeconds": v.get("dur", 8), "resolution": plan.get("resolution", "1080p"),
                  "personGeneration": "allow_adult", "negativePrompt": plan.get("negative", "")}
        models = plan.get("video_models") or [plan["video_model"]]
        for vm in models:
            st, r = req("POST", f"{B}/models/{vm}:predictLongRunning", {"instances": [inst], "parameters": params})
            if st == 200 or (st != 404 and "not found" not in str(r).lower()): break
            note(v["id"], "model unavailable", vm, st)
        plan["video_model"] = vm; plan["video_models"] = [vm] + [m for m in models if m != vm]
        if isinstance(r, dict) and r.get("name"): ops.append((v["id"], r["name"])); note(v["id"], "started", vm)
        else: note(v["id"], "FAIL start", st, str(r)[:500])
        time.sleep(3)
    pending = dict(ops); t0 = time.time()
    while pending and time.time() - t0 < 3000:
        time.sleep(20)
        for vid, name in list(pending.items()):
            st, r = req("GET", f"{B}/{name}")
            if not isinstance(r, dict) or not r.get("done"): continue
            pending.pop(vid)
            samples = (((r.get("response") or {}).get("generateVideoResponse") or {}).get("generatedSamples")) or []
            if not samples: note(vid, "FAIL", json.dumps(r)[:600]); continue
            rr = urllib.request.Request(samples[0]["video"]["uri"], headers={"x-goog-api-key": K})
            open(f"out/{vid}.mp4", "wb").write(urllib.request.urlopen(rr, timeout=600).read()); note(vid, "OK", os.path.getsize(f"out/{vid}.mp4"))
    for vid in pending: note(vid, "TIMEOUT")

if STAGE == "omni":
    import threading
    def find_videos(o, acc):
        if isinstance(o, dict):
            if o.get("type") == "video" or str(o.get("mime_type", "")).startswith("video"): acc.append(o)
            for v in o.values(): find_videos(v, acc)
        elif isinstance(o, list):
            for v in o: find_videos(v, acc)
        return acc
    def one(v):
        try:
            prompt = "<FIRST_FRAME> Use the provided image as the exact first frame. " + v["prompt"] + " Keep her face, glasses, hair and blue tropical-leaf dress identical to the image. No text, no captions, no logos."
            body = {"model": plan.get("omni_model", "gemini-omni-1.1-flash"),
                    "input": [{"type": "image", "data": b64(f"in/{v['first']}"), "mime_type": mime(v["first"])}, {"type": "text", "text": prompt}],
                    "generation_config": {"video_config": {"task": "image_to_video"}},
                    "response_format": {"type": "video", "aspect_ratio": "9:16", "resolution": plan.get("omni_res", "1080p"), "delivery": "uri"}}
            st, r = req("POST", f"{B}/interactions", body, timeout=1500)
            if not isinstance(r, dict): note(v["id"], "FAIL", st, str(r)[:700]); return
            vids = find_videos(r, [])
            if not vids: note(v["id"], "NOVIDEO", st, json.dumps(r)[:900]); return
            x = vids[0]
            if x.get("data"): open(f"out/{v['id']}.mp4", "wb").write(base64.b64decode(x["data"]))
            else:
                uri = x.get("uri") or x.get("file_uri"); fid = uri.split("/files/")[-1].split(":")[0].split("?")[0]
                for _ in range(90):
                    st2, f = req("GET", f"{B}/files/{fid}")
                    if isinstance(f, dict) and f.get("state") == "ACTIVE": break
                    time.sleep(10)
                rr = urllib.request.Request(f"{B}/files/{fid}:download?alt=media", headers={"x-goog-api-key": K})
                open(f"out/{v['id']}.mp4", "wb").write(urllib.request.urlopen(rr, timeout=600).read())
            note(v["id"], "OK", os.path.getsize(f"out/{v['id']}.mp4"))
        except Exception as e: note(v["id"], "ERR", str(e)[:400])
    th = [threading.Thread(target=one, args=(v,)) for v in plan["videos"] if not ONLY or v["id"] in ONLY]
    for t in th: t.start(); time.sleep(2)
    for t in th: t.join()

open("out/log.txt", "w").write("\n".join(log))
os.makedirs("/tmp/enc", exist_ok=True)
if STAGE == "images":
    pngs = [f for f in os.listdir("out") if f.endswith(".png")]
    if pngs:
        sh("tar", "-cf", "/tmp/wf_out.tar", "-C", "out", *pngs)
        sh("openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-salt", "-pass", "env:GEMINI_API_KEY", "-in", "/tmp/wf_out.tar", "-out", "/tmp/enc/wf_out.tar.enc")
# ---- encrypt outputs for Claude
okey = os.urandom(32).hex().encode()
sh("tar", "-cf", "/tmp/out.tar", "-C", "out", ".")
sh("openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "10000", "-salt", "-pass", "stdin", "-in", "/tmp/out.tar", "-out", "/tmp/enc/out.tar.enc", inp=okey)
open("/tmp/enc/out.key.bin", "wb").write(sh("openssl", "pkeyutl", "-encrypt", "-pubin", "-inkey", f"{P}/claude_out.pub", "-pkeyopt", "rsa_padding_mode:oaep", inp=okey))
print("outputs encrypted", os.path.getsize("/tmp/enc/out.tar.enc"))
