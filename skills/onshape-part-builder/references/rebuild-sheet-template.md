# Onshape rebuild sheet — template

Deliver as `<name>_rebuild.md`. Every number is final. Sketch coordinates are in the sketch's own plane with the origin at the Onshape origin unless stated. Following it top to bottom gives a native feature tree; the variables make it parametric.

```markdown
# <Part name> — Onshape rebuild sheet
Overall: L × W × H mm · mass ~N g (PLA) · print face: <which face on bed>

## Variables (Variable table, create first)
| Name | Value | What it controls |
|---|---|---|
| #L | 60 mm | overall length |
| #wall | 2.4 mm | shell wall |
| #hole_d | 3.4 mm | M3 clearance |

## Features (in order)
1. **Sketch 1** — plane: Top. Rectangle #L × #W centred on origin, corner fillets R4.
   (or: Insert DXF `<name>_sketch1.dxf`, mm, centred on origin)
2. **Extrude 1** — Sketch 1, Blind, #H, New.
3. **Sketch 2** — plane: top face of Extrude 1. Circles Ø#hole_d at (±25, ±15).
4. **Extrude 2** — Sketch 2, Through all, Remove.
5. **Shell 1** — remove bottom face, thickness #wall.
6. **Fillet 1** — all vertical outer edges, R2.
7. **Chamfer 1** — bottom outer edge, 0.4 mm (elephant's foot).

## Tolerances used
M3 clearance +0.4 · lid sliding fit +0.3/side · insert holes Ø4.0 × 5.7

## Assumptions to check
- ESP32 board taken as 51.5 × 28.3 mm (DevKit V1); measure yours.
```

Rules:
- Name features the way Onshape would (Sketch 1, Extrude 1…) so the sheet maps 1:1 to the tree.
- Say the plane or face for every sketch. "Top face of Extrude 1" is better than "Z = 12".
- Give coordinates for every hole/feature, not "near the corner".
- Put every number the user said he'd tweak in the variables table.
- Keep it under a page. If the part has more than ~15 features, consider splitting the part.
