"""Unpack ci/chiricahua/pack*.txt (text bundles: '#@@FILE <path>' headers) into DEST and verify every file against manifest.json."""
import glob, hashlib, json, os, sys
here = os.path.dirname(os.path.abspath(__file__)); dest = sys.argv[1]
man = json.load(open(f"{here}/manifest.json")); got = {}
for pk in sorted(glob.glob(f"{here}/pack*.txt")):
    parts = open(pk, encoding="utf-8").read().split("#@@FILE ")[1:]
    for part in parts:
        path, body = part.split("\n", 1); body = body[:-1]          # drop the separator newline
        out = os.path.join(dest, path); os.makedirs(os.path.dirname(out), exist_ok=True)
        b = body.encode("utf-8"); open(out, "wb").write(b); got[path] = hashlib.sha1(b).hexdigest()[:12]
bad = sorted(p for p in man if got.get(p) != man[p]); extra = sorted(set(got) - set(man))
print("unpacked", len(got), "files; mismatched:", bad, "missing-from-manifest:", extra)
sys.exit(1 if bad or extra else 0)
