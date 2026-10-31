# FDM design rules and tolerances (0.4 mm nozzle, 0.2 mm layers, PLA/PETG)

These are starting values. After the first fit-test print, record what he changed and use that next time.

## Walls and features
| Thing | Minimum | Preferred |
|---|---|---|
| Wall (vertical) | 0.8 mm (2 perimeters) | 1.6–2.4 mm (4–6 perimeters) for structural |
| Floor / roof | 0.8 mm | 1.2–1.6 mm (6–8 layers) |
| Pin / post diameter | 2 mm | ≥ 3 mm; add a 1 mm fillet at the base |
| Embossed text / detail | 0.6 mm height, 1.5 mm stroke | — |
| Engraved text | 0.4 mm depth | 0.8 mm |
| Slot width | 1 mm | — |

## Overhangs and bridges
- Unsupported overhang ≤ 45° from vertical. Above that: chamfer at 45°, or split the part, or accept supports (say so).
- Bridges: fine to ~8 mm; up to 20 mm with sag. Over that, add a support rib or redesign.
- Horizontal holes ≤ 8 mm: fine. Larger: teardrop (45° apex) or make the top flat (bridge).
- First layer: avoid fillets on the bed-contact edge; use a 0.3–0.5 mm chamfer instead to counter elephant's foot. Mouse-ears or a brim for tall narrow parts.

## Holes and fits (per side unless stated)
| Fit | Allowance |
|---|---|
| Vertical hole printed undersize | add 0.2–0.3 mm to diameter |
| Clearance (bolt slides through) | +0.3 mm on nominal (M3 → 3.4 mm) |
| Loose clearance (adjustable) | +0.5 mm |
| Press fit (bearing, magnet, pin) | −0.1 to −0.15 mm on diameter |
| Sliding fit (lid, drawer) | +0.3–0.4 mm per side |
| Snap-fit cantilever | arm 1.2–1.6 mm thick, length ≥ 8× thickness, 0.5–0.8 mm catch, 30° lead-in, 90° return; PLA fatigues quickly, PETG better |
| Heat-set insert M3 (standard brass) | hole 4.0 mm Ø × 5.7 mm deep, boss OD ≥ 7 mm |
| Heat-set insert M2.5 | hole 3.4 mm × 4.5 mm deep |
| Heat-set insert M4 | hole 5.6 mm × 7.0 mm deep |
| Captive hex nut M3 | 5.7 mm across flats pocket (nominal 5.5), 2.6 mm deep |
| Screw directly into plastic M3 | 2.5 mm hole (tap-forming), ≥ 6 mm engagement |
| Tapped M3 thread modelled | don't; use inserts or self-tapping |

## Strength
- Layer lines are the weak direction: orient so load is across layers, not peeling them apart. Cantilever brackets: print the arm flat on the bed if possible.
- Add gussets/ribs (1.6 mm) rather than thicker walls.
- Fillet inner corners (R ≥ 1 mm) where stress concentrates.
- PETG for anything near motors/batteries or that must flex; PLA for jigs and rigid mounts; TPU for grips/bumpers (walls ≥ 1.6 mm, no snap-fits).

## Mass and time
- Mass = volume × density: PLA 1.24, PETG 1.27, ABS 1.04, TPU 1.21 g/cm³ (solid). At 20 % infill a boxy part weighs roughly 40–60 % of solid.
- Time: ≈ 1 h per 8–12 g at 0.2 mm on a standard printer; halve for a fast printer (Bambu/Prusa Core One).

## Common robotics reference dims (verify when they matter)
- NEMA 17: 42.3 mm square, mounting holes 31 mm square, M3; pilot boss Ø22 mm × 2 mm; shaft Ø5 mm (D-flat 4.5).
- 608 bearing: 22 mm OD, 8 mm ID, 7 mm wide.
- ESP32 DevKit V1: ~51.5 × 28.3 mm, pins 2.54 mm pitch, two rows ~25.4 mm apart (board variants differ — check).
- Raspberry Pi 4: 85 × 56 mm, holes M2.5 at (3.5, 3.5) (61.5, 3.5) (3.5, 52.5) (61.5, 52.5).
- Arduino Uno: 68.6 × 53.4 mm, holes at (14, 2.5) (15.3, 50.7) (66.1, 7.6) (66.1, 35.5).
- VEX V5 structure: 12.7 mm (0.5") hole pitch, holes Ø 4.5 mm (#8-32 screws).
- Micromouse: 18 cm maze cells, 12 mm walls, 5 cm wall height.
