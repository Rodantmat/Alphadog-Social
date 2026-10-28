#!/usr/bin/env python3
"""Convert a builder shot list (JSON list, e.g. doc/yellowstone/ch1/shots.json) to the auditor's .jsonl (one shot per line)
and annotate every source that exists locally with its display geometry and frame rate, so the render-stage auditor
(analyze.py F1/F3) can judge crops and frame-rate risk on a CI runner where the source files are not present:
    src_w, src_h   display size after rotation (what the renderer sees after auto-rotate)
    src_fps        average frame rate (avg_frame_rate); src_rfps = r_frame_rate; src_vfr = true when they differ > 0.5 fps
    src_still      true for image sources (jpg/png/webp/...)
For type 'multi' the same fields are written into every entry of 'srcs'.
usage: shots_jsonl.py shots.json out.jsonl
"""
import json, os, subprocess, sys

STILL = (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp", ".gif")


def probe(path):
    out = {}
    if not path or not os.path.exists(path): return out
    if path.lower().endswith(STILL): out["src_still"] = True
    try:
        pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                        "stream=width,height,r_frame_rate,avg_frame_rate:stream_side_data=rotation:stream_tags=rotate",
                                        "-of", "json", path], capture_output=True, text=True).stdout)
        s = pr["streams"][0]
    except Exception:
        return out
    w, h = int(s["width"]), int(s["height"])
    rot = 0
    for sd in s.get("side_data_list", []) or []:
        if "rotation" in sd: rot = int(float(sd["rotation"]))
    if (s.get("tags") or {}).get("rotate"): rot = int(s["tags"]["rotate"])
    if abs(rot) % 180 == 90: w, h = h, w
    out.update(src_w=w, src_h=h)
    if not out.get("src_still"):
        def fr(x):
            try: n, d = map(float, x.split("/")); return n / d if d else 0.0
            except Exception: return 0.0
        a, r = fr(s.get("avg_frame_rate", "0/0")), fr(s.get("r_frame_rate", "0/0"))
        if a: out["src_fps"] = round(a, 3)
        if r: out["src_rfps"] = round(r, 3)
        if a and r: out["src_vfr"] = abs(a - r) > 0.5
    return out


def main():
    src, dst = sys.argv[1], sys.argv[2]
    shots = json.load(open(src))
    if isinstance(shots, dict): shots = shots.get("shots", [])
    n = 0
    with open(dst, "w") as f:
        for s in shots:
            s = dict(s)
            if s.get("type") == "multi":
                s["srcs"] = [{**x, **probe(x.get("src"))} for x in s.get("srcs", [])]
            else:
                p = probe(s.get("src")); s.update(p); n += bool(p)
            f.write(json.dumps(s) + "\n")
    print(f"{len(shots)} shots -> {dst} ({n} sources probed)")


if __name__ == "__main__":
    main()
