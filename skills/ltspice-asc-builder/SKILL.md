---
name: ltspice-asc-builder
description: Build ready-to-open LTspice .asc schematic files for circuit homework or labs, laid out like the sheet's figure and checked before sending, for any student number. Also reads the question to find every SPICE output it asks for (schematic image, .op table, plots, measured values) and explains exactly how to get each one. Use whenever someone wants an LTspice file, asks how to do a question in LTspice or SPICE, or needs simulation screenshots for an assignment, even if they don't say ".asc".
category: ee
tags: [ltspice, schematic, asc, simulation, circuits, homework]
---

# LTspice .asc builder

The user should only have to open the file, press Run, and copy what the sheet asks for into their answer. So you deliver three things per question:

1. **A ready-to-open `.asc` file** that looks like the sheet's figure and has been checked by the script.
2. **A "what the sheet wants" table**: every SPICE item the question asks for, and the clicks to get it.
3. **The numbers they should see**, from your own hand calculation, so they can tell if it worked.

`SKILL_DIR` below means the folder this file is in (shown as "Base directory for this skill" when the skill loads). The checked generator is `SKILL_DIR/scripts/ltasc.py`. Use it rather than writing `.asc` text by hand: hand-written coordinates almost always leave pins unconnected.

## Step 1: Get the student number (never assume one)

Component values usually depend on the student's number. Take it from the user's message or from a filled-in box on their sheet. If you can't find it, ask for it before building anything. Never reuse a number from an example, an earlier file, or memory: a wrong number gives every value wrong.

Use the number only for values and the file name. Don't write it inside the schematic (no title text).

## Step 2: Read the question properly

Extract the text and render the pages so you can see the figures:

```bash
pdftotext -layout sheet.pdf sheet.txt
pdftoppm -png -r 110 sheet.pdf page        # then Read page-N.png for each figure you need
```

Look at the actual figure before deciding the circuit. Don't rebuild a circuit from memory or from its name.

Then write down two lists.

**A. Values.** Find the box that maps digits to symbols (e.g. "α γ δ ε η θ λ" over the last seven digits). `symbol_values(number, ['α','γ',...])` in ltasc does the last-digits mapping. Show the mapping as a table, then each component value with its unit.
- If a formula uses a symbol that isn't in the box (a typo like σ), say so, pick the most likely meaning, and state the assumption in your reply.

**B. Deliverables.** Search the whole sheet, including the instructions on page 1, for everything about simulation:
- answer boxes such as "SPICE circuit schematic", "SPICE output", "plot", "waveform", "table", "node voltages and branch currents", "Bode plot";
- the quantity that sub-question asks for (e.g. "maximum value of Vout", "Vc at 250 µs"); the SPICE output should show *that* number;
- rules for files (e.g. "upload the .asc files labelled STUDENTNUMBER_Q1a"). Follow the exact naming, including capital letters.

If the sheet only says "SPICE output", choose the output that best proves the asked quantity (see `references/recipes.md`).

## Step 3: Pick the analysis

Read `SKILL_DIR/references/recipes.md` and pick the row that matches. Common ones:

| Asked for | Use |
|---|---|
| DC voltages, currents, Thévenin | `.op` |
| Equivalent capacitance | 1 mA charging + `.meas` |
| Peak of a sine response | `SINE(...)` source + `.tran` + `.meas MAX` |
| Value at a time after a switch | `.ic` + `.tran` + `.meas FIND ... AT` |
| Cutoff / Bode | `AC 1` source + `.ac` |

Add `.meas` lines whenever a single number is asked for. They put the answer in the SPICE Error Log, which is easier to read and screenshot than a cursor.

If there's no sheet (a lab or prelab described in the message), take the values and the list of outputs from the message itself and skip the student number.

## Step 4: Hand-calculate the expected answer

Work out the answer in Python first, with the real values. This is how you'll know the schematic is right, and the user needs it to check their run. For circuits with more than one unknown node, write one KCL equation per node and solve them together:

```python
import numpy as np
# unknowns [V2, V3]; each row is one node's KCL (currents leaving = 0), constants moved to the right
A = np.array([[1/Rg + 1/Rf, -1/Rf], [gm - 1/Rf, 1/Rf + 1/Ro + 1/RL]])
V2, V3 = np.linalg.solve(A, [Vin/Rg, 0])
```

## Step 5: Build the schematic with ltasc

Write a short build script. Lay parts out **in the same arrangement as the sheet's figure**: same left-to-right order, parallel parts stacked, ground at the bottom.

```python
import sys; sys.path.insert(0, 'SKILL_DIR/scripts')
from ltasc import Sch
s = Sch()
vp, vn = s.vsrc('Vin', 'SINE(0 250m 2k)', top=(64, 160))   # + at top
a, b   = s.h('res', 'Rg', '1008', left=(64, 96))            # horizontal: (left pin, right pin)
t, u   = s.v('res', 'Ro', '107k', top=(400, 96))            # vertical: (top pin, bottom pin)
s.wire(vp, (64, 96))         # straight segments only; pass several points for an L-shape
s.wire(b, (400, 96), t)
s.flag(b, 'v2')              # name every node you'll read: V(v2) in the output
s.gnd_drop(vn); s.gnd_drop(u)
s.directive('.tran 0 1m 0 1u', (64, 400))
s.directive('.meas TRAN vmax MAX V(v2)')
errs, warns = s.check(expect={'v2': ['Rg.1', 'Ro.0']})     # list the parts on each important node
s.save('OUT/STUDENTNUMBER_Q1b.asc'); s.preview('OUT/preview_Q1b.png'); print(s.netlist())
```

