"""
ChromoMap app icon — curved X chromosome with natural organic feel.
Apple HIG 1024x1024 full-bleed PNG.

- Deep gray background
- 4 arms with gentle outward curve (banana-like bow)
- Flat spectral gradient: red→orange→yellow→green→blue, top-left to bottom-right
- Minimalist cartoon style
"""
from PIL import Image, ImageDraw, ImageFilter
import math

SIZE = 1024
OUTPUT = 'public/icon.png'

BG = (44, 44, 46)

img = Image.new('RGBA', (SIZE, SIZE), BG + (255,))

# ---- Spectral gradient map ----
grad = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
gpix = grad.load()

def spectrum(t):
    t = max(0, min(1, t))
    if t < 0.25:
        return (255, int(t * 4 * 200), 0, 255)
    elif t < 0.5:
        return (255 - int((t - 0.25) * 4 * 155),
                200 + int((t - 0.25) * 4 * 55), 0, 255)
    elif t < 0.75:
        return (100 - int((t - 0.5) * 4 * 100),
                255, int((t - 0.5) * 4 * 120), 255)
    else:
        return (0, 255 - int((t - 0.75) * 4 * 80),
                120 + int((t - 0.75) * 4 * 135), 255)

for x in range(SIZE):
    for y in range(SIZE):
        t = x / SIZE * 0.7 + y / SIZE * 0.3
        gpix[x, y] = spectrum(t)

# ---- Curved chromosome ----
def draw_curved_arm(d, cx, cy, angle_deg, side, length, width, gap, bow_dir):
    a = math.radians(angle_deg)
    pa = a + math.radians(90)
    r = width / 2

    ox = side * gap * math.cos(pa)
    oy = side * gap * math.sin(pa)

    half = length / 2
    sx = cx + ox
    sy = cy + oy
    ex = cx + ox + half * math.cos(a)
    ey = cy + oy + half * math.sin(a)

    # Control point: midpoint pushed perpendicular to arm
    mx = (sx + ex) / 2
    my = (sy + ey) / 2
    bow = half * 0.15 * bow_dir
    cpx = mx + bow * math.cos(pa)
    cpy = my + bow * math.sin(pa)

    steps = 60
    for t in range(steps + 1):
        u = t / steps
        u1 = 1 - u
        px = u1 * u1 * sx + 2 * u1 * u * cpx + u * u * ex
        py = u1 * u1 * sy + 2 * u1 * u * cpy + u * u * ey
        d.ellipse([px - r, py - r, px + r, py + r], fill=255)

mask = Image.new('L', (SIZE, SIZE), 0)
mdraw = ImageDraw.Draw(mask)

cx = cy = SIZE // 2
arm_len = 780
arm_w = 104
gap = 34

# Top arms bow upward (+1), bottom arms bow downward (-1)
# Chromosome 1: angle -45°, top arm is negative direction, bottom is positive
for angle, bow_top, bow_bottom in [(-45, -1, 1), (45, -1, 1)]:
    a = math.radians(angle)
    pa = a + math.radians(90)
    half = arm_len / 2

    for side in [-1, 1]:
        ox = side * gap * math.cos(pa)
        oy = side * gap * math.sin(pa)
        sx = cx + ox
        sy = cy + oy

        # Upper arm (goes in -a direction from center)
        ex_top = cx + ox - half * math.cos(a)
        ey_top = cy + oy - half * math.sin(a)
        mx_top = (sx + ex_top) / 2
        my_top = (sy + ey_top) / 2
        bow_top_amt = half * 0.18 * bow_top
        cpx_top = mx_top + bow_top_amt * math.sin(a)
        cpy_top = my_top - bow_top_amt * math.cos(a)

        # Lower arm (goes in +a direction from center)
        ex_bot = cx + ox + half * math.cos(a)
        ey_bot = cy + oy + half * math.sin(a)
        mx_bot = (sx + ex_bot) / 2
        my_bot = (sy + ey_bot) / 2
        bow_bot_amt = half * 0.18 * bow_bottom
        cpx_bot = mx_bot + bow_bot_amt * math.sin(a)
        cpy_bot = my_bot - bow_bot_amt * math.cos(a)

        r = arm_w / 2
        steps = 60
        for t in range(steps + 1):
            u = t / steps
            u1 = 1 - u
            # Upper arm
            px = u1 * u1 * sx + 2 * u1 * u * cpx_top + u * u * ex_top
            py = u1 * u1 * sy + 2 * u1 * u * cpy_top + u * u * ey_top
            mdraw.ellipse([px - r, py - r, px + r, py + r], fill=255)
            # Lower arm
            px = u1 * u1 * sx + 2 * u1 * u * cpx_bot + u * u * ex_bot
            py = u1 * u1 * sy + 2 * u1 * u * cpy_bot + u * u * ey_bot
            mdraw.ellipse([px - r, py - r, px + r, py + r], fill=255)

# Centromere
mdraw.ellipse([cx - 20, cy - 12, cx + 20, cy + 12], fill=255)

# Anti-aliasing
mask = mask.filter(ImageFilter.GaussianBlur(radius=2.5))

# ---- Composite ----
result = Image.new('RGBA', (SIZE, SIZE), BG + (255,))
result.paste(grad, (0, 0), mask)

result.save(OUTPUT, 'PNG')
print(f'Icon saved: {OUTPUT} ({SIZE}x{SIZE})')
