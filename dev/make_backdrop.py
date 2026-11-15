#!/usr/bin/env python3
"""A license-free stand-in 'movie backdrop' for previews: dusk over layered hills and a sea."""
import math, random, sys
from PIL import Image, ImageDraw, ImageFilter
W, H = 1920, 1080
random.seed(7)
im = Image.new("RGB", (W, H))
px = im.load()
sky_top, sky_mid, sky_low = (38, 52, 78), (196, 120, 92), (244, 196, 140)
for y in range(H):
    t = y / H
    if t < .45:
        u = t / .45; c = [round(a + (b - a) * u) for a, b in zip(sky_top, sky_mid)]
    else:
        u = min(1, (t - .45) / .2); c = [round(a + (b - a) * u) for a, b in zip(sky_mid, sky_low)]
    for x in range(W):
        px[x, y] = tuple(c)
d = ImageDraw.Draw(im)
d.ellipse((1260, 470, 1420, 630), fill=(255, 226, 180))            # low sun
im = im.filter(ImageFilter.GaussianBlur(2))
d = ImageDraw.Draw(im)
for i, (base, amp, col) in enumerate([(640, 90, (92, 70, 78)), (700, 70, (64, 50, 60)), (770, 50, (40, 34, 42))]):
    pts = [(0, H)]
    for x in range(0, W + 40, 40):
        y = base - amp * (0.5 + 0.5 * math.sin(x / (260 + i * 90) + i * 2)) - random.randint(0, 18)
        pts.append((x, y))
    pts.append((W, H)); d.polygon(pts, fill=col)
for y in range(820, H):                                              # sea
    u = (y - 820) / (H - 820)
    d.line([(0, y), (W, y)], fill=(round(70 - 40 * u), round(62 - 34 * u), round(70 - 30 * u)))
for _ in range(260):                                                 # sun glitter
    x = random.gauss(1340, 120); y = random.uniform(822, 1000)
    d.line([(x, y), (x + random.uniform(8, 40), y)], fill=(250, 200, 150), width=1)
im.filter(ImageFilter.GaussianBlur(.8)).save(sys.argv[1], quality=90)