Sizes (grid of 16): `res`/`ind` are 80 long, `cap` 64, sources 80 tall. A part's pins are returned, so wire straight from them.

Placement helpers:

| Call | Gives | Notes |
|---|---|---|
| `s.h(sym, name, value, left=)` | (left, right) | horizontal res/cap/ind |
| `s.v(sym, name, value, top=)` | (top, bottom) | vertical res/cap/ind |
| `s.vsrc(name, value, top=, plus='top')` | (+, −) | `plus='bottom'` flips it |
| `s.isrc(name, value, top=, arrow='up')` | (top, bottom) | arrow = direction current leaves |
| `s.dep('e' or 'g', name, value, out_plus=)` | (out+, out−, ctrl+, ctrl−) | pins unconfirmed, see below |
| `s.part(sym, name, value, rot, at=, pin=)` | all pins | anything else (`f`, `h`) |

Layout rules that keep the check clean:
- Rows of horizontal parts at least 96 apart; columns of vertical parts at least 128 apart, so labels fit.
- Leave 32 to 64 of wire between a part and a corner or junction.
- Every junction must be wire **ends**. Split long wires where something joins.
- Use `gnd_drop()` so ground symbols point down.
- A source with a long value (`SINE(0 250m 2k)`) has a long label: leave about 200 clear to the right of it.
- `e`/`g` sit upright with out+ on top and the two control pins 48 to the left (ctrl+ above ctrl−). If the figure has the op amp's inverting input on top, don't cross wires to fix it: put net flags (`s.flag`) on the control pins and on the matching nodes, so they join by name.

## Step 6: Check it (don't skip)

1. `s.check(...)` must print `RESULT: OK`. Fix every ERROR. Fix WARN lines about labels sitting on wires or overlapping; move parts apart.
2. Read the preview PNG. Boxes are part bodies, dashed boxes are estimated labels. Compare it with the sheet's figure.
3. Read the printed netlist and compare it node by node with the figure: for each node, which part ends touch it? Every mismatch is a wiring bug.
4. Sign check for dependent sources: compare the current/voltage direction with the arrow on the figure (see `recipes.md`).

**Unconfirmed parts.** `e`, `g`, `f`, `h` pin positions are not yet confirmed from a real LTspice screen. When you use one:
- also `s.flag()` each of its pins with its net name, so the nets still join if a pin is off;
- save `s.netlist()` as `STUDENTNUMBER_Qx.cir` too (LTspice opens it directly) as a guaranteed backup;
- ask the user for a screenshot once it's open.

## Step 7: Deliver

Save the files, send them with SendUserFile (`display: attach`), or say where they are saved if you can't send files. Then reply with this template. Keep it short; the user wants clicks, not theory.

```
**Q1(b) in LTspice**: `25xxxxxx_Q1b.asc` is attached. Open it and press Run.

| The sheet asks for | Put this in the box | How to get it |
|---|---|---|
| SPICE circuit schematic | picture of the schematic | Open the file → Space (zoom to fit) → Win+Shift+S → paste |
| SPICE output | V(vout) plot + the vmax line | Run → click the vout wire → View > SPICE Error Log (Ctrl+L) → screenshot both |

**You should see:** vmax ≈ 1.334 V (hand calculation 1.334 V).

**When it opens:** check for hollow squares on any pin (a pin not connected). If there are any, send me a screenshot.
```

Take the "How to get it" steps from `SKILL_DIR/references/outputs-howto.md`: copy the matching steps, shortened. One row per item the sheet asks for, plus a row for any file-upload rule. For a plot, say which trace to click, what axis range shows it best, and how to read the value (cursor or `.meas`).

## When the user sends a screenshot back

Check it carefully: hollow squares (unconnected pins), labels on wires, values, and the output numbers against your hand calculation. To re-check a file they edited, run `python3 SKILL_DIR/scripts/ltasc.py check FILE.asc --png view.png`. If a screenshot confirms an unconfirmed part's pins (`ok=False` in `SYM`), tell the user so the skill can be updated.

## Facts confirmed in real LTspice

- **`g` (VCCS) sign.** Placed upright (arrow down, out+ on top at the output node, ctrl+ on top at the controlling node, matching a sheet figure that shows the arrow down), the real LTspice result matched the hand calculation only with the value **negated** (`-2202u`). The checker's `.cir` netlist and the real LTspice netlist therefore disagree in sign for `g`. So: put the **negative** gm on the schematic, say so in the reply ("the g part in LTspice points the other way, so the value is -gm"), and compare `vmax` with the hand calculation. If you give a `.cir` backup, write the same negated value there too. **`f` (CCCS) is confirmed with a positive gain**: placed R180 (arrow up) at the output node with the 0 V sense source in the controlling branch, `F1 ... Vsense 206` gave the right Rth in real LTspice (no sign flip). **`e` (VCVS, used as an ideal op amp with gain 1e6) is confirmed with a positive gain**: upright, out+ on top, ctrl+ above ctrl- (flag both control pins by name), the Howland current source matched the hand values in real LTspice. `h` sign is still unconfirmed: always compare the output with the hand calculation and try the sign flip first if it is off.
- Pins at R0: `res`/`ind` (16,16),(16,96); `cap` (16,0),(16,64); `voltage` (0,16)=+, (0,96)=−; `current` (0,0),(0,80) with its arrow pointing from the first pin to the second.
- Rotating a local offset (x,y): R90 → (−y, x), R180 → (−x, −y), R270 → (y, −x). y points down.
- Label positions (WINDOW lines) are in the part's own frame and rotate with it. On rotated parts, labels need `VTop`/`VBottom` or they read sideways. The library does this for you.
- Ground and net labels draw pointing away from the wire they sit on.
