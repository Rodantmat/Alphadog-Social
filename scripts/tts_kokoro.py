#!/usr/bin/env python3
"""Narrate segments with Kokoro TTS (Apache-2.0 open model).
Usage: tts_kokoro.py SEGMENTS_JSON OUTDIR VOICES SPEED
SEGMENTS_JSON: [{"id": "c0_01", "text": "..."}...]; VOICES: comma list (sample mode renders each segment with each voice).
Voice prefix picks the language: a=US English, b=UK English, e=Spanish, f=French, h=Hindi, i=Italian, j=Japanese, p=Portuguese (BR), z=Chinese.
Writes OUTDIR/<voice>/<id>.wav (24 kHz) and timing.json with durations."""
import json, os, sys, time
import numpy as np, soundfile as sf
from kokoro import KPipeline

segs = json.load(open(sys.argv[1])); out = sys.argv[2]; voices = sys.argv[3].split(","); speed = float(sys.argv[4])
timing = {}
for v in voices:
    lang = v[0] if v[0] in "abefhijpz" else "a"
    pipe = KPipeline(lang_code=lang)
    os.makedirs(f"{out}/{v}", exist_ok=True); timing[v] = {}
    for s in segs:
        t0 = time.time(); chunks = []
        for _, _, audio in pipe(s["text"], voice=v, speed=speed, split_pattern=r"\n+"):
            a = audio.numpy() if hasattr(audio, "numpy") else np.asarray(audio)
            chunks.append(a); chunks.append(np.zeros(int(24000 * 0.35), dtype=np.float32))
        wav = np.concatenate(chunks) if chunks else np.zeros(2400, dtype=np.float32)
        sf.write(f"{out}/{v}/{s['id']}.wav", wav, 24000)
        timing[v][s["id"]] = round(len(wav) / 24000, 3)
        print(v, s["id"], timing[v][s["id"]], "s", round(time.time() - t0, 1), "s render", flush=True)
json.dump(timing, open(f"{out}/timing.json", "w"), indent=1)
