"""Generate the chrome watch-face assets (480 px design width, round).

Usage: python gen_assets.py <helvetiker_bold.typeface.json> <out_assets_dir> <preview_png>
Digits use the same helvetiker bold outlines as the Liquid Chrome videos and are shaded
as polished chrome: a dome bevel from a blurred mask gives normals, and the normals pick
colours from a studio "sky / horizon / floor" gradient with a specular kick.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

FONT, OUT, PREVIEW = sys.argv[1], sys.argv[2], sys.argv[3]
SS = 4                       # supersampling
F = json.load(open(FONT))
RES = F["resolution"]

# ---------------------------------------------------------------- glyph outlines
def glyph_contours(ch, size):
    g = F["glyphs"][ch]; o = g["o"].split(); s = size / RES
    cs, cur, i = [], [], 0
    def P(a, b): return (float(a) * s, -float(b) * s)
    while i < len(o):
        c = o[i]; i += 1
        if c == "m":
            if cur: cs.append(cur)
            cur = [P(o[i], o[i + 1])]; i += 2
        elif c == "l":
            cur.append(P(o[i], o[i + 1])); i += 2
        elif c == "q":                                  # end x y, control x y
            ex, ey = P(o[i], o[i + 1]); cx, cy = P(o[i + 2], o[i + 3]); i += 4
            x0, y0 = cur[-1]
            for t in np.linspace(0, 1, 12)[1:]:
                cur.append(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * ex, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * ey))
        elif c == "b":                                  # end, cp1, cp2
            ex, ey = P(o[i], o[i + 1]); c1 = P(o[i + 2], o[i + 3]); c2 = P(o[i + 4], o[i + 5]); i += 6
            x0, y0 = cur[-1]
            for t in np.linspace(0, 1, 16)[1:]:
                a, b, c_, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
                cur.append((a * x0 + b * c1[0] + c_ * c2[0] + d * ex, a * y0 + b * c1[1] + c_ * c2[1] + d * ey))
        elif c == "z":
            pass
    if cur: cs.append(cur)
    return cs, g["ha"] * s

def glyph_mask(ch, size, w, h, baseline, x_off=None):
    """Even-odd fill of the glyph into a w x h mask (pixel units, already supersampled)."""
    cs, adv = glyph_contours(ch, size)
    xs = [p[0] for c in cs for p in c]
    if x_off is None: x_off = (w - (max(xs) - min(xs))) / 2 - min(xs)     # centre the ink
    m = np.zeros((h, w), bool)
    for c in cs:
        im = Image.new("1", (w, h), 0)
        ImageDraw.Draw(im).polygon([(x + x_off, y + baseline) for x, y in c], fill=1)
        m ^= np.asarray(im, bool)
    return m

# ---------------------------------------------------------------- chrome shader
SKY0, SKY1 = np.array([1.0, 1.0, 1.0]), np.array([.55, .61, .70])
HOR = np.array([.06, .07, .09])
GND0, GND1 = np.array([.22, .24, .29]), np.array([.88, .90, .93])

def env(t):
    """Studio gradient sampled at t (0 top .. 1 bottom): bright sky, dark horizon, light floor."""
    t = np.clip(t, 0, 1)[..., None]
    sky = SKY0 + (SKY1 - SKY0) * np.clip(t / .5, 0, 1)
    gnd = GND0 + (GND1 - GND0) * np.clip((t - .5) / .5, 0, 1)
    c = np.where(t < .5, sky, gnd)
    band = np.exp(-((t - .5) / .022) ** 2)                 # sharp horizon line
    return c * (1 - band) + HOR * band

def chrome(mask, bevel, y0=None, y1=None, strength=2.2, dim=1.0):
    """mask: supersampled bool array. Returns RGBA image downsampled by SS."""
    h, w = mask.shape
    m = Image.fromarray((mask * 255).astype(np.uint8))
    dome = np.asarray(m.filter(ImageFilter.GaussianBlur(bevel)), float) / 255
    height = np.clip(dome * 2.0, 0, 1) ** .6 * mask                      # rounded edge, flat top
    hb = np.asarray(Image.fromarray((height * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(bevel * .35)), float) / 255
    gy, gx = np.gradient(hb)
    n = np.dstack([-gx * strength * bevel, -gy * strength * bevel, np.ones_like(hb)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    ys = np.arange(h)[:, None] * np.ones((1, w))
    if y0 is None:
        rows = np.where(mask.any(1))[0]; y0, y1 = rows.min(), rows.max()
    t = (ys - y0) / max(1, (y1 - y0)) + n[..., 1] * .55                 # bevel normals bend the reflection
    col = env(t)
    L = np.array([-.45, -.6, .66]); L /= np.linalg.norm(L)
    H = L + np.array([0, 0, 1]); H /= np.linalg.norm(H)
    spec = np.clip((n * H).sum(2), 0, 1) ** 60
    col = col + spec[..., None] * 1.1
    rim = np.clip(1 - height * 3, 0, 1)                                  # thin dark edge for definition
    col = col * (1 - .35 * rim[..., None])
    col = np.clip(col * dim, 0, 1)
    rgba = np.dstack([col * 255, mask * 255]).astype(np.uint8)
    im = Image.fromarray(rgba, "RGBA")
    # premultiplied downsample so edges stay clean on black
    pm = np.asarray(im, float); pm[..., :3] *= pm[..., 3:4] / 255
    small = Image.fromarray(pm.astype(np.uint8), "RGBA").resize((w // SS, h // SS), Image.LANCZOS)
    a = np.asarray(small, float); out = a.copy()
    out[..., :3] = np.where(a[..., 3:4] > 0, a[..., :3] * 255 / np.maximum(a[..., 3:4], 1), 0)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")

def save(im, rel):
    p = os.path.join(OUT, rel); os.makedirs(os.path.dirname(p), exist_ok=True); im.save(p, optimize=True); return im

# ---------------------------------------------------------------- digit sets
def ink_bounds(ch, size):
    """(xmin, xmax, ymin, ymax) of the glyph's actual outline, y down from the baseline."""
    pts = [p for c in glyph_contours(ch, size)[0] for p in c]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)

