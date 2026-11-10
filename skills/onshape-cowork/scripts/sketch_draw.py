#!/usr/bin/env python3
"""Draw a dimensioned Onshape-style sketch as SVG from a small JSON spec.
Stdlib only.  Usage: sketch_draw.py spec.json out.svg

Spec (all mm, +X right, +Y up, origin = Onshape sketch origin):
{ "title": "Sketch 1: Base profile (Top plane)",
  "shapes": [
    {"type":"rect","c":[0,0],"w":60,"h":24,"r":0},        # r = corner radius, optional
    {"type":"circle","c":[22,0],"d":4.3},
    {"type":"poly","pts":[[0,0],[10,0],[10,5]],"closed":true},
    {"type":"slot","a":[-5,0],"b":[5,0],"w":4},
    {"type":"arc","c":[0,0],"r":10,"a0":0,"a1":90},
    {"type":"line","a":[0,-20],"b":[0,20],"construction":true} ],
  "dims": [
    {"type":"h","a":[-30,-12],"b":[30,-12],"off":-8,"label":"#len = 60"},
    {"type":"v","a":[30,-12],"b":[30,12],"off":8,"label":"#wid = 24"},
    {"type":"dia","c":[22,0],"d":4.3,"ang":45,"label":"dia #hole = 4.3"},
    {"type":"note","at":[0,14],"label":"symmetric about origin"} ] }
"h" measures along X and sits at y = a.y + off; "v" measures along Y at x = a.x + off.
Any shape may take "construction": true (dashed).
"""
import json, math, sys
from html import escape

INK, DIM, CON, ORG = "#111", "#0b62c4", "#888", "#c0392b"


def bounds(spec):
    xs, ys = [0.0], [0.0]
    def add(x, y): xs.append(x); ys.append(y)
    for s in spec.get("shapes", []):
        t = s["type"]
        if t == "rect":
            cx, cy = s["c"]; add(cx - s["w"]/2, cy - s["h"]/2); add(cx + s["w"]/2, cy + s["h"]/2)
        elif t == "circle":
            cx, cy = s["c"]; r = s["d"]/2; add(cx - r, cy - r); add(cx + r, cy + r)
        elif t == "arc":
            cx, cy = s["c"]; r = s["r"]; add(cx - r, cy - r); add(cx + r, cy + r)
        elif t == "poly":
            for x, y in s["pts"]: add(x, y)
        elif t == "slot":
            r = s["w"]/2
            for x, y in (s["a"], s["b"]): add(x - r, y - r); add(x + r, y + r)
        elif t == "line":
            add(*s["a"]); add(*s["b"])
    for d in spec.get("dims", []):
        t = d["type"]
        if t == "h":
            y = d["a"][1] + d.get("off", 0); add(d["a"][0], y); add(d["b"][0], y)
        elif t == "v":
            x = d["a"][0] + d.get("off", 0); add(x, d["a"][1]); add(x, d["b"][1])
        elif t == "dia":
            a = math.radians(d.get("ang", 45)); L = d["d"]/2 + d.get("lead", 0)
            add(d["c"][0] + L*math.cos(a), d["c"][1] + L*math.sin(a))
        elif t == "note":
            add(*d["at"])
    return min(xs), min(ys), max(xs), max(ys)


