"""Free real-motion AI video on a CPU GitHub runner: Wan2.1 text-to-video 1.3B (Apache-2.0, commercial use allowed).
Usage: wan.py OUT.mp4 W H FRAMES STEPS "prompt"
RAM plan (16 GB + swap): umT5 text encoder in bf16 -> encode -> free it; then the 1.3B transformer + VAE in fp32."""
import gc, os, sys, time, torch
from diffusers import AutoencoderKLWan, WanPipeline
from diffusers.schedulers.scheduling_unipc_multistep import UniPCMultistepScheduler
from diffusers.utils import export_to_video

out, W, H, F, STEPS, prompt = sys.argv[1], *map(int, sys.argv[2:6]), sys.argv[6]
torch.set_num_threads(os.cpu_count())
neg = ("bright saturated colors, overexposed, static, still image, blurry details, subtitles, text, watermark, worst quality, "
       "low quality, jpeg artifacts, ugly, deformed, extra fingers, poorly drawn hands, poorly drawn face, fused fingers, "
       "messy background, three legs, many people in the background, walking backwards, modern cars, modern clothing")
M = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
t0 = time.time()
vae = AutoencoderKLWan.from_pretrained(M, subfolder="vae", torch_dtype=torch.float32)
pipe = WanPipeline.from_pretrained(M, vae=vae, torch_dtype=torch.bfloat16)
pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config, flow_shift=3.0)
with torch.no_grad():
    pe, ne = pipe.encode_prompt(prompt=prompt, negative_prompt=neg, do_classifier_free_guidance=True, device="cpu")
pipe.text_encoder = None; gc.collect()
pipe.transformer.to(torch.float32); pe, ne = pe.float(), ne.float()
print("loaded+encoded", round(time.time() - t0), "s", flush=True)
t1 = time.time()
def cb(p, i, t, kw):
    print(f"step {i + 1}/{STEPS} {time.time() - t1:.0f}s", flush=True); return kw
frames = pipe(prompt_embeds=pe, negative_prompt_embeds=ne, height=H, width=W, num_frames=F, num_inference_steps=STEPS,
              guidance_scale=5.0, generator=torch.Generator().manual_seed(42), callback_on_step_end=cb).frames[0]
print("generated", F, "frames in", round(time.time() - t1), "s", flush=True)
export_to_video(frames, out, fps=16)
print("CLIP", out)
