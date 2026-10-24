"""Post-review SAFE-window fixes (creator end cards, title overlays, pillarboxed inserts, a performer on camera, a hand in frame,
black tails). Windows verified frame by frame (0.5 s tiles) so no dissolve into an unwanted scene reaches the cut.
Applied to plan_v2.py after unpack on every runner job; each replacement must apply exactly once."""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/doc/chiricahua/plan_v2.py"
s = open(p).read()
R = [('"yt_GqV7LUmlgFY_346": [(0, 9.5)]', '"yt_GqV7LUmlgFY_346": [(0, 8.0)]'),
     ('"yt_HJlO513toNw_325": [(4.5, 10)]', '"yt_HJlO513toNw_325": [(5.1, 8.8)]'),
     ('"yt_kIWri-oJzhU_327": [(4, 7.5), (14, 20)]', '"yt_kIWri-oJzhU_327": [(3.2, 6.2), (14.7, 17.7)]'),
     ('"yt_kIWri-oJzhU_448": [(3.5, 7)]', '"yt_kIWri-oJzhU_448": [(3.5, 6.7)]'),
     ('"yt_kMpkSDLlztM_393": [(3.5, 9.5)]', '"yt_kMpkSDLlztM_393": [(4.0, 6.8), (8.0, 10.6)]'),
     ('"yt_m8GhYxt-kAg_2": [(3.5, 12)]', '"yt_m8GhYxt-kAg_2": [(7.6, 11.2)]'),
     ('"yt_m8GhYxt-kAg_84": [(6.5, 12.5), (16.5, 20)]',
      '"yt_m8GhYxt-kAg_84": [(0, 2.2), (8.6, 12.1), (17.9, 19.8)], "loc_d2671a6179_12": [(0, 23.0)], "pb_21555_0": [(0, 7.3)]'),
     ('S_["s029"] = AMB([Y("m8GhYxt-kAg", "1:30", 7), Y("m8GhYxt-kAg", "1:30", 17)], "wind")',
      'S_["s029"] = AMB([Y("GSyujZmmm8Q", "3:32", 2), Y("GSyujZmmm8Q", 108, 30)], "wind")'),
     ('S_["s025"] = AMB([Y("kMpkSDLlztM", "6:39", 2), Y("m8GhYxt-kAg", "1:30", 2)], "wind")',
      'S_["s025"] = AMB([Y("kMpkSDLlztM", "6:39", 2), Y("GSyujZmmm8Q", 108, 4), Y("m8GhYxt-kAg", "1:30", 2)], "wind")'),
     ('Y("2y-MR_Zd5B0", "1:11", 2, label="CCC crew, 1930s"), ', '')]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f"patch_plan: expected 1 match, found {n}: {a}")
    s = s.replace(a, b)
open(p, "w").write(s); print("patch_plan ok", len(R))