def render(spec, width=720):
    x0, y0, x1, y1 = bounds(spec)
    pad, padx = 70, 150
    k = (width - 2*padx) / max(x1 - x0, 1e-6)
    k = min(k, (width - 2*pad) / max(y1 - y0, 1e-6) * 1.4)
    H = (y1 - y0)*k + 2*pad + 30
    X = lambda x: round(padx + (x - x0)*k, 2)
    Y = lambda y: round(H - pad - (y - y0)*k, 2)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{round(H)}" '
         f'viewBox="0 0 {width} {round(H)}" font-family="Helvetica,Arial,sans-serif" font-size="13">',
         f'<rect width="100%" height="100%" fill="#fff"/>',
         '<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
         f'orient="auto-start-reverse"><path d="M0,1 L10,5 L0,9 z" fill="{DIM}"/></marker></defs>']
    if spec.get("title"):
        o.append(f'<text x="20" y="24" font-size="15" font-weight="bold" fill="{INK}">{escape(spec["title"])}</text>')

    def st(s):
        if s.get("construction"):
            return f'fill="none" stroke="{CON}" stroke-width="1.2" stroke-dasharray="6 4"'
        return f'fill="none" stroke="{INK}" stroke-width="2"'

    for s in spec.get("shapes", []):
        t = s["type"]
        if t == "rect":
            cx, cy = s["c"]; w, h, r = s["w"], s["h"], s.get("r", 0)
            o.append(f'<rect x="{X(cx-w/2)}" y="{Y(cy+h/2)}" width="{round(w*k,2)}" height="{round(h*k,2)}" rx="{round(r*k,2)}" {st(s)}/>')
        elif t == "circle":
            o.append(f'<circle cx="{X(s["c"][0])}" cy="{Y(s["c"][1])}" r="{round(s["d"]/2*k,2)}" {st(s)}/>')
            cx, cy = X(s["c"][0]), Y(s["c"][1])
            o.append(f'<path d="M{cx-4},{cy} h8 M{cx},{cy-4} v8" stroke="{CON}" stroke-width="1"/>')
        elif t == "arc":
            cx, cy = s["c"]; r = s["r"]; a0, a1 = math.radians(s["a0"]), math.radians(s["a1"])
            p0 = (cx + r*math.cos(a0), cy + r*math.sin(a0)); p1 = (cx + r*math.cos(a1), cy + r*math.sin(a1))
            large = 1 if (s["a1"] - s["a0"]) % 360 > 180 else 0
            o.append(f'<path d="M{X(p0[0])},{Y(p0[1])} A{round(r*k,2)},{round(r*k,2)} 0 {large} 0 {X(p1[0])},{Y(p1[1])}" {st(s)}/>')
        elif t == "poly":
            pts = " ".join(f"{X(x)},{Y(y)}" for x, y in s["pts"])
            tag = "polygon" if s.get("closed", True) else "polyline"
            o.append(f'<{tag} points="{pts}" {st(s)}/>')
        elif t == "slot":
            (ax, ay), (bx, by) = s["a"], s["b"]; r = s["w"]/2
            L = math.hypot(bx-ax, by-ay) or 1; nx, ny = -(by-ay)/L*r, (bx-ax)/L*r
            R = round(r*k, 2)
            o.append(f'<path d="M{X(ax+nx)},{Y(ay+ny)} L{X(bx+nx)},{Y(by+ny)} A{R},{R} 0 0 1 {X(bx-nx)},{Y(by-ny)} '
                     f'L{X(ax-nx)},{Y(ay-ny)} A{R},{R} 0 0 1 {X(ax+nx)},{Y(ay+ny)} z" {st(s)}/>')
        elif t == "line":
            o.append(f'<line x1="{X(s["a"][0])}" y1="{Y(s["a"][1])}" x2="{X(s["b"][0])}" y2="{Y(s["b"][1])}" {st(s)}/>')

    # origin marker
    ox, oy = X(0), Y(0)
    o.append(f'<circle cx="{ox}" cy="{oy}" r="3.5" fill="{ORG}"/><text x="{ox+6}" y="{oy+15}" fill="{ORG}" font-size="11">origin</text>')

    ds = f'stroke="{DIM}" stroke-width="1.1"'
    def label(x, y, txt, anchor="middle", rot=None):
        tr = f' transform="rotate({rot} {x} {y})"' if rot is not None else ""
        w = len(txt)*7.2 + 6
        bx = x - w/2 if anchor == "middle" else x - 3
        o.append(f'<g{tr}><rect x="{round(bx,1)}" y="{y-13}" width="{round(w,1)}" height="17" fill="#fff" opacity="0.85"/>'
                 f'<text x="{x}" y="{y}" fill="{DIM}" text-anchor="{anchor}">{escape(txt)}</text></g>')

    for d in spec.get("dims", []):
        t = d["type"]
        if t == "h":
            y = d["a"][1] + d.get("off", 0); xa, xb = d["a"][0], d["b"][0]
            o.append(f'<line x1="{X(xa)}" y1="{Y(d["a"][1])}" x2="{X(xa)}" y2="{Y(y)}" {ds} opacity="0.6"/>')
            o.append(f'<line x1="{X(xb)}" y1="{Y(d["b"][1])}" x2="{X(xb)}" y2="{Y(y)}" {ds} opacity="0.6"/>')
            o.append(f'<line x1="{X(xa)}" y1="{Y(y)}" x2="{X(xb)}" y2="{Y(y)}" {ds} marker-start="url(#ar)" marker-end="url(#ar)"/>')
            label((X(xa)+X(xb))/2, Y(y) - 5, d["label"])
        elif t == "v":
            x = d["a"][0] + d.get("off", 0); ya, yb = d["a"][1], d["b"][1]
            o.append(f'<line x1="{X(d["a"][0])}" y1="{Y(ya)}" x2="{X(x)}" y2="{Y(ya)}" {ds} opacity="0.6"/>')
            o.append(f'<line x1="{X(d["b"][0])}" y1="{Y(yb)}" x2="{X(x)}" y2="{Y(yb)}" {ds} opacity="0.6"/>')
            o.append(f'<line x1="{X(x)}" y1="{Y(ya)}" x2="{X(x)}" y2="{Y(yb)}" {ds} marker-start="url(#ar)" marker-end="url(#ar)"/>')
            label(X(x) - 6, (Y(ya)+Y(yb))/2, d["label"], rot=-90)
        elif t == "dia":
            a = math.radians(d.get("ang", 45)); r = d["d"]/2; cx, cy = d["c"]
            px, py = cx + r*math.cos(a), cy + r*math.sin(a)
            ex, ey = X(px) + 34*math.cos(a), Y(py) - 34*math.sin(a)
            o.append(f'<line x1="{round(ex,1)}" y1="{round(ey,1)}" x2="{X(px)}" y2="{Y(py)}" {ds} marker-end="url(#ar)"/>')
            right = math.cos(a) >= 0
            tx = ex + (40 if right else -40)
            o.append(f'<line x1="{round(ex,1)}" y1="{round(ey,1)}" x2="{round(tx,1)}" y2="{round(ey,1)}" {ds}/>')
            label(round(tx + (4 if right else -4), 1), round(ey + 4, 1), d["label"], anchor="start" if right else "end")
        elif t == "note":
            label(X(d["at"][0]), Y(d["at"][1]), d["label"])
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    open(sys.argv[2], "w").write(render(json.load(open(sys.argv[1]))))
    print("wrote", sys.argv[2])
