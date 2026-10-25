# Analysis recipes

Pick the row that matches what the question asks for. Every recipe names the nodes you must flag so the output reads cleanly.

| The question asks for | Analysis and directives | Where the answer appears |
|---|---|---|
| Node voltages / branch currents of a DC circuit (resistors, DC sources, dependent sources) | `.op` | Operating Point window |
| Thévenin resistance with dependent sources | Turn independent sources off (V source → value `0`, I source → `0`). Put a **1 V** `voltage` source `Vt` across A–B (+ at A). `.op`. Rth = 1 / (−I(Vt)) | Operating Point window |
| Thévenin voltage / Norton current | Open circuit: `.op`, read V(A) with nothing across A–B. Short: wire A–B (or a `0` V source to read its current) | Operating Point window |
| RL for maximum power | Answer is RL = Rth. To show it: `.step param RL 10 200 1` with RL value `{RL}`, `.op`, then plot `V(a)*I(RL)` against RL; the peak is at Rth | plot (x-axis = RL) |
| Equivalent capacitance (or inductance) | No DC answer exists (C is open at DC). Push **1 mA** into A for **1 µs**: `current` source `1m` into A, B grounded. `.tran 0 1u 0 1n uic` · `.meas TRAN VA FIND V(a) AT 1u` · `.meas TRAN Cab PARAM 1m*1u/VA` | Error Log `cab` (farads) |
| Peak / max of a sine response | Source value `SINE(0 <amp> <freq>)`, e.g. `SINE(0 250m 2k)`. `.tran 0 <2 periods> 0 <period/500>` · `.meas TRAN vmax MAX V(vout)` · `.meas TRAN vmin MIN V(vout)` | Error Log + time plot |
| Gain of a linear amplifier | Same as above; also `.meas TRAN gain PARAM vmax/<amp>` | Error Log |
| Capacitor voltage after a switch (RC/RL step) | Model the closed switch as a wire. Set the starting voltage: `.ic V(vc)=<V0>`. `.tran 0 <5τ or more> 0 <τ/200>` · `.meas TRAN vc_t FIND V(vc) AT <t>` | Error Log + time plot |
| Switch closing at a given time | `voltage` source `PULSE(0 <V> <t0> 1n 1n 1 2)` instead of a switch | time plot |
| Frequency response / cutoff / Bode | Source value `AC 1`. `.ac dec 100 <f_low> <f_high>` · `.meas AC fc WHEN mag(V(vout))=0.7071` (for a 1 V passband) | Bode plot + Error Log |
| Transfer curve (Vout vs Vin) | `.dc Vin <start> <stop> <step>` | plot (x-axis = Vin) |
| Ideal op amp | `e` (VCVS) gain `1e6`: out+ = op-amp output, out− = ground, ctrl+ = non-inverting input, ctrl− = inverting input | as above |
| VCCS (gm) | `g`, value = **minus** gm in siemens, e.g. `-2202u` (confirmed in real LTspice for the upright part wired like the sheet's figure; check against the hand value). Current gm·V(ctrl+, ctrl−) flows **into out+**, through the source, **out of out−** | as above |
| CCCS (β·Ib) / CCVS | `f` / `h`. They sense the current through a voltage source: add a **0 V** `voltage` source `Vsense` in series with the controlling branch, arrow-direction = the sheet's Ib arrow (current into its + pin). Value of F: `Vsense <beta>` | as above |

## Units and syntax traps

| Write | Means | Trap |
|---|---|---|
| `1k` | 1 000 | |
| `1meg` | 1 000 000 | `1M` is **milli** (0.001)! |
| `1m`, `1u`, `1n`, `1p` | milli, micro, nano, pico | |
| `1` (for a capacitor) | 1 farad | `1F` is femto |
| `2202u` | 2202 µS for a gm | |
| `{RL}` | a parameter, defined by `.param RL=58` or `.step param RL ...` | needs the braces |

## Dependent sources on the sheet → LTspice part

| Sheet says | Part | Value |
|---|---|---|
| "controlled current = gm × Vgs" | `g` (ctrl pins across Vgs) | gm in S |
| "controlled voltage = A × vd" | `e` | A |
| "controlled current = β × Ib" | `f` + 0 V `Vsense` in the Ib branch | `Vsense β` |
| "controlled voltage = r × I" | `h` + 0 V `Vsense` | `Vsense r` |

## Directives look like this on the schematic

```
.op
.tran 0 1m 0 1u
.meas TRAN vmax MAX V(vout)
.ic V(vc)=9
.ac dec 100 10 1meg
.param RL=58.46
```
