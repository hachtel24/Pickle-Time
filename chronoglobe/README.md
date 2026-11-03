# Chronoglobe: a voxel history globe

A Minecraft-style rotating Earth that plays 5,000 years of political borders
(3000 BCE to 2024 CE) with typed captions, polity labels and a year counter.
`chronoglobe.html` is fully self-contained (1.8 MB: data, font and three.js inlined).

**Controls:** space or click PAUSE to pause · drag to look around · scroll to zoom ·
scrubber to jump · add `?rec=1` to hide the controls for screen recording ·
add `?t=63` to freeze on a given second.

## WWII theater views
From 1939 to 1945 the globe switches from polity colors to alliances (Allies,
Axis, Vichy France, neutral countries in their natural terrain colors). The
camera pulls in on each theater with country and city tags, a date box with a
legend, and dated captions: invasion of Poland, fall of France, Operation
Barbarossa, Pearl Harbor, El Alamein, Operation Torch, Stalingrad and D-Day.
Alliance membership changes by year (`ALLY` in `build/template.html`): for
example the USSR joins the Allies in 1941, the US in 1942 (after Pearl Harbor),
and Vichy French Africa and Italy switch sides in 1943-44.

## Battlefield zoom-ins
At six key moments the camera dives from the globe into a voxel diorama built on
that spot's real terrain (AWS Terrain Tiles at zoom 10-12), with scripted armies,
a date box and legend, a location tag and dated captions:

| Year | Battlefield | What happens |
|---|---|---|
| 331 BCE | Gaugamela | Phalanx and Persian line, scythed chariots, Alexander's cavalry charge, Darius flees |
| 1453 | Constantinople | Bombards against the Theodosian walls (with outer wall and moat), the breach, Hagia Sophia, Galata Tower, ships in the Golden Horn |
| 1914 | River Marne | Real Marne valley, Paris taxis bringing troops, German advance and retreat, trenches dug |
| 1942 | El Alamein | Real coastline and coastal railway, minefields, Allied armour breaking the Axis line |
| 1944 | Omaha Beach | Warships, landing craft, beach obstacles, bunkers on the real bluffs |
| 1989 | Brandenburg Gate | The Wall and death strip, crowds climbing the Wall, fireworks, the Wall pulled down |

Add a battle by adding a site to `build/build_sites.py` (lat, lon, window km)
and a matching entry in `SITES` inside `build/template.html`.

## Data (all real, open licenses)
| Layer | Source | License |
|---|---|---|
| Borders | Cliopatria v0.2.1, Seshat Global History Databank | CC BY 4.0 (credit required) |
| Elevation / ocean depth | AWS Terrain Tiles (Mapzen terrarium); bathymetry from NOAA ETOPO1, land from SRTM/GMTED | open |
| Land, lakes, glaciers, deserts/tundra | Natural Earth 1:50m | public domain |
| Font | Monocraft | OFL 1.1 |
| Engine | three.js r160 | MIT |

ETOPO 2022 (NOAA NCEI) could not be downloaded from the build environment,
so elevation comes from AWS Terrain Tiles. To use ETOPO 2022 instead, swap
the `elev_at()` sampler in `build/build_data.py` to read the 60 arc-second
GeoTIFF with `rasterio`.

## How it works
1. `build/build_data.py` places 110,000 blocks on a Fibonacci sphere. For each
   block it samples elevation, land/water, ice and biome. For 50 keyframe
   years it finds which Cliopatria polity contains each land block
   (shapely STRtree; the smallest polygon wins where polygons overlap) and
   picks label anchors for the largest polities. The output is gzip-packed
   into `data.json` (~0.8 MB).
2. `build/template.html` renders the blocks as a single three.js
   `InstancedMesh` with a pixel texture. It recolors land per keyframe with a
   staggered "voxel flip", darkens border blocks, and runs the captioned
   camera tour.
3. `build/assemble.py` inlines the font, three.js and data into one HTML file.

### Rebuild
```
pip install shapely numpy pillow
# download: cliopatria.geojson (github.com/Seshat-Global-History-Databank/cliopatria),
#   Natural Earth 50m geojson (land, lakes, glaciated_areas, geography_regions_polys),
#   terrarium z3 tiles (s3.amazonaws.com/elevation-tiles-prod/terrarium/3/x/y.png),
#   Monocraft.ttf, three.min.js, into a dl/ folder (see paths in the scripts)
python build_data.py dl data.json
python build_sites.py dl/sitetiles sites.json
python assemble.py . chronoglobe.html
```
Edit the `TOUR` list in `template.html` to change the story: each entry is
`[year, focus latitude, focus longitude, caption]`.
