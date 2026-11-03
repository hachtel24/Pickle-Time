# Chronoglobe: a voxel history globe

A Minecraft-style rotating Earth that plays 5,000 years of political borders
(3000 BCE to 2024 CE) with typed captions, polity labels and a year counter.
`chronoglobe.html` is fully self-contained (1.8 MB: data, font and three.js inlined).

**Start screen:** play with narration, play silently, or choose a moment.
**Narration:** the browser's built-in voice reads every caption, and the tour waits
for the narrator to finish before moving on. Toggle it with the NARRATION button.
**Menu (☰ or M):** every chapter and all 50 stops; click one to jump there. Chapter
segments in the progress bar are clickable too.
**Deep dives:** 25 major events have a fact card (key numbers, what happened, why it
matters). Open one from the menu, or from the DEEP DIVE button that appears while
that event plays; WATCH THIS MOMENT jumps to it and READ ALOUD narrates the card.
Every zoom-in also ends with an extra aftermath scene.

**Controls:** space or click PAUSE to pause · drag to look around · scroll to zoom ·
scrubber to jump · add `?rec=1` to hide the controls for screen recording ·
add `?t=63` to freeze on a given second.

## Flag colours
Each polity's blocks show its flag, stretched over the polity's own latitude and
longitude box (hoist on the west, top at north), so France reads as a blue-white-red
tricolour and the US shows stripes and a blue canton. States from before national flags
use their traditional banner or dynastic colours (Roman red and gold, Byzantine purple,
Abbasid black, Mongol sky blue and gold, and so on). Polities of fewer than 25 blocks use
the flag's strongest colour, and legend swatches are rendered mini flags. The rules are
the `FLAGS` table in `build/template.html`, matched by name; anything unmatched keeps its
generated colour. During WWII (1939–45) the alliance colours take over.

## WWII theater views
From 1939 to 1945 the globe switches from polity colors to alliances (Allies,
Axis, Vichy France, neutral countries in their natural terrain colors). The
camera pulls in on each theater with country and city tags, a date box with a
legend, and dated captions: invasion of Poland, fall of France, Operation
Barbarossa, Pearl Harbor, El Alamein, Operation Torch, Stalingrad and D-Day.
Alliance membership changes by year (`ALLY` in `build/template.html`): for
example the USSR joins the Allies in 1941, the US in 1942 (after Pearl Harbor),
and Vichy French Africa and Italy switch sides in 1943-44.

## Structure: 8 chapters, 50 stops, 13 zoom-ins (about 12 minutes)
Each chapter opens with a title card, and the red bar along the bottom is split by
chapter. Every stop is a dated theater view: the camera pulls in on the region, with
country and city tags and a legend. The legend lists alliances during WWII and the
largest real Cliopatria polities near the focus in every other era.

| Chapter | Zoom-ins (real terrain + animation) |
|---|---|
| 1 First Empires | **Giza, c. 2560 BCE**: Great Pyramid rising layer by layer; sleds hauled up the ramp; boats on the harbour canal |
| 2 The Classical World | **Gaugamela, 331 BCE**: phalanx, scythed chariots, Alexander's cavalry, Darius flees |
| 3 Rome and Han | **Pompeii, 79 CE**: Vesuvius ash column and umbrella cloud; pyroclastic flows bury Pompeii and Herculaneum |
| 4 Faith and Conquest | **Hastings, 1066**: Saxon shield wall on Senlac Hill, Norman feigned retreats, the line breaks |
| 5 Gunpowder and Sail | **Constantinople, 1453**; **Gravelines, 1588**: fireships scatter the Armada |
| 6 Revolutions and Empires | **Bastille, 1789**: crowds storm the fortress; **Waterloo, 1815**: cavalry vs. squares, Prussians arrive, the Guard breaks |
| 7 The World Wars | **Marne, 1914**; **El Alamein, 1942**; **Omaha Beach, 1944** |
| 8 The Modern World | **Apollo 11, 1969**: Saturn V liftoff with a tracking camera; **Brandenburg Gate, 1989** |

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
