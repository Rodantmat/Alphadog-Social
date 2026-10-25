"""Text-to-image stills on Modal (paid from the $30/month allowance; account spend limit $0): Qwen-Image (Apache-2.0),
the open model with the strongest prompt adherence (counts, placement, props, long natural-language prompts).
GPU: A100-80GB (bf16 model ~58 GB, no offload). Weights are baked into the image at build time (no Volumes), so later
runs start fast. One container renders all seeds of a job list (a whole story passage per run saves model loads).
Hard caps: MAX_IMAGES per run, 1 attempt, timeout.
Usage: modal run modal_t2i.py --jobs jobs.json --out outdir      (job: {id, prompt, neg?, seeds?, w?, h?, steps?, cfg?})"""
import json, os, modal

MAX_IMAGES = 30
M = "Qwen/Qwen-Image"

def _download():
    from huggingface_hub import snapshot_download
    snapshot_download(M)

image = (modal.Image.debian_slim(python_version="3.11")
         .apt_install("git")
         .pip_install("torch==2.6.0", "torchvision==0.21.0", "transformers", "accelerate", "sentencepiece", "pillow",
                      "git+https://github.com/huggingface/diffusers.git")
         .run_function(_download, timeout=3600))
app = modal.App("alphadog-t2i", image=image)

@app.function(gpu="A100-80GB", timeout=3600, max_containers=1, retries=0)
def render(todo: list) -> list:
    import io, time, torch
    from diffusers import QwenImagePipeline
    t0 = time.time()
    pipe = QwenImagePipeline.from_pretrained(M, torch_dtype=torch.bfloat16).to("cuda")
    print("loaded in", round(time.time() - t0), "s", flush=True)
    res = []
    for j, seed in todo:
        t = time.time()
        img = pipe(prompt=j["prompt"], negative_prompt=j.get("neg", " "), width=j.get("w", 1664), height=j.get("h", 928),
                   num_inference_steps=j.get("steps", 50), true_cfg_scale=j.get("cfg", 4.0),
                   generator=torch.Generator("cuda").manual_seed(seed)).images[0]
        b = io.BytesIO(); img.save(b, "JPEG", quality=92)
        res.append((f"{j['id']}_{seed}.jpg", b.getvalue()))
        print("IMG", j["id"], seed, round(time.time() - t), "s", flush=True)
    return res

@app.local_entrypoint()
def main(jobs: str, out: str):
    js = json.load(open(jobs))
    todo = [(j, s) for j in js for s in j.get("seeds", [5])][:MAX_IMAGES]
    os.makedirs(out, exist_ok=True)
    for name, data in render.remote(todo):
        open(f"{out}/{name}", "wb").write(data); print("SAVED", name, len(data))
