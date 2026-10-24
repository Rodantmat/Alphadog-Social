"""Keyframe stills for Episode 1's AI scenes, in the look the owner picked (the 'toon' stills that animated best on Modal).
Free: SDXL base + SDXL-Lightning 4-step (OpenRAIL++) on a CPU GitHub runner. Each still is the FIRST frame of a clip, so
it shows the start of the action in the right place (Chiricahua look: oak, golden grass, grey rock spires - no snow, no
pines, no red rock). SDXL reads only ~75 tokens: the style goes first, then a short beat.
Usage: keys.py OUTDIR PART NPARTS [SEQ_JSON]   (shots x seeds are split across parallel runners)"""
import os, sys, time, torch
from diffusers import StableDiffusionXLPipeline, UNet2DConditionModel, EulerDiscreteScheduler
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file

STY = ("2D animated true-crime series still, clean cel shading, bold dark outlines, semi-realistic proportions, "
       "flat muted colors, soft painted background")
LAND = "oak woodland, golden dry grass, grey rock spires, southern Arizona"
KEYS = {
    "s001_teamster": f"side view, bearded 1880s teamster walking beside two mules pulling a wagon of firewood up a dirt road, {LAND}",
    "s001_teamster_close": "close-up of a bearded 1880s teamster in a dusty felt hat and blue shirt, squinting ahead, oak trees and wagon behind",
    "s002_oak_wide": f"seen from across a rocky creek, a man in white shirt and dark vest slumped asleep against a huge oak, hat over his face, {LAND}",
    "s002_riders": f"side view, two women in long 1880s riding skirts and straw hats riding a bay horse and a grey horse on a dirt track, {LAND}",
    "s004_hand_gun": "close-up of a limp hand on dry oak leaves holding an old 1870s Colt revolver, dappled sunlight, no face",
    "s004_belt_feet": "close-up of two bare feet wrapped in white cloth strips, beside a leather cartridge belt, dry oak leaves, dappled light",
    "s024_tent": "inside an 1861 army canvas tent, young cavalry lieutenant in blue coat pointing angrily at a tall Apache leader seen from behind",
    "s025_cut_wall": "inside a canvas army tent, a knife blade slicing through the tent wall, bright daylight through the cut, 1861",
    "s025_escape": f"seen from behind, an Apache man in a calico shirt and headband running uphill away from army tents, {LAND}",
    "s030_stronghold": "two riders from behind, a scout in buckskin and a one-armed army general, entering a canyon of huge round granite boulders",
    "s039_train": "night, 1880s steam locomotive with glowing headlamp and smoke pulling wooden passenger cars up a wooded hill, moonlight",
    "s039_leap": "night, a man in a headband leaping from the platform of a slow 1880s train into dark brush, smoke, moonlight",
    "s042_posse": "dawn, five riders in long dusters and wide hats crossing a rocky juniper ridge in single file, silhouettes, pale sky",
    "s048_saloon": "night, lamplit 1880s mining camp saloon front on a dirt street, two men arguing in the doorway, horse at hitching rail",
    "s051_treasure": "dusk, rotted leather saddlebag half buried in sand in a canyon wash, spilling old silver and gold coins, grey rocks",
    "s053_deputy": f"distant view, a deputy on horseback stopping a lone rider with whiskey bottles in his saddlebag on a dusty road, {LAND}",
    "s059_tracker": f"seen from behind, a lone rider in a fringed buckskin jacket on a dun horse looking down at hoofprints on a trail, {LAND}",
    "s067_ccc": "1930s young work crew in denim, some barefoot, swinging picks building a stone trail among tall grey rock pinnacles",
}
SEEDS = (5, 23, 41, 77)

out, part, nparts = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); os.makedirs(out, exist_ok=True)
if len(sys.argv) > 4:   # story sequences file (A01..E03): replaces the single-beat list
    import json
    seq = json.load(open(sys.argv[4]))
    KEYS = {sid: beat.replace("{LAND}", LAND) for k, v in seq.items() if not k.startswith("_") for sid, beat in v["shots"]}
    SEEDS = (5, 23, 41)
jobs = [(n, s) for n in KEYS for s in SEEDS][part::nparts]
torch.set_num_threads(os.cpu_count())
base = "stabilityai/stable-diffusion-xl-base-1.0"
unet = UNet2DConditionModel.from_config(base, subfolder="unet").to(torch.float32)
unet.load_state_dict(load_file(hf_hub_download("ByteDance/SDXL-Lightning", "sdxl_lightning_4step_unet.safetensors")))
pipe = StableDiffusionXLPipeline.from_pretrained(base, unet=unet, torch_dtype=torch.float32, variant="fp16")
pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config, timestep_spacing="trailing")
pipe.set_progress_bar_config(disable=True)
for name, seed in jobs:
    t = time.time()
    img = pipe(f"{STY}, {KEYS[name]}", num_inference_steps=4, guidance_scale=0, width=1344, height=768,
               generator=torch.Generator().manual_seed(seed)).images[0]
    img.save(f"{out}/key_{name}_{seed}.jpg", quality=92); print("IMG", name, seed, round(time.time() - t), "s", flush=True)
