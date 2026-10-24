"""Free AI stills on a CPU GitHub runner: SDXL base + SDXL-Lightning 4-step UNet (both OpenRAIL++, commercial use allowed).
Usage: gen.py STYLE OUTDIR   (STYLE = real | paint)"""
import os, sys, time, torch
from diffusers import StableDiffusionXLPipeline, UNet2DConditionModel, EulerDiscreteScheduler
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file

style, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
torch.set_num_threads(os.cpu_count())
base = "stabilityai/stable-diffusion-xl-base-1.0"
unet = UNet2DConditionModel.from_config(base, subfolder="unet").to(torch.float32)
unet.load_state_dict(load_file(hf_hub_download("ByteDance/SDXL-Lightning", "sdxl_lightning_4step_unet.safetensors")))
pipe = StableDiffusionXLPipeline.from_pretrained(base, unet=unet, torch_dtype=torch.float32, variant="fp16")
pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config, timestep_spacing="trailing")
pipe.set_progress_bar_config(disable=True)

PLACE = ("1882 Arizona Territory, oak and juniper woodland in a quiet canyon of the Chiricahua Mountains, "
         "pale rhyolite rock outcrops on the hillside, dry summer grass")
BEATS = {
    "wide": f"a man in a white shirt, dark vest and wide-brimmed hat sitting at the base of a huge old oak tree with several trunks, "
            f"leaning back against the trunk, head bowed as if asleep, seen from a distance, {PLACE}, still midday heat",
    "found": f"two travelers in 1880s clothing, a man and a woman, walking slowly toward a large oak tree where a man sits slumped "
             f"in the shade, seen from behind them, a horse-drawn freight wagon on a dirt road, {PLACE}",
    "detail": "close view of an old leather boot and a dropped wide-brimmed felt hat in dry oak leaves at the foot of an oak tree, "
              "a nickel-plated single action revolver lying in the leaves, dappled light, 1880s, quiet and somber",
}
STY = {
    "real": "cinematic film still, photorealistic, 35mm film, natural light, muted earthy colors, shallow depth of field, "
            "historical drama, highly detailed, no text",
    "paint": "painterly illustration in the style of a graphic novel, oil paint and ink, visible brush strokes, "
             "warm ochre and dusty blue palette, dramatic soft light, beautifully composed, no text",
}
for name, beat in BEATS.items():
    for seed in (11, 23):
        t = time.time()
        img = pipe(f"{beat}, {STY[style]}", num_inference_steps=4, guidance_scale=0, width=1344, height=768,
                   generator=torch.Generator().manual_seed(seed)).images[0]
        img.save(f"{out}/{style}_{name}_{seed}.png"); print("IMG", style, name, seed, round(time.time() - t), "s", flush=True)
