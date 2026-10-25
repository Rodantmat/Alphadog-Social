"""Image-to-video on Modal (free $30/month allowance, account spend limit $0): Wan2.2 TI2V-5B (Apache-2.0) animates a
keyframe still in the channel's illustrated style with real motion. GPU: L4 (24 GB). Weights are baked into the image at
build time (CPU), so GPU minutes are spent only on generation. Hard caps: MAX_JOBS per run, 1 attempt per job, timeout.
Job option "flip": true mirrors the still left-right first (keeps screen direction consistent between shots).
Usage: modal run modal_i2v.py --jobs jobs.json --out outdir"""
import json, os, modal

MAX_JOBS = 8
M = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"

def _download():
    from huggingface_hub import snapshot_download
    snapshot_download(M)

image = (modal.Image.debian_slim(python_version="3.11")
         .apt_install("ffmpeg", "git")
         .pip_install("torch==2.6.0", "torchvision==0.21.0", "transformers", "accelerate", "ftfy", "imageio", "imageio-ffmpeg",
                      "sentencepiece", "pillow", "requests", "git+https://github.com/huggingface/diffusers.git")
         .run_function(_download)
         .env({"PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"}))
app = modal.App("alphadog-i2v", image=image)

@app.function(gpu="L4", timeout=4800, max_containers=4, retries=0)
def render(job: dict) -> bytes:
    import io, time, requests, torch
    from PIL import Image
    from diffusers import AutoencoderKLWan, WanImageToVideoPipeline
    from diffusers.utils import export_to_video
    t0 = time.time()
    vae = AutoencoderKLWan.from_pretrained(M, subfolder="vae", torch_dtype=torch.float32)
    pipe = WanImageToVideoPipeline.from_pretrained(M, vae=vae, torch_dtype=torch.bfloat16)
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_tiling()          # run 1 (i2v1) hit CUDA OOM in the full-frame VAE decode after 18 min of denoising
    img = Image.open(io.BytesIO(requests.get(job["image_url"], timeout=60).content)).convert("RGB")
    if job.get("flip"):
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    W, H = job.get("w", 1280), job.get("h", 704)
    img = img.resize((W, H), Image.LANCZOS)
    steps = job.get("steps", 40)
    def cb(p, i, t, kw):
        if (i + 1) % 5 == 0: print(f"{job['name']} step {i + 1}/{steps} {time.time() - t0:.0f}s", flush=True)
        return kw
    lat = pipe(image=img, prompt=job["prompt"], negative_prompt=job.get("neg", ""), height=H, width=W,
               num_frames=job.get("frames", 121), num_inference_steps=steps, guidance_scale=job.get("cfg", 5.0),
               generator=torch.Generator("cuda").manual_seed(job.get("seed", 42)), output_type="latent",
               callback_on_step_end=cb).frames
    pipe.remove_all_hooks(); pipe.transformer.to("cpu"); pipe.text_encoder.to("cpu"); torch.cuda.empty_cache()
    def decode(dev):
        v = pipe.vae.to(dev); x = lat.to(dev, v.dtype)
        mean = torch.tensor(v.config.latents_mean).view(1, v.config.z_dim, 1, 1, 1).to(dev, v.dtype)
        std = 1.0 / torch.tensor(v.config.latents_std).view(1, v.config.z_dim, 1, 1, 1).to(dev, v.dtype)
        with torch.no_grad():
            vid = v.decode(x / std + mean, return_dict=False)[0]
        return pipe.video_processor.postprocess_video(vid, output_type="pil")[0]
    try:
        frames = decode("cuda")
    except torch.OutOfMemoryError:     # never lose the 18 min of denoising: fall back to a (slow) CPU decode
        print(job["name"], "GPU decode OOM -> CPU decode", flush=True); torch.cuda.empty_cache()
        frames = decode("cpu")
    p = f"/tmp/{job['name']}.mp4"; export_to_video(frames, p, fps=24)
    print(job["name"], "done in", round(time.time() - t0), "s", flush=True)
    return open(p, "rb").read()

@app.local_entrypoint()
def main(jobs: str, out: str):
    js = json.load(open(jobs))[:MAX_JOBS]
    os.makedirs(out, exist_ok=True)
    for j, data in zip(js, render.map(js, return_exceptions=True)):
        if isinstance(data, Exception): print("FAIL", j["name"], repr(data)[-600:]); continue
        open(f"{out}/{j['name']}.mp4", "wb").write(data); print("SAVED", j["name"], len(data))
