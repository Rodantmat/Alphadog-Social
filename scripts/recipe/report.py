"""AlphaDog Studio - recipe auditor v2: dimension scores, overall gate, HTML summary, review pack (C1), fix suggestions."""
import base64, html, io, json, math, os
import numpy as np

DIMS = {
    "structure": ["S9", "S8", "Q4", "E6", "V4", "V6"],
    "story_script": ["S7", "S8", "S10", "T4"],
    "imagery_relevance": ["P2", "P6", "P7", "P8", "A4"],
    "sequence_pacing": ["R7", "Q1", "Q9", "E1", "E2", "E3", "E4", "E5", "E6"],
    "framing": ["F1", "F2", "F3", "F4", "F5", "Q8", "V5"],
    "stabilization": ["Q2", "Q3", "Q5", "ST1", "ST2", "ST3", "ST4", "ST5", "ST6"],
    "technical_quality": ["Q7", "Q10", "Q11", "Q12", "Q13", "Q14", "Q15", "Q16", "Q17"],
    "audio": ["U1", "U2", "U3", "U5", "U6", "U7", "U8", "U9", "U10", "U11", "U12"],
    "sync": ["T1", "Y1", "Y2", "V2"],
    "text_subtitles": ["T1", "T2", "T3", "V2"],
    "platform_safety": ["O2", "Q6", "V1", "V3", "V4", "V6"],
}
DEFAULT_FLOORS = {k: 70 for k in DIMS}


def scores(REP, floors=None):
    floors = {**DEFAULT_FLOORS, **(floors or {})}; out = {}
    for d, rids in DIMS.items():
        pen = 0.0; used = 0
        for rid in rids:
            r = REP.get(rid)
            if not r or r["status"] == "skipped": continue
            used += 1
            nf = sum(1 for f in r["findings"] if f["sev"] == "fail"); nw = sum(1 for f in r["findings"] if f["sev"] == "warn")
            if r["check"] != "auto": nw += nf; nf = 0                    # a warn-rule's 'fail' findings weigh as warnings
            pen += min(40, 15 * nf) + min(12, 2 * nw)
        sc = max(0.0, 100.0 - pen)
        if d == "imagery_relevance" and REP.get("P7", {}).get("measured", {}).get("sections"):
            p7 = np.mean([s["score"] for s in REP["P7"]["measured"]["sections"]]); sc = 0.5 * sc + 0.5 * float(p7)
        if d == "story_script" and REP.get("S8", {}).get("measured", {}).get("score") is not None:
            sc = 0.8 * sc + 0.2 * float(REP["S8"]["measured"]["score"])
        out[d] = {"score": round(sc, 1) if used else None, "floor": floors.get(d, 70), "rules": [r for r in rids if r in REP and REP[r]["status"] != "skipped"]}
    return out


def gate(REP, SC):
    why = [f"{rid} failed" for rid, r in REP.items() if r["status"] == "fail" and r["check"] == "auto"]
    why += [f"{d} score {v['score']} < floor {v['floor']}" for d, v in SC.items() if v["score"] is not None and v["score"] < v["floor"]]
    return {"pass": not why, "reasons": why}


