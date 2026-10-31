---
name: onshape-part-builder
description: "Design a 3D-printed part with Claude, delivered Onshape-native: questions, feature plan with variables, staged builds with previews, print check, then STEP/STL/3MF, DXF sketches and a rebuild sheet. Use whenever Albin wants a bracket, mount, case, enclosure, adapter, holder or jig modelled, CAD'd or 3D printed, even if he doesn't say Onshape."
category: tools
tags: [cad, onshape, 3d-printing, build123d, featurescript, step, dxf]
---

# Onshape Part Builder — describe a part, get an editable model

Albin explains the part; Claude does the CAD. The result must be something he can **open and edit in Onshape like he drew it himself**, not a dumb STL. This is a conversation with checkpoints, not a one-shot dump: short updates, a preview at every stage, a question only when the answer changes the design, alternatives offered where a real trade-off exists.

Why it's built this way (from people who've done it, see `references/related-work.md`): when Claude built whole parts in one go and the base shape was wrong, all the detail work was wasted. Agreeing the plan first, then building in stages, is both more accurate and far cheaper in tokens.

**Units are always mm.** Onshape, the slicer and Albin all think in mm.

## 0. Pick the delivery route (silently, then say it in one line)

| Situation | Route | What he gets |
|---|---|---|
| Default — nothing connected | **A. Rebuild sheet + STEP** | Feature plan with exact dims and variables (rebuilds natively in Onshape in minutes), STEP for import, STL/3MF to print, DXF per sketch, preview PNG |
| Onshape MCP tools present (`list_documents`, `create_sketch_*`, `create_extrude`…) | **B. Direct build** | Real feature tree in his Part Studio, built from the same plan, variables set in the variable table. Still ship STL/3MF + preview |
| Part is a *family* (same shape, different sizes/counts: motor mount for N motors, standoff set, bearing holder for any OD) or he asks for FeatureScript | **C. FeatureScript custom feature** | A `.fs` file to paste into a Feature Studio; the part becomes a feature with a dialog of parameters. Also ship route A outputs |

Route A is always produced. B and C sit on top of it. Setup for B and C is in `references/onshape-routes.md` — only read it when that route is in play.

STEP imports into Onshape as a solid with no feature tree; that's why the rebuild sheet matters. STL is a mesh and essentially uneditable, so it is only ever the print file.

## 1. Intake — ask only what changes the design

Read everything he gave first (text, photo, sketch, datasheet, Onshape link). Then ask **at most 4 questions in one message**, picked from this list, skipping anything already answered or safely defaulted:

1. **Function + mating parts.** What does it hold/attach to/sit in? Which faces touch other things? (This decides the base shape.)
2. **Critical dimensions**, and which are *fixed* (must match a real part) vs *free* (Claude can choose). Ask for a photo with a ruler, a datasheet, or the Onshape part it mates with.
3. **Fasteners / joints.** M3 screws? Heat-set inserts? Snap-fit? Press-fit? Zip-tie slots? Default for his robotics work: M3 clearance 3.4 mm, M3 heat-set insert hole 4.0 mm × 5.7 mm deep.
4. **Print setup.** Printer, material, nozzle. Default: FDM, PLA or PETG, 0.4 mm nozzle, 0.2 mm layers. This decides wall thickness and overhang rules.
5. **Which numbers will he want to tweak later?** Those become Onshape variables (`#wall`, `#hole_d`, `#length`).
6. **Where is it going** — GaelForce robot, Micromouse, FS accumulator, a lab bench? Tells you load and environment (vibration, heat, hands).

For known hardware (NEMA 17, ESP32 dev boards, 608 bearings, Raspberry Pi, VEX parts, common sensors) look the dimensions up rather than asking, and **state the numbers used** so he can correct them. Wrong reference dims are the number one reason printed parts don't fit.

Don't ask about things that don't matter yet (colour, infill, exact fillet radii). Pick a sensible default and say so.

## 2. Feature plan — the blueprint, agreed before any geometry

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

Ask: *"Build this, or change anything?"* Wait for the OK. Changing the plan costs a line; changing the model costs a rebuild.

