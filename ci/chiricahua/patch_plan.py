"""Post-review SAFE-window fixes (creator end cards, title overlays, pillarboxed inserts, a performer on camera, black tails).
Applied to plan_v2.py after unpack on every runner job; each replacement must apply exactly once."""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/doc/chiricahua/plan_v2.py"
s = open(p).read()
R = [('"yt_GqV7LUmlgFY_346": [(0, 9.5)]', '"yt_GqV7LUmlgFY_346": [(0, 8.5)]'),
     ('"yt_HJlO513toNw_325": [(4.5, 10)]', '"yt_HJlO513toNw_325": [(5.7, 9.3)]'),
     ('"yt_kIWri-oJzhU_327": [(4, 7.5), (14, 20)]', '"yt_kIWri-oJzhU_327": [(3.7, 6.6), (14.7, 18.4)]'),
     ('"yt_kIWri-oJzhU_448": [(3.5, 7)]', '"yt_kIWri-oJzhU_448": [(3.6, 7.4)]'),
     ('"yt_m8GhYxt-kAg_2": [(3.5, 12)]', '"yt_m8GhYxt-kAg_2": [(6.4, 10.8)]'),
     ('"yt_m8GhYxt-kAg_84": [(6.5, 12.5), (16.5, 20)]',
      '"yt_m8GhYxt-kAg_84": [(8.6, 12.6)], "yt_2y-MR_Zd5B0_65": [(5.2, 9.8)], "loc_d2671a6179_12": [(0, 23.0)], "pb_21555_0": [(0, 7.3)]'),
     ('S_["s029"] = AMB([Y("m8GhYxt-kAg", "1:30", 7), Y("m8GhYxt-kAg", "1:30", 17)], "wind")',
      'S_["s029"] = AMB([Y("GSyujZmmm8Q", "3:32", 2), Y("m8GhYxt-kAg", "1:30", 7)], "wind")')]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f"patch_plan: expected 1 match, found {n}: {a}")
    s = s.replace(a, b)
open(p, "w").write(s); print("patch_plan ok", len(R))
