import json, os, subprocess, sys, datetime
url, start, length, credit, tag = sys.argv[1:6]
os.makedirs("clips", exist_ok=True); raw = f"/tmp/{tag}_raw.mp4"; out = f"clips/{tag}.mp4"
if float(length) > 7: sys.exit("clip too long: keep under 7s (short, commentary-driven use only)")
subprocess.run(["yt-dlp", "-f", "mp4/best", "-o", raw, url], check=True)
subprocess.run(["ffmpeg", "-y", "-ss", start, "-t", length, "-i", raw, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart", "-map_metadata", "-1", out], check=True)
mf = "clips/manifest.json"; m = json.load(open(mf)) if os.path.exists(mf) else []
m.append({"tag": tag, "source_url": url, "credit": credit, "start": start, "length": length, "fetched": datetime.datetime.utcnow().isoformat() + "Z"})
json.dump(m, open(mf, "w"), indent=2)
