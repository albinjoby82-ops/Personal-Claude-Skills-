---
name: image-to-cad-dxf
description: Turn an image (text, logo, keyring, sign, icon) into a closed-loop mm DXF ready to extrude in Onshape/Fusion for 3D printing or laser cutting. Use whenever a picture needs to become a DXF or CAD sketch outline.
category: tools
tags: [dxf, cad, onshape, fusion, laser-cutting, 3d-printing]
---

# Image → CAD-ready DXF

Goal: a DXF that drops into a CAD sketch and extrudes first time. That means **closed polylines only, units in mm, sized for the real part, no stray specks, no text entities, no images**. CAD tools can't extrude live SVG/DXF text, open curves or raster images, so everything must be outlines.

Keep replies short and visual: a preview image and a few lines beat long explanations.

## 1. Look at the image and pick a route

| What's in the image | Route |
|---|---|
| Mostly lettering in a recognisable/standard-ish font | **A: Re-typeset from a font** (crisp, perfect curves) |
| Logo, drawing, icon, odd hand-lettering, or font can't be matched | **B: Trace the pixels** |
| Both (e.g. text + an emblem) | A for the text, B for the emblem, then merge (see 4) |

Route A beats tracing for text because a low-res screenshot traces into wobbly letters; a font gives true curves. If the font match is only approximate, say so in one line.

Ask (or infer from context) **what to include** (e.g. "just the text", not the disc or hole) and **target size**. If the user gives a part size (e.g. "60 mm disc"), fit to it straight away. Otherwise default to 100 mm wide and offer to resize.

Setup (once): `pip install fonttools ezdxf opencv-python-headless cairosvg matplotlib --break-system-packages -q`

## 2A. Re-typeset from a font

1. Identify the style (bubbly serif, slab, rounded sans, stencil…). Download 3–6 Google Fonts candidates from `https://raw.githubusercontent.com/google/fonts/main/ofl/<family>/<File>.ttf` (e.g. `gorditas/Gorditas-Bold.ttf`, `chango/Chango-Regular.ttf`, `titanone/TitanOne-Regular.ttf`, `corben/Corben-Bold.ttf`, `bagelfatone/BagelFatOne-Regular.ttf`, `rammettoone/RammettoOne-Regular.ttf`, `sansita/Sansita-Black.ttf`, `bigshotone/BigshotOne-Regular.ttf`). Bubbly retro serif in the original test → Gorditas Bold was closest.
2. Render each candidate with `--svg`, convert to PNG with cairosvg, `+append` them with ImageMagick into one strip, view it, and pick the closest one. Don't ask the user to choose unless the candidates are genuinely tied.
3. Match the layout: `|` separates lines. `--scales` sets each line's relative size; `fit` stretches a line to the reference width (useful when two lines are the same width in the original).
4. Run `scripts/text_to_dxf.py` (in section 5):
   - plain: `--width 100`
   - inside a round tag: `--disc 60 --margin 2 --top 17.5` (auto-scales so every point stays ≥ margin inside the circle; `--top` = y of text top in mm, set below a keyring hole). Text is centred on the origin, so it lands centred on a circle drawn at the sketch origin.

## 2B. Trace the pixels

`scripts/trace_to_dxf.py in.png out.dxf --width 50 [--crop x0,y0,x1,y1] [--invert] [--color R,G,B --tol 60]`

- Default picks the **dark** shapes (Otsu threshold). `--invert` for light-on-dark. `--color` grabs one colour (e.g. black text on a pink disc: default works; pink disc itself: `--color 200,0,140`).
- `--crop` to keep only the wanted part (pixel coords in the original image).
- It upsamples 4×, blurs to remove pixel stair-steps, then simplifies to ~0.03 mm. If curves look faceted, lower `--smooth`; if there are thousands of tiny segments, raise it.
- Letters that touch in the source merge into one loop. That's fine for extrusion, but mention it.

## 3. Always check before sending

