#!/usr/bin/env python3
"""Transcribe every audio/video file in DIR(s) -> <name>.transcript.json (segments start/end/text) and .txt.
English model by default; a folder whose name contains -es/-fr/-pt/-ja/-zh uses the multilingual model in that language."""
import json, os, re, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel
for D in sys.argv[1:]:
    m_ = re.search(r"-(es|fr|pt|ja|zh)\b", os.path.basename(D.rstrip("/")))
    lang = m_.group(1) if m_ else "en"
    m = WhisperModel(os.environ.get("WHISPER_MODEL", "small.en" if lang == "en" else "small"), device="cpu", compute_type="int8")
    for f in sorted(os.listdir(D)):
        if not f.endswith((".mp4", ".m4a", ".wav", ".mp3")): continue
        p = f"{D}/{f}"
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
        if len(raw) < 16000 * 4: continue
        audio = np.frombuffer(raw, np.float32)
        segs, info = m.transcribe(audio, vad_filter=True, language=lang)
        out = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs]
        json.dump(out, open(f"{D}/{f[:-4]}.transcript.json", "w"), indent=1)
        open(f"{D}/{f[:-4]}.transcript.txt", "w").write("\n".join(f"[{s['start']:7.2f}-{s['end']:7.2f}] {s['text']}" for s in out))
        print("TRANSCRIBED", f, len(out), "segments", flush=True)
