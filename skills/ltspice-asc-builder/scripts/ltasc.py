#!/usr/bin/env python3
"""ltasc: build LTspice .asc schematics from Python, check them, preview them, and export a netlist.

Build (in your own script):
    import sys; sys.path.insert(0, '<skill>/scripts'); from ltasc import Sch
    s = Sch()
    p, n = s.vsrc('Vin', 'SINE(0 250m 2k)', top=(64, 128))   # + at top; returns (+ pin, - pin)
    a, b = s.h('res', 'Rg', '1008', left=(64, 128))           # horizontal part, pin0 on the left
    t, u = s.v('res', 'Ro', '107k', top=(400, 128))           # vertical part, pin0 on top
    s.wire(p, a); s.gnd_drop(n)                               # wires must be straight
    s.flag(b, 'v2')                                           # name nodes you will read
    s.directive('.tran 0 1m 0 1u')
    s.check(expect={'v2': ['Rg.1', ...]})                     # prints nets, warnings, errors
    s.save('STUDENTNUMBER_Q1b.asc'); s.preview('preview.png'); print(s.netlist())

Check an existing file (e.g. one the user edited):
    python3 ltasc.py check FILE.asc [--png preview.png]
Self-test:
    python3 ltasc.py selftest
"""
import re
import sys

# ---------------------------------------------------------------------------------------------
# Geometry. Coordinates: y points DOWN, grid of 16.
# Rotation of a symbol-local offset into the schematic (verified in LTspice for R0/R180/R270).
ROT = {'R0': lambda x, y: (x, y), 'R90': lambda x, y: (-y, x),
       'R180': lambda x, y: (-x, -y), 'R270': lambda x, y: (y, -x)}

# pins are in SPICE node order. ok=True means confirmed against real LTspice symbols.
SYM = {
    'res':     dict(pins=[(16, 16), (16, 96)], body=((0, 24), (32, 88)), ok=True),
    'ind':     dict(pins=[(16, 16), (16, 96)], body=((0, 24), (32, 88)), ok=True),
    'cap':     dict(pins=[(16, 0), (16, 64)], body=((0, 22), (32, 42)), ok=True),
    'voltage': dict(pins=[(0, 16), (0, 96)], body=((-32, 24), (32, 88)), ok=True),   # pin0 = +
    'current': dict(pins=[(0, 0), (0, 80)], body=((-32, 8), (32, 72)), ok=True),     # arrow pin0 -> pin1
    # dependent sources: node order (out+, out-, ctrl+, ctrl-). Pin positions NOT yet confirmed.
    'e':       dict(pins=[(0, 16), (0, 96), (-48, 32), (-48, 80)], body=((-32, 24), (32, 88)), ok=False),
    'g':       dict(pins=[(0, 16), (0, 96), (-48, 32), (-48, 80)], body=((-32, 24), (32, 88)), ok=False),
    'f':       dict(pins=[(0, 0), (0, 80)], body=((-32, 8), (32, 72)), ok=False),
    'h':       dict(pins=[(0, 16), (0, 96)], body=((-32, 24), (32, 88)), ok=False),
}
DEFAULT_WIN = {  # LTspice's own default label spots (local coords) when no WINDOW line is written
    'res': {0: (36, 40, 'Left'), 3: (36, 76, 'Left')}, 'ind': {0: (36, 40, 'Left'), 3: (36, 76, 'Left')},
    'cap': {0: (24, 8, 'Left'), 3: (24, 56, 'Left')}, 'voltage': {0: (24, 16, 'Left'), 3: (24, 96, 'Left')},
    'current': {0: (24, 0, 'Left'), 3: (24, 80, 'Left')}, 'e': {0: (24, 16, 'Left'), 3: (24, 96, 'Left')},
    'g': {0: (24, 16, 'Left'), 3: (24, 96, 'Left')}, 'f': {0: (24, 0, 'Left'), 3: (24, 80, 'Left')},
    'h': {0: (24, 16, 'Left'), 3: (24, 96, 'Left')},
}
# Label spots that read horizontally and sit clear of the part. Rotated parts need V-justify,
# otherwise LTspice draws the text sideways (verified).
_R2 = {'R0': {0: (40, 44, 'Left'), 3: (40, 68, 'Left')},
       'R270': {0: (32, 56, 'VTop'), 3: (0, 56, 'VBottom')}, 'R90': {0: (0, 56, 'VBottom'), 3: (32, 56, 'VTop')}}
