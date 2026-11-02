#!/usr/bin/env python3
"""Build the complete Yellowstone film from p1.mp4 p2.mp4 p3.mp4 (cwd) - usage: yt_film_build.py "t1,t2,t3" /path/to/footage_clone
Each part is kept for t seconds (0 = whole part). Video+audio re-encoded uniformly (1080p30, AAC 48k), subtitles and the ES/PT
dub tracks are cut and shifted with the same offsets, and chapter lines are merged into the description (out/)."""
import json, os, re, subprocess, sys
trims = [float(x) for x in sys.argv[1].split(",")]; FB = sys.argv[2]
IDS = ["-vkXqMrSljM", "P99Gu3GCZVw", "jbZbPS173wc"]
def dur(p): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
D = [dur(f"p{i}.mp4") for i in (1, 2, 3)]
K = [t if t > 0 else D[i] for i, t in enumerate(trims)]          # kept length per part
OFF = [0, K[0], K[0] + K[1]]
print("durations", D, "kept", K, "offsets", OFF)
os.makedirs("out", exist_ok=True)
# video: each part cut + 0.4 s fade-out/in at the joins, then concatenated
parts = []
for i in range(3):
    o = f"c{i+1}.mp4"; k = K[i]
    vf = f"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p"
    if i < 2: vf += f",fade=t=out:st={k-0.4:.3f}:d=0.4"
    if i > 0: vf += ",fade=t=in:st=0:d=0.4"
    af = "aresample=48000,aformat=channel_layouts=stereo" + (f",afade=t=out:st={k-0.4:.3f}:d=0.4" if i < 2 else "") + (",afade=t=in:st=0:d=0.3" if i > 0 else "")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"p{i+1}.mp4", "-t", f"{k:.3f}", "-vf", vf, "-af", af, "-c:v", "libx264", "-preset", "medium",
                    "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", o], check=True)
    parts.append(o)
open("list.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", "-movflags", "+faststart", "film.mp4"], check=True)
print("film", dur("film.mp4"), "expected", sum(K))
assert abs(dur("film.mp4") - sum(K)) < 1.0
# subtitles
def ts(s):
    h, m, r = s.split(":"); sec, ms = r.split(","); return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000
def fmt(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000); return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
langs = ["en", "es", "fr", "pt", "zh-Hans", "ja"]
for L in langs:
    cues = []
    for i in range(3):
        src = f"{FB}/yellowstone-release/ch{i+1}/yellowstone_ch{i+1}.{L}.srt"
        for blk in re.split(r"\n\s*\n", open(src, encoding="utf-8-sig").read().strip()):
            ln = blk.strip().splitlines()
            if len(ln) < 3 or "-->" not in ln[1]: continue
            a, b = [ts(x.strip()) for x in ln[1].split("-->")]
            if a >= K[i]: continue
            cues.append((a + OFF[i], min(b, K[i]) + OFF[i], "\n".join(ln[2:])))
    open(f"out/yellowstone_film.{L}.srt", "w", encoding="utf-8").write("".join(f"{n+1}\n{fmt(a)} --> {fmt(b)}\n{t}\n\n" for n, (a, b, t) in enumerate(cues)))
    print("srt", L, len(cues))
# ES / PT dub tracks with the same cuts
for L in ("es", "pt"):
    ins = []; fc = []
    for i in range(3):
        ins += ["-i", f"{FB}/audio-tracks/{IDS[i]}_{L}.m4a"]
        fc.append(f"[{i}:a]atrim=0:{K[i]:.3f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,apad=whole_dur={K[i]:.3f}[a{i}]")
    fc.append("[a0][a1][a2]concat=n=3:v=0:a=1[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fc), "-map", "[a]", "-c:a", "aac", "-b:a", "192k", f"out/film_{L}.m4a"], check=True)
    print("dub", L, dur(f"out/film_{L}.m4a"))
# chapters from each part's description
def chap(i):
    out = []
    for ln in open(f"{FB}/yellowstone-release/ch{i+1}/desc_long.txt", encoding="utf-8"):
        m = re.match(r"^(\d+):(\d\d)\s+(.*)", ln.strip())
        if m:
            t = int(m.group(1)) * 60 + int(m.group(2))
            if t < K[i] - 5: out.append((t + OFF[i], m.group(3)))
    return out
def mmss(t): t = int(t); h, r = divmod(t, 3600); m, s = divmod(r, 60); return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
lines = []
for i, name in enumerate(["Part 1: What's Really Under Yellowstone?", "Part 2: When the Cavalry Guarded the Geysers", "Part 3: 13 Days in Yellowstone: The Nez Perce, 1877"]):
    for k, (t, title) in enumerate(chap(i)):
        lines.append(f"{mmss(t)} {name.split(':')[0]} · {title}" if k else f"{mmss(t)} {name}")
open("out/chapters.txt", "w", encoding="utf-8").write("\n".join(lines) + "\n")
print(open("out/chapters.txt").read())
json.dump({"durations": D, "kept": K, "offsets": OFF}, open("out/film_cuts.json", "w"))