def fixes(REP, ctx):
    """machine-readable repair suggestions builders can consume (rule, action, t, t_end, params)"""
    fx = []; fps = ctx["fps"]
    def add(rule, action, t=None, t_end=None, **p):
        d = {"rule": rule, "action": action}
        if t is not None: d["t"] = round(float(t), 3)
        if t_end is not None: d["t_end"] = round(float(t_end), 3)
        if t is not None: d["frame"] = int(round(t * fps))
        if t_end is not None: d["frame_end"] = int(round(t_end * fps))
        d.update(p); fx.append(d)
    for f in REP.get("R7", {}).get("findings", []):
        if f["sev"] == "fail" and f.get("t_end"): add("R7", "hold_previous_frame", f["t"], f["t_end"], note="flash shot: hold the frame before it (or extend the neighbour) over this range")
    for f in REP.get("E3", {}).get("findings", []):
        if f["sev"] == "fail": add("E3", "smooth_jump", f["t"] - 0.2, f["t"] + 0.2, note="in-shot jump: trim the clip before the jump or cross-dissolve 6 frames")
    for f in REP.get("Q3", {}).get("findings", []):
        if f["sev"] == "fail": add("Q3", "trim_or_retime", f["t"], f.get("t_end"), note="frozen tail inside a moving shot: end the shot before the freeze")
    segs = ctx.get("segments") or []
    if ctx.get("vertical") and len(segs) >= 2:
        a, b = segs[-1]; pa, pb = segs[-2]
        if pb - pa < 1.2 and ctx["duration"] - a < 6: add("R7", "start_end_card_at", pa, note=f"a {pb - pa:.2f}s flash sits right before the end card: start the end card at the earlier cut")
    U1 = REP.get("U1", {}).get("measured", {})
    if U1.get("integrated_lufs") is not None and abs(U1["integrated_lufs"] + 14) > 1: add("U1", "gain_db", value=round(-14 - U1["integrated_lufs"], 2))
    if U1.get("true_peak_dbtp") is not None and U1["true_peak_dbtp"] > -1.5: add("U1", "true_peak_limit_dbtp", value=-2.0, measured=U1["true_peak_dbtp"])
    dr = REP.get("T1", {}).get("drift")
    if dr and abs(dr.get("median_signed_s", 0)) > 0.15: add("T1", "shift_subtitles_s", value=round(-dr["median_signed_s"], 3))
    for f in REP.get("T3", {}).get("findings", []):
        if "chars/s" in f["msg"] and f.get("t_end"): add("T3", "extend_or_split_cue", f["t"], f["t_end"], msg=f["msg"][:80])
        elif "line" in f["msg"] and f["t"] > 0: add("T3", "rewrap_cue", f["t"], msg=f["msg"][:80])
    H = ctx["height"]
    for f in REP.get("V3", {}).get("findings", []):
        box = f.get("box")
        if box: add("V3", "move_caption", f["t"], to="bottom" if (box[1] + box[3]) / 2 < H / 2 else "top", face_box=box)
    for f in REP.get("V1", {}).get("findings", []):
        if f.get("box"): add("V1", "move_text_into_safe_area", f["t"], box=f["box"], safe=[170, 400, 910, 1220])
    for f in REP.get("Q8", {}).get("findings", []):
        if f["sev"] == "fail": add("Q8", "crop_or_blur_fill", f["t"], f.get("t_end"), box=f.get("box"))
    for f in REP.get("ST2", {}).get("findings", []):
        if f["sev"] == "fail": add("ST2", "increase_stabilization_crop", f["t"], f.get("t_end"), note="vidstab: raise zoom / optzoom=1 or replace the clip")
    for f in REP.get("S9", {}).get("findings", []):
        if f["sev"] == "fail": add("S9", "align_card_to_timeline", f["t"], msg=f["msg"][:100])
    for f in REP.get("U8", {}).get("findings", []):
        add("U8", "audio_crossfade_ms", f["t"] - 0.02, f["t"] + 0.02, value=10)
    for f in REP.get("U9", {}).get("findings", []):
        if "cut" in f["msg"]: add("U9", "audio_crossfade_ms", f["t"] - 0.03, f["t"] + 0.03, value=30)
    for f in REP.get("P8", {}).get("findings", []):
        if f["sev"] == "fail": add("P8", "replace_shot_to_match_words", f["t"], f.get("t_end"), word=f.get("word"), msg=f["msg"][:100])
    for f in REP.get("V4", {}).get("findings", []):
        add("V4", "open_on_motion" if "static" in f["msg"] else "enlarge_or_move_hook_text", f["t"], f.get("t_end"), min_font_px=58, safe=[170, 400, 910, 1220], box=f.get("box"))
    for f in REP.get("V5", {}).get("findings", []):
        add("V5", "crop_full_frame_on_subject", f["t"], f.get("t_end"))
    for f in REP.get("V6", {}).get("findings", []):
        add("V6", "extend_cta" if "only" in f["msg"] else "enlarge_or_move_cta", f["t"], f.get("t_end"), min_seconds=2.0, min_font_px=58, safe=[170, 400, 910, 1220], box=f.get("box"))
    for f in REP.get("Q4", {}).get("findings", []):
        if f["sev"] == "fail": add("Q4", "remove_black", f["t"], f.get("t_end"))
    return fx


def _thumb_b64(path, width=900, q=62):
    from PIL import Image
    try:
        im = Image.open(path); im.thumbnail((width, width * 4)); b = io.BytesIO(); im.convert("RGB").save(b, "JPEG", quality=q)
        return base64.b64encode(b.getvalue()).decode()
    except Exception: return None


