"""Fetch real local terrain for each zoom-in battlefield (AWS Terrain Tiles, terrarium PNG).

Usage: python build_sites.py <tile_cache_dir> <out.json>
Each site becomes a G x G grid of elevations in metres, gzip+base64 packed (int16).
"""
import sys, os, math, json, gzip, base64, urllib.request, io
import numpy as np
from PIL import Image

CACHE, OUT = sys.argv[1], sys.argv[2]
G = 112
# key: (lat, lon, window km)
SITES = {
    "gaugamela":      (36.565, 43.430, 20),
    "constantinople": (41.016, 28.952, 11),
    "marne":          (48.960, 3.050, 30),
    "alamein":        (30.820, 28.950, 34),
    "normandy":       (49.355, -0.860, 9),
    "berlin":         (52.5165, 13.3790, 5),
    "giza":           (29.9770, 31.1360, 2.6),
    "pompeii":        (40.7900, 14.4400, 16),
    "hastings":       (50.9110, 0.4875, 3),
    "armada":         (51.0100, 1.9800, 22),
    "bastille":       (48.8520, 2.3670, 1.4),
    "waterloo":       (50.6800, 4.4100, 6),
    "apollo":         (28.6060, -80.5990, 4),
}

def tile(z, x, y):
    p = os.path.join(CACHE, f"{z}_{x}_{y}.png")
    if not os.path.exists(p):
        url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
        with urllib.request.urlopen(url, timeout=60) as r:
            open(p, "wb").write(r.read())
    a = np.asarray(Image.open(p).convert("RGB"), np.float32)
    return a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768

def gpx(lat, lon, z):
    n = 2 ** z * 256
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y

out = {}
os.makedirs(CACHE, exist_ok=True)
for key, (lat0, lon0, km) in SITES.items():
    # zoom where one 256px tile spans about the window, so 112 samples ~ native resolution
    z = int(round(math.log2(40075 * math.cos(math.radians(lat0)) / km)))
    z = max(5, min(14, z))
    elev = np.zeros((G, G), np.float32)
    lats = lat0 + (0.5 - (np.arange(G) + 0.5) / G) * km / 111.32          # row j: north -> south
    lons = lon0 + ((np.arange(G) + 0.5) / G - 0.5) * km / (111.32 * math.cos(math.radians(lat0)))
    cache = {}
    for j, la in enumerate(lats):
        for i, lo in enumerate(lons):
            x, y = gpx(la, lo, z)
            tx, ty = int(x // 256), int(y // 256)
            if (tx, ty) not in cache:
                cache[(tx, ty)] = tile(z, tx, ty)
            t = cache[(tx, ty)]
            px, py = min(255, int(x % 256)), min(255, int(y % 256))
            elev[j, i] = t[py, px]
    print(key, "z", z, "tiles", len(cache), "elev range", int(elev.min()), int(elev.max()))
    out[key] = {"lat": lat0, "lon": lon0, "km": km, "g": G,
                "elev": base64.b64encode(gzip.compress(np.round(elev).astype(np.int16).tobytes(), 9)).decode()}
json.dump(out, open(OUT, "w"), separators=(",", ":"))
print("bytes", os.path.getsize(OUT))
