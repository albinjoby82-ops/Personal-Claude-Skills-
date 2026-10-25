---
name: ltspice-asc-builder
description: Build ready-to-open LTspice .asc schematic files for circuit homework, laid out like the sheet's figure, with every connection and label checked before sending. Use whenever Albin wants an LTspice schematic, .asc file, or asks how to do a question in LTspice.
category: ee
tags: [ltspice, schematic, asc, simulation, circuits]
---

# LTspice .asc builder

Write the schematic file so Albin only opens it and presses Run. Never make him draw it by hand.

## Workflow

1. **Read the figure.** Render the homework PDF page and look at it. List every node and which part ends touch it. Get values from the student-number mapping (the ee-homework-tutor table).
2. **Hand-calculate first** so you know what LTspice should print.
3. **Pick the analysis** from the recipes below.
4. **Write a build script** with the `ltasc.py` library (bottom of this file). Save it to `/home/claude/spice/ltasc.py` once, then write a small `qXX_build.py` per question.
5. **Run `check(expect=...)`.** It must print `OK` with no `label ... sits on wire` or `overlaps` warnings. Fix the layout until clean.
6. **Look at the preview PNG** (`s.preview(path)`, then Read it). It is a rough model: boxes are part bodies, dashed boxes are estimated labels. Check it looks like the sheet's figure.
7. **Save and send** `STUDENTNUMBER_qXX.asc` with SendUserFile (`display: attach`). Say in one short table what he should see (Error Log line or .op values).
8. **Ask for a screenshot** of it open in LTspice, then check it with the ltspice-helper skill. If it confirms a symbol marked `ok=False`, set it to `True` and propose a skill update.

## Albin's preferences

- Lay it out **like the figure on the sheet** (same left-to-right order, parallel parts stacked).
- **No title or comment with his student number** on the schematic. Only directives, plus short node notes like `B = ground` if useful.
- Labels horizontal and clear of wires. Values always with units (`1005p`, `16k`, `2202u`).
- Only build for the student number he asks for.

## Verified LTspice facts (from real screenshots, Oct 2026)

| Fact | Detail |
|---|---|
| Coordinates | y points **down**; use multiples of 16 |
| `cap` pins | (16,0) and (16,64) at R0 ✓ |
| `current` pins | (0,0) and (0,80) at R0 ✓; current flows pin0 → pin1 (arrow points down) |
| Rotation of a local offset | R90: (−y, x) · R180: (−x, −y) · R270: (y, −x) ✓ |
| `current` at R180 | arrow points **up**; pin0 is at the bottom ✓ |
| WINDOW lines | coordinates are in the symbol's **local** frame and rotate with it ✓ |
| Rotated parts (R90/R270) | plain `Left`/`Center` labels read sideways ✓. Fix: `VTop`/`VBottom` (the `NEAT` table), standard in LTspice's own files; confirm on first use |
| R180 | `Left` justification shows as right-aligned (text to the left) ✓ |
| Ground / net flags | drawn pointing **away** from the wire they sit on ✓ |
| Junctions | a filled square appears where 3+ wire ends/pins meet ✓ |

Not yet confirmed (from memory, the checker warns): `res`/`ind` pins (16,16),(16,96); `voltage` pins (0,16)=+, (0,96)=−; `e`/`g` pins out+ (0,16), out− (0,96), ctrl+ (−48,32), ctrl− (−48,80).

## Layout rules

- Place parts **by pin position** (`pin0=`), never by guessing origins.
- Every junction is wire **end points**. Split wires at every junction. The checker errors if a pin or wire end sits mid-wire.
- Horizontal parts: rows at least **96** apart. Vertical parts: columns at least **128** apart. That leaves room for labels.
- Leave a wire of 32 to 64 between a part and a rail corner so labels and junction dots don't collide.
- Ground: run a short wire **down** from the node and put `gnd()` at its end, so the symbol points down.
- Name every node you will read with a lowercase flag (`a`, `n1`, `vout`) so outputs read `V(vout)`.
- Put directives under the circuit with `directive()`.

## Analysis recipes

