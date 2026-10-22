#!/usr/bin/env python3
"""Render cinematic 3D terrain flyovers (and 2D shaded basemaps) of a real place from public-domain data.
DEM: USGS 3DEP 1/3 arc-second (10 m) COGs on AWS (public domain); fallback Copernicus GLO-30.
Imagery: NAIP (USDA, public domain) via Planetary Computer STAC, or Sentinel-2 L2A (Copernicus, free) via Earth Search.
Reads are windowed through WarpedVRT so only the needed area/overview is downloaded.
Usage: terrain_flyover.py CONFIG_JSON OUTDIR
CONFIG: {"bbox": [W,S,E,N], "grid": 1400, "tex": 4096, "exag": 1.15, "imagery": "naip|s2",
         "basemaps": [{"name": "region", "bbox": [W,S,E,N], "px": 2400, "imagery": "s2"}],
         "shots": [{"name": "...", "secs": 10, "path": [[lon,lat,alt_m_above_ground],...], "look": [[lon,lat,elev_offset],...]}]}"""
import json, math, os, sys, time
import numpy as np
import rasterio
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.transform import from_bounds as tfb

T0 = time.time()
def say(*a): print(f"[{time.time()-T0:7.1f}s]", *a, flush=True)
CFG = json.loads(open(sys.argv[1]).read()) if os.path.exists(sys.argv[1]) else json.loads(sys.argv[1])
OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("GDAL_HTTP_MULTIRANGE", "YES"); os.environ.setdefault("GDAL_HTTP_MERGE_CONSECUTIVE_RANGES", "YES")
log = {}

def warp_read(href, bbox, w, h, bands=(1,), resampling=Resampling.bilinear, nodata=None):
    W_, S_, E_, N_ = bbox
    with rasterio.open(href) as src:
        with WarpedVRT(src, crs="EPSG:4326", transform=tfb(W_, S_, E_, N_, w, h), width=w, height=h,
                       resampling=resampling, src_nodata=nodata if nodata is not None else src.nodata, nodata=0) as vrt:
            return vrt.read(list(bands)).astype(np.float32)

def get_dem(bbox, n):
    W_, S_, E_, N_ = bbox; dem = np.zeros((n, n), np.float32); have = np.zeros((n, n), bool)
    for lat in range(math.floor(S_), math.floor(N_) + 1):
        for lon in range(math.floor(W_), math.floor(E_) + 1):
            t = f"n{lat+1:02d}w{abs(lon):03d}"
            url = f"/vsicurl/https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/{t}/USGS_13_{t}.tif"
            try:
                part = warp_read(url, bbox, n, n)[0]; m = (part != 0) & ~have
                dem[m] = part[m]; have |= part != 0; log[f"dem:{t}"] = "ok"
            except Exception as e:
                log[f"dem:{t}"] = str(e)[:160]
    if have.mean() < 0.95:
        for lat in range(math.floor(S_), math.floor(N_) + 1):
            for lon in range(math.floor(W_), math.floor(E_) + 1):
                nm = f"Copernicus_DSM_COG_10_N{lat:02d}_00_W{abs(lon):03d}_00_DEM"
                try:
                    part = warp_read(f"/vsicurl/https://copernicus-dem-30m.s3.amazonaws.com/{nm}/{nm}.tif", bbox, n, n)[0]
                    m = (part != 0) & ~have; dem[m] = part[m]; have |= part != 0; log[f"cop:{nm}"] = "ok"
                except Exception as e:
                    log[f"cop:{nm}"] = str(e)[:160]
    if have.any(): dem[~have] = np.median(dem[have])
    return dem

def get_imagery(bbox, px, kind):
    W_, S_, E_, N_ = bbox; tex = np.zeros((3, px, px), np.float32); filled = np.zeros((px, px), bool)
    if kind == "naip":
        try:
            import planetary_computer, pystac_client
            cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=planetary_computer.sign_inplace)
            items = list(cat.search(collections=["naip"], bbox=list(bbox), sortby=[{"field": "properties.datetime", "direction": "desc"}], max_items=60).items())
            if items:
                yr = items[0].properties["datetime"][:4]; items = [i for i in items if i.properties["datetime"][:4] == yr]
                log["naip"] = {"year": yr, "items": len(items)}
                for it in items:
                    try:
                        part = warp_read(it.assets["image"].href, bbox, px, px, bands=(1, 2, 3), resampling=Resampling.average, nodata=0)
                    except Exception as e:
                        log.setdefault("naip_err", []).append(str(e)[:120]); continue
                    m = (part[0] > 0) & ~filled
                    for b in range(3): tex[b][m] = part[b][m] / 255.0
                    filled |= m
                    say("naip item", it.id, round(float(filled.mean()), 3))
                    if filled.mean() > 0.995: break
        except Exception as e:
            log["naip_err0"] = str(e)[:200]
    if filled.mean() < 0.95:
        try:
            import pystac_client
            cat = pystac_client.Client.open("https://earth-search.aws.element84.com/v1")
            items = list(cat.search(collections=["sentinel-2-l2a"], bbox=list(bbox), datetime="2025-04-01/2026-10-01",
                                    query={"eo:cloud_cover": {"lt": 2}}, max_items=20).items())
            items.sort(key=lambda i: i.properties.get("eo:cloud_cover", 99))
            for it in items:
                part = np.stack([warp_read(it.assets[k].href, bbox, px, px, resampling=Resampling.cubic)[0] for k in ("red", "green", "blue")])
                m = (part[0] > 0) & ~filled
                for b in range(3): tex[b][m] = np.clip(part[b][m] / 2800.0, 0, 1) ** 0.85
                filled |= m; log.setdefault("s2", []).append(it.id); say("s2 item", it.id, round(float(filled.mean()), 3))
                if filled.mean() > 0.995: break
        except Exception as e:
            log["s2_err"] = str(e)[:200]
    tex = np.clip((tex - 0.5) * 1.12 + 0.5, 0, 1); tex[0] *= 1.04; tex[2] *= 0.96
    return np.clip(tex, 0, 1)

