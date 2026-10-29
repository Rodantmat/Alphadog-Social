"""Documentary render engine: shot plan -> 1920x1080 episode.
Shot types:
  video: {"type":"video","src":path,"ss":s,"dur":d,"speed":1.0,"drift":0.04,"fx":0.5,"fy":0.5}
  photo: {"type":"photo","src":path,"dur":d,"z0":1.0,"z1":1.12,"x0":.5,"y0":.5,"x1":.5,"y1":.45}
  card:  {"type":"card","dur":d,"title":"...","sub":"...","style":"chapter|date|title"}
  map:   {"type":"map","src":mp4} (pre-rendered)
Common: "label": lower-third text, "date": corner date stamp.
"""
import os, subprocess, json, math, hashlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

W, H, FPS = 1920, 1080, 30
FD = "/usr/share/fonts/opentype/inter/"
SERIF = None
for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"]:
    if os.path.exists(p): SERIF = p; break
def F(w, s):
    return ImageFont.truetype(FD + {"black": "InterDisplay-Black.otf", "bold": "Inter-Bold.otf", "semi": "Inter-SemiBold.otf",
                                    "med": "Inter-Medium.otf", "light": "Inter-Light.otf" if os.path.exists(FD + "Inter-Light.otf") else "Inter-Medium.otf"}[w], s)
def SF(s, bold=False):
    for p in (["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"] if bold else []) + [SERIF]:
        if p and os.path.exists(p): return ImageFont.truetype(p, s)
    return F("bold", s)

GRADE = "eq=contrast=1.06:saturation=1.05:gamma=0.98,vignette=PI/5"
CACHE = os.environ.get("ENGINE_CACHE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")); os.makedirs(CACHE, exist_ok=True)

def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode: raise RuntimeError(p.stderr[-1500:])

ENGINE_VER = 4   # v2 (2026-10-25): video shots resampled to FPS by timestamp before zoompan (speed + 24 fps sources were wrong)
                 # v3: slowed shots (0.8-1x) get blended in-between frames instead of duplicated ones (no pulldown judder)
def key(shot):
    k = dict(shot)
    if shot.get("type") == "video": k["_engine"] = ENGINE_VER
    if shot.get("type") == "multi": k["_engine_multi"] = 2      # v2: 9:16 panels (cached v1 renders were cropped to W/n)
    return hashlib.md5(json.dumps(k, sort_keys=True).encode()).hexdigest()[:12]