Design rules that go into the plan (full list in `references/fdm-rules.md`):
- One flat face on the bed; design the part *around* its print orientation.
- Walls ≥ 1.2 mm (3 perimeters at 0.4 mm), prefer 2.0–2.4 mm for anything structural.
- Overhangs ≤ 45°; use chamfers (45°) rather than fillets on downward-facing edges.
- Horizontal holes: teardrop or ≤ 8 mm bridged. Vertical holes print 0.2–0.3 mm undersize — add clearance.
- Clearance fit 0.2–0.3 mm per side; press-fit −0.1 mm; sliding 0.4 mm.
- Fillet vertical edges (free strength, prints fine); avoid fillets on the bed-contact edge (elephant's foot).

## 3. Build stage by stage, preview every stage

Mirror the plan in **build123d** (Python, OpenCascade kernel, exports true STEP). One script, one stage at a time, in the same feature order as the plan so the code reads like the feature tree. Cheatsheet and gotchas: `references/build123d-cheatsheet.md` — read it before writing the first line; it saves failed runs.

Setup once: `pip install build123d cairosvg pillow --break-system-packages -q` (takes a couple of minutes the first time; say so).

Run every stage through `scripts/cad_run.py` (listing in section 7 if the file isn't on disk):

```
python3 scripts/cad_run.py model.py --name bracket --stage 2
```

It executes the model file, expects a variable `part`, and writes `out/bracket_s2.png` (iso + top + front + right in one image), prints bounding box, volume and PLA mass, and on the final stage (`--final`) also writes `.step`, `.stl`, `.3mf` and a DXF for each sketch stored in `sketches` (a dict of name → sketch). **Look at the PNG with Read before sending it.** If the shape is wrong, fix it before showing him — he should see a candidate, not a bug.

Per-stage message to him (this is the whole update; keep it to this):
- the preview image
- 1–2 lines: what was added, any number you chose
- a question **only if** the next stage depends on something he hasn't decided

Stage grouping: base body → cutouts/holes → shell/pockets → fillets/chamfers → final. Don't preview every fillet; group small operations. Three to five previews is normal for a bracket; a case might be six.

If he says "looks wrong", ask what specifically in one line, or offer two guesses with a preview of each if cheap. Don't rebuild from scratch; change the stage.

## 4. Print check before delivery

Run through this on the final preview and state the result in a few words (not a paragraph):
- Flat bottom? Which face is on the bed?
- Any overhang > 45° without a chamfer? Any bridge > 8 mm?
- Thinnest wall ≥ 1.2 mm? Smallest feature ≥ 0.8 mm?
- Holes: clearance added for printing? Horizontal holes teardropped?
- Mass and print time estimate (mass from script; time ≈ 1 h per 10 g at 0.2 mm as a rough figure).
- Does every fixed dimension from intake appear in the model? Re-check them against the source.

If something fails, fix it in the model, don't just warn.

## 5. Deliver

Send with SendUserFile:
1. `name.step` — "Import into Onshape (Create → Import) for the solid."
2. `name.stl` and `name.3mf` — for the slicer.
3. `name_<sketch>.dxf` for each sketch — "Insert into a sketch on the plane named in the rebuild sheet, mm, then extrude" (same trick as his image-to-cad-dxf skill).
4. Final preview PNG.
5. `name_rebuild.md` — the **Onshape rebuild sheet**: the agreed feature plan with final numbers, variables table first, one line per feature (plane/face, sketch contents with coordinates, operation, depth, end condition), print orientation, and tolerances used. Template: `references/rebuild-sheet-template.md`. This is the "native" part: following it gives him a full parametric feature tree in a few minutes, with variables he can change.
6. Route C only: `name.fs` with a 3-line paste-in instruction.
7. Route B only: the Onshape document link, and still the STL/3MF.

Reply in 3–6 lines: what it is, overall size, mass, the one assumption most likely to be wrong, and the import tip. Offer one next step (fit-test print of just the critical feature, a lid, a mirrored version) only if it's a real one.

## 6. Token economy — this skill is used a lot

- Ask in batches of ≤ 4; never one question per message.
- One image per stage, 800 px wide, four views composed into one PNG. No separate images per view.
- No essays. A stage update is an image plus two lines.
- Reuse the model file; edit the stage, don't regenerate the whole script in chat. Show code only when he asks.
- Look up datasheet numbers once, record them in the plan, don't re-search.
- Read reference files only when needed: cheatsheet before the first build in a session, onshape-routes only for B/C, fdm-rules only for unusual geometry.
- If the first install of build123d fails on the Python version (needs 3.10–3.12), say so once and fall back to CadQuery (`pip install cadquery`) with the same plan; don't loop on installs.

## 7. Script — scripts/cad_run.py

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
```

Model file pattern (keep stages in plan order; bump `STAGE` or comment out later blocks when previewing early stages):

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

## References (read only when needed)

- `references/build123d-cheatsheet.md` — the API patterns this workflow uses, and the errors that waste runs
- `references/fdm-rules.md` — printability and tolerance numbers
- `references/onshape-routes.md` — Onshape MCP (route B) and FeatureScript (route C) setup and templates; STEP import + direct-edit tips
- `references/rebuild-sheet-template.md` — the deliverable's format
- `references/related-work.md` — the repos and write-ups this skill borrows from
