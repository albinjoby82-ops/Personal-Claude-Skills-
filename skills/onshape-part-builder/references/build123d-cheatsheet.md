# build123d cheatsheet for this workflow

build123d = Python parametric CAD on OpenCascade. Builder mode (`with BuildPart()`) reads like an Onshape feature tree, which is why we use it. Docs: https://build123d.readthedocs.io

## Imports and structure
```python
from build123d import *
with BuildPart() as bp:
    ...                      # features in Onshape order
part = bp.part               # what cad_run.py expects
```
Everything inside `BuildPart` auto-combines: new solids ADD by default; use `mode=Mode.SUBTRACT` to cut, `Mode.INTERSECT` to keep the overlap.

## Sketches (= Onshape Sketch feature)
```python
with BuildSketch() as s:                     # on XY = Onshape "Top" plane
with BuildSketch(Plane.XZ) as s:             # XZ = "Front", Plane.YZ = "Right"
with BuildSketch(bp.faces().sort_by(Axis.Z)[-1]) as s:   # on the topmost face
with BuildSketch(Plane.XY.offset(10)) as s:  # plane offset 10 mm up
```
Shapes (all centred on the sketch origin unless placed): `Rectangle(w, h)`, `RectangleRounded(w, h, r)`, `Circle(r)`, `Ellipse(a, b)`, `RegularPolygon(r, n)`, `SlotOverall(length, width)`, `Polygon((0,0),(10,0),(10,5))`, `Text("A", 8)`.
Place copies: `with Locations((x, y), (x2, y2)): Circle(r)`; grids: `with GridLocations(x_spacing, y_spacing, nx, ny): ...`; rings: `PolarLocations(radius, count)`.
Cut inside a sketch: `Circle(5); Circle(3, mode=Mode.SUBTRACT)`.
Sketch of a profile for Onshape DXF export: keep each sketch as its own `with BuildSketch() as sN:` and store `sketches['sketchN'] = sN`.

## 3D features
| Onshape feature | build123d |
|---|---|
| Extrude (blind) | `extrude(amount=10)` after a sketch; negative amount = other way |
| Extrude remove | `extrude(amount=-10, mode=Mode.SUBTRACT)` |
| Extrude through all | `extrude(amount=big, mode=Mode.SUBTRACT)` or `extrude(until=Until.LAST, mode=Mode.SUBTRACT)` |
| Extrude symmetric | `extrude(amount=5, both=True)` |
| Revolve | `revolve(axis=Axis.Z, revolution_arc=360)` |
| Sweep | `sweep(path=my_wire)` |
| Loft | two sketches then `loft()` |
| Shell | `offset(amount=-wall, openings=bp.faces().sort_by(Axis.Z)[0])` (negative = inward) |
| Fillet | `fillet(bp.edges().filter_by(Axis.Z), radius=2)` |
| Chamfer | `chamfer(bp.edges().group_by(Axis.Z)[0], length=1)` |
| Hole | `with Locations(...): Hole(radius=1.7, depth=10)` (depth None = through) |
| Counterbore | `CounterBoreHole(radius, counter_bore_radius, counter_bore_depth)` |
| Countersink | `CounterSinkHole(radius, counter_sink_radius)` |
| Mirror | `mirror(about=Plane.YZ)` (keeps original + mirrored) |
| Linear pattern | `with Locations(...)` or `GridLocations` around the primitive |
| Circular pattern | `with PolarLocations(r, n): ...` |
| Boolean with another part | `add(other_part, mode=Mode.SUBTRACT)` |
| Primitives (no sketch) | `Box(l, w, h)`, `Cylinder(r, h)`, `Sphere(r)`, `Cone(r1, r2, h)`, `Torus(R, r)` |

Primitives are centred on the origin; put them with `with Locations((x, y, z)):` or `align=(Align.CENTER, Align.CENTER, Align.MIN)` to sit on Z = 0 (most useful: the part's bed face at Z = 0).

## Selecting geometry (the part Onshape does by clicking)
```python
bp.faces().sort_by(Axis.Z)[-1]        # top face;  [0] bottom
bp.faces().filter_by(Axis.Z)          # all faces whose normal is ±Z
bp.edges().filter_by(Axis.Z)          # edges parallel to Z (vertical edges)
bp.edges().group_by(Axis.Z)[-1]       # edges at the highest Z level
bp.faces().filter_by(GeomType.CYLINDER)   # hole walls
bp.edges().filter_by(GeomType.CIRCLE)     # circular edges (for chamfering hole mouths)
bp.faces().sort_by(Axis.X)[-1]        # +X side face
bp.edges().filter_by(Axis.Z).sort_by(Axis.X)[:2]   # the two leftmost vertical edges
```
Selections are evaluated when written, so select **after** the geometry that creates the edges exists and **before** later features change them.

## Teardrop hole (horizontal holes for FDM)
```python
with BuildSketch(Plane.XZ) as s:
    Circle(r); 
    with Locations((0, r * 0.414)): Rectangle(2 * r * 0.707, 2 * r * 0.707, rotation=45)   # 45° cap on top
extrude(amount=L, mode=Mode.SUBTRACT)
```

## Gotchas that waste runs
- `Plane.XZ` has its normal pointing −Y; "up" in that sketch is +Z. If a cut goes the wrong way, flip the sign of `amount`.
- `offset()` for shells needs a face selection that exists; select the opening face *after* fillets if you fillet first, or shell before filleting (Onshape order usually: shell then fillet outer edges).
- `fillet` fails if radius ≥ half the wall thickness or on edges already touched by a chamfer; reduce the radius or select fewer edges. An error message mentioning `BRep_API: command not done` means exactly that.
- `Hole` depth is measured from the sketch plane downward along −Z of that plane; use `depth=None` for through-all.
- `part.solids()` > 1 after a cut means a feature didn't touch the body — usually a sketch on the wrong plane or an offset in the wrong direction.
- Export: `export_step(part, "x.step")`, `export_stl(part, "x.stl")`, 3MF via `Mesher()`. DXF via `ExportDXF` on a sketch/face, as in cad_run.py.
- Python 3.13+: build123d's kernel wheels (cadquery-ocp) may be missing. Use Python 3.10–3.12, or CadQuery as fallback (same ideas, fluent API: `cq.Workplane("XY").box(60,40,12).faces(">Z").workplane().hole(3.4)`).
- Big fillet selections on complex parts are slow; do them last and once.