def overlay_png(shot):
    """Lower-third label and/or date stamp as transparent PNG (None if nothing)."""
    if not shot.get("label") and not shot.get("date"): return None
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if shot.get("date"):
        f = F("semi", 42); t = shot["date"].upper()
        tw = d.textlength(t, font=f)
        d.rectangle([90, 84, 90 + 7, 84 + 56], fill=(214, 160, 82, 255))
        d.text((112, 88), t, font=f, fill=(245, 238, 225, 255), stroke_width=2, stroke_fill=(0, 0, 0, 140))
    if shot.get("label"):
        f = F("med", 34); t = shot["label"]
        tw = d.textlength(t, font=f)
        x, y = 90, H - 130
        g = Image.new("RGBA", (int(tw + 60), 64), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        gd.rounded_rectangle([0, 0, g.width, g.height], 8, fill=(10, 10, 12, 150))
        im.alpha_composite(g, (x - 20, y - 10))
        d.text((x + 10, y), t, font=f, fill=(235, 230, 220, 255))
    p = f"{CACHE}/ov_{key({'l': shot.get('label'), 'd': shot.get('date')})}.png"; im.save(p); return p

def card_png(shot):
    im = Image.new("RGB", (W, H), (12, 11, 10)); d = ImageDraw.Draw(im)
    # subtle warm radial
    arr = np.zeros((H, W, 3), np.float32)
    yy, xx = np.mgrid[0:H, 0:W]; r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
    glow = np.clip(1 - r * 1.6, 0, 1)[..., None] * np.array([46, 34, 22], np.float32)
    im = Image.fromarray(np.clip(arr + 12 + glow, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    st = shot.get("style", "chapter")
    if st == "chapter":
        if shot.get("kicker"): d.text((W / 2, H / 2 - 120), shot["kicker"].upper(), font=F("semi", 30), fill=(214, 160, 82), anchor="mm")
        fs = 84
        while d.textlength(shot["title"], font=SF(fs, True)) > W - 240 and fs > 40: fs -= 4
        d.text((W / 2, H / 2 - 20), shot["title"], font=SF(fs, True), fill=(240, 232, 218), anchor="mm")
        d.line([(W / 2 - 60, H / 2 + 60), (W / 2 + 60, H / 2 + 60)], fill=(214, 160, 82), width=3)
        if shot.get("sub"): d.text((W / 2, H / 2 + 110), shot["sub"], font=F("med", 34), fill=(190, 182, 168), anchor="mm")
    elif st == "date":
        d.text((W / 2, H / 2), shot["title"], font=SF(96, True), fill=(240, 232, 218), anchor="mm")
        if shot.get("sub"): d.text((W / 2, H / 2 + 90), shot["sub"].upper(), font=F("semi", 30), fill=(214, 160, 82), anchor="mm")
    elif st == "title":
        d.text((W / 2, H / 2 - 30), shot["title"], font=SF(120, True), fill=(244, 236, 220), anchor="mm")
        if shot.get("sub"): d.text((W / 2, H / 2 + 80), shot["sub"], font=F("semi", 38), fill=(214, 160, 82), anchor="mm")
    p = f"{CACHE}/card_{key(shot)}.png"; im.save(p); return p

def render_shot(shot, out):
    dur = shot["dur"]; t = shot["type"]; frames = int(round(dur * FPS))
    ov = overlay_png(shot)
    fades = []
    if shot.get("fin"): fades.append(f"fade=t=in:st=0:d={shot['fin']}")
    if shot.get("fout"): fades.append(f"fade=t=out:st={max(0, dur - shot['fout']):.3f}:d={shot['fout']}")
    fade = ",".join(fades) if fades else None
    vf_tail = [GRADE, f"fps={FPS}", "format=yuv420p"]
    if t == "video":
        sp = shot.get("speed", 1.0); drift = shot.get("drift", 0.035)
        # cover-crop to 16:9 around focus, then slow push-in drift
        fx, fy = shot.get("fx", 0.5), shot.get("fy", 0.5)
        z = f"(1+{drift}*on/{max(frames,1)})"
        # zoompan (d=1) emits one frame per input frame, so frames must already sit on the output clock: setpts applies the
        # speed, fps= resamples to FPS by timestamp (24/25 fps sources play real-time, slowed shots really slow down)
        ex = shot.get("vf_extra") or (f"minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" if sp < 0.97 else
                                      f"minterpolate=fps={FPS}:mi_mode=blend" if sp < 0.999 else None)   # slow motion without pulldown judder
        if drift:
            vf = [f"setpts=PTS/{sp}"] + ([ex] if ex else []) + [f"fps={FPS}", "tpad=stop_mode=clone:stop_duration=60"] + [ f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase",
                  f"crop={W*2}:{H*2}:(in_w-{W*2})*{fx}:(in_h-{H*2})*{fy}",
                  f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}"] + vf_tail
        else:   # v4: no push-in (no zoompan rounding jitter); clip is used as filmed, cover-cropped once
            zm = float(shot.get("zoom", 1.0))   # static framing zoom (e.g. to cut a burned-in source stamp); never animated
            vf = [f"setpts=PTS/{sp}"] + ([ex] if ex else []) + [f"fps={FPS}", f"scale={int(W*zm)//2*2}:{int(H*zm)//2*2}:force_original_aspect_ratio=increase:flags=lanczos",
                  f"crop={W}:{H}:(in_w-{W})*{fx}:(in_h-{H})*{fy}", "tpad=stop_mode=clone:stop_duration=0.5"] + vf_tail   # frame-exact length (A/V sync); build2 guarantees footage, the analyzer flags any hold
        if fade: vf.append(fade)
        inp = ["-ss", str(shot.get("ss", 0)), "-t", str(dur * sp + 0.5), "-i", shot["src"]]
    elif t == "multi":
        srcs = shot["srcs"]; n = len(srcs); gap = 14; ph = H - 2 * gap
        pw = min((W - gap * (n + 1)) // n, int(ph * 9 / 16) // 2 * 2)        # never wider than a 9:16 panel -> no crop
        x0 = (W - (n * pw + (n - 1) * gap)) // 2
        inp = []; fc = []
        for k, x in enumerate(srcs):
            inp += ["-ss", str(x.get("ss", 0)), "-t", str(dur + 0.5), "-i", x["src"]]
            fc.append(f"[{k}:v]fps={FPS},scale={pw}:{ph}:force_original_aspect_ratio=increase:flags=lanczos,crop={pw}:{ph},setsar=1[p{k}]")
        fc.append(f"[0:v]fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:2,eq=brightness=-0.22:saturation=0.8[bg]")
        prev = "bg"
        for k in range(n):
            fc.append(f"[{prev}][p{k}]overlay={x0 + k * (pw + gap)}:{gap}:shortest=0[o{k}]"); prev = f"o{k}"
        fc.append(f"[{prev}]{','.join(vf_tail + ([fade] if fade else []))}[v]")
        cmd = ["ffmpeg", "-v", "error", "-y"] + inp + ["-filter_complex", ";".join(fc), "-map", "[v]", "-frames:v", str(frames), "-an",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-r", str(FPS), out]
        run(cmd); return out
    elif t == "photo":
        z0, z1 = shot.get("z0", 1.0), shot.get("z1", 1.12)
        x0, y0, x1, y1 = shot.get("x0", .5), shot.get("y0", .5), shot.get("x1", .5), shot.get("y1", .5)
        e = f"(on/{frames})"; ez = f"(0.5-0.5*cos(PI*{e}))"
        z = f"({z0}+({z1}-{z0})*{ez})"
        x = f"(({x0}+({x1}-{x0})*{ez})*iw-iw/zoom/2)"; y = f"(({y0}+({y1}-{y0})*{ez})*ih-ih/zoom/2)"
        bg = shot.get("bg", "cover")
        if bg == "cover":
            pre = f"scale={W*3}:{H*3}:force_original_aspect_ratio=increase,crop={W*3}:{H*3}"
        else:  # fit with blurred fill (for portraits / documents)
            pre = (f"split[a][b];[a]scale={W*3}:{H*3}:force_original_aspect_ratio=increase,crop={W*3}:{H*3},boxblur=40:2,eq=brightness=-0.15[bgx];"
                   f"[b]scale={W*3}:{H*3}:force_original_aspect_ratio=decrease[fg];[bgx][fg]overlay=(W-w)/2:(H-h)/2")
        vf = [pre, f"zoompan=z='{z}':x='max(0,min(iw-iw/zoom,{x}))':y='max(0,min(ih-ih/zoom,{y}))':d={frames}:s={W}x{H}:fps={FPS}"] + vf_tail
        if shot.get("sepia"): vf.insert(-2, "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131")
        if fade: vf.append(fade)
        inp = ["-loop", "1", "-t", str(dur + 0.2), "-i", shot["src"]]
    elif t == "card":
        png = card_png(shot)
        vf = [f"zoompan=z='1+0.03*on/{frames}':d={frames}:s={W}x{H}:fps={FPS}", "format=yuv420p",
              f"fade=t=in:st=0:d=0.6", f"fade=t=out:st={dur-0.6}:d=0.6"]
        inp = ["-loop", "1", "-t", str(dur + 0.2), "-i", png]
    elif t == "map":
        vf = ["tpad=stop_mode=clone:stop_duration=60", f"scale={W}:{H}", f"fps={FPS}", "format=yuv420p"] + ([fade] if fade else [])
        inp = (["-ss", str(shot["ss"])] if shot.get("ss") else []) + ["-i", shot["src"]]
    else:
        raise ValueError(t)
    chain = ",".join(vf)
    if ov:
        fc = f"[0:v]{chain}[v0];[v0][1:v]overlay=0:0:format=auto,format=yuv420p[v]"
        cmd = ["ffmpeg", "-v", "error", "-y"] + inp + ["-loop", "1", "-i", ov, "-filter_complex", fc, "-map", "[v]"]
    else:
        cmd = ["ffmpeg", "-v", "error", "-y"] + inp + ["-vf", chain]
    cmd += ["-frames:v", str(frames), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-r", str(FPS), out]
    run(cmd)
    return out

def render_all(shots, workdir):
    os.makedirs(workdir, exist_ok=True); files = []
    for i, s in enumerate(shots):
        f = f"{workdir}/{i:04d}_{key(s)}.mp4"
        if not os.path.exists(f):
            render_shot(s, f)
        files.append(f)
    lst = f"{workdir}/concat.txt"; open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
    return lst

def mix_audio(narr_wav, music, out, music_db=-20, duck=True):
    """music bed ducked under narration."""
    if music:
        fc = (f"[1:a]volume={10**(music_db/20):.3f},aloop=loop=-1:size=2e9[m];"
              f"[m][0:a]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[md];"
              f"[0:a][md]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5[a]")
        run(["ffmpeg", "-v", "error", "-y", "-i", narr_wav, "-i", music, "-filter_complex", fc, "-map", "[a]", "-ar", "48000", out])
    else:
        run(["ffmpeg", "-v", "error", "-y", "-i", narr_wav, "-af", "loudnorm=I=-16:TP=-1.5", "-ar", "48000", out])

def final(concat_list, audio, out):
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-i", audio,
         "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", "-map_metadata", "-1", out])