NEAT = {('res', k): v for k, v in _R2.items()}
NEAT.update({('ind', k): v for k, v in _R2.items()})
NEAT.update({('cap', 'R0'): {0: (40, 20, 'Left'), 3: (40, 44, 'Left')},
             ('cap', 'R270'): {0: (32, 32, 'VTop'), 3: (0, 32, 'VBottom')},
             ('cap', 'R90'): {0: (0, 32, 'VBottom'), 3: (32, 32, 'VTop')}})
for _s, _mid in (('voltage', 56), ('h', 56), ('e', 56), ('g', 56), ('current', 40), ('f', 40)):
    NEAT[(_s, 'R0')] = {0: (40, _mid - 12, 'Left'), 3: (40, _mid + 12, 'Left')}      # right of the part
    NEAT[(_s, 'R180')] = {0: (40, _mid + 12, 'Left'), 3: (40, _mid - 12, 'Left')}    # shows LEFT of it

TH, CW = 22, 14          # rough text height / character width at LTspice size 2


def _screen_just(j, rot):
    v = j.startswith('V')
    if rot in ('R0', 'R180'):
        if v:
            return 'VERTICAL'
        return j if rot == 'R0' else {'Left': 'Right', 'Right': 'Left', 'Top': 'Bottom', 'Bottom': 'Top'}.get(j, j)
    if not v:
        return 'VERTICAL'
    return {'R90': {'VBottom': 'Bottom', 'VTop': 'Top'}, 'R270': {'VTop': 'Bottom', 'VBottom': 'Top'}}[rot].get(j, 'Center')


def _bbox(ax, ay, text, sj):
    w, h = CW * len(text), TH
    return {'Left': (ax, ay - h / 2, ax + w, ay + h / 2), 'Right': (ax - w, ay - h / 2, ax, ay + h / 2),
            'Center': (ax - w / 2, ay - h / 2, ax + w / 2, ay + h / 2),
            'Bottom': (ax - w / 2, ay - h, ax + w / 2, ay), 'Top': (ax - w / 2, ay, ax + w / 2, ay + h)}[sj]


def _hit(a, b, pad=2):
    return a[0] < b[2] - pad and b[0] < a[2] - pad and a[1] < b[3] - pad and b[1] < a[3] - pad


def _seg_box(p, q, b):
    x0, x1 = sorted((p[0], q[0])); y0, y1 = sorted((p[1], q[1]))
    return _hit((x0 - 1, y0 - 1, x1 + 1, y1 + 1), b)


def _value_traps(name, value):
    v = str(value).strip()
    out = []
    if ' ' in v and not v.upper().startswith(('SINE', 'PULSE', 'PWL', 'AC', 'EXP', 'SFFM')) and '{' not in v:
        out.append(f"{name}: value '{v}' has a space (breaks unless it is a source function or 'Vsense gain')")
    if re.fullmatch(r'[\d.]+M', v):
        out.append(f"{name}: '{v}' means MILLI in SPICE. Use '{v[:-1]}meg' for mega")
    if re.fullmatch(r'[\d.]+F', v, re.I) and name.upper().startswith('C'):
        out.append(f"{name}: '{v}' means FEMTO. Write farads as a plain number")
    if v.upper() in ('R', 'C', 'L', 'V', 'I', 'E', 'G', 'F', 'H', ''):
        out.append(f"{name}: value never set")
    return out