def _svg_curve(vals, w=640, h=90, color="#4b8bd6"):
    if not vals: return ""
    mx = max(vals) or 1; n = len(vals)
    pts = " ".join(f"{i * w / max(1, n - 1):.1f},{h - 4 - (v / mx) * (h - 12):.1f}" for i, v in enumerate(vals))
    return f'<svg viewBox="0 0 {w} {h}" width="100%" height="{h}" role="img"><polyline fill="none" stroke="{color}" stroke-width="2" points="{pts}"/><text x="4" y="12" font-size="11" fill="currentColor">max {mx:g}</text></svg>'


def write_html(path, rep, out_dir):
    e = html.escape; R = rep["rules"]; SC = rep["scores"]; G = rep["gate"]
    css = """:root{--bg:#f7f7f5;--fg:#1d1d1f;--mut:#6b6b70;--card:#fff;--bd:#e2e2e0;--ok:#1f8a4c;--warn:#b7791f;--bad:#c53030;--bar:#e9e9e6}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#141416;--fg:#ececef;--mut:#9a9aa2;--card:#1e1e22;--bd:#2e2e34;--bar:#2a2a30}}
:root[data-theme=dark]{--bg:#141416;--fg:#ececef;--mut:#9a9aa2;--card:#1e1e22;--bd:#2e2e34;--bar:#2a2a30}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:1100px;margin:0 auto;padding:16px}h1{font-size:20px;margin:4px 0}h2{font-size:16px;margin:22px 0 8px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:12px 14px;margin:10px 0}
.pill{display:inline-block;padding:2px 9px;border-radius:99px;font-weight:600;font-size:12px;color:#fff}
.pass{background:var(--ok)}.warn{background:var(--warn)}.fail{background:var(--bad)}.skipped,.info{background:#777}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:8px}
.bar{height:8px;background:var(--bar);border-radius:4px;position:relative;margin-top:4px}.bar i{display:block;height:8px;border-radius:4px}
.bar b{position:absolute;top:-3px;width:2px;height:14px;background:var(--fg);opacity:.5}
table{border-collapse:collapse;width:100%}td,th{border-top:1px solid var(--bd);padding:5px 6px;text-align:left;vertical-align:top;font-size:13px}
.mut{color:var(--mut)}details summary{cursor:pointer}img{max-width:100%;border-radius:6px;margin:6px 0}code{font-size:12px}
.f-fail{color:var(--bad)}.f-warn{color:var(--warn)}"""
    h = [f"<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>Recipe QA {e(rep['video'])}</title><style>{css}</style></head><body><main>"]
    h.append(f"<h1>Recipe audit v2 - {e(rep['video'])}</h1><div class=mut>{rep['mode']} {rep['width']}x{rep['height']} {rep['fps']} fps, {rep['duration_s']} s, {rep['cuts_detected']} cuts, analysed in {rep['elapsed_s']} s</div>")
    h.append(f"<div class=card><span class='pill {'pass' if G['pass'] else 'fail'}'>{'GATE PASS' if G['pass'] else 'GATE FAIL'}</span> "
             + (" ".join(f"<span class=mut>{e(x)};</span>" for x in G["reasons"][:30]) or "<span class=mut>all auto rules pass and every score is above its floor</span>") + "</div>")
    h.append("<h2>Scores</h2><div class=grid>")
    for d, v in SC.items():
        s = v["score"]
        if s is None: h.append(f"<div class=card><b>{d.replace('_', ' ')}</b> <span class=mut>n/a</span></div>"); continue
        col = "var(--ok)" if s >= v["floor"] + 10 else "var(--warn)" if s >= v["floor"] else "var(--bad)"
        h.append(f"<div class=card><b>{d.replace('_', ' ')}</b> <span style='float:right;font-weight:700;color:{col}'>{s:.0f}</span><div class=bar><i style='width:{s}%;background:{col}'></i><b style='left:{v['floor']}%'></b></div><div class=mut style='font-size:12px'>floor {v['floor']} - {', '.join(v['rules'])}</div></div>")
    h.append("</div>")
    E2 = R.get("E2", {}).get("measured", {})
    if E2.get("pacing_curve_cpm"): h.append(f"<h2>Pacing (cuts/min per {E2.get('window_s')} s)</h2><div class=card>{_svg_curve(E2['pacing_curve_cpm'])}</div>")
    E6 = R.get("E6", {}).get("measured", {})
    if E6.get("change_events_per_min"): h.append(f"<h2>Visual change events per minute</h2><div class=card>{_svg_curve(E6['change_events_per_min'], color='#8a5cd6')}</div>")
    h.append("<h2>Rules</h2><div class=card><table><tr><th>rule</th><th>status</th><th>findings</th></tr>")
    order = {"fail": 0, "warn": 1, "pass": 2, "skipped": 3}
    for rid, r in sorted(R.items(), key=lambda kv: (order.get(kv[1]["status"], 4), kv[0])):
        fl = [f for f in r["findings"] if f["sev"] in ("fail", "warn")]
        items = "".join(f"<li class='f-{f['sev']}'><code>{f['tc']}</code> {e(f['msg'][:160])}</li>" for f in fl[:40])
        more = f"<li class=mut>+{len(fl) - 40} more</li>" if len(fl) > 40 else ""
        body = f"<details><summary>{len(fl)} findings</summary><ul>{items}{more}</ul></details>" if fl else ""
        h.append(f"<tr><td><b>{rid}</b><div class=mut style='font-size:12px'>{e(r.get('rule', '')[:110])}</div></td><td><span class='pill {r['status']}'>{r['status']}</span></td><td>{e(r.get('summary', '')[:220])}{body}</td></tr>")
    h.append("</table></div>")
    sheets = rep.get("sheets", [])
    if sheets:
        h.append("<h2>Flagged frames</h2>")
        for s in sheets[:40]:
            b = _thumb_b64(os.path.join(out_dir, s))
            if b: h.append(f"<div class=card><b>{e(s)}</b><img alt='{e(s)}' src='data:image/jpeg;base64,{b}'></div>")
    h.append("<p class=mut>scripts/recipe/analyze.py v2 - rules: content/recipe/recipe.yaml</p></main></body></html>")
    open(path, "w").write("".join(h))


