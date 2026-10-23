#!/usr/bin/env python3
"""Transcribe every .mp4 with an audio stream in DIR(s) -> <name>.transcript.json (segments start/end/text) and .txt."""
import json, os, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel
m = WhisperModel(os.environ.get("WHISPER_MODEL", "small.en"), device="cpu", compute_type="int8")
for D in sys.argv[1:]:
    for f in sorted(os.listdir(D)):
        if not f.endswith((".mp4", ".m4a", ".wav", ".mp3")): continue
        p = f"{D}/{f}"
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
        if len(raw) < 16000 * 4: continue
        audio = np.frombuffer(raw, np.float32)
        segs, info = m.transcribe(audio, vad_filter=True)
        out = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs]
        json.dump(out, open(f"{D}/{f[:-4]}.transcript.json", "w"), indent=1)
        open(f"{D}/{f[:-4]}.transcript.txt", "w").write("\n".join(f"[{s['start']:7.2f}-{s['end']:7.2f}] {s['text']}" for s in out))
        print("TRANSCRIBED", f, len(out), "segments", flush=True)
