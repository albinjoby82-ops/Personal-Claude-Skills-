# Getting each output out of LTspice

Plain click-by-click steps for LTspice 24 on Windows (Mac differences at the end). Copy the steps that match each thing the sheet asks for into the "How to get it" column of your reply. Keep each to a few short steps.

## Contents
1. Schematic image
2. DC table (.op): node voltages and branch currents
3. Measured numbers (.meas) in the SPICE Error Log
4. Time plot (.tran)
5. Frequency plot / Bode (.ac)
6. Sweep plot (.dc or .step)
7. Reading values with cursors
8. Making plots look good for a report
9. Exporting data
10. Mac differences

---

## 1. Schematic image ("SPICE circuit schematic")

1. Open the `.asc` file (double-click it, or File > Open).
2. Press **Space** (zoom to fit) so the whole circuit and the directives show.
3. Take a screenshot: **Win + Shift + S**, drag around the schematic, paste it into the Word answer box.
   - Or **Tools > Copy bitmap to Clipboard**, then paste. That gives a cleaner image.
4. Make sure the analysis directive (`.op`, `.tran`...) is visible in the image. Markers look for it.

## 2. DC table: node voltages and branch currents (`.op`)

1. Click **Run** (running-man icon), or Simulate > Run.
2. A window titled **Operating Point** pops up: a table of `V(node)` and `I(part)`.
3. Screenshot that window for the "SPICE output" box.
4. If it doesn't pop up, the file probably also has `.tran` or `.ac` on it. Only `.op` gives the table.
5. To show values on the schematic itself: right-click a wire > **Place .op Data Label**. Good for one key number.

Reading it:
- Named nodes show as `V(a)`, `V(vout)`. Unnamed ones show as `V(n001)`: match them by value.
- `I(R1)` is positive when current flows from pin 1 to pin 2 of R1.
- A voltage source supplying power shows a **negative** current. That's normal.
- Tiny numbers like `1e-15` mean zero.

## 3. Measured numbers in the SPICE Error Log (`.meas`)

1. Run.
2. **View > SPICE Error Log** (or **Ctrl + L**).
3. Scroll to the lines that start with the measurement names, e.g. `cab: 1m*1u/va=5.48e-10`.
4. Screenshot those lines (or copy the text) for the "SPICE output" box.

## 4. Time plot (`.tran`)

1. Run. A blank plot pane opens above the schematic.
2. Move the mouse over a **wire**: it turns into a probe. Click to plot that node's voltage.
   - Click a **part body** to plot its current.
   - To plot a voltage *across* a part: click and hold on one end, drag to the other end, release.
3. Add more traces: right-click the plot > **Add Traces**, then pick e.g. `V(vout)` and `V(vin)`.
4. Zoom: drag a box on the plot. Right-click the plot > **View > Zoom Full** to go back.
5. Set exact axis limits: hover the axis numbers until the cursor becomes a ruler, then right-click and type the limits.

## 5. Frequency plot / Bode (`.ac`)

1. The input source needs **AC 1** in its value (right-click the source > Advanced > AC Amplitude = 1, or a Value like `AC 1`).
2. Run. Click the output wire. The solid line is magnitude in dB, the dashed line is phase.
3. Cutoff (-3 dB) point: attach a cursor (section 7) and slide it until the magnitude reads **-3 dB** below the passband level. Read the frequency.
4. Log/linear axes: right-click the axis numbers > tick **Logarithmic**.

## 6. Sweep plot (`.dc` or `.step`)

- `.dc Vin 0 5 0.01` sweeps the source; the x-axis becomes the source value.
- `.step param RL list 10 50 100` runs once per value. All runs plot on top of each other.
  Right-click the plot > **Select Steps** to show one run.
- To plot power in a part: **Alt + click** the part body.

## 7. Reading values with cursors

1. **Click the trace name** at the top of the plot (e.g. `V(vout)`) once: cursor 1 appears.
   Click it again for cursor 2.
2. Drag the cross-hair along the trace. A small window shows **Horz** (time or frequency) and **Vert** (value).
   With two cursors it also shows the difference.
3. Screenshot the plot with the cursor window visible as proof of the reading.

## 8. Making plots look good for a report

- White background: **Tools > Color Preferences > WaveForm tab**, set Background to white.
- Thicker traces: Tools > Settings (Control Panel) > Waveforms > tick "Plot data with thick lines".
- Rename a trace or add maths: right-click the trace name, type an expression like `V(vout)/V(vin)`.

## 9. Exporting data

- With the plot window selected: **File > Export data as text**. Pick the traces. Gives a `.txt` with columns (time, value...).
- Useful when the sheet asks for a table of values at specific times: export, then read the rows.

## 10. Mac differences

- Mac LTspice has no menus for most things: right-click the schematic or plot for the same options.
- Error Log: right-click the schematic > **View > SPICE Error Log**.
- Screenshot: **Cmd + Shift + 4**.
- Run: the running-man button, or right-click > Run.
