"""logisim_kit.py - build, reroute and check Logisim-evolution .circ files without running Logisim.

Usage as a library:
    import sys; sys.path.insert(0, "/home/claude/scripts"); from logisim_kit import *
CLI:
    python3 -I logisim_kit.py check   file.circ              # wiring problems + net list
    python3 -I logisim_kit.py compare a.circ b.circ          # same connections?
    python3 -I logisim_kit.py render  file.circ out.png      # rough preview picture
    python3 -I logisim_kit.py sim     file.circ "X=1,1,0,0"  # clocked sim, one pulse per value
"""
import re, sys, itertools
import xml.etree.ElementTree as ET

LIB = {"Pin": "0", "Clock": "0", "Constant": "0", "Probe": "0", "Tunnel": "0",
       "NOT Gate": "1", "AND Gate": "1", "OR Gate": "1", "NAND Gate": "1", "NOR Gate": "1",
       "XOR Gate": "1", "XNOR Gate": "1",
       "J-K Flip-Flop": "5", "D Flip-Flop": "5", "T Flip-Flop": "5", "LED": "6", "Text": "7"}

# Geometry that was checked against a real Logisim-evolution save.  Anything else is
# reported as UNVERIFIED so the reply can say so.
VERIFIED = {"AND Gate", "OR Gate", "NOT Gate", "J-K Flip-Flop", "Pin", "Clock", "Constant", "LED", "Probe", "Tunnel"}

def _xy(s):
    return tuple(map(int, re.findall(r"-?\d+", s)))