| Question type | Parts / directive | Read the answer |
|---|---|---|
| DC resistor networks, dependent sources, Thevenin | `.op` | .op window: `V(name)`, `I(R1)` |
| Equivalent capacitance (no DC answer exists) | 1 mA `current` source into A, B grounded; `.tran 0 1u 0 1n uic`; `.meas TRAN VA FIND V(a) AT 1u`; `.meas TRAN Cab PARAM 1m*1u/VA` | View > SPICE Error Log: `cab` |
| Sine input, peak output | voltage value `SINE(0 0.25 2k)`; `.tran 0 2m 0 1u`; `.meas TRAN vmax MAX V(vout)` | Error Log `vmax` + plot |
| RC switching from an initial voltage | source, R, C; `.ic V(vc)=9`; `.tran 0 1m 0 1u`; `.meas TRAN vc250 FIND V(vc) AT 250u` | Error Log |
| Thevenin resistance with dependent sources | sources off, 1 V test `voltage` at A–B; `.op`; Rth = 1 / I(Vtest) | .op window |
| Max power / sweeps | `.step param RL list ...` with `{RL}` as the value | plot or `.meas` |
| Ideal op amp | `e` with gain `1e6` (out+, out−, ctrl+ = non-inverting, ctrl− = inverting) | .op |
| VCCS (gm) | `g` with value = gm in siemens (`2202u`) | .op |
| CCCS / CCVS | `f` / `h` need a 0 V `voltage` in series to sense the current; value = `Vsense gain` | .op |

Signs: an `I(R)` current is positive from pin0 to pin1. A voltage source's current is measured **into its + pin**, so a source delivering power reads negative. That's normal.

## Fallback

If a symbol is unverified and wiring matters, also send a `.cir` netlist (plain SPICE) as a backup. LTspice opens it directly.

## Library: save as /home/claude/spice/ltasc.py

