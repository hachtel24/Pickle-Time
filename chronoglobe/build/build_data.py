"""Bake real geodata onto a voxel Fibonacci sphere for the Chronoglobe player.

Inputs (all downloaded, open licenses):
  - Cliopatria v0.2.1 (Seshat, CC BY 4.0) polity borders
  - AWS Terrain Tiles (terrarium z3; bathymetry from NOAA ETOPO1, land from SRTM/GMTED)
  - Natural Earth 1:50m land, glaciated areas, lakes, geography regions (public domain)
Output: data.json with gzip+base64 packed typed arrays.
"""
import json, math, sys, gzip, base64, colorsys, hashlib
import numpy as np
from PIL import Image
from shapely.geometry import shape, Point
from shapely import STRtree, points as mkpoints
import shapely

DL = sys.argv[1]
OUT = sys.argv[2]
N = 110000

# ---------- Fibonacci sphere
i = np.arange(N) + 0.5
phi = np.arccos(1 - 2 * i / N)              # 0..pi from north pole
theta = np.pi * (1 + 5 ** 0.5) * i
lat = 90 - np.degrees(phi)
lon = (np.degrees(theta) + 180) % 360 - 180

# ---------- elevation from terrarium tiles (web mercator z3, 2048px)
Z = 3; T = 256; S = T * 2 ** Z
mer = np.zeros((S, S), np.float32)
for x in range(8):
    for y in range(8):
        a = np.asarray(Image.open(f"{DL}/tiles/3_{x}_{y}.png").convert("RGB"), np.float32)
        mer[y*T:(y+1)*T, x*T:(x+1)*T] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
def elev_at(la, lo):
    la = np.clip(la, -85.0, 85.0)
    px = (lo + 180) / 360 * S
    py = (1 - np.log(np.tan(np.radians(la)) + 1 / np.cos(np.radians(la))) / np.pi) / 2 * S
    # bilinear-ish: average 2x2 neighborhood for smoother sampling
    x0 = np.clip(px.astype(int), 0, S - 2); y0 = np.clip(py.astype(int), 0, S - 2)
    return (mer[y0, x0] + mer[y0, x0+1] + mer[y0+1, x0] + mer[y0+1, x0+1]) / 4
elev = elev_at(lat, lon)
# beyond the mercator limit: Antarctic ice sheet / Arctic ocean
elev[lat < -85] = 2800
elev[lat > 85] = -3000

pts = mkpoints(lon, lat)

def load(name):
    return [shape(f["geometry"]) for f in json.load(open(f"{DL}/{name}.geojson"))["features"]]

def inside_any(geoms):
    tree = STRtree(geoms)
    idx_pt, _ = tree.query(pts, predicate="within")
    m = np.zeros(N, bool); m[np.unique(idx_pt)] = True
    return m

land = inside_any(load("ne_50m_land"))
lakes = inside_any(load("ne_50m_lakes"))
ice = inside_any(load("ne_50m_glaciated_areas"))
land &= ~lakes
land |= lat < -85            # Antarctica beyond polygon precision
ice |= lat < -85
regions = json.load(open(f"{DL}/ne_50m_geography_regions_polys.geojson"))["features"]
deserts = [shape(f["geometry"]) for f in regions if f["properties"]["FEATURECLA"] == "Desert"]
tundra = [shape(f["geometry"]) for f in regions if f["properties"]["FEATURECLA"] == "Tundra"]
desert = inside_any(deserts) & land
tun = inside_any(tundra) & land

# ---------- terrain class per block
# 0 deep ocean,1 ocean,2 shallow,3 sand/beach,4 grass,5 forest,6 taiga,7 desert,8 stone,9 snow/ice,10 tundra,11 jungle
cls = np.zeros(N, np.uint8)
alat = np.abs(lat)
ocean = ~land
cls[ocean & (elev < -3500)] = 0
cls[ocean & (elev >= -3500)] = 1
cls[ocean & (elev >= -400)] = 2
L = land
cls[L] = 4
cls[L & (alat < 15)] = 11
cls[L & (alat >= 15) & (alat < 50) & (elev > 300)] = 4
cls[L & (alat >= 48) & (alat < 66)] = 6
cls[L & desert] = 7
cls[L & tun] = 10
cls[L & (alat >= 66)] = 10
cls[L & (elev > 2600)] = 8
cls[L & (elev > 4300)] = 9
cls[L & ice] = 9
cls[L & (elev < 25) & (alat < 45) & ~desert] = np.where(np.random.default_rng(1).random((L & (elev < 25) & (alat < 45) & ~desert).sum()) < 0.25, 3, cls[L & (elev < 25) & (alat < 45) & ~desert])
# break up big uniform grass with forest patches (deterministic noise on lat/lon)
noise = (np.sin(lat * 0.37 + lon * 0.21) + np.sin(lat * 0.11 - lon * 0.43 + 1.7) + np.sin((lat + lon) * 0.9)) / 3
cls[(cls == 4) & (noise > 0.18)] = 5