def digit_set(folder, em, extra, dim=1.0, bevel_k=.055):
    # Size every box from the measured ink (round digits overshoot the cap height),
    # plus a margin, so no glyph is ever cropped. All glyphs in a set share one height
    # and baseline so they line up when the watch tiles them.
    chars = list("0123456789") + [c for c, _ in extra]
    b = {c: ink_bounds(c, em) for c in chars}
    top = min(v[2] for v in b.values()); bot = max(v[3] for v in b.values())
    pad = max(4, math.ceil(em * .06))           # room for the anti-aliased edge
    hpad = 3                                                # sides only need anti-alias room; keeps digits tight
    hpx = math.ceil(bot - top) + 2 * pad
    baseline = pad - top
    dig_ink = max(b[d][1] - b[d][0] for d in "0123456789")
    wpx = math.ceil(dig_ink) + 2 * hpad                      # fixed width so the clock never shifts
    out = {}
    for ch in chars:
        name = dict(extra).get(ch, ch)
        cw = wpx if ch.isdigit() else math.ceil(b[ch][1] - b[ch][0]) + 2 * hpad
        m = glyph_mask(ch, em * SS, cw * SS, hpx * SS, baseline * SS)
        out[name] = save(chrome(m, bevel=em * SS * bevel_k, y0=(baseline + top) * SS, y1=(baseline + bot) * SS, dim=dim), f"{folder}/{name}.png")
    return out, wpx, hpx

big, BW, BH = digit_set("time", 104, [(":", "colon")])
aod, _, _ = digit_set("time_aod", 104, [(":", "colon")], dim=.42)
small, SW, SH = digit_set("data", 26, [("%", "percent")], bevel_k=.07)

# ---------------------------------------------------------------- icons (drawn as vector shapes, chromed)
def icon(name, draw_fn, size=50):
    S = size * SS; im = Image.new("1", (S, S), 0); d = ImageDraw.Draw(im); draw_fn(d, S)
    return save(chrome(np.asarray(im, bool), bevel=S * .06), f"icons/{name}.png")

def steps_icon(d, S):        # two shoe soles with toes
    for ox, oy in [(.30, .55), (.66, .38)]:
        d.ellipse([S * (ox - .13), S * (oy - .22), S * (ox + .13), S * (oy + .14)], fill=1)
        d.ellipse([S * (ox - .10), S * (oy + .17), S * (ox + .10), S * (oy + .33)], fill=1)
