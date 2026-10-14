---
name: ltspice-helper
description: Use when building, checking or debugging LTspice simulations, especially from screenshots of schematics, .op output, error messages or waveforms, for circuit homework.
category: ee
tags: [ltspice, simulation, circuits, debugging]
---

# LTspice helper

Help the user build schematics that match a homework figure, and debug their LTspice screenshots. Replies are short: a verdict first, then numbered fixes or a comparison table. Never a wall of text.

---

## 0. First, work out what was sent

| Screenshot shows | Go to |
|---|---|
| Schematic (grey background, blue wires) | Section 2: read the schematic |
| Text window titled `...net` with `--- Operating Point ---` | Section 4: read .op output |
| Error dialog or SPICE Error Log | Section 5: errors |
| Waveform plot (black or white axes, traces) | Section 6: plots |
| Component Attribute Editor or Select Component dialog | Section 3: parts |

If the homework figure is available, look at it (render the PDF page) before judging anything. Never check a schematic against a remembered topology.

If a screenshot is too small or cropped to read values, pin squares or dots, say exactly what can't be read. For connectivity disputes, ask for **View > SPICE Netlist** copied as text: it shows every connection exactly.

---

## 1. LTspice visual language (how to read a schematic image)

| What you see | What it means |
|---|---|
| Blue lines | wires |
| **Filled square** on a wire | a junction: 3 or more wires join here (connected) |
| Wires crossing with **no** filled square | **not connected** |
| **Small open (hollow) square** at a component pin | **that pin is unconnected**: a key bug sign |
| Wire end stopping near, but not on, a pin | not connected (no square on the pin end) |
| Wire running straight through a component body | that component is **shorted** |
| Triangle (or 3 stacked bars) symbol | ground, node 0 |
| Text attached to a wire end (net label / flag) | a named net; joins **only** other labels with the identical name |
| Black text starting with `.` (e.g. `.op`) | a SPICE directive (active) |
| Blue text, or text starting with `;` | a comment (ignored!) |
| Name above a part (R1, V1, E1) and value below (1k, 12) | instance name and value |
| Value that just repeats the default letter (`R`, `V`, `I`, `E`) | **value never set** |
| Circle with + and - | voltage source; + terminal at the + mark |
| Circle with an arrow | current source; current flows **out of the arrow tip** |
| Circle (or diamond) with 4 pins, labelled E | VCVS. In `e`: left pins are the controls (+ top, - bottom), right/top-bottom pins are the output |
| Window title `Draft1.asc` / `.net` | unsaved, so remind them of the filename convention |

---

## 2. Reading and debugging a schematic

Do this systematically. Don't eyeball it.

1. **List the parts and values** you can read. Check each value against the expected one (from the student-number mapping). Flag unit traps (Section 3).
2. **Build the node list from the image**: for every junction, write which pins touch it. Example: "Node X: R1 right, R2 top, R3 left."
3. **Build the node list from the homework figure** the same way.
4. **Compare node by node.** Every difference is a fix.
5. **Run the checklist:**
   - [ ] Ground symbol present, on the right node (usually the bottom rail)
   - [ ] `.op` (or the required analysis) present as a directive, not a comment
   - [ ] No open squares on any pin (check VCVS output - and the control pins especially)
   - [ ] Every crossing that should join has a filled square; every crossing that shouldn't, doesn't
   - [ ] Every net label has a partner with the identical name
   - [ ] Source polarity and current-source arrow match the figure
   - [ ] No wire passes through a component body
   - [ ] Dependent-source control pins on the correct nodes (+ and - not swapped)
6. **Reply format:**
   - One-line verdict ("Values are right; 3 wiring problems.")
   - Numbered fixes, each saying **where** in the picture ("the small square under E1") and **what to do**
   - What they should see after fixing (a short table of expected values)

If parts are named differently from the figure (R1 for Rs, etc.), give a mapping table and suggest renaming. It's optional, but it helps the marker.

---

## 3. Parts, values and unit traps

**Values (case-insensitive, except where noted):**

| Type | Means | Trap |
|---|---|---|
| `k` | kilo | `10K` and `10k` are both fine |
| `m` or `M` | **milli** | `1M` is 1 milli-ohm, NOT 1 megaohm |
| `meg` | mega | use `1meg` |
| `u` or `µ` | micro | |
| `n`, `p` | nano, pico | |
| `f` | **femto** | `1F` is a femtofarad; write `1` for 1 farad |
| space inside a value | breaks it | `10 k` is wrong |

Currents: `1m` = 1 mA, `1006u` = 1006 uA.

**Components:**

