"""Still-check for Episode 1 AI scenes. Cheap and fast on a free CPU runner: one still per shot, 2 seeds, so the owner can
approve the picture before any clip is animated. Takes a JSON list of {id, prompt, neg}.
Usage: stills.py OUTDIR PART NPARTS JOBS_JSON"""
import os, sys, json, time, torch
from diffusers import StableDiffusionXLPipeline, UNet2DConditionModel, EulerDiscreteScheduler
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file

out, part, nparts, jobs_path = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
os.makedirs(out, exist_ok=True)
jobs = json.load(open(jobs_path))
todo = [(j, s) for j in jobs for s in (5, 23)][part::nparts]
torch.set_num_threads(os.cpu_count())
base = "stabilityai/stable-diffusion-xl-base-1.0"
unet = UNet2DConditionModel.from_config(base, subfolder="unet").to(torch.float32)
unet.load_state_dict(load_file(hf_hub_download("ByteDance/SDXL-Lightning", "sdxl_lightning_4step_unet.safetensors")))
pipe = StableDiffusionXLPipeline.from_pretrained(base, unet=unet, torch_dtype=torch.float32, variant="fp16")
pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config, timestep_spacing="trailing")
pipe.set_progress_bar_config(disable=True)
for j, seed in todo:
    t = time.time()
    img = pipe(j["prompt"], negative_prompt=j["neg"], num_inference_steps=4, guidance_scale=0, width=1344, height=768,
               generator=torch.Generator().manual_seed(seed)).images[0]
    img.save(f"{out}/{j['id']}_{seed}.jpg", quality=92); print("IMG", j["id"], seed, round(time.time() - t), "s", flush=True)
