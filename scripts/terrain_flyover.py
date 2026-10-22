#!/usr/bin/env python3
"""Render cinematic 3D terrain flyovers of a real place from public-domain data.
DEM: USGS 3DEP 1/3 arc-second (10 m) COGs on AWS (public domain).
Imagery: NAIP (USDA, public domain) via Microsoft Planetary Computer STAC; fallback Sentinel-2 (Copernicus, free) via Earth Search.
Usage: terrain_flyover.py CONFIG_JSON OUTDIR
CONFIG: {"bbox": [W,S,E,N], "grid": 1400, "tex": 4096, "exag": 1.15,
         "shots": [{"name": "east_approach", "secs": 10, "path": [[lon,lat,alt_m_above_ground], ...], "look": [[lon,lat,elev_offset],...]}],
         "fps": 30, "w": 1920, "h": 1080}"""
import json, math, os, subprocess, sys
import numpy as np

CFG = json.loads(open(sys.argv[1]).read()) if os.path.exists(sys.argv[1]) else json.loads(sys.argv[1])
OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
W, S, E, N = CFG["bbox"]
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import reproject, Resampling, transform_bounds
from rasterio.transform import from_bounds as tfb

GRID = CFG.get("grid", 1400); TEX = CFG.get("tex", 4096)
log = {}

# ---------- DEM (3DEP 1/3 arc-second tiles named by NW corner) ----------
def tile_names():
    names = set()
    for lat in range(math.floor(S), math.floor(N) + 1):
        for lon in range(math.floor(W), math.floor(E) + 1):
            names.add(f"n{lat+1:02d}w{abs(lon):03d}")
    return sorted(names)
dem = np.full((GRID, GRID), np.nan, dtype=np.float32)
dst_tf = tfb(W, S, E, N, GRID, GRID)
for t in tile_names():
    url = f"/vsicurl/https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/{t}/USGS_13_{t}.tif"
    try:
        with rasterio.open(url) as src:
            part = np.full((GRID, GRID), np.nan, dtype=np.float32)
            reproject(rasterio.band(src, 1), part, dst_transform=dst_tf, dst_crs="EPSG:4326", resampling=Resampling.bilinear,
                      dst_nodata=np.nan)
            dem = np.where(np.isnan(dem), part, dem)
            log[f"dem:{t}"] = "ok"
    except Exception as e:
        log[f"dem:{t}"] = str(e)[:200]
if np.isnan(dem).all():
    # fallback: Copernicus GLO-30
    for lat in range(math.floor(S), math.floor(N) + 1):
        for lon in range(math.floor(W), math.floor(E) + 1):
            nm = f"Copernicus_DSM_COG_10_N{lat:02d}_00_W{abs(lon):03d}_00_DEM"
            try:
                with rasterio.open(f"/vsicurl/https://copernicus-dem-30m.s3.amazonaws.com/{nm}/{nm}.tif") as src:
                    part = np.full((GRID, GRID), np.nan, dtype=np.float32)
                    reproject(rasterio.band(src, 1), part, dst_transform=dst_tf, dst_crs="EPSG:4326", resampling=Resampling.bilinear, dst_nodata=np.nan)
                    dem = np.where(np.isnan(dem), part, dem); log[f"cop:{nm}"] = "ok"
            except Exception as e:
                log[f"cop:{nm}"] = str(e)[:200]
dem = np.nan_to_num(dem, nan=float(np.nanmin(dem)) if not np.isnan(dem).all() else 0.0)
log["dem_range"] = [float(dem.min()), float(dem.max())]

# ---------- Imagery ----------
tex = None
try:
    import planetary_computer, pystac_client
    cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=planetary_computer.sign_inplace)
    items = list(cat.search(collections=["naip"], bbox=[W, S, E, N], sortby=[{"field": "properties.datetime", "direction": "desc"}], max_items=40).items())
    log["naip_items"] = len(items)
    if items:
        newest_year = items[0].properties["datetime"][:4]
        items = [i for i in items if i.properties["datetime"][:4] == newest_year]
        log["naip_year"] = newest_year
        tex = np.zeros((3, TEX, TEX), dtype=np.float32); filled = np.zeros((TEX, TEX), bool)
        ttf = tfb(W, S, E, N, TEX, TEX)
        for it in items:
            with rasterio.open(it.assets["image"].href) as src:
                for b in range(3):
                    part = np.zeros((TEX, TEX), dtype=np.float32)
                    reproject(rasterio.band(src, b + 1), part, dst_transform=ttf, dst_crs="EPSG:4326", resampling=Resampling.average, src_nodata=0, dst_nodata=0)
                    m = (part > 0) & ~filled
                    tex[b][m] = part[m]
                filled |= tex[0] > 0
        log["naip_fill"] = float(filled.mean())
        tex = np.clip(tex / 255.0, 0, 1)
except Exception as e:
    log["naip_err"] = str(e)[:300]
