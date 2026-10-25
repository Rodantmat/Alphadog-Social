"""Episode 1 AI story stills: job lists per passage for scripts/modal/modal_t2i.py (Qwen-Image).
One shared style + character sheet keeps faces/costumes consistent. Usage: gen_ep1_stills.py OUTDIR"""
import json, sys, os
OUT = sys.argv[1] if len(sys.argv) > 1 else "."; os.makedirs(OUT, exist_ok=True)
STY = ("2D animated true-crime documentary series still, clean cel shading, bold dark outlines, semi-realistic adult "
       "proportions, flat muted earthy colors, soft painted background, wide 16:9 cinematic")
LAND = "scattered Emory oaks, golden dry grass, grey rhyolite rock spires on the hills"
TEAM = ("the bearded teamster, a man in his forties with a full dark brown beard, a dusty brown wide-brim felt hat, "
        "a faded blue work shirt and brown suspenders")
RINGO = ("a lean man in his thirties with dark hair and a dark mustache, wearing a white long-sleeved shirt, a dark vest, "
         "dark trousers and a dusty brown wide-brim hat")
NEG = ("red rock, red sandstone, pine trees, snow, cactus, modern objects, text, watermark, photo, 3d render, anime, "
       "Disney, Pixar, cute, big eyes, deformed hands, extra fingers, extra limbs, extra legs, blurry")
GORE = "blood, gore, wound, corpse face"
def J(i, shot, scene, neg_extra="", seeds=(5, 23, 41)):
    return {"id": i, "seeds": list(seeds), "steps": 50, "cfg": 4.0,
            "prompt": f"{STY} {shot}. {scene}",
            "neg": ", ".join(x for x in (neg_extra, GORE, NEG) if x)}

