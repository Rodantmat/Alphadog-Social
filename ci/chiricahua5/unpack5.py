"""Unpack ci/chiricahua5/pack*.txt ('#@@FILE <path>' text bundles) into DEST; every file must match manifest.json (sha1[:12])."""
import glob, hashlib, json, os, sys
here = os.path.dirname(os.path.abspath(__file__)); dest = sys.argv[1]; man = json.load(open(f"{here}/manifest.json")); got = {}
for pk in sorted(glob.glob(f"{here}/pack*.txt")):
    for part in open(pk, encoding="utf-8").read().split("#@@FILE ")[1:]:
        path, body = part.split("\n", 1); body = body[:-1]
        out = os.path.join(dest, path); os.makedirs(os.path.dirname(out), exist_ok=True)
        b = body.encode("utf-8"); open(out, "wb").write(b); got[path] = hashlib.sha1(b).hexdigest()[:12]
bad = sorted(p for p in man if got.get(p) != man[p]); extra = sorted(set(got) - set(man))
print("unpacked", len(got), "files; mismatched:", bad, "not in manifest:", extra)
sys.exit(1 if bad or extra else 0)