```python
"""ltasc - write LTspice .asc schematics from Python, with connectivity + overlap checks and a PNG preview.

Usage:
    from ltasc import Sch
    s = Sch()
    s.part('cap', 'C1', '1005p', 'R270', pin0=(96, 256))      # place by pin-0 position
    s.wire((48, 256), (96, 256))
    s.flag((48, 256), 'a'); s.gnd((560, 400))
    s.directive('.op')
    s.check(expect={'a': ['I1.1', 'C1.0'], ...})            # nets by flag name or any pin
    s.save('25382076_q1a.asc'); s.preview('preview.png')
"""
import math

# Rotation of a symbol-local offset into schematic coordinates (y points DOWN).
# R270 verified from a real LTspice screenshot; R90 is its inverse; R180 verified.
ROT = {'R0': lambda x, y: (x, y), 'R90': lambda x, y: (-y, x),
       'R180': lambda x, y: (-x, -y), 'R270': lambda x, y: (y, -x)}

# pins: order = SPICE node order. body: local bbox. win: default label windows {0: name, 3: value}.
SYM = {
    'cap':     dict(pins=[(16, 0), (16, 64)], body=((0, 22), (32, 42)),
                    win={0: (24, 8, 'Left'), 3: (24, 56, 'Left')}, ok=True),
    'res':     dict(pins=[(16, 16), (16, 96)], body=((0, 24), (32, 88)),
                    win={0: (36, 40, 'Left'), 3: (36, 76, 'Left')}, ok=False),
    'ind':     dict(pins=[(16, 16), (16, 96)], body=((0, 24), (32, 88)),
                    win={0: (36, 40, 'Left'), 3: (36, 76, 'Left')}, ok=False),
    'voltage': dict(pins=[(0, 16), (0, 96)], body=((-32, 24), (32, 88)),
                    win={0: (24, 16, 'Left'), 3: (24, 96, 'Left')}, ok=False),   # pin0 = +
    'current': dict(pins=[(0, 0), (0, 80)], body=((-32, 8), (32, 72)),
                    win={0: (24, 0, 'Left'), 3: (24, 80, 'Left')}, ok=True),     # current flows pin0 -> pin1 (arrow)
    'e':       dict(pins=[(0, 16), (0, 96), (-48, 32), (-48, 80)], body=((-32, 24), (32, 88)),
                    win={0: (24, 16, 'Left'), 3: (24, 96, 'Left')}, ok=False),   # out+, out-, ctrl+, ctrl-
    'g':       dict(pins=[(0, 16), (0, 96), (-48, 32), (-48, 80)], body=((-32, 24), (32, 88)),
                    win={0: (24, 16, 'Left'), 3: (24, 96, 'Left')}, ok=False),   # current out+ -> out- inside
}

# Label windows that read horizontally and sit clear of the part (local coords).
NEAT = {
    ('cap', 'R0'):   {0: (40, 20, 'Left'), 3: (40, 44, 'Left')},
    ('cap', 'R180'): {0: (40, 20, 'Left'), 3: (40, 44, 'Left')},
    ('cap', 'R90'):  {0: (0, 32, 'VBottom'), 3: (32, 32, 'VTop')},
    ('cap', 'R270'): {0: (32, 32, 'VTop'), 3: (0, 32, 'VBottom')},
    ('res', 'R0'):   {0: (40, 44, 'Left'), 3: (40, 68, 'Left')},
    ('res', 'R90'):  {0: (0, 56, 'VBottom'), 3: (32, 56, 'VTop')},
    ('res', 'R270'): {0: (32, 56, 'VTop'), 3: (0, 56, 'VBottom')},
}
NEAT[('current', 'R0')] = {0: (40, 28, 'Left'), 3: (40, 52, 'Left')}     # labels right of the source
NEAT[('current', 'R180')] = {0: (40, 52, 'Left'), 3: (40, 28, 'Left')}   # R180 flips: shows LEFT of the source
NEAT[('voltage', 'R0')] = {0: (40, 44, 'Left'), 3: (40, 68, 'Left')}
NEAT[('ind', 'R0')], NEAT[('ind', 'R90')], NEAT[('ind', 'R270')] = NEAT[('res', 'R0')], NEAT[('res', 'R90')], NEAT[('res', 'R270')]

TH, CW = 22, 14          # approx text height / char width at size 2


def _screen_just(j, rot):
    """Where text sits relative to its anchor on screen, or 'VERTICAL' if it will read sideways."""
    v = j.startswith('V')
    if rot in ('R0', 'R180'):
        if v:
            return 'VERTICAL'
        return j if rot == 'R0' else {'Left': 'Right', 'Right': 'Left', 'Top': 'Bottom', 'Bottom': 'Top'}.get(j, j)
    if not v:
        return 'VERTICAL'
    m = {'R90': {'VBottom': 'Bottom', 'VTop': 'Top'}, 'R270': {'VTop': 'Bottom', 'VBottom': 'Top'}}[rot]
    return m.get(j, 'Center')


def _bbox(ax, ay, text, sj):
    w, h = CW * len(text), TH
    return {'Left': (ax, ay - h / 2, ax + w, ay + h / 2), 'Right': (ax - w, ay - h / 2, ax, ay + h / 2),
            'Center': (ax - w / 2, ay - h / 2, ax + w / 2, ay + h / 2),
            'Bottom': (ax - w / 2, ay - h, ax + w / 2, ay), 'Top': (ax - w / 2, ay, ax + w / 2, ay + h)}[sj]


def _hit(a, b, pad=2):
    return a[0] < b[2] - pad and b[0] < a[2] - pad and a[1] < b[3] - pad and b[1] < a[3] - pad


def _seg_box(p, q, b, pad=2):
    x0, x1 = sorted((p[0], q[0])); y0, y1 = sorted((p[1], q[1]))
    return _hit((x0 - 1, y0 - 1, x1 + 1, y1 + 1), b, pad)


class Sch:
    def __init__(self):
        self.wires, self.flags, self.parts, self.texts = [], [], [], []

    # ---- building -------------------------------------------------------------
    def part(self, sym, name, value, rot='R0', pin0=None, origin=None, pin=0, labels='neat'):
        """Place `sym` so that pin number `pin` lands on `pin0` (or give origin directly)."""
        d = SYM[sym]
        if origin is None:
            dx, dy = ROT[rot](*d['pins'][pin])
            origin = (pin0[0] - dx, pin0[1] - dy)
        ox, oy = origin
        pins = [(ox + ROT[rot](*p)[0], oy + ROT[rot](*p)[1]) for p in d['pins']]
        win = NEAT.get((sym, rot)) if labels == 'neat' else None
        if isinstance(labels, dict):
            win = labels
        self.parts.append(dict(sym=sym, name=name, value=value, rot=rot, origin=origin, pins=pins, win=win))
        return pins

    def wire(self, *pts):
        for p, q in zip(pts, pts[1:]):
            assert p[0] == q[0] or p[1] == q[1], f'wire not straight {p}->{q}'
            self.wires.append((tuple(p), tuple(q)))

    def flag(self, p, name):
        self.flags.append((tuple(p), name))

    def gnd(self, p):
        self.flag(p, '0')

    def text(self, p, s):
        self.texts.append((tuple(p), ';' + s))

    def directive(self, s, p=None):
        if p is None:
            ys = [t[0][1] for t in self.texts if t[1].startswith('!')]
            y = (max(ys) + 32) if ys else self._extent()[3] + 64
            p = (self._extent()[0], y)
        self.texts.append((tuple(p), '!' + s))

    # ---- geometry helpers --------------------------------------------------------
    def _labels(self):
        out = []
        for P in self.parts:
            d = SYM[P['sym']]; win = dict(d['win']); win.update(P['win'] or {})
            for k, txt in ((0, P['name']), (3, P['value'])):
                lx, ly, j = win[k]
                sx, sy = ROT[P['rot']](lx, ly)
                ax, ay = P['origin'][0] + sx, P['origin'][1] + sy
                sj = _screen_just(j, P['rot'])
                out.append(dict(owner=P['name'], text=txt, sj=sj,
                                box=_bbox(ax, ay, txt, 'Center' if sj == 'VERTICAL' else sj)))
        for (p, s) in self.texts:
            out.append(dict(owner='TEXT', text=s[1:], sj='Left', box=_bbox(p[0], p[1], s[1:], 'Left')))
        return out

    def _body(self, P):
        (a, b), (c, e) = SYM[P['sym']]['body']
        pts = [ROT[P['rot']](x, y) for x, y in ((a, b), (c, e))]
        xs = sorted(P['origin'][0] + p[0] for p in pts); ys = sorted(P['origin'][1] + p[1] for p in pts)
        return (xs[0], ys[0], xs[1], ys[1])

    def _extent(self):
        pts = [p for w in self.wires for p in w] + [p for P in self.parts for p in P['pins']] + [f[0] for f in self.flags]
        if not pts:
            return (0, 0, 0, 0)
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    # ---- checks ---------------------------------------------------------------
    def nets(self):
        par = {}
        def f(p):
            par.setdefault(p, p)
            while par[p] != p:
                par[p] = par[par[p]]; p = par[p]
            return p
        def u(a, b): par[f(a)] = f(b)
        for a, b in self.wires: u(a, b)
        byname = {}
        for p, n in self.flags:
            f(p); byname.setdefault(n, []).append(p)
        for ps in byname.values():
            for q in ps[1:]: u(ps[0], q)
        for P in self.parts:
            for p in P['pins']: f(p)
        groups = {}
        for P in self.parts:
            for i, p in enumerate(P['pins']):
                groups.setdefault(f(p), []).append(f"{P['name']}.{i}")
        names = {}
        for p, n in self.flags:
            names.setdefault(f(p), n)
        return {names.get(r, '?' + ','.join(v[:1])): sorted(v) for r, v in groups.items()}

    def check(self, expect=None, quiet=False):
        errs, warns = [], []
        ends = {p for w in self.wires for p in w} | {f[0] for f in self.flags}
        allpins = [(P['name'], i, p) for P in self.parts for i, p in enumerate(P['pins'])]
        pinpts = [p for _, _, p in allpins]
        for n, i, p in allpins:
            if p not in ends and pinpts.count(p) < 2:
                errs.append(f'{n} pin {i} at {p} touches nothing (hollow square in LTspice)')
        for a, b in self.wires:                       # pins / wire ends sitting mid-wire
            for q in list(ends) + pinpts:
                if q in (a, b):
                    continue
                if (a[0] == b[0] == q[0] and min(a[1], b[1]) < q[1] < max(a[1], b[1])) or \
                   (a[1] == b[1] == q[1] and min(a[0], b[0]) < q[0] < max(a[0], b[0])):
                    errs.append(f'point {q} lies in the middle of wire {a}->{b}: split the wire there')
        labs = self._labels()
        for L in labs:
            if L['sj'] == 'VERTICAL':
                errs.append(f"label '{L['text']}' of {L['owner']} will read sideways: use V-justify on rotated parts")
        for i, L in enumerate(labs):
            for a, b in self.wires:
                if _seg_box(a, b, L['box']):
                    warns.append(f"label '{L['text']}' ({L['owner']}) sits on wire {a}->{b}")
            for P in self.parts:
                if _hit(L['box'], self._body(P)):
                    warns.append(f"label '{L['text']}' ({L['owner']}) overlaps part {P['name']}")
            for M in labs[i + 1:]:
                if _hit(L['box'], M['box']):
                    warns.append(f"label '{L['text']}' overlaps '{M['text']}'")
        for P in self.parts:
            if not SYM[P['sym']]['ok']:
                warns.append(f"{P['name']}: '{P['sym']}' pin geometry not yet confirmed from a screenshot")
        nets = self.nets()
        if expect:
            got = {tuple(v) for v in nets.values()}
            for k, v in expect.items():
                if tuple(sorted(v)) not in got:
                    errs.append(f'net {k} expected {sorted(v)} but nets are {nets}')
        if not quiet:
            for k, v in nets.items(): print(f'  net {k:>6}: {v}')
            for w in sorted(set(warns)): print('  WARN', w)
            for e in errs: print('  ERROR', e)
            print('  OK' if not errs else f'  {len(errs)} error(s)')
        return errs, warns

    # ---- output ---------------------------------------------------------------
    def save(self, path):
        x0, y0, x1, y1 = self._extent()
        L = ['Version 4', f'SHEET 1 {max(880, x1 + 200)} {max(680, y1 + 300)}']
        L += [f'WIRE {a[0]} {a[1]} {b[0]} {b[1]}' for a, b in self.wires]
        L += [f'FLAG {p[0]} {p[1]} {n}' for p, n in self.flags]
        for P in self.parts:
            L.append(f"SYMBOL {P['sym']} {P['origin'][0]} {P['origin'][1]} {P['rot']}")
            for k, (lx, ly, j) in (P['win'] or {}).items():
                L.append(f'WINDOW {k} {lx} {ly} {j} 2')
            L += [f"SYMATTR InstName {P['name']}", f"SYMATTR Value {P['value']}"]
        L += [f'TEXT {p[0]} {p[1]} Left 2 {s}' for p, s in self.texts]
        open(path, 'w', newline='').write('\r\n'.join(L) + '\r\n')

    def preview(self, png, scale=1.6):
        import cairosvg
        x0, y0, x1, y1 = self._extent()
        labs = self._labels()
        for L in labs:
            x0, y0 = min(x0, L['box'][0]), min(y0, L['box'][1]); x1, y1 = max(x1, L['box'][2]), max(y1, L['box'][3])
        x0, y0, x1, y1 = x0 - 40, y0 - 40, x1 + 40, y1 + 40
        e = [f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="#c0c0c0"/>']
        for a, b in self.wires:
            e.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="#1f3fff" stroke-width="1.5"/>')
        cnt = {}
        for a, b in self.wires:
            for p in (a, b): cnt[p] = cnt.get(p, 0) + 1
        for P in self.parts:
            for p in P['pins']: cnt[p] = cnt.get(p, 0) + 1
            bx = self._body(P)
            e.append(f'<rect x="{bx[0]}" y="{bx[1]}" width="{bx[2] - bx[0]}" height="{bx[3] - bx[1]}" fill="#e8e8e8" stroke="#000080"/>')
            e.append(f'<text x="{(bx[0] + bx[2]) / 2}" y="{(bx[1] + bx[3]) / 2 + 4}" font-size="10" text-anchor="middle" fill="#000080">{P["sym"]}</text>')
            for p in P['pins']:
                e.append(f'<circle cx="{p[0]}" cy="{p[1]}" r="2.5" fill="none" stroke="#000"/>')
        for p, c in cnt.items():
            if c >= 3:
                e.append(f'<rect x="{p[0] - 3}" y="{p[1] - 3}" width="6" height="6" fill="#1f3fff"/>')
        for p, n in self.flags:
            col = '#006000' if n == '0' else '#900'
            e.append(f'<circle cx="{p[0]}" cy="{p[1]}" r="4" fill="{col}"/><text x="{p[0] + 6}" y="{p[1] - 6}" font-size="13" fill="{col}">{"GND" if n == "0" else n}</text>')
        for L in labs:
            b = L['box']
            col = '#000' if L['owner'] != 'TEXT' else '#00a'
            e.append(f'<rect x="{b[0]}" y="{b[1]}" width="{b[2] - b[0]}" height="{b[3] - b[1]}" fill="none" stroke="#f80" stroke-dasharray="3 2"/>')
            e.append(f'<text x="{b[0] + 1}" y="{b[3] - 5}" font-size="17" font-weight="bold" fill="{col}">{L["text"].replace("&", "&amp;").replace("<", "&lt;")}</text>')
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {x1 - x0} {y1 - y0}" width="{(x1 - x0) * scale}" height="{(y1 - y0) * scale}">{"".join(e)}</svg>'
        cairosvg.svg2png(bytestring=svg.encode(), write_to=png)
```