Render the DXF and look at it:
```python
import ezdxf,matplotlib;matplotlib.use('Agg')
from ezdxf.addons.drawing import matplotlib as m
m.qsave(ezdxf.readfile('out.dxf').modelspace(),'check.png',bg='#FFFFFF')
```
Check: every shape is a closed loop, holes (O, A, D, B, R…) are separate inner loops, there are no specks, and the size printed by the script matches what was asked for. Fix and re-run if anything is off.

## 4. Deliver

- Send the `.dxf` with SendUserFile (also an `.svg` if they asked for one; the `--svg` output is outlines with even-odd fill, so it's CAD-safe too).
- Reply in 2–4 short lines: size in mm, where the origin is, font used (if route A), and one tip: *"Insert DXF into a sketch, choose mm, then Extrude"*. If they're putting it on an existing part, offer to fit it to that part's size.
- If it doesn't fit their part (they send a screenshot), work out the size from it and re-run with `--disc`/`--width`. Don't just tell them to scale it by hand.
- Merging A + B: run both and then append the entities of one DXF into the other with ezdxf (`for e in src.modelspace(): dst.modelspace().add_foreign_entity(e)`), shifting with `e.transform(Matrix44.translate(dx,dy,0))`.

## 5. Scripts

Write these to files before use (they aren't bundled on disk).

### scripts/text_to_dxf.py
```python
"""Typeset text as outlined, closed DXF polylines (mm), centred on origin.
usage: python3 text_to_dxf.py font.ttf out.dxf "LINE 1|LINE 2|..." [--scales 0.55,1,0.6,fit]
        [--width 100 | --disc 60 --margin 2 --top 17.5] [--gap 0.2] [--svg preview.svg]
--scales: per-line size relative to the widest/reference line; 'fit' = stretch line to reference width.
--disc D: auto-scale so every point stays inside a D mm circle minus --margin; --top = y of top of text (mm),
          use it to keep clear of a keyring hole."""
import argparse, math, ezdxf
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.basePen import decomposeQuadraticSegment
from ezdxf import path as P
a=argparse.ArgumentParser()
a.add_argument('font'); a.add_argument('out'); a.add_argument('text')
a.add_argument('--scales'); a.add_argument('--width',type=float,default=100)
a.add_argument('--disc',type=float); a.add_argument('--margin',type=float,default=2); a.add_argument('--top',type=float)
a.add_argument('--gap',type=float,default=0.2); a.add_argument('--svg')
o=a.parse_args()
f=TTFont(o.font); gs=f.getGlyphSet(); cm=f.getBestCmap(); hm=f['hmtx']
cap=getattr(f['OS/2'],'sCapHeight',0) or 0.7*f['head'].unitsPerEm
lines=o.text.split('|')
sc=(o.scales.split(',') if o.scales else ['1']*len(lines))
W=lambda t:sum(hm[cm[ord(c)]][0] for c in t)
fixed=[W(t)*float(s) for t,s in zip(lines,sc) if s!='fit']
ref=max(fixed) if fixed else max(W(t) for t in lines)
sc=[ref/W(t) if s=='fit' else float(s) for t,s in zip(lines,sc)]
loops=[]; y=0   # font units, y down
for t,s in zip(lines,sc):
    y+=cap*s; x=(ref-W(t)*s)/2
    for c in t:
        g=cm[ord(c)]
        r=RecordingPen(); gs[g].draw(TransformPen(r,(s,0,0,s,x,-y)))
        p=None
        for op,v in r.value:
            if op=='moveTo': p=P.Path(v[0])
            elif op=='lineTo': p.line_to(v[0])
            elif op=='qCurveTo':
                v=v[:-1] if v[-1] is None else v
                for c1,e in decomposeQuadraticSegment(v): p.curve3_to(e,c1)
            elif op=='curveTo': p.curve4_to(v[2],v[0],v[1])
            elif op in('closePath','endPath'):
                loops.append([(q.x,q.y) for q in p.flattening(2)])
        x+=hm[g][0]*s
    y+=cap*o.gap
pts=[q for l in loops for q in l]
cx=(min(p[0] for p in pts)+max(p[0] for p in pts))/2; ty=max(p[1] for p in pts); by=min(p[1] for p in pts)
if o.disc:
    R=o.disc/2-o.margin
    top=o.top if o.top is not None else None
    def place(k):
        oy=(top-ty*k) if top is not None else -(ty+by)/2*k
        return lambda p:((p[0]-cx)*k,p[1]*k+oy)
    k=10.0
    while max(math.hypot(*place(k)(p)) for p in pts)>R: k*=0.995
else:
    k=o.width/(max(p[0] for p in pts)-min(p[0] for p in pts))
    place=lambda k:(lambda p:((p[0]-cx)*k,(p[1]-(ty+by)/2)*k))
T=place(k)
doc=ezdxf.new('R2010'); doc.header['$INSUNITS']=4; msp=doc.modelspace()
out=[[T(p) for p in l] for l in loops]
for l in out: msp.add_lwpolyline(l,close=True)
doc.saveas(o.out)
xs=[p[0] for l in out for p in l]; ys=[p[1] for l in out for p in l]
print(f'{len(out)} loops, {max(xs)-min(xs):.1f} x {max(ys)-min(ys):.1f} mm, y {min(ys):.1f}..{max(ys):.1f}')
if o.svg:
    d=' '.join('M'+' L'.join(f'{x:.3f},{-y:.3f}' for x,y in l)+' Z' for l in out)
    pad=2; open(o.svg,'w').write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min(xs)-pad} {-max(ys)-pad} {max(xs)-min(xs)+2*pad} {max(ys)-min(ys)+2*pad}"><path fill-rule="evenodd" d="{d}"/></svg>')
```

### scripts/trace_to_dxf.py
```python
"""Trace dark (or chosen-colour) regions of an image into closed DXF polylines in mm.
usage: python3 trace_to_dxf.py in.png out.dxf --width 60 [--invert] [--color R,G,B --tol 60] [--crop x0,y0,x1,y1] [--smooth 0.03]"""
import argparse, cv2, numpy as np, ezdxf
a=argparse.ArgumentParser()
a.add_argument('inp'); a.add_argument('out'); a.add_argument('--width',type=float,required=True)
a.add_argument('--invert',action='store_true'); a.add_argument('--color'); a.add_argument('--tol',type=int,default=60)
a.add_argument('--crop'); a.add_argument('--smooth',type=float,default=0.03,help='simplify tolerance in mm')
a.add_argument('--min-area',type=float,default=0.5,help='drop specks smaller than this (mm^2)')
o=a.parse_args()
img=cv2.imread(o.inp)
if o.crop: x0,y0,x1,y1=map(int,o.crop.split(',')); img=img[y0:y1,x0:x1]
img=cv2.resize(img,None,fx=4,fy=4,interpolation=cv2.INTER_CUBIC)  # upsample = smoother curves
if o.color:
    c=np.array([int(v) for v in o.color.split(',')][::-1]); m=(np.linalg.norm(img.astype(int)-c,axis=2)<o.tol).astype(np.uint8)*255
else:
    g=cv2.GaussianBlur(cv2.cvtColor(img,cv2.COLOR_BGR2GRAY),(5,5),0)
    _,m=cv2.threshold(g,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    if o.invert: m=255-m
m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
m=(cv2.GaussianBlur(m,(0,0),3)>127).astype(np.uint8)*255  # round off pixel stair-steps
cs,h=cv2.findContours(m,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)
ys,xs=np.nonzero(m); x0,x1,y1=xs.min(),xs.max(),ys.max()
k=o.width/(x1-x0)
doc=ezdxf.new('R2010'); doc.header['$INSUNITS']=4; msp=doc.modelspace(); n=0
for c in cs:
    if cv2.contourArea(c)*k*k<o.min_area: continue
    c=cv2.approxPolyDP(c,o.smooth/k,True)
    if len(c)<3: continue
    msp.add_lwpolyline([((p[0][0]-x0)*k,(y1-p[0][1])*k) for p in c],close=True); n+=1
doc.saveas(o.out)
print(f'{n} closed loops, {o.width:.1f} x {(y1-ys.min())*k:.1f} mm')
```