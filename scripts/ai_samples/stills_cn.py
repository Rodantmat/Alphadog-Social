"""Layout-controlled still for Episode 1 AI scenes. Free CPU runner.
A line layout is drawn by code (counts and placement are fixed), then SDXL base + the diffusers Canny ControlNet
renders the picture on that layout, with real negative prompts and CFG on.
Usage: stills_cn.py OUTDIR PART NPARTS JOBS_JSON     (each job: {id, prompt, neg, guidance?, steps?, seeds?})"""
import os, sys, json, time, torch
from PIL import Image, ImageDraw
from diffusers import StableDiffusionXLControlNetPipeline, ControlNetModel, EulerDiscreteScheduler

out, part, nparts, jobs_path = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
os.makedirs(out, exist_ok=True)
jobs = json.load(open(jobs_path))
todo = [(j, s) for j in jobs for s in j.get("seeds", [5])][part::nparts]
W, H = 1024, 576


def layout_A01():
    # one standing teamster (left), two mules (centre), wagon with wood (right), road at the bottom
    im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im); k = 0.762   # drawn at 1344x768, scaled
    def s(*p): return [v * k for v in p]
    d.polygon([(0, H), (W, H), (W, 0.68 * H), (0, 0.78 * H)], outline="black", width=3)
    d.ellipse(s(330, 250, 380, 300), outline="black", width=5)
    d.rectangle(s(340, 300, 372, 470), outline="black", width=5)
    d.line(s(340, 470, 330, 600) + s(372, 470, 382, 600), fill="black", width=5)
    d.line(s(340, 330, 300, 400) + s(372, 330, 400, 400), fill="black", width=5)
    for x in (520, 660):
        d.rounded_rectangle(s(x, 380, x + 120, 470), radius=22, outline="black", width=5)
        d.rectangle(s(x + 100, 330, x + 140, 380), outline="black", width=5)
        for lx in (x + 15, x + 35, x + 85, x + 105): d.line(s(lx, 470, lx, 560), fill="black", width=5)
    d.rectangle(s(800, 400, 1100, 500), outline="black", width=5)
    for wx in (850, 1060): d.ellipse(s(wx - 40, 470, wx + 40, 550), outline="black", width=5)
    for i in range(6): d.ellipse(s(830 + i * 40, 360, 880 + i * 40, 400), outline="black", width=4)
    return im


LAYOUTS = {"A01": layout_A01}
torch.set_num_threads(os.cpu_count())
cn = ControlNetModel.from_pretrained("diffusers/controlnet-canny-sdxl-1.0", torch_dtype=torch.float32)
pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0", controlnet=cn, torch_dtype=torch.float32, variant="fp16")
pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
pipe.set_progress_bar_config(disable=True)
for j, seed in todo:
    t = time.time()
    ctrl = LAYOUTS[j["id"]]()
    img = pipe(j["prompt"], negative_prompt=j["neg"], image=ctrl, controlnet_conditioning_scale=j.get("cn_scale", 0.9),
               num_inference_steps=j.get("steps", 25), guidance_scale=j.get("guidance", 6.0), width=W, height=H,
               generator=torch.Generator().manual_seed(seed)).images[0]
    img.save(f"{out}/{j['id']}_{seed}.jpg", quality=92); print("IMG", j["id"], seed, round(time.time() - t), "s", flush=True)
