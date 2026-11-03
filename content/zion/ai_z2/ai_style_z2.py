"""Zion Part 2 AI story passages ("The Day the Mountain Fell"): house look (Qwen-Image still -> Wan2.2 TI2V-5B clip).
Only for moments no camera recorded. No likeness of named people (Underwood, Flanigan, Moore, Bradybaugh); people small,
generic, faces not detailed. Passages: S = Sentinel rock avalanche + lake (~4,800 years ago), H = lodge history 1917-1966,
R = 1995 Sentinel slide night, F = freeze-thaw crack.
usage: python3 ai_style_z2.py REPO_DIR -> content/zion/ai_z2/stills_v1.json"""
import json, os, sys
sys.path.insert(0, "/home/claude/doc/yellowstone")
from ai_style_ch1 import STY, NEG, J, VSTY, VNEG, NOSHAKE
MODERN = "buildings, houses, cars, roads, power lines, signs, people"
CANYON = ("Zion Canyon, Utah: a wide flat-floored canyon between towering sheer cliffs of red, orange and cream Navajo "
          "sandstone with diagonal cross-bedded layers and dark desert varnish streaks")
ANCIENT = f"{CANYON}, about five thousand years ago, wild and untouched, no trails, no roads, no people"
S = [
 J("S01", "very wide shot", f"{ANCIENT}. High on the west wall an enormous slab of the cliff face breaks away and begins to "
   "collapse, cracks racing across the rock, the first blocks falling, a plume of orange dust bursting out.", MODERN),
 J("S02", "wide side view across the canyon", f"{ANCIENT}. A colossal avalanche of shattered sandstone pours down the cliff and "
   "races across the canyon floor toward the opposite wall, a churning front of boulders and a huge rolling dust cloud.", MODERN),
 J("S03", "high wide shot", f"{ANCIENT}. A vast hummocky field of fresh rubble and giant boulders fills the canyon floor from "
   "wall to wall, dust still drifting in the air, the green river corridor buried.", MODERN),
 J("S04", "high wide shot looking up the canyon", f"{ANCIENT}. Behind a huge dam of rubble the river backs up: brown water "
   "spreads across the canyon floor, drowning cottonwoods, creeping up the base of the cliffs.", MODERN),
 J("S05", "very wide shot from above", f"{ANCIENT}. A long calm lake of deep blue-green water fills the canyon floor between "
   "the towering cliffs, the cliffs reflected in the still surface, a rubble dam at the far end.", MODERN),
 J("S06", "wide shot", f"{ANCIENT}. At the low point of the rubble dam the lake water spills over the crest and cuts a "
   "foaming brown channel down through the debris.", MODERN),
 J("S07", "high wide shot", f"{ANCIENT}. A shallow shrinking lake with broad flats of tan mud and sand spreading across it, "
   "green reeds and young cottonwoods growing on the new flat land, the river winding through.", MODERN),
 J("S08", "medium shot", f"{CANYON}, present day, bright sun. A geologist in a sun hat and field clothes, seen from behind, "
   "chisels a small sample from the top of a giant sandstone boulder, a field notebook and a rock hammer beside him.",
   "faces, crowd, cars"),
]
H = [
 J("H01", "wide shot", f"{CANYON}, summer 1917. On the canyon floor among cottonwoods a small row of white canvas tent cabins "
   "on wooden platforms, a dirt wagon road, a few small figures in 1910s clothes, faces not detailed.", "cars, modern buildings, paved road"),
 J("H02", "wide shot", "Southern Utah high desert, 1923: a black steam locomotive with passenger cars pulls into a small "
   "wooden railway station, red cliffs and juniper hills behind, a few small figures in 1920s clothes on the platform, "
   "faces not detailed.", "modern cars, modern buildings"),
 J("H03", "very wide shot", f"{CANYON}, 1920s. A single long steel cable runs from the top of a sheer 2,000-foot cliff down to "
   "the canyon floor; a bundle of sawn lumber slides down the wire high above the canyon, a small wooden frame structure "
   "on the cliff top.", "people close up, modern buildings"),
 J("H04", "wide shot", f"{CANYON} at night, winter 1966. A large rustic stone-and-timber lodge building is on fire, orange "
   "flames and sparks rising into the dark, smoke against the moonlit cliffs, small dark silhouettes watching from a "
   "distance, faces not visible.", "bodies, injured people, gore"),
 J("H05", "wide shot", f"{CANYON}, spring 1966. A work crew in hard hats raises a plain low boxy prefabricated building on "
   "a cleared site among cottonwoods, a small crane lifting a wall panel, stacked panels on the ground, faces not detailed.",
   "modern cars, smartphones"),
]
R = [
 J("R01", "wide shot", f"{CANYON} at night, April 1995. A two-lane road runs along the river at the foot of a steep slope of "
   "loose broken rock and soil; the slope has begun to slump, cracks opening in the road, moonlight, no people.", "people, cars"),
 J("R02", "wide shot", f"{CANYON} at night. Earth and rock slide down the slope into the river, blocking it, muddy water "
   "pooling and swirling behind the debris, the edge of the road breaking away.", "people, cars"),
 J("R03", "wide shot", f"{CANYON} at night. Floodlights on tall stands light a bulldozer and an excavator cutting a narrow "
   "rough track into the base of the canyon wall, dust in the white light, small workers in hard hats, faces not detailed.",
   "crowd"),
 J("R04", "medium shot", f"{CANYON}, daytime, overcast. Fast muddy brown floodwater tears at the edge of a paved road, chunks of "
   "asphalt breaking off and falling into the current.", "people, cars"),
]
F = [
 J("F01", "extreme close-up", "A narrow crack in a cliff of orange Navajo sandstone in Zion: water trickles into the crack, ice "
   "crystals form inside it, frost on the rock face, winter light.", "people"),
]
ALL = S + H + R + F
CLIPS = {
 "S01": (121, "Real-time: the cliff slab tilts and breaks apart, blocks falling away, orange dust billowing out. Slow push-in.", "people", True),
 "S02": (121, "Real-time: the avalanche of rock surges across the canyon floor, boulders tumbling, the dust cloud rolling and "
              "growing toward the camera.", "people", True),
 "S03": (97, "Real-time: dust drifts slowly over the still rubble field, settling, light shifting through the haze.", "people", False),
 "S04": (121, "Real-time: the brown water slowly spreads and rises across the canyon floor, ripples moving, trees sinking.", "people", False),
 "S05": (121, "Real-time: gentle ripples move across the calm lake, cloud shadows drift over the cliffs. Slow aerial drift.", "people", False),
 "S06": (97, "Real-time: the water pours over the crest and rushes down the new channel, foam and spray, the channel deepening.", "people", False),
 "S07": (121, "Real-time: the shallow water glints and slowly retreats, reeds sway in the wind, the river winds through the flats. "
              "Slow aerial drift.", "people", False),
 "S08": (97, "Real-time: the geologist taps the chisel with the hammer, small rock chips fly, he lifts the sample.", "", False),
 "H01": (97, "Real-time: the canvas tents ripple in the breeze, cottonwood leaves move, a small figure walks along the road.", "", False),
 "H02": (121, "Real-time: the steam locomotive slowly rolls into the station, steam and smoke billowing, the figures turn to watch.", "", False),
 "H03": (121, "Real-time: the bundle of lumber glides steadily down the long cable toward the canyon floor, the wire sagging slightly.", "", False),
 "H04": (121, "Real-time: the flames roar and leap from the lodge roof, sparks swirl up into the night, smoke drifts.", "people moving", False),
 "H05": (97, "Real-time: the crane slowly lifts the wall panel into place, workers guide it, dust drifts.", "", False),
 "R01": (97, "Real-time: the slope slowly creeps downhill, small rocks roll onto the road, a crack in the asphalt widens.", "", True),
 "R02": (121, "Real-time: soil and rocks slide into the river, the muddy water churns and backs up behind the debris.", "", True),
 "R03": (97, "Real-time: the excavator arm scoops and dumps rock, the bulldozer pushes forward, dust swirls in the floodlights.", "", False),
 "R04": (97, "Real-time: the fast muddy water rushes past, chunks of road edge crack and fall into the current.", "", True),
 "F01": (97, "Real-time: water trickles into the crack, frost spreads across the rock, ice crystals grow inside the crack.", "", False),
}
def clip_jobs(picks, seed=42, suffix=""):
    out = []
    for sid, still in picks.items():
        fr, mot, neg, shake = CLIPS[sid.rstrip("b")]
        out.append({"name": f"{sid}{suffix}", "image_url": f"https://raw.githubusercontent.com/Rodantmat/Alphadog-Social/main/{still}",
                    "w": 1280, "h": 704, "frames": fr, "steps": 40, "cfg": 5.0, "seed": seed,
                    "prompt": f"{VSTY} {mot}", "neg": ", ".join(x for x in (neg, VNEG + ("" if shake else NOSHAKE)) if x)})
    return out
if __name__ == "__main__":
    d = os.path.join(sys.argv[1], "content/zion/ai_z2"); os.makedirs(d, exist_ok=True)
    json.dump(ALL, open(f"{d}/stills_v1.json", "w"), indent=1); print(len(ALL), "shots", sum(len(j["seeds"]) for j in ALL), "images")
