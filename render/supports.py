# Supports for the site's viewer: the support extrusions of a sliced G-code, in its STL's own frame.
# python3 render/supports.py <gcode> <stl> <out.bin>; slice_k1.sh runs it after slicing.
# The slicer arranges the part on the bed (centred, sometimes turned 90 deg), so the bed frame is found by matching the
# G-code's object outline (EXCLUDE_OBJECT_DEFINE) to the STL's outline. Output: int16 x0 y0 x1 y1 z h per line, in 0.01 mm.
import math, re, struct, sys

gcode, stl, out = sys.argv[1:4]


def hull(pts):
    pts = sorted(set(pts))
    def half(seq):
        h = []
        for p in seq:
            while len(h) > 1 and (h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0]) <= 0:
                h.pop()
            h.append(p)
        return h[:-1]
    return half(pts) + half(pts[::-1])


def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


d = open(stl, "rb").read()
n = struct.unpack("<I", d[80:84])[0]
assert len(d) == 84 + 50 * n, "binary STL expected"
ref = hull([(round(v[0], 3), round(v[1], 3)) for i in range(n)
            for v in (struct.unpack("<3f", d[84 + 50 * i + o: 96 + 50 * i + o]) for o in (12, 24, 36))])

poly, segs, typ, x, y, z, h = None, [], None, 0.0, 0.0, 0.0, 0.2
for line in open(gcode):
    if line.startswith("EXCLUDE_OBJECT_DEFINE"):
        assert poly is None, "one object per plate expected"
        poly = [tuple(map(float, p)) for p in re.findall(r"\[(-?[\d.]+),(-?[\d.]+)\]", line)]
    elif line.startswith(";TYPE:"): typ = line[6:].strip()
    elif line.startswith(";Z:"): z = float(line[3:])
    elif line.startswith(";HEIGHT:"): h = float(line[8:])
    elif line.startswith(("G0 ", "G1 ", "G2 ", "G3 ")):
        w = dict((m[0], float(m[1:])) for m in line.split(";")[0].split()[1:] if m[0] in "XYE")
        nx, ny = w.get("X", x), w.get("Y", y)
        if typ and typ.startswith("Support") and w.get("E", 0) > 0 and (nx, ny) != (x, y):
            segs.append((x, y, nx, ny, z, h))   # shortcut: arcs (G2/G3) become chords; the slicer here writes none
        x, y = nx, ny


def turn(p, k):   # by k quarter turns
    for _ in range(k):
        p = (-p[1], p[0])
    return p


def fit(k):
    q = [turn(p, k) for p in poly]
    t = (min(v[0] for v in ref) - min(v[0] for v in q), min(v[1] for v in ref) - min(v[1] for v in q))
    q = [(v[0] + t[0], v[1] + t[1]) for v in q]
    return sum(min(seg_dist(p, ref[i - 1], ref[i]) for i in range(len(ref))) for p in q) / len(q), t


err, t, k = min((*fit(k), k) for k in range(4))
assert err < 0.5, f"G-code outline doesn't match the STL (mean {err:.2f} mm off)"
data = []
for x0, y0, x1, y1, z, h in segs:
    a, b = turn((x0, y0), k), turn((x1, y1), k)
    data += [round(100 * v) for v in (a[0] + t[0], a[1] + t[1], b[0] + t[0], b[1] + t[1], z, h)]
open(out, "wb").write(struct.pack(f"<{len(data)}h", *data))
print(f"{out}: {len(segs)} support lines, {k * 90} deg turn, outline within {err:.2f} mm")
