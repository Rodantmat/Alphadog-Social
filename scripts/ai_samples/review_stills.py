"""Automatic review of still-check images (free, runs on the CI runner).
Counts people and horses with a COCO detector (YOLOv8n), compares the person count with the job's expect_person,
and writes report.json plus a contact sheet. Usage: review_stills.py JOBS_JSON STILLS_DIR OUT_DIR"""
import os, sys, json
from PIL import Image, ImageDraw
from ultralytics import YOLO

jobs_path, stills, out = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)
jobs = {j["id"]: j for j in json.load(open(jobs_path))}
model = YOLO("yolov8n.pt")
PERSON, HORSE = 0, 17          # COCO class ids
report, thumbs = {}, []
for fn in sorted(os.listdir(stills)):
    if not fn.lower().endswith(".jpg"):
        continue
    jid = fn.split("_")[0]
    res = model.predict(os.path.join(stills, fn), conf=0.25, verbose=False)[0]
    cls = [int(c) for c in res.boxes.cls.tolist()]
    person, horse = cls.count(PERSON), cls.count(HORSE)
    exp = jobs.get(jid, {}).get("expect_person")
    report[fn] = {"person": person, "horse": horse, "expect_person": exp,
                  "person_ok": (exp is None) or (person == exp)}
    thumbs.append((fn, Image.open(os.path.join(stills, fn)).convert("RGB").resize((448, 252))))

cols = 3
rows = (len(thumbs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 448, max(1, rows) * 270), (20, 20, 20))
d = ImageDraw.Draw(sheet)
for i, (fn, im) in enumerate(thumbs):
    x, y = (i % cols) * 448, (i // cols) * 270
    sheet.paste(im, (x, y))
    r = report[fn]
    d.text((x + 6, y + 256), f"{fn}  person={r['person']} horse={r['horse']} ok={r['person_ok']}", fill=(255, 255, 255))
sheet.save(os.path.join(out, "sheet.jpg"), quality=88)
json.dump(report, open(os.path.join(out, "report.json"), "w"), indent=1)
print(json.dumps(report, indent=1))
