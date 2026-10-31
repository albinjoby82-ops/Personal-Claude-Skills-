---
name: onshape-part-builder
description: "Use Claude as the CAD tool: Albin describes a 3D-printed part, sign or plaque and Claude designs it (mockup, plan, staged build, print check, files): Onshape rebuild sheet, STEP, STL, Bambu multi-colour 3MF. Use for any bracket, mount, case, sign, keyring, holder or 'design/model/print this'."
category: tools
tags: [cad, onshape, 3d-printing, build123d, featurescript, step, dxf, bambu, multicolour, signs]
---

# Onshape Part Builder: describe a part, get an editable model

Albin explains the part and Claude does the CAD. Mechanical parts must be something he can **open and edit in Onshape like he drew them himself**, not a dumb STL. Flat artwork pieces (signs, plaques, keyrings, logos) must load in Bambu Studio with the colours already sorted. This is a conversation with checkpoints, not a one-shot dump: short updates, a picture at every stage, a question only when the answer changes the design, and alternatives where a real trade-off exists.

Why it's built this way (from people who've done it, see `references/related-work.md` if present): when Claude built whole parts in one go and the base shape was wrong, all the detail work was wasted. Agreeing the plan or mockup first and then building in stages is both more accurate and far cheaper in tokens.

**Units are always mm.** Onshape, the slicer and Albin all think in mm. He prints on a Bambu (256 × 256 mm plate, treat 250 × 250 as usable) and has an AMS for multi-colour.

## How he likes it run (learned from real sessions)

- **Match the effort to the job.** When he says "it should be easy" or "this is a simple one", don't hold a formal plan checkpoint. Show a picture, then build. Keep the full feature-plan checkpoint for mechanical parts with real fits.
- **Picture first.** When he asks what a design could look like or says "show me", send a quick 2D mockup image to scale *before* any CAD or long text. Sending text first got "show images first".
- **Simple beats busy.** For cartoon artwork, a clean style (one outline weight, flat colours, few details) won over sprinkles, drips and drop shadows. If he says "too simple", add only 2–3 touches. If he says "too complex", go back to his reference's level of detail.
- **Stands start small.** A full-width wedge stand was "way too big and thick". Default to the smallest thing that works, such as two small slot feet, or ask whether it should just lie flat. He sometimes drops the stand entirely.
- **Short replies.** He's dyslexic: give the image plus 2–4 lines, and use bullets over paragraphs.
- **Your own artwork only.** If he sends a stock image as a style reference (watermarked, from pngtree and the like), draw an original in that style rather than tracing it, and say so in one line.

## 0. Pick the delivery route (silently, then say it in one line)

| Situation | Route | What he gets |
|---|---|---|
| Default mechanical part, nothing connected | **A. Rebuild sheet + STEP** | Feature plan with exact dims and variables (rebuilds natively in Onshape in minutes), STEP for import, STL/3MF to print, DXF per sketch, preview PNG |
| Flat artwork: sign, plaque, keyring, badge, logo, anything multi-colour | **S. Flat artwork** | SVG mockup → shapely 2D colour regions → black body with flush colour inlays → Bambu 3MF (named parts, filament slots pre-assigned) + per-colour STL zip + STEP + coloured preview |
| Onshape MCP tools present (`list_documents`, `create_sketch_*`, `create_extrude`…) | **B. Direct build** | A real feature tree in his Part Studio, built from the same plan, with variables set in the variable table. Still ship STL/3MF + preview |
| Part is a *family* (same shape at different sizes or counts: a motor mount for N motors, a standoff set, a bearing holder for any OD) or he asks for FeatureScript | **C. FeatureScript custom feature** | A `.fs` file to paste into a Feature Studio; the part becomes a feature with a dialog of parameters. Also ship route A outputs |

For mechanical parts, route A is always produced and B and C sit on top of it. Setup for B and C is in `references/onshape-routes.md` if present. Read it only when that route is in play.