# height in voxel layers
h = np.zeros(N, np.int8)
h[L] = np.clip(1 + np.round(np.sqrt(np.maximum(elev[L], 0)) / 12), 1, 9)
h[L & ice & (lat < -60)] = np.maximum(h[L & ice & (lat < -60)], 4)
h[ocean] = np.where(elev[ocean] > -400, 0, np.where(elev[ocean] > -3500, -1, -2))

landIdx = np.where(L)[0]
print("blocks", N, "land", len(landIdx))

# ---------- neighbors for land blocks (for border outlines), 6 nearest via unit vectors in a grid hash
xyz = np.stack([np.sin(phi) * np.cos(np.radians(lon)), np.cos(phi), -np.sin(phi) * np.sin(np.radians(lon))], 1)
from collections import defaultdict
spacing = math.sqrt(4 * math.pi / N)
cell = spacing * 1.6
keys = np.floor(xyz / cell).astype(int)
grid = defaultdict(list)
for k, p in zip(map(tuple, keys), range(N)):
    grid[k].append(p)
nbr = np.full((len(landIdx), 6), -1, np.int32)
for j, p in enumerate(landIdx):
    k = keys[p]; cand = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                cand += grid.get((k[0]+dx, k[1]+dy, k[2]+dz), [])
    cand = np.array([c for c in cand if c != p])
    d = np.linalg.norm(xyz[cand] - xyz[p], axis=1)
    nbr[j, :min(6, len(cand))] = cand[np.argsort(d)[:6]]

# ---------- Cliopatria polities per keyframe year
YEARS = [-3000, -2560, -2500, -2200, -1800, -1750, -1500, -1274, -1250, -1000, -800, -600, -500, -480, -400, -331, -323, -250, -221, -218, -200, -100, -44, 1, 79, 117, 200, 220, 300, 330, 400, 476, 600, 632, 700, 750, 800, 850, 1000, 1066, 1099, 1100, 1200, 1279, 1347, 1350, 1453, 1492, 1500, 1521, 1533, 1550, 1588, 1600, 1650, 1700, 1750, 1776, 1789, 1800, 1815, 1850, 1869, 1880, 1900, 1914, 1917, 1918, 1920, 1939, 1940, 1941, 1942, 1943, 1944, 1945, 1948, 1950, 1960, 1962, 1969, 1975, 1989, 1991, 2024]
clio = json.load(open(f"{DL}/clio/cliopatria_polities_only_v021.geojson"))["features"]
clio = [f for f in clio if f["properties"].get("Type", "POLITY") == "POLITY" and f["geometry"]]
names = []; nameId = {}
def nid(n):
    if n not in nameId:
        nameId[n] = len(names); names.append(n)
    return nameId[n]
landPts = pts[landIdx]
frames = []
labels = {}
for y in YEARS:
    act = [f for f in clio if f["properties"]["FromYear"] <= y <= f["properties"]["ToYear"]]
    geoms = [shape(f["geometry"]) for f in act]
    geoms = [shapely.make_valid(g) if not g.is_valid else g for g in geoms]
    area = np.array([f["properties"]["Area"] or 1e12 for f in act])
    owner = np.zeros(len(landIdx), np.uint16)   # 0 = unclaimed
    best = np.full(len(landIdx), np.inf)
    if geoms:
        tree = STRtree(geoms)
        ip, ig = tree.query(landPts, predicate="intersects")
        for p, gi in zip(ip, ig):
            if area[gi] < best[p]:
                best[p] = area[gi]; owner[p] = nid(act[gi]["properties"]["Name"]) + 1
    frames.append(owner)
    # label anchors: biggest polities by block count
    u, c = np.unique(owner[owner > 0], return_counts=True)
    top = u[np.argsort(-c)][:14]
    lab = []
    for o in top:
        v = xyz[landIdx[owner == o]].mean(0); v /= np.linalg.norm(v) + 1e-9
        lab.append([int(o) - 1, round(float(v[0]), 4), round(float(v[1]), 4), round(float(v[2]), 4), int(c[u == o][0])])
    labels[y] = lab
    print(y, len(act), "polities;", int((owner > 0).sum()), "claimed blocks")

def col(n):
    hsh = int(hashlib.md5(n.encode()).hexdigest()[:8], 16)
    hue = (hsh % 360) / 360; sat = 0.55 + (hsh >> 9) % 30 / 100; val = 0.78 + (hsh >> 15) % 18 / 100
    r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
    return "#%02x%02x%02x" % (int(r*255), int(g*255), int(b*255))

def pack(a):
    return base64.b64encode(gzip.compress(np.ascontiguousarray(a).tobytes(), 9)).decode()

out = {
    "n": N, "years": YEARS, "names": names, "colors": [col(n) for n in names],
    "cls": pack(cls), "h": pack(h), "landIdx": pack(landIdx.astype(np.int32)),
    "nbr": pack(nbr), "frames": pack(np.stack(frames)), "labels": labels,
}
json.dump(out, open(OUT, "w"), separators=(",", ":"))
import os; print("data bytes", os.path.getsize(OUT))
