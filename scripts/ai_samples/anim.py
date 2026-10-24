"""Animate AI stills for free on CPU: monocular depth (Depth-Anything-V2-Small, Apache-2.0) -> 2.5D parallax push-in,
or a plain Ken Burns move ("basic"). Usage: anim.py IMG OUT.mp4 MODE SECONDS   (MODE = parallax | kenburns)"""
import sys, subprocess, numpy as np, cv2
from PIL import Image

img_p, out, mode, secs = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
W, H, FPS = 1920, 1080, 30
M = 1.12                                                  # render margin so edges never show
src = cv2.cvtColor(np.array(Image.open(img_p).convert("RGB")), cv2.COLOR_RGB2BGR)
src = cv2.resize(src, (int(W * M), int(H * M)), interpolation=cv2.INTER_LANCZOS4)
sh, sw = src.shape[:2]
if mode == "parallax":
    from transformers import pipeline
    dep = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf")(Image.open(img_p).convert("RGB"))["depth"]
    d = cv2.resize(np.array(dep).astype(np.float32), (sw, sh), interpolation=cv2.INTER_CUBIC)
    d = (d - d.min()) / (np.ptp(d) + 1e-6)                # 1 = near
    d = cv2.GaussianBlur(d, (0, 0), 9)                    # soft depth = no tearing at edges
else:
    d = np.zeros((sh, sw), np.float32)
dd = cv2.resize(d, (W, H))
ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
cx, cy = W / 2, H / 2
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
N = int(secs * FPS)
for k in range(N):
    p = k / (N - 1); e = p * p * (3 - 2 * p)              # ease in/out
    if mode == "parallax":
        # far plane barely moves, near plane pushes in and drifts sideways: reads as a slow dolly through the scene
        z = 1.0 + (0.025 + 0.07 * dd) * e
        mx = cx + (xs - cx) / z + (sw - W) / 2 - 18 * e * dd
        my = cy + (ys - cy) / z + (sh - H) / 2 - 6 * e * dd
    else:
        z = 1.0 + 0.08 * e
        mx = cx + (xs - cx) / z + (sw - W) / 2 + 30 * (e - 0.5)
        my = cy + (ys - cy) / z + (sh - H) / 2
    fr = cv2.remap(src, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    a = min(1.0, k / 12, (N - 1 - k) / 12)                # short fade in/out
    ff.stdin.write((fr * a).astype(np.uint8).tobytes())
ff.stdin.close(); ff.wait(); print("CLIP", out)
