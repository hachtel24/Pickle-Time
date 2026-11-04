"""Generate the chrome watch-face assets for both screen shapes.

  round  : 480 x 480 circle            -> assets/common.r/   (GTR 3/4, Balance, Active 2 round ...)
  square : 390 x 450, 86 px corners     -> assets/square.s/   (Active 2 Square, GTS 3/4, Bip 5 ...)

Usage: python gen_assets.py <helvetiker_bold.typeface.json> <assets_dir> <preview_dir>
Writes the images, layout.json, and watchface/layouts.js (the numbers the watch code reads).
Digits use the same helvetiker bold outlines as the Liquid Chrome videos and are shaded
as polished chrome: a dome bevel from a blurred mask gives normals, and the normals pick
colours from a studio "sky / horizon / floor" gradient with a specular kick.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

FONT, ASSETS, PREVIEW_DIR = sys.argv[1], sys.argv[2], sys.argv[3]
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = None                    # set per profile in build()
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

# Frosted teal chrome for the hands: teal studio, soft wide horizon (satin, not mirror),
# broad dim highlight and a fine grain, like brushed / bead-blasted anodised metal.
TSKY0, TSKY1 = np.array([.62, .97, .93]), np.array([.12, .60, .62])
THOR = np.array([.02, .20, .23])
TGND0, TGND1 = np.array([.04, .30, .33]), np.array([.36, .80, .78])

def env_teal(t):
    t = np.clip(t, 0, 1)[..., None]
    sky = TSKY0 + (TSKY1 - TSKY0) * np.clip(t / .5, 0, 1)
    gnd = TGND0 + (TGND1 - TGND0) * np.clip((t - .5) / .5, 0, 1)
    c = np.where(t < .5, sky, gnd)
    band = np.exp(-((t - .5) / .09) ** 2)                  # blurred horizon = frosted
    return c * (1 - band) + THOR * band

def chrome(mask, bevel, y0=None, y1=None, strength=2.2, dim=1.0, env_fn=None,
           spec_pow=60, spec_k=1.1, grain=0.0, alpha=1.0, seed=7):
    """mask: supersampled bool array. Returns RGBA image downsampled by SS."""
    env_fn = env_fn or env
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
    col = env_fn(t)
    L = np.array([-.45, -.6, .66]); L /= np.linalg.norm(L)
    H = L + np.array([0, 0, 1]); H /= np.linalg.norm(H)
    spec = np.clip((n * H).sum(2), 0, 1) ** spec_pow
    col = col + spec[..., None] * spec_k
    if grain:
        col = col * (1 + grain * np.random.default_rng(seed).standard_normal((h, w, 1)))
    rim = np.clip(1 - height * 3, 0, 1)                                  # thin dark edge for definition
    col = col * (1 - .35 * rim[..., None])
    col = np.clip(col * dim, 0, 1)
    rgba = np.dstack([col * 255, mask * 255 * alpha]).astype(np.uint8)
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
    hpad = 3                                    # sides only need anti-alias room; keeps digits tight
    hpx = math.ceil(bot - top) + 2 * pad
    baseline = pad - top
    dig_ink = max(b[d][1] - b[d][0] for d in "0123456789")
    wpx = math.ceil(dig_ink) + 2 * hpad         # fixed width so the clock never shifts
    out = {}
    for ch in chars:
        name = dict(extra).get(ch, ch)
        cw = wpx if ch.isdigit() else math.ceil(b[ch][1] - b[ch][0]) + 2 * hpad
        m = glyph_mask(ch, em * SS, cw * SS, hpx * SS, baseline * SS)
        out[name] = save(chrome(m, bevel=em * SS * bevel_k, y0=(baseline + top) * SS, y1=(baseline + bot) * SS, dim=dim), f"{folder}/{name}.png")
    return out, wpx, hpx

# ---------------------------------------------------------------- icons (drawn as vector shapes, chromed)
def icon(name, draw_fn, size):
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

# ---------------------------------------------------------------- screen outline as a signed distance (px, < 0 inside)
def screen_sdf(P, yy, xx):
    """Distance from the physical screen edge, in output pixels (negative = inside)."""
    W, H = P["W"], P["H"]; x = xx / SS - W / 2; y = yy / SS - H / 2
    if P["shape"] == "round":
        return np.hypot(x, y) - W / 2
    R = P["radius"]; qx = np.abs(x) - (W / 2 - R); qy = np.abs(y) - (H / 2 - R)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - R

def screen_mask(P):
    yy, xx = np.mgrid[0:P["H"], 0:P["W"]] * SS + SS / 2
    return Image.fromarray(((screen_sdf(P, yy, xx) < 0) * 255).astype(np.uint8))

# ---------------------------------------------------------------- frosted teal chrome hands
# Each hand is drawn pointing at 12 with its pivot at (posX, posY) inside the image;
# Zepp's TIME_POINTER rotates the image about that point (hour_posX / hour_posY etc.).
def frosted(mask, bevel, dim=1.0, alpha=.93):
    return chrome(mask, bevel, strength=1.6, dim=dim, env_fn=env_teal, spec_pow=14, spec_k=.38, grain=.05, alpha=alpha)

def halo(im, r=3, k=.55):
    """Soft dark outline so the hands stay readable when they sweep over the chrome digits."""
    a = im.split()[3].filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(r))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(a.point(lambda v: int(v * k)))
    sh.alpha_composite(im); return sh

def hand(name, length, tail, width, tip_w, shape, dim=1.0, alpha=.93):
    m = 8                                                   # margin for the halo
    W = int(width + 2 * m); H = int(length + tail + 2 * m)
    px_, py_ = W // 2, m + length                          # pivot
    im = Image.new("1", (W * SS, H * SS), 0); d = ImageDraw.Draw(im)
    X = lambda v: (px_ + v) * SS; Y = lambda v: (py_ - v) * SS     # v measured up from the pivot
    if shape == "dauphine":                                 # widest a third of the way out, sharp tip
        pts = [(0, length), (width / 2, length * .32), (width * .30, -tail), (-width * .30, -tail), (-width / 2, length * .32)]
        d.polygon([(X(x), Y(y)) for x, y in pts], fill=1)
        d.ellipse([X(-width * .42), Y(width * .42), X(width * .42), Y(-width * .42)], fill=1)
    else:                                                   # needle with a round counterweight
        d.polygon([(X(x), Y(y)) for x, y in [(-tip_w / 2, length), (tip_w / 2, length), (width * .16, -tail), (-width * .16, -tail)]], fill=1)
        d.ellipse([X(-width / 2), Y(-tail * .62 + width / 2), X(width / 2), Y(-tail * .62 - width / 2)], fill=1)
    img = halo(frosted(np.asarray(im, bool), bevel=SS * max(1.2, width * .16), dim=dim, alpha=alpha))
    save(img, f"hands/{name}.png")
    return img, (px_, py_)

# ---------------------------------------------------------------- per-shape profiles
PROFILES = {
    "round": dict(shape="round", W=480, H=480, dir="common.r",
                  time_em=104, data_em=26, icon=50, TIME_Y=124, ICON_Y=266, DATA_Y=322, COLS=[122, 240, 358], DATA_W=140,
                  hour=(122, 22, 28), minute=(190, 26, 21), second=(206, 46, 12), CAP=26),
    # Zepp OS square screens (Active 2 Square, GTS 3/4, Bip 5 ...): 390 x 450, 86 px corner radius
    "square": dict(shape="square", W=390, H=450, radius=86, dir="square.s",
                   time_em=88, data_em=20, icon=42, TIME_Y=112, ICON_Y=256, DATA_Y=306, COLS=[86, 195, 304], DATA_W=108,
                   hour=(98, 18, 24), minute=(158, 22, 18), second=(172, 38, 11), CAP=22),
}

def build(name, P):
    global OUT
    OUT = os.path.join(ASSETS, P["dir"])
    W, H = P["W"], P["H"]; CX, CY = W // 2, H // 2
    big, BW, BH = digit_set("time", P["time_em"], [(":", "colon")])
    digit_set("time_aod", P["time_em"], [(":", "colon")], dim=.42)
    small, SW, SH = digit_set("data", P["data_em"], [("%", "percent")], bevel_k=.07)
    icons = {"steps": icon("steps", steps_icon, P["icon"]), "cal": icon("cal", flame_icon, P["icon"]),
             "battery": icon("battery", battery_icon, P["icon"])}

    # background: chrome bezel that follows the screen outline, plus 12 hour ticks, on black
    yy, xx = np.mgrid[0:H * SS, 0:W * SS]
    d = screen_sdf(P, yy + .5, xx + .5)
    ring = (d > -11) & (d < -3)
    ang = np.arctan2(yy - CY * SS, xx - CX * SS); rr = np.hypot(xx - CX * SS, yy - CY * SS) / SS
    tick = np.zeros_like(ring)
    for k in range(12):
        a = k * math.pi / 6; da = np.abs(np.angle(np.exp(1j * (ang - a))))
        major = k % 3 == 0
        tick |= (da < .5) & (da * rr < (3.2 if major else 1.6)) & (d > (-36 if major else -28)) & (d < -16)
    bg = Image.new("RGBA", (W, H), (0, 0, 0, 255)); bg.alpha_composite(chrome(ring | tick, bevel=SS * 2.2, y0=0, y1=H * SS))
    save(bg.convert("RGB"), "bg.png")

    hands = {}
    for k in ("hour", "minute"):
        L_, T_, Wd = P[k]
        hands[k] = hand(k, L_, T_, Wd, 0, "dauphine")
        hands[k + "_aod"] = hand(k + "_aod", L_, T_, Wd, 0, "dauphine", dim=.45)
    L_, T_, Wd = P["second"]; hands["second"] = hand("second", L_, T_, Wd, 2.6 if W > 400 else 2.3, "needle", alpha=1.0)
    CAP = P["CAP"]
    cm = Image.new("1", (CAP * SS, CAP * SS), 0); ImageDraw.Draw(cm).ellipse([0, 0, CAP * SS - 1, CAP * SS - 1], fill=1)
    cap = frosted(np.asarray(cm, bool), bevel=SS * 3, alpha=1.0)
    pm = Image.new("1", (CAP * SS, CAP * SS), 0); r0 = CAP * SS * .28
    ImageDraw.Draw(pm).ellipse([CAP * SS / 2 - r0, CAP * SS / 2 - r0, CAP * SS / 2 + r0, CAP * SS / 2 + r0], fill=1)
    cap.alpha_composite(chrome(np.asarray(pm, bool), bevel=SS * 1.5)); save(cap, "hands/cap.png")

    L = {"W": W, "H": H, "CX": CX, "CY": CY, "BIG_W": BW, "BIG_H": BH, "COLON_W": big["colon"].width,
         "DATA_H": SH, "DATA_W": P["DATA_W"], "ICON": P["icon"], "TIME_Y": P["TIME_Y"], "ICON_Y": P["ICON_Y"],
         "DATA_Y": P["DATA_Y"], "COLS": P["COLS"], "CAP": CAP,
         "HANDS": {k: {"posX": v[1][0], "posY": v[1][1]} for k, v in hands.items() if not k.endswith("_aod")}}

    def put_hand(im, key, deg):
        img, (hx, hy) = hands[key]
        c = Image.new("RGBA", (600, 600), (0, 0, 0, 0)); c.alpha_composite(img, (300 - hx, 300 - hy))
        im.alpha_composite(c.rotate(-deg, resample=Image.BICUBIC, center=(300, 300)), (CX - 300, CY - 300))

    def compose(time_txt, data, hms):
        im = bg.copy().convert("RGBA")
        h, mi, se = hms                                     # hands first: they sit behind digits + stats
        put_hand(im, "hour", (h % 12 + mi / 60) * 30); put_hand(im, "minute", (mi + se / 60) * 6); put_hand(im, "second", se * 6)
        im.alpha_composite(cap, (CX - CAP // 2, CY - CAP // 2))
        x = (W - (4 * BW + L["COLON_W"])) // 2
        for ch in time_txt:
            g = big["colon"] if ch == ":" else big[ch]; im.alpha_composite(g, (x, P["TIME_Y"])); x += g.width
        for cx, key, txt in zip(P["COLS"], ("steps", "cal", "battery"), data):
            ic = icons[key]; im.alpha_composite(ic, (cx - ic.width // 2, P["ICON_Y"]))
            gl = [small["percent"] if c == "%" else small[c] for c in txt]
            x = cx - sum(g.width for g in gl) // 2
            for g in gl: im.alpha_composite(g, (x, P["DATA_Y"])); x += g.width
        out = Image.new("RGBA", (W, H), (0, 0, 0, 0)); out.paste(im, (0, 0), screen_mask(P))
        return out
    pv = compose("10:08", ("8532", "412", "87%"), (10, 8, 36))
    compose("23:58", ("12408", "1037", "100%"), (23, 58, 12)).save(os.path.join(PREVIEW_DIR, f"preview_{name}_wide.png"))
    pv.save(os.path.join(PREVIEW_DIR, f"preview_{name}.png"))
    save(pv.resize((W // 2, H // 2), Image.LANCZOS), "preview.png")
    save(pv.resize((248, 248) if W == H else (234, 270), Image.LANCZOS), "icon.png")
    return L

LAYOUTS = {n: build(n, P) for n, P in PROFILES.items()}
json.dump(LAYOUTS, open(os.path.join(ROOT, "layout.json"), "w"), indent=1)
with open(os.path.join(ROOT, "watchface", "layouts.js"), "w") as f:
    f.write("// Generated by tools/gen_assets.py: image sizes and positions per screen shape. Do not edit by hand.\n")
    for n, L in LAYOUTS.items():
        f.write(f"export const {n.upper()} = {json.dumps(L)};\n")
print("assets ok", json.dumps(LAYOUTS))