def flame_icon(d, S):        # outer flame with an inner cut-out
    def flame(cx, cy, w, h):
        pts = []
        for k in range(60):
            a = k / 60 * 2 * math.pi
            up = max(0, math.sin(a))
            r = 1 - .78 * up ** 1.6                        # narrows to a sharp tip
            lean = .22 * up ** 2 * w                       # tip leans right like a flicker
            pts.append((cx + math.cos(a) * w * r + lean, cy - math.sin(a) * h * (1.45 if math.sin(a) > 0 else .62)))
        return pts
    d.polygon(flame(S * .5, S * .62, S * .30, S * .40), fill=1)
    d.polygon(flame(S * .27, S * .70, S * .11, S * .22), fill=1)      # small side lick
    d.polygon(flame(S * .5, S * .72, S * .13, S * .20), fill=0)
def battery_icon(d, S):      # outline body, nub and three cells
    d.rounded_rectangle([S * .08, S * .26, S * .84, S * .74], radius=S * .08, fill=1)
    d.rounded_rectangle([S * .15, S * .33, S * .77, S * .67], radius=S * .04, fill=0)
    d.rectangle([S * .84, S * .40, S * .93, S * .60], fill=1)
    for k in range(3): d.rectangle([S * (.19 + k * .19), S * .37, S * (.33 + k * .19), S * .63], fill=1)

icons = {"steps": icon("steps", steps_icon), "cal": icon("cal", flame_icon), "battery": icon("battery", battery_icon)}

# ---------------------------------------------------------------- background: chrome bezel ring + hour ticks on black
S = 480 * SS; yy, xx = np.mgrid[0:S, 0:S]; r = np.hypot(xx - S / 2, yy - S / 2) / SS
ring = (r < 238) & (r > 229)
ang = np.arctan2(yy - S / 2, xx - S / 2)
tick = np.zeros_like(ring)
for k in range(12):
    a = k * math.pi / 6; da = np.abs(np.angle(np.exp(1j * (ang - a))))
    tick |= (da * r < (3.2 if k % 3 == 0 else 1.6)) & (r > (206 if k % 3 == 0 else 214)) & (r < 224)
bez = chrome(ring | tick, bevel=SS * 2.2, y0=0, y1=S)
bg = Image.new("RGBA", (480, 480), (0, 0, 0, 255)); bg.alpha_composite(bez)
save(bg.convert("RGB"), "bg.png")

# ---------------------------------------------------------------- layout constants (shared with the JS)
TIME_Y, ICON_Y, DATA_Y, COLS = 124, 266, 322, [122, 240, 358]   # keep in sync with watchface/index.js
LAYOUT = {"BW": BW, "BH": BH, "CW": big["colon"].width, "SW": SW, "SH": SH, "PW": small["percent"].width}
json.dump(LAYOUT, open(os.path.join(OUT, "..", "..", "layout.json"), "w"))

# ---------------------------------------------------------------- mock preview with sample values
def compose(time_txt, data):
    im = bg.copy().convert("RGBA")
    tw = 4 * BW + LAYOUT["CW"]; x = (480 - tw) // 2; y = TIME_Y
    for ch in time_txt:
        g = big["colon"] if ch == ":" else big[ch]; im.alpha_composite(g, (x, y)); x += g.width
    for cx, key, txt in data:
        ic = icons[key]; im.alpha_composite(ic, (cx - ic.width // 2, ICON_Y))
        glyphs = [small["percent"] if c == "%" else small[c] for c in txt]
        wsum = sum(g.width for g in glyphs); x = cx - wsum // 2
        for g in glyphs: im.alpha_composite(g, (x, DATA_Y)); x += g.width
    mask = Image.new("L", (480, 480), 0); ImageDraw.Draw(mask).ellipse([0, 0, 479, 479], fill=255)
    out = Image.new("RGBA", (480, 480), (0, 0, 0, 0)); out.paste(im, (0, 0), mask)
    return out
pv = compose("10:08", [(COLS[0], "steps", "8532"), (COLS[1], "cal", "412"), (COLS[2], "battery", "87%")])
compose("23:58", [(COLS[0], "steps", "12408"), (COLS[1], "cal", "1037"), (COLS[2], "battery", "100%")]).save(PREVIEW.replace(".png", "_wide.png"))
pv.save(PREVIEW); save(pv.resize((240, 240), Image.LANCZOS), "preview.png")
print("assets ok", LAYOUT)