STEP imports into Onshape as a solid with no feature tree; that's why the rebuild sheet matters. STL is a mesh and essentially uneditable, so it is only ever the print file. Route S artwork isn't parametric, so skip the rebuild sheet and DXF-per-sketch there unless he asks.

## 1. Intake: ask only what changes the design

Read everything he gave first (text, photo, sketch, datasheet, Onshape link). Then ask **at most 4 questions in one message**, picked from this list, skipping anything already answered or safely defaulted:

1. **Function and mating parts.** What does it hold, attach to or sit in? Which faces touch other things? (This decides the base shape.)
2. **Critical dimensions**, and which are *fixed* (must match a real part) and which are *free* (Claude can choose). Ask for a photo with a ruler, a datasheet, or the Onshape part it mates with.
3. **Fasteners and joints.** M3 screws? Heat-set inserts? Snap-fit? Press-fit? Zip-tie slots? Default for his robotics work: M3 clearance 3.4 mm, M3 heat-set insert hole 4.0 mm × 5.7 mm deep.
4. **Print setup.** Default: Bambu with AMS, PLA or PETG, 0.4 mm nozzle, 0.2 mm layers. This decides wall thickness and overhang rules.
5. **Which numbers he'll want to tweak later.** Those become Onshape variables (`#wall`, `#hole_d`, `#length`).
6. **Where it's going:** GaelForce robot, Micromouse, FS accumulator, a lab bench, an event table. This tells you load and environment (vibration, heat, hands).

For a sign the only real questions are size, thickness, colours, text, and **stand or lie flat**.

For known hardware (NEMA 17, ESP32 dev boards, 608 bearings, Raspberry Pi, VEX parts, common sensors), look the dimensions up rather than asking, and **state the numbers used** so he can correct them. Wrong reference dims are the number one reason printed parts don't fit.

Don't ask about things that don't matter yet (infill, exact fillet radii). Pick a sensible default and say so.

## 2. Quick mockup (route S, and any part where looks matter)

Draw it as SVG and render it to PNG with cairosvg, **in mm, on the build plate**: a dashed 250 × 250 box with a label, 800 px wide. It takes about 30 seconds and settles the style before any CAD.

- Use only his colours, plus black outlines at one stroke weight: about 4.5 mm on a 250 mm sign, about 3.5 mm on a 150–200 mm one.
- For arched lettering use `<textPath>`, then check nothing is clipped. Characters that run past the end of the path silently vanish, so shrink the font or lengthen the path.
- **Outlined lettering:** draw a black copy with a thick stroke *behind*, then the white text with no stroke on top. `paint-order=stroke` with a fat stroke clogs small letter holes (B, A, e) into blobs.
- **Fonts:** Fredoka Bold prints cleanly (rounded, open counters). Avoid fonts with tiny counters, such as Luckiest Guy, for lettering under about 40 mm. GitHub raw is blocked here, so get fonts from npm and convert them:
  ```bash
  cd /tmp && npm pack @fontsource/fredoka -q && tar xzf fontsource-fredoka-*.tgz
  pip install --break-system-packages -q fonttools brotli
  python3 -c "import os;from fontTools.ttLib import TTFont;f=TTFont('package/files/fredoka-latin-700-normal.woff');f.flavor=None;os.makedirs(os.path.expanduser('~/.fonts'),exist_ok=True);f.save(os.path.expanduser('~/.fonts/FredokaBold.ttf'))" && fc-cache -f
  ```
- To offer options, put 2–3 concepts side by side in one image, each with its size underneath.
- **Look at the PNG with Read before sending it**, checking for clipped text and odd blobs.

## 3. Feature plan (route A): the blueprint, agreed before any geometry

Write the part as an **ordered list of Onshape features** with a **variables table**. This *is* the design, written the way Onshape thinks, so it doubles as the rebuild sheet later. Keep it compact:

```
Variables: #L = 60, #W = 40, #H = 12, #wall = 2.4, #hole_d = 3.4, #slot_w = 4
1. Sketch 1 on Top plane: rectangle #L × #W centred on origin, corner R = 4
2. Extrude 1: #H, new
3. Sketch 2 on top face: 4 × Ø#hole_d at (±25, ±15)
4. Extrude 2: through all, remove
5. Shell: remove bottom face, thickness #wall
6. Fillet: vertical outer edges R = 2
```

Then give **1–2 real alternatives** where a genuine trade-off exists, each in one line with its consequence:
- "Snap-fit lid instead of screws: no inserts needed, but PLA snaps fatigue after ~50 cycles."
- "Split into two parts: prints flat with no supports, costs you 4 screws."

Ask *"Build this, or change anything?"* and wait for the OK (skip this when he's said it's a simple one). Changing the plan costs a line; changing the model costs a rebuild.

Design rules that go into the plan (full list in `references/fdm-rules.md` if present):
- Keep one flat face on the bed, and design the part *around* its print orientation.
- Walls ≥ 1.2 mm (3 perimeters at 0.4 mm); prefer 2.0–2.4 mm for anything structural. Smallest feature ≥ 0.8 mm. Printed text ≥ about 8 mm tall.
- Overhangs ≤ 45°; use chamfers (45°) rather than fillets on downward-facing edges.
- Horizontal holes: teardrop, or ≤ 8 mm bridged. Vertical holes print 0.2–0.3 mm undersize, so add clearance.
- Clearance fit 0.2–0.3 mm per side; press-fit −0.1 mm; sliding 0.4 mm. A slot for an 8 mm plate is 8.4 mm.
- Fillet vertical edges (free strength, prints fine); avoid fillets on the bed-contact edge (elephant's foot).

## 4. Build stage by stage, preview every stage

Setup once: `pip install build123d cairosvg pillow shapely matplotlib trimesh rtree --break-system-packages -q`. It takes a couple of minutes the first time, so say so. build123d installs fine on Python 3.10–3.13; if it fails, say so once and fall back to CadQuery (`pip install cadquery`) with the same plan rather than looping on installs. Read `references/build123d-cheatsheet.md` before the first build if it exists.

### build123d gotchas (each of these cost a failed run)
- **`import build123d as bd`** whenever shapely is also in the script. `from build123d import *` shadows shapely's `Polygon` and fails with "Expected floats".
- **Extrude direction follows the face normal.** A clockwise outline (common after shapely ops or a y-flip) extrudes *downward*. Pass `bd.extrude(face, amount=dz, dir=(0, 0, 1))`.
- **Booleans on many-island slabs can fail silently.** A fuse can drop a whole slab, and a cut can return an invalid solid. After every boolean, check `volume`, the z-range of the bounding box and `is_valid`. Prefer **fuse** (base slab + top-layer black slab) over cutting many pockets, and use `.fix()` if `is_valid` is False.
- **`bd.Mesher` can raise "3mf mesh is invalid"** even on usable parts. Fall back to the 3MF writer in section 7 (`scripts/bambu_3mf.py`), fed from the STLs.
- Verify meshes with trimesh: `is_watertight`, plus `mesh.section(...)` areas at a few heights to prove each layer is what you expect.

### Route A: staged parametric build
Mirror the plan in **build123d** (Python, OpenCascade kernel, exports true STEP). Use one script, built one stage at a time in the same feature order as the plan, so the code reads like the feature tree.

Run every stage through `scripts/cad_run.py` (listing in section 9 if the file isn't on disk):

```
python3 scripts/cad_run.py model.py --name bracket --stage 2
```

The script executes the model file and expects a variable `part`. It writes `out/bracket_s2.png` (iso + top + front + right in one image) and prints bounding box, volume and PLA mass. On the final stage (`--final`) it also writes `.step`, `.stl`, `.3mf` and a DXF for each sketch stored in `sketches` (a dict of name → sketch). **Look at the PNG with Read before sending it.** If the shape is wrong, fix it before showing him; he should see a candidate, not a bug.

Each stage message to him is the whole update:
- the preview image
- 1–2 lines: what was added, and any number you chose
- a question **only if** the next stage depends on something he hasn't decided

Group stages as base body → cutouts/holes → shell/pockets → fillets/chamfers → final. Don't preview every fillet; group small operations. Three to five previews is normal for a bracket; a case might be six.

If he says "looks wrong", ask what specifically in one line, or offer two guesses with a preview of each if that's cheap. Don't rebuild from scratch; change the stage.

### Route S: flat artwork with flush colour inlays
This pattern worked for a 250 mm cupcake sign and a 200 mm ribbon plaque:
1. **Rebuild the mockup shapes in shapely**, in the same SVG coordinates. Sample the beziers with a small M/L/Q/C/Z sampler, use `Point.buffer` for circles and `LineString.buffer(w/2, cap_style="round")` for stroked lines.
2. **Outline logic:** `silhouette = union(shapes).buffer(stroke/2)`. Each colour region is `shape.buffer(-stroke/2)` minus everything drawn on top of it (buffered by its stroke). Black is whatever is left: `silhouette − colours`.
3. **Text:** get glyphs from `matplotlib.textpath.TextPath(..., prop=FontProperties(fname=ttf))`. Union the polygons that share the largest one's orientation and subtract the opposite ones (nonzero fill), then flip y. Use fontTools `hmtx` advances to place each character along a curve, rotated to the tangent. An outlined word is `text.buffer(outline)` subtracted from the colour under it.
4. **Clean:** simplify at 0.02–0.03 mm and drop islands under about 0.5 mm². Raise that to about 4 mm² for a colour that sits *around* outlined text, because it leaves specks inside letter holes such as the O. Check the coloured preview for specks.
5. Flip y, centre on the origin, and scale to the size he asked for ("200 mm long" means scale by width). Check the bbox fits 250 × 250.
6. **3D:** the black body is `slab(silhouette, 0, T−INLAY)` fused with `slab(black_top, T−INLAY, INLAY)`. Each colour is `slab(region, T−INLAY, INLAY)`. Use INLAY 1.0–1.2 mm so white over black doesn't look grey. Thickness: about 8 mm for a 250 mm sign, 6 mm for about 200 mm.
7. **Print orientation:** *face-up* keeps colour changes to the last few layers (little purge, ironable top). *Face-down* (rotate 180° about Y, lift to z = 0) gives a smooth plate-textured front and lets legs rise off the back. Both worked; say which you picked.
8. **Preview** with matplotlib + `shapely.plotting.plot_polygon`, filling each region in its real colour. It's faster and clearer than cad_run's line projections, which drown in text edges.

### Stands for signs (simplest first)
- **Lies flat:** no stand. This is often the right answer for small tabletop plaques.
- **Two small slot feet (separate parts):** each 25 mm wide with a profile about 74 deep × 18 tall. The slot is thickness + 0.4, tilted back 15°, with a 5 mm floor, and the feet reach about twice the sign's COM offset behind it. The sign needs a **dead-flat bottom edge**, so straighten or clip it.
- **One piece:** print face-down with two triangular legs off the back behind the bottom corners, lean the sign back about 10°, and cut everything below the tilted table plane. A perfectly upright thin sign tips forward.

## 5. Print check before delivery

Run through this on the final preview and state the result in a few words, not a paragraph:
- Flat bottom? Which face is on the bed?
- Any overhang > 45° without a chamfer? Any bridge > 8 mm?
- Thinnest wall ≥ 1.2 mm? Smallest feature ≥ 0.8 mm? Smallest text ≥ 8 mm?
- Holes: clearance added for printing? Horizontal holes teardropped?
- Stray colour islands or specks removed? Every part watertight?
- Mass and print time estimate. Solid mass = volume × 1.24 g/cm³ for PLA (1.27 for PETG); a real print at 15% infill comes to roughly 35–45% of that. Time ≈ 1 h per 10 g at 0.2 mm as a rough figure.
- Does every fixed dimension from intake appear in the model? Re-check them against the source.

If something fails, fix it in the model; don't just warn.

## 6. Deliver

Send with SendUserFile.

**Route A:**
1. `name.step`: "Import into Onshape (Create → Import) for the solid."
2. `name.stl` and `name.3mf`, for the slicer.
3. `name_<sketch>.dxf` for each sketch: "Insert into a sketch on the plane named in the rebuild sheet, mm, then extrude" (the same trick as his image-to-cad-dxf skill).
4. Final preview PNG.
5. `name_rebuild.md`, the **Onshape rebuild sheet**: the agreed feature plan with final numbers. Put the variables table first, then one line per feature (plane or face, sketch contents with coordinates, operation, depth, end condition), then print orientation and tolerances used. Template: `references/rebuild-sheet-template.md` if present. This is the "native" part: following it gives him a full parametric feature tree in a few minutes, with variables he can change.
6. Route C only: `name.fs` with a 3-line paste-in instruction.
7. Route B only: the Onshape document link, and still the STL/3MF.

**Route S:** `name_BAMBU.3mf` (main file), `name_STLs_by_colour.zip` (backup), `name.step` (for Onshape), and the final coloured preview.

Reply in 3–6 lines: what it is, overall size, mass, the one assumption most likely to be wrong (slot fit, small text), and the import or Bambu load tip. Offer one next step (a fit-test print of just the critical feature, a lid, a mirrored version) only if it's a real one.

## 7. Bambu Studio 3MF with colours pre-assigned

He found clicking colour regions in the Bambu viewport painful: lots of tiny loose islands, and part names lost. So for anything multi-colour, ship **one object with named parts and filament slots set**, for example slot 1 black, 2 white, 3 pink, 4 red. Always ship a backup zip of per-colour STLs too. With those he drags all of them in at once, answers **Yes** to "single object with multiple parts", then picks each part by *name* in the object list rather than in the 3D view. This writer hasn't been confirmed in Bambu yet. If he reports a problem, fix it and note here what changed.

The writer is `scripts/bambu_3mf.py` (`bambu_3mf(path, obj_name, [(name, trimesh_mesh, slot), ...])`). If it isn't on disk, write it from this listing:

```python
import zipfile, numpy as np
def bambu_3mf(path, obj_name, parts, centre=(128, 128)):
    """parts: [(name, trimesh.Trimesh, filament_slot)] -> one object, named parts, slots preset."""
    allv = np.vstack([m.vertices for _, m, _ in parts]); lo, hi = allv.min(0), allv.max(0)
    off = np.array([centre[0]-(lo[0]+hi[0])/2, centre[1]-(lo[1]+hi[1])/2, -lo[2]])
    objs, comps, cfg = [], [], []
    for i, (n, m, slot) in enumerate(parts, 1):
        m = m.copy(); m.merge_vertices(); m.apply_translation(off)
        v = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in m.vertices)
        t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m.faces)
        objs.append(f'<object id="{i}" type="model"><mesh><vertices>{v}</vertices><triangles>{t}</triangles></mesh></object>')
        comps.append(f'<component objectid="{i}"/>')
        cfg.append(f'<part id="{i}" subtype="normal_part"><metadata key="name" value="{n}"/><metadata key="extruder" value="{slot}"/></part>')
    top = len(parts) + 1
    model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021">'
             '<metadata name="Application">BambuStudio-01.10.00.00</metadata><metadata name="BambuStudio:3mfVersion">1</metadata><resources>'
             + "".join(objs) + f'<object id="{top}" type="model"><components>{"".join(comps)}</components></object></resources>'
             f'<build><item objectid="{top}" printable="1"/></build></model>')
    config = (f'<?xml version="1.0" encoding="UTF-8"?><config><object id="{top}"><metadata key="name" value="{obj_name}"/>'
              '<metadata key="extruder" value="1"/>' + "".join(cfg) + '</object></config>')
    ct = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
          '<Default Extension="config" ContentType="text/xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct); z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model); z.writestr("Metadata/model_settings.config", config)
```

After writing it, reload it with trimesh and confirm every part is watertight with the expected volume.

## 8. Token economy: this skill is used a lot

- Ask in batches of ≤ 4, never one question per message.
- One image per stage, 800 px wide, with the four views composed into one PNG. No separate images per view.
- No essays. A stage update is an image plus two lines.
- Reuse the model file: edit the stage rather than regenerating the whole script in chat. Show code only when he asks.
- Look up datasheet numbers once, record them in the plan, and don't re-search.
- Read reference files only when needed, and only if they exist: the cheatsheet before the first build in a session, onshape-routes only for B/C, fdm-rules only for unusual geometry.

## 9. Script: scripts/cad_run.py

Write this to `scripts/cad_run.py` if it isn't on disk.

```python
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
print(f"volume {vol_mm3/1000:.2f} cm3   mass ~{vol_mm3/1000*args.density:.1f} g solid at {args.density} g/cm3")
print(f"faces {len(part.faces())}  edges {len(part.edges())}  solids {len(part.solids())}  valid {part.is_valid}")
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
    try:
        m = Mesher(); m.add_shape(part); m.write(f"{args.outdir}/{args.name}.3mf")
    except RuntimeError as e:
        print('3mf skipped:', e, '-> build it from the STL with scripts/bambu_3mf.py')
    for sname, sk in ns.get('sketches', {}).items():
        sk = sk.sketch if hasattr(sk, 'sketch') else sk
        ex = ExportDXF(unit=Unit.MM); ex.add_layer('0'); ex.add_shape(sk, layer='0')
        ex.write(f"{args.outdir}/{args.name}_{sname}.dxf")
    print('exported step/stl/3mf', '+ dxf' if ns.get('sketches') else '')
```

Model file pattern (keep the stages in plan order; bump `STAGE` or comment out later blocks when previewing early stages):

```python
from build123d import *
L, W, H, wall, hole_d = 60, 40, 12, 2.4, 3.4          # = Onshape variables
sketches = {}
with BuildPart() as bp:
    with BuildSketch() as s1:                          # Sketch 1 on Top plane
        RectangleRounded(L, W, 4)
    sketches['sketch1'] = s1
    extrude(amount=H)                                  # Extrude 1
    with BuildSketch(bp.faces().sort_by(Axis.Z)[-1]) as s2:   # Sketch 2 on top face
        with Locations((25, 15), (-25, 15), (25, -15), (-25, -15)):
            Circle(hole_d / 2)
    sketches['sketch2'] = s2
    extrude(amount=-H, mode=Mode.SUBTRACT)             # Extrude 2, remove
    offset(amount=-wall, openings=bp.faces().sort_by(Axis.Z)[0])   # Shell, bottom open
    fillet(bp.edges().filter_by(Axis.Z), radius=2)     # Fillet vertical edges
part = bp.part
```

## References (read only when needed, if they exist)

- `references/build123d-cheatsheet.md`: the API patterns this workflow uses, and the errors that waste runs
- `references/fdm-rules.md`: printability and tolerance numbers
- `references/onshape-routes.md`: Onshape MCP (route B) and FeatureScript (route C) setup and templates; STEP import and direct-edit tips
- `references/rebuild-sheet-template.md`: the rebuild sheet's format
- `references/related-work.md`: the repos and write-ups this skill borrows from
