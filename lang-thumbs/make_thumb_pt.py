import sys; sys.path.insert(0, '/tmp/claude-0/-home-claude/dec8b92c-7892-53c1-883c-b82ef908e078/scratchpad')
from thumbtext import *
import numpy as np, cv2
D = '/home/claude/doc/chiricahua/'
es = np.array(Image.open(D + 'thumb_B_es.jpg').convert('RGB'))
en = np.array(Image.open(D + 'thumbs_v3/thumb_B.png').convert('RGB'))
WHITE, YEL = (255, 255, 255), (255, 214, 74)
def mask_for(lines, cap, tops, x=51, wt='ExtraBold', track=-2, stroke=10, grow=6):
    s = cap_size(wt, cap); f = ImageFont.truetype(FONT % wt, s)
    fill = Image.new('RGB', (1280, 720)); st = Image.new('L', (1280, 720))
    for t, y in zip(lines, tops): draw_line(fill, st, x, y, t, f, track, (255, 255, 255), stroke)
    m = np.array(st) > 0
    return cv2.dilate(m.astype(np.uint8), np.ones((2 * grow + 1, 2 * grow + 1), np.uint8)) > 0
m_es = mask_for(["SU HISTORIA", "ES MÁS OSCURA", "QUE SUS", "ROCAS"], 64, [82, 171, 260, 349], grow=10)
m_en = mask_for(["ITS HISTORY", "IS DARKER", "THAN ITS", "ROCKS"], 75, [85, 191, 297, 403], x=52, grow=10)
# sanity: how much text-colored pixel falls outside the masks?
def texty(a): return (a.min(2) > 235) | ((a[..., 0] > 230) & (abs(a[..., 1].astype(int) - 214) < 25) & (a[..., 2] < 120))
print('es text px outside mask:', int((texty(es) & ~m_es)[:, :800].sum()), ' en:', int((texty(en) & ~m_en)[:, :800].sum()))
bg = es.copy()
use_en = m_es & ~m_en; bg[use_en] = en[use_en]
hole = (m_es & m_en).astype(np.uint8) * 255
print('hole px', int((hole > 0).sum()))
T = cv2.inpaint(bg, hole, 9, cv2.INPAINT_TELEA).astype(np.float32)
valid = (hole == 0)
bf = bg.astype(np.float32)
skyv = valid & (bf[..., 2] > bf[..., 0] + 60) & (bf[..., 2] > 150)
skyv[:, 800:] = False
yy, xx = np.mgrid[0:720, 0:1280].astype(np.float32) / 720
def P(x, y): return np.stack([np.ones_like(x), x, y, x * x, y * y, x * y, y ** 3], -1)
W, *_ = np.linalg.lstsq(P(xx[skyv], yy[skyv]), bf[skyv], rcond=None)
SKY = P(xx, yy) @ W
print('sky model resid', float(np.abs(SKY[skyv] - bf[skyv]).mean()))
issky = (T[..., 2] > T[..., 0] + 25).astype(np.float32)
issky[:182, :700] = 1
issky = cv2.GaussianBlur(issky, (0, 0), 3)[..., None]
F = issky * SKY + (1 - issky) * T
rng = np.random.default_rng(7); F = F + rng.normal(0, 1.5, F.shape)
h = (hole > 0)[..., None]
bg = np.where(h, np.clip(F, 0, 255), bg).astype(np.uint8)
Image.fromarray(bg).save(sys.argv[1] if len(sys.argv) > 1 else 'bg_clean.png')
# Portuguese text, same layout: cap 64, pitch 89, x=51, longest line fitted to <= 778 px
lines = [("A HISTÓRIA", WHITE), ("É MAIS SOMBRIA", YEL), ("QUE SUAS", WHITE), ("ROCHAS", YEL)]
cap = 64
while True:
    s = cap_size('ExtraBold', cap); f = ImageFont.truetype(FONT % 'ExtraBold', s)
    wmax = max(line_width(t, f, -2) for t, _ in lines)
    if wmax <= 735 or cap <= 56: break
    cap -= 1
print('cap', cap, 'size', s, 'widest', round(wmax))
pitch = 89 * cap / 64; top0 = 82 + (64 - cap) * 2
fillc = Image.new('RGBA', (1280, 720), (0, 0, 0, 0)); st = Image.new('L', (1280, 720))
for i, (t, c) in enumerate(lines):
    draw_line(fillc, st, 51, round(top0 + i * pitch), t, f, -2, c + (255,), 10)
out = Image.fromarray(bg).convert('RGBA')
black = Image.new('RGBA', (1280, 720), (8, 8, 8, 255))
st_soft = st.filter(__import__('PIL.ImageFilter', fromlist=['x']).GaussianBlur(0.8))
out = Image.composite(black, out, st_soft)
out.alpha_composite(fillc)
out.convert('RGB').save(D + 'thumb_B_pt.jpg', quality=92, optimize=True)
print('saved')
