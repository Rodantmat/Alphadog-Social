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

# SDXL's text encoders read only ~75 tokens: style goes FIRST and scenes stay short, or the style gets cut off
BEATS = {
    "wide": "a cowboy in white shirt and dark vest sitting slumped against a huge old oak tree, head bowed, hat low, seen from far away, "
            "oak woodland canyon, grey rhyolite rock spires, Arizona 1882",
    "found": "a man and a woman in 1880s clothes walking toward a big oak tree where a cowboy sits slumped in the shade, "
             "a freight wagon behind them, oak woodland, Arizona 1882",
    "detail": "a worn leather boot, a felt hat and an old revolver lying in dry oak leaves at the foot of an oak trunk, dappled light",
}
STY = {
    "real": "photorealistic cinematic film still, 35mm, natural light, muted earthy color, historical drama",
    "paint": "graphic novel painting, oil paint and ink, bold brush strokes, warm ochre and dusty blue, dramatic light",
}
for name, beat in BEATS.items():
    for seed in (11, 23):
        t = time.time()
        img = pipe(f"{STY[style]}, {beat}", num_inference_steps=4, guidance_scale=0, width=1344, height=768,
                   generator=torch.Generator().manual_seed(seed)).images[0]
        img.save(f"{out}/{style}_{name}_{seed}.png"); print("IMG", style, name, seed, round(time.time() - t), "s", flush=True)
