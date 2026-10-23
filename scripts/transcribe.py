#!/usr/bin/env python3
"""Transcribe every .mp4 with an audio stream in DIR -> DIR/<name>.transcript.json (segments with start/end/text) and .txt."""
import json, os, subprocess, sys
from faster_whisper import WhisperModel
D = sys.argv[1]; m = WhisperModel(os.environ.get("WHISPER_MODEL", "small.en"), device="cpu", compute_type="int8")
for f in sorted(os.listdir(D)):
    if not f.endswith(".mp4"): continue
    p = f"{D}/{f}"
    has = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", p],
                         capture_output=True, text=True).stdout.strip()
    if not has: continue
    segs, info = m.transcribe(p, vad_filter=True, word_timestamps=False)
    out = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs]
    json.dump(out, open(f"{D}/{f[:-4]}.transcript.json", "w"), indent=1)
    open(f"{D}/{f[:-4]}.transcript.txt", "w").write("\n".join(f"[{s['start']:7.2f}-{s['end']:7.2f}] {s['text']}" for s in out))
    print("TRANSCRIBED", f, len(out), "segments", flush=True)