| Need | Key / name | Notes |
|---|---|---|
| Resistor | R | Ctrl+R rotates |
| Voltage source | F2, `voltage` | + at the top by default |
| Current source | F2, `current` | arrow points **down** by default; Ctrl+R twice to point up |
| Ground | G | required |
| Net label | F4 | |
| VCVS | F2, `e` | controls: + top-left, - bottom-left. Value = gain (e.g. `107k`) |
| VCVS (alt) | `e2` | controls swapped: **- top-left, + bottom-left**. Prefer `e` |
| VCCS / CCCS / CCVS | `g` / `f` / `h` | `f` and `h` need a controlling voltage source name |
| Edit values | right-click the part | or Ctrl+right-click for the full Attribute Editor; change the **Value** row |
| Analysis | `.op` via Simulate > Edit Simulation Cmd > DC op pnt | |

**Netlist form** (offer this when drawing is a pain):
```
Rname  n1 n2 value
Vname  n+ n- value
Iname  nfrom nto value      (current flows from nfrom through the source to nto)
Ename  out+ out- ctrl+ ctrl- gain
.op
.end
```
Node `0` is ground.

---

## 4. Reading `.op` output

The format is `V(node): value voltage` and `I(part): value device_current`.

1. **Map nodes to the figure.** Unnamed nets show as `n001`, `n002`... (the numbering isn't meaningful). Identify each one by its value against your hand calculation. Named nets show as `V(name)`, so suggest F4 labels for clearer output.
2. **Make a comparison table:** quantity | LTspice | hand | ✓ or ✗.
3. **Interpret numbers:**
   - `1e-25`, `9.4e-26` and the like mean **0** (numerical noise), so that node is effectively at ground.
   - The sign of a resistor current is positive from **pin 1 to pin 2**. Unrotated vertical: pin 1 is at the top, so positive means top to bottom. A negative value with the right magnitude means the resistor is drawn the other way round; it is not a wrong answer. Fix it by rotating 180 degrees.
   - A voltage-source current is measured **into the + terminal**, so a source delivering power reads **negative**. That's normal.
   - Ground not on the bottom rail shifts every node voltage by a constant; currents are unchanged. Spot it when a node you expect at 0 isn't, or one reads negative.
4. **Compute what the homework needs** from the readings (e.g. P = V × I, voltage across a part = difference of its two node voltages).

**Symptom → likely cause**

| Symptom | Likely cause |
|---|---|
| Right magnitude, wrong sign | part orientation, or arrow/polarity reversed |
| Off by exactly 1000 or 10^6 | unit prefix (`M` vs `meg`, `m` vs `k`, `u` missing) |
| A current is 0 that shouldn't be | open pin, a missing junction dot, or a part shorted by a wire |
| A node equals the source voltage unexpectedly | a resistor shorted, or a wire through a part |
| Everything is 0 | source value unset or 0, or the source is shorted |
| A node far from expected | wrong node on a dependent-source control pin, or a label not joined |
| VCVS/op-amp: V(+ input) < V(- input) while the output is positive | **control pins swapped**. Note that ideal linear SPICE can still give a plausible-looking `.op` answer with swapped pins (there's no saturation), so check visually and check that V(+) is slightly above V(-) |
| A huge vo while Vout is small | normal if a load pulls current through a series resistor; the feedback raises vo to compensate |

Always explain what notable numbers mean physically, in one or two lines (e.g. "vo = 1.94 V because RL pulls 18 mA through R4").

---

## 5. Errors

| Message | Cause | Fix |
|---|---|---|
| `Singular matrix` / `Node X is floating` | no ground; a node with only one connection; an open pin | add ground; find the open square; connect the pin |
| `Voltage source loop` / sources in parallel | two voltage sources (or a source plus a wire) across the same nodes | remove the loop |
| Current source in series with an open | the current has nowhere to go | close the path |
| `Unknown parameter` / `missing value` | typo in a value, or a space in a value | retype the value |
| No output window | no analysis directive, or it's a comment | add `.op` as a directive |

---

## 6. Plots (transient / AC / DC sweep)

- Read the axis units and scale before judging. Note the cursor values if shown.
- Flat at 0: wrong probe point or unconnected. Flat at a rail: saturation.
- To check a value, ask for the cursor reading (click the trace label, then attach a cursor).

---

## 7. Useful verification runs

- **Superposition:** zero one source at a time (V source → `0`, I source → `0`); (i) + (ii) should equal (iii).
- **Open circuit:** set the load to `1T`. **Short circuit:** set it to `1u`.
- **Norton/Thevenin:** short A–B with a wire to read In; build In with Rn and the load as a second circuit, and the load current should match.

## 8. Submission

- Save as `STUDENTNUMBER_q1a.asc` and so on (not Draft1).
- Screenshot the full schematic (with ground and `.op` visible) and the `.op` window for the SPICE boxes.