## Example: Q1(a) of EEEN20020 HW2

```python
import sys; sys.path.insert(0, '/home/claude/spice')
from ltasc import Sch
s = Sch()
s.part('current', 'I1', '1m', 'R180', pin0=(48, 336)); s.gnd((48, 336)); s.flag((48, 256), 'a')
s.part('cap', 'C1', '1005p', 'R270', pin0=(96, 256))
s.part('cap', 'C2', '1008p', 'R270', pin0=(240, 160)); s.part('cap', 'C3', '1003p', 'R270', pin0=(240, 352))
for n, v, y in (('C4', '1002p', 160), ('C5', '1007p', 256), ('C6', '1006p', 352)):
    s.part('cap', n, v, 'R270', pin0=(432, y))
s.wire((48, 256), (96, 256)); s.wire((160, 256), (192, 256))
s.wire((192, 160), (192, 256), (192, 352))
s.wire((192, 160), (240, 160)); s.wire((304, 160), (368, 160))
s.wire((192, 352), (240, 352)); s.wire((304, 352), (368, 352))
s.wire((368, 160), (368, 256), (368, 352))
for y in (160, 256, 352):
    s.wire((368, y), (432, y)); s.wire((496, y), (560, y))
s.wire((560, 160), (560, 256), (560, 352), (560, 400)); s.gnd((560, 400))
s.flag((192, 160), 'n1'); s.flag((368, 160), 'n2'); s.text((584, 248), 'B = ground')
s.directive('.tran 0 1u 0 1n uic', (48, 480))
s.directive('.meas TRAN VA FIND V(a) AT 1u')
s.directive('.meas TRAN Cab PARAM 1m*1u/VA')
s.check(expect={'a': ['I1.1', 'C1.0'], 'n1': ['C1.1', 'C2.0', 'C3.0'],
                'n2': ['C2.1', 'C3.1', 'C4.0', 'C5.0', 'C6.0'], 'gnd': ['I1.0', 'C4.1', 'C5.1', 'C6.1']})
s.save('/home/claude/spice/25382076_q1a.asc'); s.preview('/tmp/q1a.png')
```

Expected in the Error Log: `va: v(a)=1.824`, `cab: 1m*1u/va=5.483e-10` (548.3 pF).