A = [
 J("A06", "side view",
   f"Southern Arizona, July 1882, the afternoon before. Exactly two women ride side by side at a walk along a dirt track "
   f"from left to right: both wear long dark 1880s riding skirts, long-sleeved high-collared blouses and wide straw hats; "
   f"one rides a bay horse, the other a grey horse. They glance casually toward a huge old oak beside a rocky creek in the "
   f"middle distance, where a man sits against the trunk with his head bowed and hat tipped down, small in the frame, as if "
   f"napping. Peaceful, ordinary, {LAND}.",
   "third rider, men riding, cowboys, sidesaddle on the wrong side, extra horses, extra legs on horses"),
 J("A07", "medium-wide shot from behind",
   f"Southern Arizona, July 1882, late morning, eerie silence. {TEAM}, seen from behind, has left his mule and walks slowly "
   f"across flat grey stones of a shallow creek toward a huge old oak. Under the oak, {RINGO} sits motionless against the "
   f"trunk with his legs stretched out, head slumped forward, hat tipped down hiding his face; his feet are bare and wrapped "
   f"in strips of torn white cloth. Long shadows, dappled light, {LAND}. Only these two people.",
   "boots, shoes, third person, extra people, visible face of the seated man"),
 J("A08", "extreme close-up",
   "A man's limp right hand resting palm up on dry brown oak leaves and dirt, loosely holding an old 1870s single-action "
   "revolver with a worn wooden grip; the white shirt cuff at the wrist; dappled sunlight through oak leaves, very still. "
   "No face, only the hand, the gun and the ground.",
   "face, second hand, finger on trigger, aiming, pointing gun, modern pistol, oversized gun"),
 J("A09", "close-up",
   "Two bare human feet resting on dry oak leaves and dirt at the base of a thick oak trunk, each foot wrapped round and "
   "round in strips of torn white undershirt cloth, the hems of dark trousers above them; dappled sunlight, quiet and "
   "still. Only the feet and the trouser hems are in frame.",
   "boots, shoes, socks, sandals, extra feet, extra toes, face"),
 J("A10", "close-up at waist level",
   f"The waist of a man sitting against an oak trunk, wearing a white shirt and a dark vest: two leather cartridge belts are "
   f"buckled around his hips; the upper belt is worn normally, the lower belt is buckled on upside down, its brass buckle "
   f"inverted and its brass cartridges pointing downward out of their loops. Dappled sunlight, dry oak leaves. No face.",
   "face, hands holding the belt, extra belts, modern belt"),
]
B = [
 J("B01", "wide shot",
   "Apache Pass, southern Arizona, February 1861, cold clear winter light. A column of about a dozen US Army infantrymen in "
   "dark blue 1861 uniforms and forage caps rides mules in single file up a rocky mountain pass, a young officer in front and a "
   "small swallow-tailed guidon flag; oak and juniper, pale dry grass, grey rocks.",
   "cowboy hats, modern uniforms, tanks, cars, red rock"),
 J("B02", "wide shot",
   "Apache Pass, February 1861. A small US Army camp of white canvas wall tents at the mouth of a rocky pass, a few soldiers "
   "in dark blue uniforms and forage caps standing near the tents, a cook fire smoking; in the distance a small group of "
   "Chiricahua Apache men and women approach on foot across the pale grass. Oak and juniper, grey rocky hills.",
   "modern tents, cars, red rock"),
 J("B03", "interior medium shot",
   "Inside a white canvas army wall tent in 1861, daylight glowing through the canvas. A young clean-shaven lieutenant in a "
   "dark blue officer's frock coat with shoulder straps stands behind a small wooden camp table, pointing accusingly and "
   "speaking sharply. In the foreground, facing him with his back to the camera, stands a tall Chiricahua Apache leader with "
   "long black hair, a red cloth headband and a loose cotton shirt; only his back and shoulders are visible, never his face.",
   "Apache face visible, Apache facing the camera, feathered war bonnet, Plains headdress, extra people"),
 J("B04", "interior medium shot",
   "Inside the white canvas army tent, 1861. Two US soldiers in dark blue uniforms and forage caps step in through the tent "
   "flap holding rifles across their chests, blocking the only way out. In the foreground, a tall Apache leader with long black "
   "hair and a red cloth headband is seen from behind, his shoulders tensing; his face is never shown.",
   "Apache face visible, feathered war bonnet, Plains headdress"),
 J("B05", "close-up",
   "Inside a white canvas army tent, 1861: a steel knife blade held in a fist slices downward through the canvas side wall, "
   "and bright winter daylight bursts through the long cut. Only the hand, the knife and the canvas are in frame.",
   "face, blood, extra hands"),
 J("B06", "wide shot from behind",
   "Apache Pass, February 1861. Seen from behind, a tall Apache man with long black hair, a red cloth headband, a loose cotton "
   "shirt and knee-high moccasins sprints uphill away from white army tents into the rocky hills, a slit canvas tent behind "
   "him; far behind, small soldiers in dark blue run out and raise their rifles. His face is never shown.",
   "Apache face visible, feathered war bonnet, Plains headdress, horses"),
 J("B07", "medium shot",
   "Apache Pass, February 1861, overcast. A few Chiricahua Apache captives, a man and two women in cotton clothing and "
   "blankets, sit on the ground beside white army tents, heads lowered, while US soldiers in dark blue uniforms and forage "
   "caps stand guard over them with rifles. Somber, faces partly in shadow, no violence.",
   "feathered war bonnets, Plains headdress, blood, chains, modern clothes"),
 J("B08", "long shot",
   "Apache Pass, February 1861. Far away across the pale grass, a lone Apache man on foot approaches a small army camp of "
   "white tents, holding up a white cloth tied to a long pole as a flag of truce; soldiers in dark blue watch from the camp. "
   "The lone man is small and seen from behind, his face not visible.",
   "Apache face visible, feathered war bonnet, extra flags, American flag"),
 J("B09", "wide low-angle shot",
   "Apache Pass, February 1861. Dozens of mounted Chiricahua Apache warriors with long hair and headbands sit on their "
   "horses in a long line along a high rocky ridge above the pass, dark silhouettes against a pale winter sky; below, the "
   "tiny white tents of the army camp. Ominous and still.",
   "feathered war bonnets, Plains headdress, tipis, guns pointing at camera"),
]
C = [
 J("C01", "wide night shot",
   "Missouri, September 1886, night. An 1880s steam locomotive with a glowing headlamp and a tall smokestack pours smoke as "
   "it labors slowly up a steep wooded grade, pulling a line of dark wooden passenger cars with dim lamplit windows; "
   "moonlight, leafy dark forest on both sides.",
   "modern train, electric train, snow, desert"),
 J("C02", "night medium shot",
   "Missouri, September 1886, night. On the open platform between two moving wooden railroad passenger cars, an Apache man "
   "with long black hair, a cloth headband, a dark cotton shirt and trousers crouches low, gripping the iron railing, looking "
   "out into the dark woods rushing past; wind in his hair, smoke and sparks drifting, moonlight.",
   "modern train, soldiers on the platform, extra people"),
 J("C03", "night side shot",
   "Missouri, September 1886, night. An Apache man with long black hair and a headband leaps from the platform of a slowly "
   "moving 1880s passenger train toward the dark brush beside the tracks, body in mid-air, arms out; smoke and sparks from "
   "the locomotive, moonlight on the rails, dark leafy woods.",
   "modern train, extra people, falling under the wheels"),
 J("C04", "night wide shot",
   "Missouri, September 1886, night. The red tail lamp of a train fades into the distance along curving rails through dark "
   "woods, and in the foreground, beside the tracks, a lone Apache man with long black hair and a headband slowly rises from "
   "the tall weeds, watching it go; moonlight, drifting smoke.",
   "modern train, extra people"),
 J("C05", "night shot",
   "An Apache man with long black hair and a headband runs alone through dark Midwestern woods at night, moonlight falling "
   "in shafts through the leafy canopy, low mist between the trunks; seen from the side, moving fast and quietly.",
   "extra people, snow, desert"),
 J("C06", "very wide night shot",
   "A tiny lone figure of a man walks across wide open rolling plains under an immense night sky full of stars and the Milky "
   "Way; faint distant hills on the horizon; he is very small in the frame.",
   "extra people, city lights, cars, roads"),
 J("C07", "wide dawn shot from behind",
   "At dawn, a lone Apache man with long black hair and a headband stands on a rocky ridge, seen from behind, looking out at "
   "distant Southwestern desert mountains glowing orange and pink in the first light, juniper and grass at his feet. "
   "Tired but home.",
   "Apache face visible, extra people, city"),
]
D = [
 J("D01", "medium shot from behind",
   f"Southern Arizona, July 1882, hot still afternoon. {RINGO} sits alone on the shaded porch of a small plank-and-adobe "
   f"ranch house, seen from behind and slightly to the side, slumped in a wooden chair and drinking from a glass whiskey "
   f"bottle; a second empty bottle on the boards beside him; glaring sun on the dusty yard, {LAND}.",
   "extra people, cigarette, modern furniture"),
 J("D02", "long shot",
   f"Southern Arizona, July 1882, afternoon. On a dusty road through the grass, two riders meet and stop their horses facing "
   f"each other: a deputy with a tin star on his vest, and {RINGO}, who holds up two whiskey bottles from his saddlebag. Seen "
   f"from a distance, {LAND}.",
   "third rider, extra horses, extra legs on horses, guns drawn"),
 J("D03", "wide shot",
   f"Southern Arizona, July 13, 1882, late afternoon. Beside a small ranch house and a wooden corral, two ranch hands in work "
   f"clothes freeze and turn their heads toward the distant wooded hills, as if they have just heard a single far-off "
   f"gunshot; a horse in the corral lifts its head. Long shadows, {LAND}.",
   "gunfire visible, smoke, extra people"),
 J("D04", "wide shot",
   f"West Turkey Creek valley, southern Arizona, July 14, 1882, morning. A small group of five 1880s men in work clothes "
   f"and hats stand quietly in a loose half-circle near a huge old oak beside a shallow rocky creek, some holding their "
   f"hats in their hands, looking down toward the foot of the tree; horses and a wagon waiting on the road behind them. "
   f"Solemn, {LAND}.",
   "visible body, blood, extra crowds"),
 J("D05", "medium-wide shot",
   f"West Turkey Creek, July 14, 1882. {RINGO} sits dead still against the trunk of a huge oak, head slumped to one side, "
   f"hat fallen low, legs stretched out, his feet bare and wrapped in white cloth strips, a revolver in his right hand "
   f"resting on the ground; two men in work clothes stand a respectful distance away, looking at him. Seen from a "
   f"respectful distance, quiet dappled light, {LAND}.",
   "boots, shoes, visible face details, extra people"),
 J("D06", "close-up",
   "An old 1870s lever-action rifle leaning against the rough grey-brown bark of an oak trunk, dry oak leaves and dirt "
   "around its butt, dappled sunlight. Only the rifle and the tree.",
   "people, hands, modern rifle, scope"),
 J("D07", "close-up from the side",
   "The hip and thigh of a man sitting against an oak trunk in dark trousers and a white shirt: two leather cartridge belts "
   "lie across his hips, rows of brass cartridges glinting, the lower belt twisted upside down so its cartridges point "
   "downward; his limp right hand rests on the dry leaves nearby. Dappled light. No face.",
   "face, extra belts, modern belt"),
]
E = [
 J("E01", "wide night shot",
   "Galeyville, a rough mining camp in the Chiricahua Mountains of Arizona, May 1881, night. A dirt street of plank and "
   "canvas buildings with false fronts, warm lamplight spilling from a saloon doorway, horses tied at a hitching rail, dark "
   "wooded hills and stars above.",
   "modern buildings, cars, electric lights, snow"),
 J("E02", "interior medium shot",
   "Inside a lamplit 1881 frontier saloon of rough planks, night. A big drunk outlaw with curly dark hair and a heavy "
   "mustache, in a dark shirt and vest, shoves a lean man in a grey coat at the bar, jabbing a finger in his chest; the lean "
   "man steps back; a few onlookers lean away; bottles and glasses on the bar.",
   "guns drawn, blood, modern clothes, women"),
 J("E03", "interior medium shot",
   "Inside a lamplit 1881 frontier saloon, night. The lean man in a grey coat fires a revolver, a bright muzzle flash and a "
   "puff of white smoke, while the big curly-haired outlaw with the heavy mustache staggers backward against the bar, one "
   "hand clutching his jaw and neck; onlookers duck behind the bar. No blood visible.",
   "blood, gore, wound, modern clothes, extra guns"),
]
for name, lst in (("A2", A), ("B", B), ("C", C + E), ("D", D)):
    json.dump(lst, open(f"{OUT}/stills_{name}.json", "w"), indent=0)
    print(name, len(lst), "shots", sum(len(j["seeds"]) for j in lst), "images")
