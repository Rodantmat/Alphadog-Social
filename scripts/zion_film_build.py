#!/usr/bin/env python3
"""Build the complete Zion film from p1.mp4 p2.mp4 p3.mp4 (cwd) - usage: yt_film_build.py "t1,t2,t3" /path/to/footage_clone
Each part is kept for t seconds (0 = whole part). Video+audio re-encoded uniformly (1080p30, AAC 48k), subtitles and the ES/PT
dub tracks are cut and shifted with the same offsets, and chapter lines are merged into the description (out/)."""
import json, os, re, subprocess, sys
trims = [float(x) for x in sys.argv[1].split(",")]; FB = sys.argv[2]
def dur(p): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
D = [dur(f"p{i}.mp4") for i in (1, 2, 3)]
K = [t if t > 0 else (D[i] + t if t < 0 else D[i]) for i, t in enumerate(trims)]   # t<0: cut |t| seconds off the end          # kept length per part
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
EC = f"{FB}/zion-film-endcard-none.mp4"; ECD = 0.0
if os.path.exists(EC):   # film end card (logo + subscribe + video-element slot) replaces Part 3's podcast sign-off
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", EC, "-vf", "scale=1920:1080,fps=30,format=yuv420p,fade=t=in:st=0:d=0.4", "-af", "aresample=48000,aformat=channel_layouts=stereo",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "c4.mp4"], check=True)
    parts.append("c4.mp4"); ECD = dur("c4.mp4")
open("list.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", "-movflags", "+faststart", "film.mp4"], check=True)
print("film", dur("film.mp4"), "expected", sum(K))
assert abs(dur("film.mp4") - sum(K) - ECD) < 1.0
# subtitles
def ts(s):
    h, m, r = s.split(":"); sec, ms = r.split(","); return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000
def fmt(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000); return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
langs = ["en", "es", "pt"]
for L in langs:
    cues = []
    for i in range(3):
        src = f"{FB}/yellowstone-release/zion{i+1}/zion_ch{i+1}.{L}.srt"
        for blk in re.split(r"\n\s*\n", open(src, encoding="utf-8-sig").read().strip()):
            ln = blk.strip().splitlines()
            if len(ln) < 3 or "-->" not in ln[1]: continue
            a, b = [ts(x.strip()) for x in ln[1].split("-->")]
            if a >= K[i]: continue
            cues.append((a + OFF[i], min(b, K[i]) + OFF[i], "\n".join(ln[2:])))
    open(f"out/zion_film.{L}.srt", "w", encoding="utf-8").write("".join(f"{n+1}\n{fmt(a)} --> {fmt(b)}\n{t}\n\n" for n, (a, b, t) in enumerate(cues)))
    print("srt", L, len(cues))
# chapters from each part's description
def chap(i):
    out = []
    for ln in open(f"{FB}/yellowstone-release/zion{i+1}/desc_long.txt", encoding="utf-8"):
        m = re.match(r"^(\d+):(\d\d)\s+(.*)", ln.strip())
        if m:
            t = int(m.group(1)) * 60 + int(m.group(2))
            if t < K[i] - 5: out.append((t + OFF[i], m.group(3)))
    return out
def mmss(t): t = int(t); h, r = divmod(t, 3600); m, s = divmod(r, 60); return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
lines = []
for i, name in enumerate(["Part 1: What's Really Under Zion?", "Part 2: When the Cavalry Guarded the Geysers", "Part 3: 13 Days in Zion: The Nez Perce, 1877"]):
    for k, (t, title) in enumerate(chap(i)):
        lines.append(f"{mmss(t)} {name.split(':')[0]} · {title}" if k else f"{mmss(t)} {name}")
open("out/chapters.txt", "w", encoding="utf-8").write("\n".join(lines) + "\n")
print(open("out/chapters.txt").read())
json.dump({"durations": D, "kept": K, "offsets": OFF, "endcard": ECD}, open("out/film_cuts.json", "w"))
