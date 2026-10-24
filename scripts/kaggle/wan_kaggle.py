"""Runs INSIDE a Kaggle GPU notebook (2x T4): Wan2.1 T2V 1.3B (Apache-2.0) for a list of jobs (jobs.json next to this
script, embedded at push time). Step 1: encode all prompts with umT5 on CPU (fp32, once). Step 2: one worker per GPU
renders its share in fp16. Outputs: /kaggle/working/<name>.mp4 + progress.txt."""
import json, os, sys, time, subprocess, gc
JOBS = json.loads(JOBS_JSON)   # JOBS_JSON is prepended at push time by kaggle-wan.yml
OUT = "/kaggle/working"; M = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
NEG = ("bright saturated colors, overexposed, static, still image, frozen, blurry details, subtitles, text, watermark, logo, worst quality, "
       "low quality, jpeg artifacts, ugly, deformed, extra fingers, poorly drawn hands, poorly drawn face, fused fingers, "
       "messy background, three legs, walking backwards, modern cars, modern clothing, saguaro cactus")
def log(*a):
    msg = time.strftime("%H:%M:%S ") + " ".join(map(str, a)); print(msg, flush=True)
    open(f"{OUT}/progress.txt", "a").write(msg + "\n")

if len(sys.argv) == 1:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "diffusers>=0.33", "transformers", "accelerate", "ftfy", "imageio", "imageio-ffmpeg"], check=True)
    import torch
    from transformers import AutoTokenizer, UMT5EncoderModel
    from huggingface_hub import snapshot_download
    snapshot_download(M, allow_patterns=["*.json", "*.txt", "tokenizer/*", "text_encoder/*", "transformer/*", "vae/*", "scheduler/*"])
    tok = AutoTokenizer.from_pretrained(M, subfolder="tokenizer")
    te = UMT5EncoderModel.from_pretrained(M, subfolder="text_encoder", torch_dtype=torch.float32).eval()
    def enc(t):
        ids = tok([t], padding="max_length", max_length=512, truncation=True, add_special_tokens=True, return_attention_mask=True, return_tensors="pt")
        with torch.no_grad():
            h = te(ids.input_ids, ids.attention_mask).last_hidden_state
        n = int(ids.attention_mask.sum()); h = h[:, :n]
        return torch.cat([h, h.new_zeros(1, 512 - n, h.shape[-1])], 1)    # same padding scheme as WanPipeline._get_t5_prompt_embeds
    t0 = time.time()
    negE = enc(NEG)
    for j in JOBS:
        torch.save({"pe": enc(j["prompt"]), "ne": negE}, f"/tmp/emb_{j['name']}.pt")
    del te; gc.collect(); log("encoded", len(JOBS), "prompts in", round(time.time() - t0), "s")
    n = torch.cuda.device_count(); procs = []
    for g in range(n):
        mine = [j["name"] for k, j in enumerate(JOBS) if k % n == g]
        procs.append(subprocess.Popen([sys.executable, __file__, str(g)] + mine))
    for p in procs: p.wait()
    log("ALL_DONE", sorted(f for f in os.listdir(OUT) if f.endswith(".mp4")))
else:
    g = int(sys.argv[1]); names = sys.argv[2:]
    os.environ["CUDA_VISIBLE_DEVICES"] = str(g)
    import torch
    from diffusers import AutoencoderKLWan, WanPipeline
    from diffusers.schedulers.scheduling_unipc_multistep import UniPCMultistepScheduler
    from diffusers.utils import export_to_video
    vae = AutoencoderKLWan.from_pretrained(M, subfolder="vae", torch_dtype=torch.float32)
    pipe = WanPipeline.from_pretrained(M, vae=vae, text_encoder=None, tokenizer=None, torch_dtype=torch.float16).to("cuda")
    by = {j["name"]: j for j in JOBS}
    for name in names:
        j = by[name]; e = torch.load(f"/tmp/emb_{name}.pt")
        pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config, flow_shift=j.get("shift", 3.0))
        t1 = time.time(); steps = j.get("steps", 30)
        def cb(p, i, t, kw):
            if (i + 1) % 5 == 0: log(f"gpu{g} {name} step {i + 1}/{steps} {time.time() - t1:.0f}s")
            return kw
        try:
            fr = pipe(prompt_embeds=e["pe"].to("cuda", torch.float16), negative_prompt_embeds=e["ne"].to("cuda", torch.float16),
                      height=j.get("h", 480), width=j.get("w", 832), num_frames=j.get("frames", 81), num_inference_steps=steps,
                      guidance_scale=j.get("cfg", 5.0), generator=torch.Generator("cuda").manual_seed(j.get("seed", 42)),
                      callback_on_step_end=cb).frames[0]
            export_to_video(fr, f"{OUT}/{name}.mp4", fps=16); log(f"gpu{g} DONE {name} {time.time() - t1:.0f}s")
        except Exception as ex:
            log(f"gpu{g} FAIL {name} {repr(ex)[:300]}")
        torch.cuda.empty_cache()