def hillshade(dem, cell, az=315, alt=40, z=1.6):
    gy, gx = np.gradient(dem * z, cell)
    slope = np.pi / 2 - np.arctan(np.hypot(gx, gy)); aspect = np.arctan2(-gx, gy)
    a, al = np.radians(az), np.radians(alt)
    hs = np.sin(al) * np.sin(slope) + np.cos(al) * np.cos(slope) * np.cos(a - aspect)
    return np.clip(hs, 0, 1)

from PIL import Image
# ---------- 2D basemaps ----------
for bm in CFG.get("basemaps", []):
    say("basemap", bm["name"])
    bb = bm["bbox"]; px = bm.get("px", 2400)
    dem = get_dem(bb, px); cell = (bb[3] - bb[1]) * 110540 / px
    hs = hillshade(dem, cell)
    img = get_imagery(bb, px, bm.get("imagery", "s2"))
    rgb = img.transpose(1, 2, 0) * (0.55 + 0.6 * hs[..., None])
    Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).save(f"{OUT}/basemap_{bm['name']}.jpg", quality=92)
    Image.fromarray((hs * 255).astype(np.uint8)).save(f"{OUT}/hillshade_{bm['name']}.jpg", quality=90)
    json.dump({"bbox": bb, "px": px}, open(f"{OUT}/basemap_{bm['name']}.json", "w"))

if not CFG.get("shots"):
    json.dump(log, open(f"{OUT}/flyover_log.json", "w"), indent=1); sys.exit(0)

# ---------- 3D ----------
W, S, E, N = CFG["bbox"]; GRID = CFG.get("grid", 1400); TEX = CFG.get("tex", 4096)
say("dem"); dem = get_dem((W, S, E, N), GRID); log["dem_range"] = [float(dem.min()), float(dem.max())]
say("imagery"); tex = get_imagery((W, S, E, N), TEX, CFG.get("imagery", "naip"))
Image.fromarray((tex.transpose(1, 2, 0) * 255).astype(np.uint8)).save(f"{OUT}/texture.jpg", quality=92)
say("mesh")
import pyvista as pv
lat0 = (S + N) / 2; mx = 111320 * math.cos(math.radians(lat0)); my = 110540; exag = CFG.get("exag", 1.15)
xs = np.linspace(0, (E - W) * mx, GRID); ys = np.linspace((N - S) * my, 0, GRID)
X, Y = np.meshgrid(xs, ys); base = float(dem.min()); Z = (dem - base) * exag
grid = pv.StructuredGrid(X, Y, Z)
U, V = np.meshgrid(np.linspace(0, 1, GRID), np.linspace(1, 0, GRID))
grid.active_texture_coordinates = np.c_[U.ravel(order="F"), V.ravel(order="F")]
texture = pv.read_texture(f"{OUT}/texture.jpg")

def to_xyz(lon, lat, alt):
    i = int(np.clip((N - lat) / (N - S) * (GRID - 1), 0, GRID - 1)); j = int(np.clip((lon - W) / (E - W) * (GRID - 1), 0, GRID - 1))
    return np.array([(lon - W) * mx, (lat - S) * my, (dem[i, j] - base) * exag + alt])

def spline(pts, n):
    pts = np.array(pts, dtype=float); tt = np.linspace(0, 1, n); tt = 3 * tt**2 - 2 * tt**3
    if len(pts) == 2: return pts[0] + (pts[1] - pts[0]) * tt[:, None]
    P = np.vstack([pts[0], pts, pts[-1]]); segs = len(pts) - 1; out = []
    for t in tt:
        s = min(int(t * segs), segs - 1); lt = t * segs - s; p0, p1, p2, p3 = P[s], P[s + 1], P[s + 2], P[s + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * lt + (2 * p0 - 5 * p1 + 4 * p2 - p3) * lt**2 + (-p0 + 3 * p1 - 3 * p2 + p3) * lt**3))
    return np.array(out)

FPS = CFG.get("fps", 30)
pl = pv.Plotter(off_screen=True, window_size=(CFG.get("w", 1920), CFG.get("h", 1080)))
pl.add_mesh(grid, texture=texture, smooth_shading=True, ambient=0.35, diffuse=0.75, specular=0.05)
pl.set_background([0.70, 0.78, 0.88], top=[0.32, 0.47, 0.72])
pl.add_light(pv.Light(position=to_xyz(W - (E - W), S + (N - S) * 0.2, 25000), light_type="scene light", intensity=0.85, color=[1.0, 0.95, 0.85]))
try: pl.enable_anti_aliasing("ssaa")
except Exception: pass
pl.camera.view_angle = CFG.get("fov", 40)
for shot in CFG["shots"]:
    n = int(shot["secs"] * FPS); cam = spline([to_xyz(*p) for p in shot["path"]], n); look = spline([to_xyz(*p) for p in shot["look"]], n)
    pl.open_movie(f"{OUT}/{shot['name']}.mp4", framerate=FPS, quality=9)
    for k in range(n):
        pl.camera.position = cam[k]; pl.camera.focal_point = look[k]; pl.camera.up = (0, 0, 1); pl.camera.clipping_range = (10, 300000)
        pl.write_frame()
    log[f"shot:{shot['name']}"] = n; say("shot", shot["name"], n)
pl.close()
json.dump(log, open(f"{OUT}/flyover_log.json", "w"), indent=1)
say("done", json.dumps(log)[:1500])
