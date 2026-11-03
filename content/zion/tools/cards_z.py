"""Zion title + end cards, same design as the Yellowstone series (cards23.py), plain warm background (no Yellowstone hillshade).
usage: python3 cards_z.py {p1|p2|p3} {all|title|end|stills}"""
import sys
sys.path.insert(0, "/home/claude/doc/yellowstone/graphics/src")
import cards
cards.HS = "/nonexistent"
from cards23 import title_still, end_still
from cards import push_render
OUT = "/home/claude/doc/zion/graphics"
CFG = {
 "p1": dict(title=("ZION, PART 1", "ZION'S DEADLIEST DAY", "WATER · ROCK · HEIGHT"),
            end=("NEXT  ·  PART 2", "Zion: The Day", "the Mountain Fell", "Subscribe for Part 2", "NEXT"), end_dur=12.0,
            slot_img="/home/claude/doc/zion/media/pd_ch1/img/own_al_1109144848.jpg"),
 "p2": dict(title=("ZION, PART 2", "THE DAY THE MOUNTAIN FELL", "ROCK · LAKE · LODGE"),
            end=("NEXT  ·  PART 3", "Zion: The", "Impossible Tunnel", "Subscribe for Part 3", "NEXT"), end_dur=12.0,
            slot_img="/home/claude/doc/zion/media/pd_ch2/img/z2_usgs_down_canyon_1925.jpg"),
}
if __name__ == "__main__":
    p = sys.argv[1]; what = sys.argv[2] if len(sys.argv) > 2 else "all"; c = CFG[p]; n = p[1]
    if what == "stills":
        title_still(*c["title"]).convert("RGB").reduce(2).save(f"{OUT}/{p}_title.jpg"); end_still(*c["end"]).convert("RGB").reduce(2).save(f"{OUT}/{p}_end.jpg"); sys.exit()
    if what in ("all", "title"): push_render(title_still(*c["title"]), 4.5, f"{OUT}/yc{n}_title_card.mp4")
    if what in ("all", "end"):
        from PIL import Image, ImageOps
        im = end_still(*c["end"]).convert("RGB"); sc = im.width / 1920                     # end card is rendered at 2x
        x0, y0, x1, y1 = [int(v * sc) for v in cards.SLOT]
        if c.get("slot_img"):   # QA F6: the next-video slot is never an empty box -> a frame from the next part's footage
            ph = ImageOps.fit(Image.open(c["slot_img"]).convert("RGB"), (x1 - x0, y1 - y0), Image.LANCZOS); im.paste(ph, (x0, y0))
        push_render(im, c["end_dur"], f"{OUT}/yc{n}_end_card.mp4", z1=1.0, fin=0.6, fout=0.0)
