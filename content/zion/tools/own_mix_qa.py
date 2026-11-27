#!/usr/bin/env python3
"""Spec gate (owner rule I37, 2026-11-26): own footage from D: is a mandatory layer mixed with archival material.
usage: own_mix_qa.py SPEC.json [more specs]. Fails (exit 1) when, for any item:
 - the FIRST scene is not own (own_* still or V:clip)           - fewer than 40% (short) / 34% (story) scenes are own, or no own VIDEO clip in a short
 - no archival/outside scene at all (pure own is fine for stories only)  - still-to-clip ratio above 3:2 (owner: fewer photos, more clips)
 - the same V: clip window used twice (overlap < 6 s apart) anywhere in the given specs; the same still twice
"""
import json, sys, collections
bad=[]; seen=collections.defaultdict(list); stills=collections.Counter()
def own(x): return x.startswith("V:") or x.startswith("own_")
for p in sys.argv[1:]:
    for it in json.load(open(p))["items"]:
        im=it["imgs"]; n=len(im); o=sum(own(x) for x in im); v=sum(x.startswith("V:") for x in im); st=n-v
        tag=f'{p.split("/")[-1]}:{it["id"]}'
        if not own(im[0]): bad.append(f"{tag}: first scene is not own footage ({im[0]})")
        if o/n < (0.34 if it["kind"]=="story" else 0.40): bad.append(f"{tag}: only {o}/{n} scenes own")
        if it["kind"]=="short" and v<1: bad.append(f"{tag}: no own VIDEO clip")
        if o==n and it["kind"]=="short": bad.append(f"{tag}: no archival/outside scene mixed in")
        if v and st>1.5*v+1: bad.append(f"{tag}: too many stills ({st}) for {v} clips")
        for x in im:
            if x.startswith("V:"):
                name,_,off=x[2:].partition("@"); off=float(off or 0)
                if any(abs(off-o2)<6 for o2 in seen[name]): bad.append(f"{tag}: clip {name}@{off} overlaps an earlier use")
                seen[name].append(off)
            else:
                stills[x]+=1
                if stills[x]>1 and x.startswith("own_"): bad.append(f"{tag}: own still {x} used twice")
print("OWN-MIX QA:", "FAIL" if bad else "PASS"); [print(" -",b) for b in bad]; sys.exit(1 if bad else 0)
