"""Run a build123d model file stage by stage: preview PNG, stats, exports.
usage: python3 cad_run.py model.py --name part [--stage N] [--final] [--outdir out]
model.py must define `part` (a build123d Part/Solid/Compound). Optionally `sketches`:
dict name -> build123d Sketch/Face/Compound of faces, exported to DXF on --final."""
import argparse, runpy, sys, os
from build123d import *
import cairosvg
from PIL import Image

a = argparse.ArgumentParser()
a.add_argument('model'); a.add_argument('--name', default='part')
a.add_argument('--stage', type=int, default=0); a.add_argument('--final', action='store_true')
a.add_argument('--outdir', default='out'); a.add_argument('--density', type=float, default=1.24)  # g/cm3, PLA; PETG 1.27
args = a.parse_args()
os.makedirs(args.outdir, exist_ok=True)
ns = runpy.run_path(args.model)
part = ns['part']
if hasattr(part, 'part'): part = part.part          # BuildPart object passed by mistake
bb = part.bounding_box(); size = bb.size
vol_mm3 = part.volume
print(f"bbox X {size.X:.2f}  Y {size.Y:.2f}  Z {size.Z:.2f} mm   (min {bb.min.X:.1f},{bb.min.Y:.1f},{bb.min.Z:.1f})")
print(f"volume {vol_mm3/1000:.2f} cm3   mass ~{vol_mm3/1000*args.density:.1f} g at {args.density} g/cm3")
print(f"faces {len(part.faces())}  edges {len(part.edges())}  solids {len(part.solids())}")
if len(part.solids()) > 1: print("WARNING: more than one solid — did a cut or boolean miss?")

def view_png(shape, direction, up, path, px=400):
    vis, hid = shape.project_to_viewport(viewport_origin=direction, viewport_up=up, look_at=(0, 0, 0))
    allc = Compound(children=vis + hid)
    m = max(allc.bounding_box().size.X, allc.bounding_box().size.Y, 1e-3)
    ex = ExportSVG(scale=90 / m, line_weight=0.5)
    ex.add_layer('vis'); ex.add_layer('hid', line_color=(150, 150, 150), line_type=LineType.ISO_DOT)
    ex.add_shape(vis, layer='vis'); ex.add_shape(hid, layer='hid')
    svg = path.replace('.png', '.svg'); ex.write(svg)
    cairosvg.svg2png(url=svg, write_to=path, output_width=px, background_color='white'); os.remove(svg)

tag = 'final' if args.final else f's{args.stage}'
d = max(size.X, size.Y, size.Z) * 3
views = [((d, -d, d), (0, 0, 1), 'iso'), ((0, 0, d), (0, 1, 0), 'top'),
         ((0, -d, 0), (0, 0, 1), 'front'), ((d, 0, 0), (0, 0, 1), 'right')]
tiles = []
for direction, up, label in views:
    p = f"{args.outdir}/_{label}.png"; view_png(part, direction, up, p); tiles.append((label, Image.open(p)))
W = sum(t.width for _, t in tiles); H = max(t.height for _, t in tiles)
sheet = Image.new('RGB', (W, H), 'white'); x = 0
for label, t in tiles: sheet.paste(t, (x, 0)); x += t.width
out_png = f"{args.outdir}/{args.name}_{tag}.png"; sheet.save(out_png)
for _, t in tiles: os.remove(t.filename)
print('preview', out_png, '(iso | top | front | right)')

if args.final:
    export_step(part, f"{args.outdir}/{args.name}.step")
    export_stl(part, f"{args.outdir}/{args.name}.stl", tolerance=0.02, angular_tolerance=0.1)
    m = Mesher(); m.add_shape(part); m.write(f"{args.outdir}/{args.name}.3mf")
    for sname, sk in ns.get('sketches', {}).items():
        sk = sk.sketch if hasattr(sk, 'sketch') else sk
        ex = ExportDXF(unit=Unit.MM); ex.add_layer('0'); ex.add_shape(sk, layer='0')
        ex.write(f"{args.outdir}/{args.name}_{sname}.dxf")
    print('exported step/stl/3mf', '+ dxf' if ns.get('sketches') else '')
