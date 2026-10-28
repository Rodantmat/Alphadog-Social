from PIL import Image, ImageDraw, ImageFont
import numpy as np
FONT="/tmp/claude-0/-home-claude/dec8b92c-7892-53c1-883c-b82ef908e078/scratchpad/fonts/Poppins-%s.ttf"
def cap_size(weight, cap):
    for s in range(40, 160):
        f = ImageFont.truetype(FONT % weight, s); b = f.getbbox("H")
        if b[3] - b[1] >= cap: return s
def line_width(text, font, track):
    w = 0
    for i, ch in enumerate(text):
        w += font.getlength(ch) + (track if i < len(text) - 1 else 0)
    return w
def draw_line(img_fill, img_stroke, x, ytop_cap, text, font, track, color, stroke):
    """ytop_cap = y of cap top. Draws char by char with tracking."""
    d1 = ImageDraw.Draw(img_fill); d2 = ImageDraw.Draw(img_stroke)
    off = font.getbbox("H")[1]
    cx = x - font.getbbox(text[0])[0]
    for ch in text:
        d2.text((cx, ytop_cap - off), ch, font=font, fill=255, stroke_width=stroke, stroke_fill=255)
        d1.text((cx, ytop_cap - off), ch, font=font, fill=color)
        cx += font.getlength(ch) + track