def _gate_dy(n, size=50):
    """Input y-offsets for a multi-input gate (Logisim-evolution AbstractGate rule)."""
    if n <= 3 and size >= 40:
        start, dist, low = -10, 20, 20
    else:
        start, dist, low = -5, 10, 10
    out = []
    for i in range(n):
        if n % 2:
            out.append(start * (n - 1) + dist * i)
        else:
            out.append(start * n + dist * i + (low if i >= n // 2 else 0))
    return out

def ports(name, loc, attrs):
    """Port positions for an east-facing component (default facing for gates / FFs)."""
    x, y = loc
    f = attrs.get("facing", "east")
    if name in ("AND Gate", "OR Gate", "NAND Gate", "NOR Gate", "XOR Gate", "XNOR Gate"):
        if f != "east":
            raise ValueError(f"{name} at {loc}: only east-facing gates supported")
        size = int(attrs.get("size", 50)); n = int(attrs.get("inputs", 2))
        if name in ("NAND Gate", "NOR Gate", "XOR Gate", "XNOR Gate"):
            dx = size + 10          # UNVERIFIED guess: bubble / extra curve
        else:
            dx = size
        p = {f"in{i}": (x - dx, y + d) for i, d in enumerate(_gate_dy(n, size))}
        p["out"] = (x, y)
        return p
    if name == "NOT Gate":
        if f != "east":
            raise ValueError("NOT gate must face east")
        w = 30 if attrs.get("size", "30") == "30" else 20
        return {"in": (x - w, y), "out": (x, y)}
    if name == "J-K Flip-Flop":
        return {"J": (x - 40, y), "CLK": (x - 40, y + 10), "K": (x - 40, y + 20), "Q": (x, y), "Qn": (x, y + 20)}
    if name in ("D Flip-Flop", "T Flip-Flop"):   # UNVERIFIED (classic look)
        return {"D" if name[0] == "D" else "T": (x - 40, y), "CLK": (x - 40, y + 20), "Q": (x, y), "Qn": (x, y + 20)}
    if name in ("Pin", "Clock", "Constant", "LED", "Probe", "Tunnel"):
        return {"p": (x, y)}
    return {}

class Circuit:
    def __init__(self, path=None, name="main"):
        self.comps, self.wires, self.texts = [], [], []
        self.root = None
        if path:
            self.root = ET.parse(path).getroot()
            circ = [c for c in self.root.findall("circuit") if c.get("name") == name][0]
            for c in circ:
                if c.tag == "comp":
                    attrs = {a.get("name"): a.get("val") for a in c.findall("a")}
                    rec = {"name": c.get("name"), "lib": c.get("lib"), "loc": _xy(c.get("loc")), "attrs": attrs}
                    (self.texts if rec["name"] == "Text" else self.comps).append(rec)
                elif c.tag == "wire":
                    self.wires.append((_xy(c.get("from")), _xy(c.get("to"))))
        for c in self.comps:
            c.setdefault("key", c["attrs"].get("label") or f"{c['name']}@{c['loc'][0]},{c['loc'][1]}")

    def port_map(self):
        pm = {}
        for c in self.comps:
            for pn, p in ports(c["name"], c["loc"], c["attrs"]).items():
                pm[(c["key"], pn)] = p
        return pm

def on_interior(p, w):
    (x1, y1), (x2, y2) = w
    if x1 == x2 == p[0]:
        return min(y1, y2) < p[1] < max(y1, y2)
    if y1 == y2 == p[1]:
        return min(x1, x2) < p[0] < max(x1, x2)
    return False

def nets(circ):
    """Logisim joins wires only where endpoints meet. Returns list of sets of (compkey, port)."""
    parent = {}
    def f(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for a, b in circ.wires:
        parent[f(a)] = f(b)
    groups = {}
    for k, p in circ.port_map().items():
        groups.setdefault(f(p), set()).add(k)
    return [frozenset(s) for s in groups.values()]

def canon(netlist, keymap=None, swap_inputs=True):
    """Normalise for comparison: rename keys, treat a gate's inputs as interchangeable."""
    keymap = keymap or {}
    out = set()
    for s in netlist:
        if len(s) < 2:
            continue
        out.add(frozenset((keymap.get(k, k), "in" if swap_inputs and pn.startswith("in") else pn) for k, pn in s))
    return out

def same_connections(a, b, limit=200000):
    """True if b wires up the same circuit as a. Labelled parts match by label; unlabelled
    parts (gates) are matched by trying every pairing of same-type parts."""
    def groups(c):
        g = {}
        for x in c.comps:
            if "label" not in x["attrs"]:
                g.setdefault((x["name"], x["attrs"].get("inputs", "2")), []).append(x["key"])
        return g
    ga, gb = groups(a), groups(b)
    if {k: len(v) for k, v in ga.items()} != {k: len(v) for k, v in gb.items()}:
        return False, "different parts list"
    A = canon(nets(a))
    Nb = nets(b)
    kinds = sorted(ga)
    perms = [list(itertools.permutations(gb[k])) for k in kinds]
    best = None
    for n, combo in enumerate(itertools.product(*perms)):
        if n > limit:
            return False, "too many pairings to try"
        km = {}
        for k, p in zip(kinds, combo):
            km.update(dict(zip(p, ga[k])))
        B = canon(Nb, km)
        if A == B:
            return True, km
        d = len(A ^ B)
        if best is None or d < best[0]:
            best = (d, A - B, B - A)
    return False, best

def problems(circ):
    """Things that silently break a Logisim file."""
    msgs = []
    pm = circ.port_map()
    segs = circ.wires
    for (k, pn), p in pm.items():
        for s in segs:
            if on_interior(p, s):
                msgs.append(f"port {k}.{pn} {p} sits mid-wire on {s} (NOT connected)")
    for s in segs:
        for t in segs:
            if s is t:
                continue
            for p in t:
                if on_interior(p, s):
                    msgs.append(f"wire end {p} lands mid-wire on {s} (T-junction not split -> NOT connected)")
    for s, t in itertools.combinations(segs, 2):
        for ax in (0, 1):
            o = 1 - ax
            if s[0][ax] == s[1][ax] == t[0][ax] == t[1][ax]:
                lo = max(min(s[0][o], s[1][o]), min(t[0][o], t[1][o]))
                hi = min(max(s[0][o], s[1][o]), max(t[0][o], t[1][o]))
                if lo < hi:
                    msgs.append(f"overlapping wires {s} and {t}")
    for s in segs:
        if s[0][0] != s[1][0] and s[0][1] != s[1][1]:
            msgs.append(f"diagonal wire {s}")
    ends = {}
    for s in segs:
        for p in s:
            ends[p] = ends.get(p, 0) + 1
    portpts = set(pm.values())
    for p, n in ends.items():
        if n == 1 and p not in portpts:
            msgs.append(f"dangling wire end {p}")
    for (k, pn), p in pm.items():
        if p not in ends and not any(p == q for kk, q in pm.items() if kk != (k, pn)):
            msgs.append(f"unconnected port {k}.{pn} {p}")
    for c in circ.comps:
        if c["name"] not in VERIFIED:
            msgs.append(f"UNVERIFIED geometry for {c['name']} ({c['key']}) - ask the user to check it in Logisim")
    return msgs

# ------------------------------------------------------------------ building
class Builder:
    """Lay out a circuit on the 10-px grid with polylines; split() makes T-junctions real."""
    def __init__(self):
        self.comps, self.polys, self.texts = [], [], []
        self.rails, self.taps = {}, {}

    def add(self, key, name, loc, **attrs):
        self.comps.append({"key": key, "name": name, "lib": LIB[name], "loc": loc, "attrs": attrs})
        return ports(name, loc, attrs)

    def wire(self, *pts):
        self.polys.append(list(pts))

    def rail(self, name, y):
        """Horizontal bus line; its length is trimmed to the outermost taps."""
        self.rails[name] = y; self.taps[name] = []

    def tap(self, rail, x):
        self.taps[rail].append(x)

    def drop(self, rail, x, port):
        """Vertical from a rail to the port's row, then horizontal into the port."""
        self.polys.append([(x, self.rails[rail]), (x, port[1]), port]); self.tap(rail, x)

    def rise(self, port, x, rail):
        """From an output, across to x, then vertical to the rail."""
        self.polys.append([port, (x, port[1]), (x, self.rails[rail])]); self.tap(rail, x)

    def text(self, loc, s, font="SansSerif plain 12"):
        self.texts.append({"name": "Text", "lib": "7", "loc": loc,
                           "attrs": {"font": font, "halign": "left", "text": s}})

    def segments(self):
        polys = list(self.polys)
        for r, xs in self.taps.items():
            if xs:
                polys.append([(min(xs), self.rails[r]), (max(xs), self.rails[r])])
        segs = []
        for pl in polys:
            for a, b in zip(pl, pl[1:]):
                if a != b:
                    if a[0] != b[0] and a[1] != b[1]:
                        raise ValueError(f"diagonal segment {a}->{b}")
                    segs.append((a, b))
        changed = True
        while changed:                       # split wherever an endpoint lands mid-wire
            changed = False
            pts = {p for s in segs for p in s}
            out = []
            for s in segs:
                cut = [p for p in pts if on_interior(p, s)]
                if cut:
                    changed = True
                    allp = sorted(set([s[0], s[1]] + cut))
                    out += list(zip(allp, allp[1:]))
                else:
                    out.append(s)
            segs = out
        return sorted({tuple(sorted(s)) for s in segs})

    def circuit(self):
        c = Circuit()
        c.comps = [dict(x) for x in self.comps]
        c.texts = list(self.texts)
        c.wires = self.segments()
        return c

def write(circ, out_path, template_path=None, circuit_name="main"):
    """Write circ into a copy of template_path (keeps libs/options/toolbar) or a fresh project."""
    if template_path:
        root = ET.parse(template_path).getroot()
    else:
        root = ET.fromstring(BLANK)
    node = [c for c in root.findall("circuit") if c.get("name") == circuit_name][0]
    for c in list(node):
        if c.tag in ("comp", "wire"):
            node.remove(c)
    for c in circ.comps + circ.texts:
        e = ET.SubElement(node, "comp", {"lib": c["lib"], "loc": f"({c['loc'][0]},{c['loc'][1]})", "name": c["name"]})
        for k, v in c["attrs"].items():
            ET.SubElement(e, "a", {"name": k, "val": str(v)})
    for a, b in circ.wires:
        ET.SubElement(node, "wire", {"from": f"({a[0]},{a[1]})", "to": f"({b[0]},{b[1]})"})
    ET.indent(root, "  ")
    with open(out_path, "w") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + ET.tostring(root, encoding="unicode") + "\n")

BLANK = """<project source="3.9.0" version="1.0">
  This file is intended to be loaded by Logisim-evolution (https://github.com/logisim-evolution/).
  <lib desc="#Wiring" name="0"><tool name="Pin"><a name="appearance" val="classic"/></tool></lib>
  <lib desc="#Gates" name="1"/><lib desc="#Plexers" name="2"/><lib desc="#Arithmetic" name="3"/>
  <lib desc="#Memory" name="5"/><lib desc="#I/O" name="6"/><lib desc="#Base" name="7"/>
  <main name="main"/>
  <options><a name="gateUndefined" val="ignore"/><a name="simlimit" val="1000"/><a name="simrand" val="0"/></options>
  <mappings><tool map="Button2" name="Menu Tool"/><tool map="Button3" name="Menu Tool"/><tool map="Ctrl Button1" name="Menu Tool"/></mappings>
  <toolbar><tool name="Poke Tool"/><tool name="Edit Tool"/><tool name="Text Tool"/></toolbar>
  <circuit name="main"><a name="circuit" val="main"/><a name="clabelfont" val="SansSerif plain 12"/></circuit>
</project>"""

# ------------------------------------------------------------------ simulation
def simulate(circ, steps, clock_each_step=True):
    """steps: list of {input_label: 0/1}. Returns list of {output_label: value} after each clock pulse
    (or after settling when clock_each_step=False). Flip-flops start at 0, trigger on rising edge."""
    netlist = nets(circ)
    net_of = {}
    for i, s in enumerate(netlist):
        for k in s:
            net_of[k] = i
    byk = {c["key"]: c for c in circ.comps}
    state = {c["key"]: 0 for c in circ.comps if "Flip-Flop" in c["name"]}
    pins_in = [c for c in circ.comps if c["name"] == "Pin" and c["attrs"].get("type") != "output"]
    pins_out = [c for c in circ.comps if c["name"] in ("Pin", "LED", "Probe") and
                (c["attrs"].get("type") == "output" or c["name"] != "Pin")]
    fn = {"AND Gate": all, "OR Gate": any,
          "NAND Gate": lambda v: not all(v), "NOR Gate": lambda v: not any(v),
          "XOR Gate": lambda v: sum(v) % 2 == 1, "XNOR Gate": lambda v: sum(v) % 2 == 0}

    def settle(inputs):
        val = {}
        def get(k, pn):
            n = net_of.get((k, pn))
            if n is None or n not in val:
                raise RuntimeError(f"floating input {k}.{pn}")
            return val[n]
        for c in pins_in:
            val[net_of[(c["key"], "p")]] = inputs[c["attrs"].get("label", c["key"])]
        for c in circ.comps:
            if c["name"] == "Constant":
                val[net_of[(c["key"], "p")]] = int(c["attrs"].get("value", "0x1"), 0) & 1
            if c["key"] in state:
                val[net_of[(c["key"], "Q")]] = state[c["key"]]
                if (c["key"], "Qn") in net_of:
                    val[net_of[(c["key"], "Qn")]] = 1 - state[c["key"]]
        for _ in range(len(circ.comps) + 2):
            for c in circ.comps:
                pm = ports(c["name"], c["loc"], c["attrs"])
                try:
                    if c["name"] == "NOT Gate":
                        val[net_of[(c["key"], "out")]] = 1 - get(c["key"], "in")
                    elif c["name"] in fn:
                        ins = [get(c["key"], p) for p in pm if p.startswith("in")]
                        val[net_of[(c["key"], "out")]] = int(bool(fn[c["name"]](ins)))
                except RuntimeError:
                    pass
        return val, get

    results = []
    for inp in steps:
        val, get = settle(inp)
        if clock_each_step:
            nxt = {}
            for k in state:
                c = byk[k]; q = state[k]
                if c["name"] == "J-K Flip-Flop":
                    j, kk = get(k, "J"), get(k, "K")
                    nxt[k] = (j and not q) or (not kk and q)
                elif c["name"] == "D Flip-Flop":
                    nxt[k] = get(k, "D")
                elif c["name"] == "T Flip-Flop":
                    nxt[k] = q ^ get(k, "T")
            state.update({k: int(v) for k, v in nxt.items()})
            val, get = settle(inp)
        out = {c["attrs"].get("label", c["key"]): get(c["key"], "p") for c in pins_out}
        out.update({f"{k}.Q": v for k, v in state.items()})
        results.append(out)
    return results

# ------------------------------------------------------------------ preview
def render(circ, png):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    fig, ax = plt.subplots(figsize=(16, 9))
    for a, b in circ.wires:
        ax.plot([a[0], b[0]], [a[1], b[1]], color="green", lw=1.5)
    ends = {}
    for s in circ.wires:
        for p in s:
            ends[p] = ends.get(p, 0) + 1
    for p, n in ends.items():
        if n >= 3:
            ax.plot(*p, "o", color="green", ms=4)
    for c in circ.comps:
        pm = ports(c["name"], c["loc"], c["attrs"])
        xs = [p[0] for p in pm.values()] or [c["loc"][0]]; ys = [p[1] for p in pm.values()] or [c["loc"][1]]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys) - 10, max(ys) + 10
        if x1 - x0 < 20:
            x0 -= 10; x1 += 10
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, color="k"))
        ax.text(x0 + 2, y1 - 2, c["attrs"].get("label", c["name"].split()[0]), fontsize=6, va="top")
    for t in circ.texts:
        ax.text(*t["loc"], t["attrs"]["text"], fontsize=7, va="bottom")
    ax.set_aspect("equal"); ax.invert_yaxis(); ax.grid(alpha=.2)
    plt.savefig(png, dpi=110, bbox_inches="tight")

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "check":
        c = Circuit(sys.argv[2])
        for m in problems(c) or ["no problems found"]:
            print(m)
        for s in nets(c):
            if len(s) > 1:
                print("NET", sorted(s))
    elif cmd == "compare":
        ok, info = same_connections(Circuit(sys.argv[2]), Circuit(sys.argv[3]))
        if ok:
            print("SAME CONNECTIONS")
        else:
            print("DIFFERENT:", info if isinstance(info, str) else "")
            if not isinstance(info, str) and info:
                for s in info[1]: print(" only in first :", sorted(s))
                for s in info[2]: print(" only in second:", sorted(s))
    elif cmd == "render":
        render(Circuit(sys.argv[2]), sys.argv[3])
    elif cmd == "sim":
        c = Circuit(sys.argv[2])
        cols = {}
        for part in sys.argv[3].split(";"):
            k, v = part.split("=")
            cols[k.strip()] = [int(x) for x in v.split(",")]
        n = len(next(iter(cols.values())))
        steps = [{k: v[i] for k, v in cols.items()} for i in range(n)]
        for i, r in enumerate(simulate(c, steps)):
            print(i, steps[i], r)