def review_pack(out_dir, frames_dir, sfps, segs, chapters, en_cues, words, shot_at, tc, vert, max_tiles=60):
    """key frame per shot (from pass-B samples) as strips per chapter + transcript excerpt -> review_pack.json + review_<n>.jpg"""
    from PIL import Image, ImageDraw, ImageFont
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except Exception: font = ImageFont.load_default()
    jp = sorted(os.listdir(frames_dir)) if os.path.isdir(frames_dir) else []
    if not jp: return None
    def frame_at(t):
        k = int(max(0, min(len(jp) - 1, round(t * sfps - 0.5)))); return os.path.join(frames_dir, jp[k])
    secs = chapters or [("all", 0.0, segs[-1][1] if segs else 0.0)]
    TW = 108 if vert else 192; TH = 192 if vert else 108; cols = 10
    pack = {"chapters": [], "how_to_use": "C1 critique: for each chapter look at the strip (one key frame per on-screen shot, time-labelled) and read the transcript; score history, imagery, coherence, script, context, audio, pacing, excitement for young/older/history buff/critic/casual viewers."}
    for ci, (name, a, b) in enumerate(secs):
        ss = [(x, y) for x, y in segs if a <= (x + y) / 2 < b]
        if not ss: continue
        tiles = []
        for x, y in ss[:max_tiles]:
            try: im = Image.open(frame_at((x + y) / 2)).convert("RGB")
            except Exception: continue
            im.thumbnail((TW, TH)); c = Image.new("RGB", (TW, TH + 16), (15, 15, 15)); c.paste(im, ((TW - im.width) // 2, 0))
            s = shot_at((x + y) / 2); lab = f"{tc(x)} {y - x:.1f}s" + (f" {s['type'][0]}" if s else "")
            ImageDraw.Draw(c).text((3, TH + 1), lab, fill=(230, 230, 230), font=font); tiles.append(c)
        if not tiles: continue
        rows = math.ceil(len(tiles) / cols); sh = Image.new("RGB", (cols * (TW + 2), rows * (TH + 18)), (0, 0, 0))
        for k, t in enumerate(tiles): sh.paste(t, ((k % cols) * (TW + 2), (k // cols) * (TH + 18)))
        fn = f"review_{ci + 1:02d}.jpg"; sh.save(os.path.join(out_dir, fn), quality=80)
        txt = " ".join(t for x, y, t in en_cues if a <= x < b) if en_cues else " ".join(w for x, y, w in words if a <= x < b)
        pack["chapters"].append({"name": name, "start": round(a, 2), "end": round(b, 2), "start_tc": tc(a), "shots": len(ss), "strip": fn,
                                 "transcript": txt[:2500] + ("..." if len(txt) > 2500 else "")})
    json.dump(pack, open(os.path.join(out_dir, "review_pack.json"), "w"), indent=1)
    return pack
