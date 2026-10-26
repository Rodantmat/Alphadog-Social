#!/usr/bin/env python3
"""Private memorial generation on GitHub Actions (public repo, so everything private is encrypted).
modes:
  keys    make the workflow's RSA keypair; private half encrypted with GEMINI_API_KEY -> content/private/memorial_wf.{pub,key.enc}
  gen     decrypt content/private/memorial_in.{tar.enc,key.enc}; run plan.json stage (STAGE=list|images|videos);
          encrypt ./out for Claude's public key (content/private/claude_out.pub) -> /tmp/enc/out.{tar.enc,key.enc}
Never prints the API key. Gemini: image model for keyframes (her photos as identity references + the original frame as layout),
Veo for image-to-video (first frame, optional last frame)."""
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

# ---- gen: decrypt inputs
sh("openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-a", "-pass", "env:GEMINI_API_KEY", "-in", f"{P}/memorial_wf.key.enc", "-out", "/tmp/wf.key")
akey = sh("openssl", "pkeyutl", "-decrypt", "-inkey", "/tmp/wf.key", "-pkeyopt", "rsa_padding_mode:oaep", "-in", f"{P}/memorial_in.key.bin")
os.makedirs("in", exist_ok=True)
sh("openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "10000", "-pass", "stdin", "-in", f"{P}/memorial_in.tar.enc", "-out", "/tmp/in.tar", inp=akey)
sh("tar", "-xf", "/tmp/in.tar", "-C", "in"); os.remove("/tmp/in.tar"); os.remove("/tmp/wf.key")
plan = json.load(open("in/plan.json")); STAGE = os.environ.get("STAGE", "list"); ONLY = [x for x in os.environ.get("ONLY", "").split(",") if x]
os.makedirs("out", exist_ok=True); log = []
def note(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.append(s)

if STAGE == "list":
    st, r = req("GET", f"{B}/models?pageSize=200")
    for m in (r.get("models", []) if isinstance(r, dict) else []):
        n = m["name"]
        if any(k in n for k in ("image", "veo", "imagen")): note(n, m.get("supportedGenerationMethods"))
    if not isinstance(r, dict): note("list failed", st, r)

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
        st, r = req("POST", f"{B}/models/{plan['video_model']}:predictLongRunning", {"instances": [inst], "parameters": params})
        if st != 200 and "resolution" in str(r):
            params["resolution"] = "720p"; st, r = req("POST", f"{B}/models/{plan['video_model']}:predictLongRunning", {"instances": [inst], "parameters": params})
        if st != 200 and "personGeneration" in str(r):
            params.pop("personGeneration"); st, r = req("POST", f"{B}/models/{plan['video_model']}:predictLongRunning", {"instances": [inst], "parameters": params})
        if isinstance(r, dict) and r.get("name"): ops.append((v["id"], r["name"])); note(v["id"], "started", params["resolution"])
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
            uri = samples[0]["video"]["uri"]
            rr = urllib.request.Request(uri, headers={"x-goog-api-key": K})
            open(f"out/{vid}.mp4", "wb").write(urllib.request.urlopen(rr, timeout=600).read()); note(vid, "OK", os.path.getsize(f"out/{vid}.mp4"))
    for vid in pending: note(vid, "TIMEOUT")

open("out/log.txt", "w").write("\n".join(log))
# ---- encrypt outputs for Claude
os.makedirs("/tmp/enc", exist_ok=True); okey = os.urandom(32).hex().encode()
sh("tar", "-cf", "/tmp/out.tar", "-C", "out", ".")
sh("openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "10000", "-salt", "-pass", "stdin", "-in", "/tmp/out.tar", "-out", "/tmp/enc/out.tar.enc", inp=okey)
open("/tmp/enc/out.key.bin", "wb").write(sh("openssl", "pkeyutl", "-encrypt", "-pubin", "-inkey", f"{P}/claude_out.pub", "-pkeyopt", "rsa_padding_mode:oaep", inp=okey))
print("outputs encrypted", os.path.getsize("/tmp/enc/out.tar.enc"))
