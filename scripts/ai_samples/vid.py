"""Free real-motion AI clip on a CPU GitHub runner: LTX-Video 2B (OpenRAIL-M, commercial use allowed) image-to-video.
Usage: vid.py IMG OUT.mp4 W H FRAMES STEPS "prompt"
RAM plan (16 GB runner): encode the prompt with T5 in bf16, free T5, then run the 2B transformer + VAE in fp32."""
import gc, os, sys, time, torch
from diffusers import LTXImageToVideoPipeline
from diffusers.utils import export_to_video
from PIL import Image

img_p, out, W, H, F, STEPS, prompt = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:7]), sys.argv[7]
torch.set_num_threads(os.cpu_count())
neg = "worst quality, inconsistent motion, blurry, jittery, distorted, deformed hands, extra limbs, text, watermark"
t0 = time.time()
pipe = LTXImageToVideoPipeline.from_pretrained("Lightricks/LTX-Video", torch_dtype=torch.bfloat16)
with torch.no_grad():
    pe, pm, ne, nm = pipe.encode_prompt(prompt, neg, do_classifier_free_guidance=True, max_sequence_length=128, device="cpu")
pipe.text_encoder = None; gc.collect()
pipe.transformer.to(torch.float32); pipe.vae.to(torch.float32)
pe, ne = pe.float(), ne.float()
print("loaded+encoded", round(time.time() - t0), "s", flush=True)
img = Image.open(img_p).convert("RGB").resize((W, H), Image.LANCZOS)
t1 = time.time()
frames = pipe(image=img, prompt_embeds=pe, prompt_attention_mask=pm, negative_prompt_embeds=ne, negative_prompt_attention_mask=nm,
              width=W, height=H, num_frames=F, num_inference_steps=STEPS, guidance_scale=3.0, decode_timestep=0.03,
              decode_noise_scale=0.025, generator=torch.Generator().manual_seed(7)).frames[0]
print("generated", F, "frames in", round(time.time() - t1), "s", flush=True)
export_to_video(frames, out, fps=24)
print("CLIP", out)
