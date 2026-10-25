"""Instruction-based still editing on Modal (paid from the $30/month allowance; account spend limit $0):
Qwen-Image-Edit (Apache-2.0). Fixes a detail of an otherwise good still (remove a stray figure, change footwear, ...)
while keeping the rest of the picture. GPU: A100-80GB, bf16, no offload. Weights baked into the image (no Volumes).
Hard caps: MAX_IMAGES per run, 1 container, 1 attempt.
Usage: modal run modal_edit.py --jobs jobs.json --out outdir   (job: {id, image_url, prompt, neg?, seeds?, steps?, cfg?})"""
import json, os, modal

MAX_IMAGES = 8
M = "Qwen/Qwen-Image-Edit"

def _download():
    from huggingface_hub import snapshot_download
    snapshot_download(M)

image = (modal.Image.debian_slim(python_version="3.11")
         .apt_install("git")
         .pip_install("torch==2.6.0", "torchvision==0.21.0", "transformers", "accelerate", "sentencepiece", "pillow",
                      "requests", "git+https://github.com/huggingface/diffusers.git")
         .run_function(_download, timeout=3600))
app = modal.App("alphadog-edit", image=image)

@app.function(gpu="A100-80GB", timeout=2400, max_containers=1, retries=0)
def render(todo: list) -> list:
    import io, time, requests, torch
    from PIL import Image
    from diffusers import QwenImageEditPipeline
    t0 = time.time()
    pipe = QwenImageEditPipeline.from_pretrained(M, torch_dtype=torch.bfloat16).to("cuda")
    print("loaded in", round(time.time() - t0), "s", flush=True)
    res, cache = [], {}
    for j, seed in todo:
        if j["image_url"] not in cache:
            cache[j["image_url"]] = Image.open(io.BytesIO(requests.get(j["image_url"], timeout=60).content)).convert("RGB")
        src = cache[j["image_url"]]
        t = time.time()
        img = pipe(image=src, prompt=j["prompt"], negative_prompt=j.get("neg", " "),
                   num_inference_steps=j.get("steps", 50), true_cfg_scale=j.get("cfg", 4.0),
                   generator=torch.Generator("cuda").manual_seed(seed)).images[0]
        img = img.resize(src.size, Image.LANCZOS)          # keep the source frame size
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