if tex is None or log.get("naip_fill", 0) < 0.9:
    try:
        import pystac_client
        cat = pystac_client.Client.open("https://earth-search.aws.element84.com/v1")
        items = list(cat.search(collections=["sentinel-2-l2a"], bbox=[W, S, E, N], datetime="2025-04-01/2026-09-30",
                                query={"eo:cloud_cover": {"lt": 3}}, max_items=10).items())
        log["s2_items"] = len(items)
        it = items[0]; tex = np.zeros((3, TEX, TEX), dtype=np.float32); ttf = tfb(W, S, E, N, TEX, TEX)
        for b, key in enumerate(["red", "green", "blue"]):
            with rasterio.open(it.assets[key].href) as src:
                reproject(rasterio.band(src, 1), tex[b], dst_transform=ttf, dst_crs="EPSG:4326", resampling=Resampling.cubic)
        tex = np.clip(tex / 3000.0, 0, 1) ** 0.85
        log["s2_used"] = it.id
    except Exception as e:
        log["s2_err"] = str(e)[:300]
if tex is None:
    tex = np.ones((3, TEX, TEX), dtype=np.float32) * 0.6
# grade: slight warmth + contrast for cinematic look
tex = np.clip((tex - 0.5) * 1.12 + 0.5, 0, 1); tex[0] *= 1.04; tex[2] *= 0.96
tex8 = (np.clip(tex, 0, 1).transpose(1, 2, 0) * 255).astype(np.uint8)
from PIL import Image
Image.fromarray(tex8).save(f"{OUT}/texture.jpg", quality=92)
np.save(f"{OUT}/dem.npy", dem)

# ---------- Mesh ----------
import pyvista as pv
lat0 = (S + N) / 2
mx = 111320 * math.cos(math.radians(lat0)); my = 110540
exag = CFG.get("exag", 1.15)
xs = np.linspace(0, (E - W) * mx, GRID); ys = np.linspace((N - S) * my, 0, GRID)
X, Y = np.meshgrid(xs, ys)
Z = (dem - dem.min()) * exag
grid = pv.StructuredGrid(X, Y, Z)
u = np.linspace(0, 1, GRID); v = np.linspace(1, 0, GRID)
U, V = np.meshgrid(u, v)
grid.active_texture_coordinates = np.c_[U.ravel(order="F"), V.ravel(order="F")]
texture = pv.read_texture(f"{OUT}/texture.jpg")
base = float(dem.min())

def to_xyz(lon, lat, alt_above_ground):
    x = (lon - W) * mx; y = (lat - S) * my
    i = int(np.clip((N - lat) / (N - S) * (GRID - 1), 0, GRID - 1)); j = int(np.clip((lon - W) / (E - W) * (GRID - 1), 0, GRID - 1))
    ground = (dem[i, j] - base) * exag
    return np.array([x, y, ground + alt_above_ground])

def spline(pts, n):
    pts = np.array(pts, dtype=float)
    if len(pts) == 2:
        t = np.linspace(0, 1, n)[:, None]; return pts[0] + (pts[1] - pts[0]) * (3 * t**2 - 2 * t**3)
    # Catmull-Rom through points, eased
    P = np.vstack([pts[0], pts, pts[-1]]); segs = len(pts) - 1; out = []
    tt = np.linspace(0, 1, n); tt = 3 * tt**2 - 2 * tt**3
    for t in tt:
        s = min(int(t * segs), segs - 1); lt = t * segs - s
        p0, p1, p2, p3 = P[s], P[s + 1], P[s + 2], P[s + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * lt + (2 * p0 - 5 * p1 + 4 * p2 - p3) * lt**2 + (-p0 + 3 * p1 - 3 * p2 + p3) * lt**3))
    return np.array(out)

FPS = CFG.get("fps", 30); WID = CFG.get("w", 1920); HEI = CFG.get("h", 1080)
pl = pv.Plotter(off_screen=True, window_size=(WID, HEI))
pl.add_mesh(grid, texture=texture, smooth_shading=True, ambient=0.35, diffuse=0.75, specular=0.05)
pl.set_background([0.62, 0.74, 0.88], top=[0.30, 0.45, 0.70])
light = pv.Light(position=to_xyz(W - (E - W), S + (N - S) * 0.2, 25000), light_type="scene light", intensity=0.85, color=[1.0, 0.95, 0.85])
pl.add_light(light)
try:
    pl.enable_depth_peeling(); pl.enable_anti_aliasing("ssaa")
except Exception:
    pass
pl.camera.view_angle = CFG.get("fov", 38)
for shot in CFG["shots"]:
    n = int(shot["secs"] * FPS)
    cam = spline([to_xyz(*p) for p in shot["path"]], n)
    look = spline([to_xyz(*p) for p in shot["look"]], n)
    fn = f"{OUT}/{shot['name']}.mp4"
    pl.open_movie(fn, framerate=FPS, quality=9)
    for k in range(n):
        pl.camera.position = cam[k]; pl.camera.focal_point = look[k]; pl.camera.up = (0, 0, 1)
        pl.camera.clipping_range = (10, 200000)
        pl.write_frame()
    log[f"shot:{shot['name']}"] = n
    print("shot", shot["name"], n, flush=True)
pl.close()
json.dump(log, open(f"{OUT}/flyover_log.json", "w"), indent=1)
print(json.dumps(log, indent=1))