class Sch:
    def __init__(self):
        self.wires, self.flags, self.parts, self.texts = [], [], [], []

    # ---- placing parts ------------------------------------------------------------------------
    def part(self, sym, name, value, rot='R0', at=None, pin=0, origin=None, labels='neat'):
        """Low level: place `sym` so pin number `pin` lands on point `at` (or give the origin)."""
        d = SYM[sym]
        if origin is None:
            dx, dy = ROT[rot](*d['pins'][pin])
            origin = (at[0] - dx, at[1] - dy)
        pins = [(origin[0] + ROT[rot](*p)[0], origin[1] + ROT[rot](*p)[1]) for p in d['pins']]
        win = labels if isinstance(labels, dict) else (NEAT.get((sym, rot)) if labels == 'neat' else None)
        self.parts.append(dict(sym=sym, name=name, value=str(value), rot=rot, origin=origin, pins=pins, win=win))
        return pins

    def h(self, sym, name, value, left):
        """Horizontal res/cap/ind. Returns (left pin, right pin). Length: res/ind 80, cap 64."""
        return tuple(self.part(sym, name, value, 'R270', at=left, pin=0))

    def v(self, sym, name, value, top):
        """Vertical res/cap/ind. Returns (top pin, bottom pin)."""
        return tuple(self.part(sym, name, value, 'R0', at=top, pin=0))

    def vsrc(self, name, value, top, plus='top'):
        """Voltage source, 80 tall. Returns (+ pin, - pin)."""
        if plus == 'top':
            return tuple(self.part('voltage', name, value, 'R0', at=top, pin=0))
        pins = self.part('voltage', name, value, 'R180', at=top, pin=1)
        return pins[0], pins[1]

    def isrc(self, name, value, top, arrow='up'):
        """Current source, 80 tall. arrow='up': current leaves the TOP pin. Returns (top pin, bottom pin)."""
        if arrow == 'down':
            a, b = self.part('current', name, value, 'R0', at=top, pin=0)
            return a, b
        p0, p1 = self.part('current', name, value, 'R180', at=top, pin=1)
        return p1, p0

    def dep(self, kind, name, value, out_plus):
        """e (VCVS) or g (VCCS), upright. Returns (out+, out-, ctrl+, ctrl-).
        g: current value*V(ctrl+,ctrl-) flows INTO out+ and through the source to out-.
        UNCONFIRMED pin positions: also flag every pin with its net name."""
        return tuple(self.part(kind, name, value, 'R0', at=out_plus, pin=0))

    # ---- wiring -------------------------------------------------------------------------------
    def wire(self, *pts):
        for p, q in zip(pts, pts[1:]):
            assert p[0] == q[0] or p[1] == q[1], f'wire must be straight: {p}->{q}'
            if p != q:
                self.wires.append((tuple(p), tuple(q)))

    def flag(self, p, name):
        self.flags.append((tuple(p), name))

    def gnd(self, p):
        self.flag(p, '0')

    def gnd_drop(self, p, drop=32):
        """Short wire down from p, ground symbol at the end (so it points down)."""
        q = (p[0], p[1] + drop)
        self.wire(p, q); self.gnd(q)
        return q

    def text(self, p, s):
        self.texts.append((tuple(p), ';' + s))

    def directive(self, s, p=None):
        if p is None:
            ds = [t[0] for t in self.texts if t[1].startswith('!')]
            if ds:                                   # line up under the previous directive
                p = (ds[0][0], max(q[1] for q in ds) + 32)
            else:
                p = (self._extent()[0], self._extent()[3] + 80)
        self.texts.append((tuple(p), '!' + s))

    # ---- geometry ---------------------------------------------------------------------------------
    def _labels(self):
        out = []
        for P in self.parts:
            win = dict(DEFAULT_WIN.get(P['sym'], {0: (24, 0, 'Left'), 3: (24, 24, 'Left')}))
            win.update(P['win'] or {})
            for k, txt in ((0, P['name']), (3, P['value'])):
                lx, ly, j = win[k]
                sx, sy = ROT[P['rot']](lx, ly)
                sj = _screen_just(j, P['rot'])
                out.append(dict(owner=P['name'], text=txt, sj=sj,
                                box=_bbox(P['origin'][0] + sx, P['origin'][1] + sy, txt, 'Center' if sj == 'VERTICAL' else sj)))
        for p, s in self.texts:
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
        return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))

    # ---- nets -------------------------------------------------------------------------------------
    def _union(self):
        par = {}

        def f(p):
            par.setdefault(p, p)
            while par[p] != p:
                par[p] = par[par[p]]; p = par[p]
            return p
        for a, b in self.wires:
            par[f(a)] = f(b)
        byname = {}
        for p, n in self.flags:
            f(p); byname.setdefault(n, []).append(p)
        for ps in byname.values():
            for q in ps[1:]:
                par[f(ps[0])] = f(q)
        for P in self.parts:
            for p in P['pins']:
                f(p)
        return f

    def nets(self):
        """{net name: sorted list of 'Part.pin'}. Unnamed nets are called ?N1, ?N2..."""
        f = self._union()
        groups = {}
        for P in self.parts:
            for i, p in enumerate(P['pins']):
                groups.setdefault(f(p), []).append(f"{P['name']}.{i}")
        names = {}
        for p, n in self.flags:
            names.setdefault(f(p), n)
        out, k = {}, 1
        for r, v in groups.items():
            nm = names.get(r)
            if nm is None:
                nm = f'?N{k}'; k += 1
            out[nm] = sorted(v)
        return out

    def netlist(self, title='* generated by ltasc'):
        f = self._union()
        names = {}
        for p, n in self.flags:
            names.setdefault(f(p), n)
        auto = {}

        def node(p):
            r = f(p)
            if r in names:
                return names[r]
            auto.setdefault(r, f'N{len(auto) + 1:03d}')
            return auto[r]
        L = [title]
        for P in self.parts:
            L.append(f"{P['name']} {' '.join(node(p) for p in P['pins'])} {P['value']}")
        L += [s[1:] for _, s in self.texts if s.startswith('!')]
        L.append('.end')
        return '\n'.join(L)

    # ---- checking ---------------------------------------------------------------------------------
    def check(self, expect=None, quiet=False):
        """Errors = it will not work or will look broken. Warnings = worth a look."""
        errs, warns = [], []
        ends = {p for w in self.wires for p in w} | {fl[0] for fl in self.flags}
        allpins = [(P['name'], i, p) for P in self.parts for i, p in enumerate(P['pins'])]
        pinpts = [p for _, _, p in allpins]
        for n, i, p in allpins:
            if p not in ends and pinpts.count(p) < 2:
                errs.append(f'{n} pin {i} at {p} touches nothing (shows as a hollow square)')
        for a, b in self.wires:
            for q in set(ends) | set(pinpts):
                if q in (a, b):
                    continue
                if (a[0] == b[0] == q[0] and min(a[1], b[1]) < q[1] < max(a[1], b[1])) or \
                   (a[1] == b[1] == q[1] and min(a[0], b[0]) < q[0] < max(a[0], b[0])):
                    errs.append(f'point {q} sits in the middle of wire {a}->{b}: split the wire there')
        for P in self.parts:
            bx = self._body(P)
            for a, b in self.wires:
                if a in P['pins'] or b in P['pins']:
                    continue
                if _seg_box(a, b, (bx[0] + 3, bx[1] + 3, bx[2] - 3, bx[3] - 3)):
                    errs.append(f"wire {a}->{b} runs through {P['name']}")
        labs = self._labels()
        for L in labs:
            if L['sj'] == 'VERTICAL':
                errs.append(f"label '{L['text']}' of {L['owner']} will read sideways")
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
            if P['sym'] not in SYM:
                warns.append(f"{P['name']}: unknown symbol '{P['sym']}', pins not checked")
            elif not SYM[P['sym']]['ok']:
                warns.append(f"{P['name']}: '{P['sym']}' pin positions unconfirmed: flag every pin and send a .cir backup")
            for t in _value_traps(P['name'], P['value']):
                warns.append(t)
        if not any(n == '0' for _, n in self.flags):
            errs.append('no ground: add gnd()')
        if not any(s.startswith('!.') for _, s in self.texts):
            errs.append('no analysis directive (.op / .tran / .ac / .dc)')
        nets = self.nets()
        if expect:
            got = {tuple(v) for v in nets.values()}
            for k, v in expect.items():
                if tuple(sorted(v)) not in got:
                    errs.append(f'net {k}: expected {sorted(v)}')
        if not quiet:
            for k, v in sorted(nets.items()):
                print(f'  net {k:>6}: {v}')
            for w in sorted(set(warns)):
                print('  WARN ', w)
            for e in errs:
                print('  ERROR', e)
            print('  RESULT: OK' if not errs else f'  RESULT: {len(errs)} error(s)')
        return errs, sorted(set(warns))

    # ---- files ------------------------------------------------------------------------------------
    def save(self, path):
        x0, y0, x1, y1 = self._extent()
        L = ['Version 4', f'SHEET 1 {max(880, x1 + 240)} {max(680, y1 + 320)}']
        L += [f'WIRE {a[0]} {a[1]} {b[0]} {b[1]}' for a, b in self.wires]
        L += [f'FLAG {p[0]} {p[1]} {n}' for p, n in self.flags]
        for P in self.parts:
            L.append(f"SYMBOL {P['sym']} {P['origin'][0]} {P['origin'][1]} {P['rot']}")
            for k, (lx, ly, j) in (P['win'] or {}).items():
                L.append(f'WINDOW {k} {lx} {ly} {j} 2')
            L += [f"SYMATTR InstName {P['name']}", f"SYMATTR Value {P['value']}"]
        L += [f'TEXT {p[0]} {p[1]} Left 2 {s}' for p, s in self.texts]
        with open(path, 'w', newline='') as fh:
            fh.write('\r\n'.join(L) + '\r\n')

    @classmethod
    def load(cls, path):
        s, cur = cls(), None
        for raw in open(path, encoding='utf-8', errors='replace'):
            t = raw.rstrip('\r\n').split(' ')
            if t[0] == 'WIRE':
                s.wires.append(((int(t[1]), int(t[2])), (int(t[3]), int(t[4]))))
            elif t[0] == 'FLAG':
                s.flags.append(((int(t[1]), int(t[2])), t[3]))
            elif t[0] == 'SYMBOL':
                sym, rot = t[1].split('\\')[-1], t[4]
                o = (int(t[2]), int(t[3]))
                d = SYM.get(sym)
                pins = [(o[0] + ROT[rot](*p)[0], o[1] + ROT[rot](*p)[1]) for p in d['pins']] if d else []
                cur = dict(sym=sym if d else sym, name='?', value='', rot=rot, origin=o, pins=pins, win={})
                s.parts.append(cur)
                if not d:
                    SYM[sym] = dict(pins=[], body=((0, 0), (0, 0)), ok=False)
            elif t[0] == 'WINDOW' and cur is not None:
                cur['win'][int(t[1])] = (int(t[2]), int(t[3]), t[4])
            elif t[0] == 'SYMATTR' and cur is not None:
                if t[1] == 'InstName':
                    cur['name'] = t[2]
                elif t[1] == 'Value':
                    cur['value'] = ' '.join(t[2:])
            elif t[0] == 'TEXT':
                body = ' '.join(t[5:])
                s.texts.append(((int(t[1]), int(t[2])), body if body[:1] in '!;' else ';' + body))
        return s

    def preview(self, png, scale=1.6):
        """Rough picture for checking layout. Boxes = part bodies, dashed = estimated labels."""
        import cairosvg
        x0, y0, x1, y1 = self._extent()
        labs = self._labels()
        for L in labs:
            x0, y0 = min(x0, L['box'][0]), min(y0, L['box'][1]); x1, y1 = max(x1, L['box'][2]), max(y1, L['box'][3])
        x0, y0, x1, y1 = x0 - 40, y0 - 40, x1 + 40, y1 + 40
        esc = lambda z: str(z).replace('&', '&amp;').replace('<', '&lt;')
        e = [f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="#c0c0c0"/>']
        for a, b in self.wires:
            e.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="#1f3fff" stroke-width="1.5"/>')
        cnt = {}
        for a, b in self.wires:
            for p in (a, b):
                cnt[p] = cnt.get(p, 0) + 1
        for P in self.parts:
            for p in P['pins']:
                cnt[p] = cnt.get(p, 0) + 1
            bx = self._body(P)
            e.append(f'<rect x="{bx[0]}" y="{bx[1]}" width="{bx[2] - bx[0]}" height="{bx[3] - bx[1]}" fill="#e8e8e8" stroke="#000080"/>')
            e.append(f'<text x="{(bx[0] + bx[2]) / 2}" y="{(bx[1] + bx[3]) / 2 + 4}" font-size="10" text-anchor="middle" fill="#000080">{P["sym"]}</text>')
            for i, p in enumerate(P['pins']):
                e.append(f'<circle cx="{p[0]}" cy="{p[1]}" r="2.5" fill="none" stroke="#000"/>')
        for p, c in cnt.items():
            if c >= 3:
                e.append(f'<rect x="{p[0] - 3}" y="{p[1] - 3}" width="6" height="6" fill="#1f3fff"/>')
        for p, n in self.flags:
            col = '#006000' if n == '0' else '#900'
            e.append(f'<circle cx="{p[0]}" cy="{p[1]}" r="4" fill="{col}"/><text x="{p[0] + 6}" y="{p[1] - 6}" font-size="13" fill="{col}">{"GND" if n == "0" else esc(n)}</text>')
        for L in labs:
            b = L['box']
            col = '#000' if L['owner'] != 'TEXT' else '#00a'
            e.append(f'<rect x="{b[0]}" y="{b[1]}" width="{b[2] - b[0]}" height="{b[3] - b[1]}" fill="none" stroke="#f80" stroke-dasharray="3 2"/>')
            e.append(f'<text x="{b[0] + 1}" y="{b[3] - 5}" font-size="17" font-weight="bold" fill="{col}">{esc(L["text"])}</text>')
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {x1 - x0} {y1 - y0}" '
               f'width="{(x1 - x0) * scale}" height="{(y1 - y0) * scale}">{"".join(e)}</svg>')
        cairosvg.svg2png(bytestring=svg.encode(), write_to=png)


