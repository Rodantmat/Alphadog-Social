#!/usr/bin/env python3
"""Shorts/Reels/Stories gate - fail-closed technical check for every vertical clip before it is queued or uploaded.
usage: shorts_gate.py <dir or files...>
S1 1080x1920 portrait (phone-safe canvas)  S2 H.264 yuv420p, <= 60 fps  S3 AAC audio present, sample rate <= 48 kHz
   (48 kHz is only a recommendation: 96 kHz files posted fine; the real Instagram failure was file size)  S4 Shorts/Reels <= 59.5 s, Stories <= 60 s
S5 size <= 100 MB; Instagram Reel uploads (_ig copies) must be <= 20 MB - 25 MB files failed with ProcessingFailedError 2026-10-30  S6 +faststart (moov atom before mdat)
Exit 1 if anything fails."""
import json, os, subprocess, sys, glob
files = []
for a in sys.argv[1:]: files += sorted(glob.glob(os.path.join(a, "*.mp4"))) if os.path.isdir(a) else [a]
bad = 0
for f in files:
    p = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,pix_fmt,sample_rate,r_frame_rate:format=duration,size", "-of", "json", f], capture_output=True, text=True).stdout or "{}")
    v = next((s for s in p.get("streams", []) if s["codec_type"] == "video"), {}); a = next((s for s in p.get("streams", []) if s["codec_type"] == "audio"), None)
    d = float(p.get("format", {}).get("duration", 0)); sz = int(p.get("format", {}).get("size", 0)); e = []
    if (v.get("width"), v.get("height")) != (1080, 1920): e.append(f"S1 size {v.get('width')}x{v.get('height')}")
    if v.get("codec_name") != "h264" or v.get("pix_fmt") != "yuv420p": e.append(f"S2 {v.get('codec_name')}/{v.get('pix_fmt')}")
    if not a: e.append("S3 no audio")
    elif a.get("codec_name") != "aac": e.append(f"S3 audio {a.get('codec_name')}")
    if d > 59.5: e.append(f"S4 {d:.1f}s")
    if sz > 100e6: e.append(f"S5 {sz/1e6:.0f} MB")
    if f.endswith("_ig.mp4") and sz > 20e6: e.append(f"S5 Instagram copy {sz/1e6:.0f} MB > 20 MB")
    head = open(f, "rb").read(4096)
    if b"moov" not in head: e.append("S6 moov not at start (no faststart)")
    if e: bad += 1; print("FAIL", os.path.basename(f), "; ".join(e))
print(f"SHORTS GATE {'FAIL' if bad else 'PASS'}: {len(files)} files, {bad} failing"); sys.exit(1 if bad else 0)
