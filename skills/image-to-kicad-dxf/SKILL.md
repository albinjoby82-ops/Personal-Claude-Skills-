---
name: image-to-kicad-dxf
description: Turn an image (logo, outline, silhouette, drawing) into a DXF for KiCad Edge.Cuts. Use when the user wants a custom board shape, PCB outline, or 'make this a dxf for KiCad'.
category: ee
tags: [kicad, pcb, dxf, edge-cuts, image]
---

# Image to KiCad DXF

Converts a picture into ONE closed polyline in millimetres, ready for KiCad's File > Import > Graphics onto Edge.Cuts. A single closed contour is what KiCad needs for a valid board outline, so the script always produces exactly one.

## Workflow

1. Find the image (uploads folder, or the attachment path). Read it once to see what it is.
2. Write the script below to the scratchpad as `img2dxf.py`. Install deps if missing: `pip install --break-system-packages ezdxf opencv-python-headless scipy`.
3. Run: `python3 img2dxf.py IMAGE OUT.dxf --height 100 --preview preview.png`
   - Size: `--height MM` or `--width MM`. If the user gave no size, use 100 mm tall and say so; KiCad's import dialog can rescale.
   - `--edge inner|outer`: only for hollow outline drawings. `inner` (default) follows the inside edge of the drawn line, which keeps sharp details such as star points. Use `outer` if the user wants the board to include the stroke.
   - `--invert`: when the shape is light on a dark background.
4. **Look at preview.png** (green line over the faded original) and zoom into small details such as points and notches. If something is rounded off or wobbly, change the options and rerun rather than shipping it.
5. Verify with ezdxf that the file has one closed LWPOLYLINE.
6. Send the DXF and the preview with SendUserFile.

## What to tell the user (keep it short)

- Final size in mm.
- Import steps: KiCad PCB Editor > File > Import > Graphics > pick the DXF > layer **Edge.Cuts**, units mm.
- One-line warning if there are tight inside corners: board houses mill with about a 1 mm radius, so very small notches come out slightly rounded.

## Why the script works this way

- Hollow outline drawings are traced by finding the background regions enclosed by the stroke. Tracing the stroke itself would give a ring (two contours), which is not a valid outline.
- Corners above 35 degrees are detected and kept sharp. Only the curves between them are spline-smoothed. Smoothing everything turns stars and points into blobs, which was the first-attempt failure.
- Image Y points down and CAD Y points up, so Y is flipped. Without that the shape imports upside down.
- JPEG or PNG transparency is composited on white before thresholding.

## Script (img2dxf.py)

```python
#!/usr/bin/env python3
import argparse, cv2, numpy as np, ezdxf
from scipy.interpolate import splprep, splev

ap = argparse.ArgumentParser()
ap.add_argument('image'); ap.add_argument('out')
ap.add_argument('--height', type=float, help='final height in mm (default 100)')
ap.add_argument('--width', type=float, help='final width in mm (overrides --height)')
ap.add_argument('--edge', choices=['inner', 'outer'], default='inner')
ap.add_argument('--invert', action='store_true', help='shape is light on dark')
ap.add_argument('--preview', default=None, help='preview PNG path')
a = ap.parse_args()
S = 8  # upscale for sub-pixel accuracy

raw = cv2.imread(a.image, cv2.IMREAD_UNCHANGED)
if raw.ndim == 3 and raw.shape[2] == 4:      # transparent PNG -> composite on white
    al = raw[..., 3:4] / 255.0
    raw = (raw[..., :3] * al + 255 * (1 - al)).astype(np.uint8)
gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY) if raw.ndim == 3 else raw
big = cv2.resize(gray, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
big = cv2.GaussianBlur(big, (0, 0), S * 0.6)
ink = big < 128
if a.invert: ink = ~ink

# background regions not touching the border = hollow inside of an outline drawing
nb, lab = cv2.connectedComponents((~ink).astype(np.uint8))
border = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
inside = np.isin(lab, [l for l in range(1, nb) if l not in border])
if inside.sum() > 0.02 * ink.size:           # outline drawing
    shape = inside if a.edge == 'inner' else (inside | ink)
else:                                        # solid silhouette
    shape = ink

cs, _ = cv2.findContours(shape.astype(np.uint8) * 255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
c = max(cs, key=cv2.contourArea).reshape(-1, 2).astype(float)

# uniform resample
seg = np.hypot(*np.diff(np.vstack([c, c[:1]]), axis=0).T)
L = np.r_[0, np.cumsum(seg)]
n = int(L[-1] / 4); t = np.linspace(0, L[-1], n, endpoint=False)
c = np.c_[np.interp(t, L, np.r_[c[:, 0], c[0, 0]]), np.interp(t, L, np.r_[c[:, 1], c[0, 1]])]

# find real corners (keep sharp), smooth everything between them
k = 10
v1 = c - np.roll(c, k, 0); v2 = np.roll(c, -k, 0) - c
ang = np.degrees(np.abs(np.arctan2(v1[:, 0]*v2[:, 1] - v1[:, 1]*v2[:, 0], (v1*v2).sum(1))))
corners = [i for i in range(n) if ang[i] > 35 and ang[i] == max(ang[(i+j) % n] for j in range(-k, k+1))]
out = []
if len(corners) < 2:
    corners = [0]
idx = corners + [corners[0] + n]
for s0, s1 in zip(idx[:-1], idx[1:]):
    sg = np.array([c[i % n] for i in range(s0, s1 + 1)]); m = len(sg)
    if m < 6: out += list(sg[:-1]); continue
    w = np.ones(m); w[0] = w[-1] = 1000
    tck, _ = splprep(sg.T, w=w, s=m * 6, k=3)
    q = np.array(splev(np.linspace(0, 1, max(8, m * 2)), tck)).T
    out += list(q[:-1])
p = cv2.approxPolyDP(np.array(out, np.float32).reshape(-1, 1, 2), 0.25 * S / 4, True).reshape(-1, 2)

x0, y1 = p[:, 0].min(), p[:, 1].max()
hpx, wpx = y1 - p[:, 1].min(), p[:, 0].max() - x0
s = a.width / wpx if a.width else (a.height or 100.0) / hpx
pts = [(round((x - x0) * s, 4), round((y1 - y) * s, 4)) for x, y in p]   # flip Y for CAD
doc = ezdxf.new('R2000'); doc.units = ezdxf.units.MM
doc.modelspace().add_lwpolyline(pts, close=True)
doc.saveas(a.out)
print(f'{len(pts)} pts, {wpx*s:.1f} x {hpx*s:.1f} mm, {len(corners)} sharp corners -> {a.out}')

if a.preview:
    o = cv2.cvtColor(cv2.resize(gray, None, fx=2, fy=2), cv2.COLOR_GRAY2BGR)
    o = (o * 0.35 + 255 * 0.65).astype(np.uint8)
    cv2.polylines(o, [(p / S * 2).astype(np.int32)], True, (0, 140, 0), 2, cv2.LINE_AA)
    cv2.imwrite(a.preview, o)
```

## Limits

- Only the largest shape in the image is traced. Holes and cutouts inside the board are not produced. If the user wants internal cutouts, trace those separately and add them as extra closed polylines.
- Very noisy or low-contrast photos need to be cleaned up first. This is for clean logos, line art and silhouettes.