def symbol_values(student_number, symbols):
    """Map the LAST len(symbols) digits of the student number onto the symbols, in order.
    Use only when the sheet's box says the symbols take the last digits (most UCD sheets do)."""
    d = re.sub(r'\D', '', str(student_number))[-len(symbols):]
    return dict(zip(symbols, (int(c) for c in d)))


def _selftest():
    s = Sch()
    top, bot = s.isrc('I1', '1m', top=(48, 256), arrow='up')
    s.gnd(bot); s.flag(top, 'a')
    l1, r1 = s.h('cap', 'C1', '1005p', left=(96, 256))
    l2, r2 = s.h('res', 'R1', '1k', left=(224, 256))
    t3, b3 = s.v('res', 'R2', '2k', top=(352, 256))
    s.wire(top, l1); s.wire(r1, (192, 256), l2); s.wire(r2, (336, 256), t3)
    s.gnd_drop(b3)
    s.directive('.op', (48, 480))
    errs, _ = s.check(expect={'a': ['C1.0', 'I1.1']}, quiet=True)
    assert not errs, errs
    print('selftest OK')


if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == 'check':
        sch = Sch.load(sys.argv[2])
        sch.check()
        print(sch.netlist('* netlist read back from ' + sys.argv[2]))
        if '--png' in sys.argv:
            sch.preview(sys.argv[sys.argv.index('--png') + 1])
    elif len(sys.argv) >= 2 and sys.argv[1] == 'selftest':
        _selftest()
    else:
        print(__doc__)
