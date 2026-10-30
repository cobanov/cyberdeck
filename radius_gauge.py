# Corner radius gauge for the keyboard (same radius as the iPhone 12 mini): press the corner into each
# tile's inside corner; the right one touches along the whole arc and both straight edges with no light gap.
# Smaller radius: the corner sits clear of the straight edges. Larger: light shows at the middle of the arc.
# Run inside FreeCAD: exec(open("/Volumes/cobanov-ssd/Workspace/3d-projects/cyberdeck/radius_gauge.py").read(), {})
import os
import FreeCAD as App, Part, MeshPart, Draft
from FreeCAD import Vector as V

DIR = "/Volumes/cobanov-ssd/Workspace/3d-projects/cyberdeck"
RADII = [7.0 + 0.5 * i for i in range(10)]          # 7.0 .. 11.5 mm
TILE, LEG, T, GAP = 30.0, 9.0, 2.4, 4.0
FONT = "/System/Library/Fonts/Monaco.ttf"

if "RadiusGauge" in App.listDocuments():
    App.closeDocument("RadiusGauge")
doc = App.newDocument("RadiusGauge")
tiles = []
for i, r in enumerate(RADII):
    x0, y0 = (i % 5) * (TILE + GAP), (i // 5) * (TILE + GAP)
    hole = Part.makeBox(TILE, TILE, T + 2, V(x0 + LEG, y0 + LEG, -1))
    corner = [e for e in hole.Edges if e.BoundBox.XLength < 1e-6 and e.BoundBox.YLength < 1e-6
              and abs(e.BoundBox.XMin - x0 - LEG) < 1e-6 and abs(e.BoundBox.YMin - y0 - LEG) < 1e-6]
    tile = Part.makeBox(TILE, TILE, T, V(x0, y0, 0)).cut(hole.makeFillet(r, corner))
    label = Draft.make_shapestring(String=f"{r:g}", FontFile=FONT, Size=5.0)
    doc.recompute()
    txt = label.Shape.copy()
    txt.translate(V(x0 + 12, y0 + 2, T - 0.6))
    tiles.append(tile.cut(txt.extrude(V(0, 0, 1))))
    doc.removeObject(label.Name)

gauge = Part.makeCompound(tiles)
assert len(gauge.Solids) == len(RADII)
Part.show(gauge, "RadiusGauge")

# Case: the tiles stack inside; a lid slides in from the front along dovetail grooves (1:2 bevel, so the box prints
# upright and the lid flat, both without supports). A U-cut in the front wall lets fingers pinch the tiles out.
CLR, LID_CLR = 0.4, 0.2                  # tile stack to cavity, lid to grooves (per side)
WALL_C, FLOOR_C, LID, LIP = 2.4, 1.6, 2.0, 1.0
CW = TILE + 2 * CLR                      # cavity
H = FLOOR_C + len(RADII) * T + 0.4 + LID
OUT = CW + 2 * WALL_C


def slab(c):
    """Lid shape shrunk by c: wide bottom, narrow top, flat front at y=0 (y=-1 for the cut)."""
    rect = lambda x0, x1, y1, z: Part.makePolygon([V(x0, -1 if c == 0 else 0, z), V(x1, -1 if c == 0 else 0, z),
                                                     V(x1, y1, z), V(x0, y1, z), V(x0, -1 if c == 0 else 0, z)])
    return Part.makeLoft([rect(WALL_C - LIP + c, WALL_C + CW + LIP - c, WALL_C + CW + LIP - c, H - LID),
                          rect(WALL_C + c, WALL_C + CW - c, WALL_C + CW - c, H)], True, True)


box = Part.makeBox(OUT, OUT, H)
box = box.makeFillet(2.0, [e for e in box.Edges if e.BoundBox.ZLength > H - 1e-6])
box = box.cut(Part.makeBox(CW, CW, H, V(WALL_C, WALL_C, FLOOR_C))).cut(slab(0))
zu = FLOOR_C + 8 + 7                                                     # U-cut: 14 wide, bottom 8 mm off the floor
box = box.cut(Part.makeBox(14, WALL_C + 2, H, V(OUT / 2 - 7, -1, zu))).cut(
    Part.makeCylinder(7, WALL_C + 2, V(OUT / 2, -1, zu), V(0, 1, 0)))
box = box.removeSplitter()
lid = slab(LID_CLR)
lid = lid.cut(Part.makeCylinder(8, OUT, V(-1, 7, H + 8 - 0.8), V(1, 0, 0)))   # thumb scoop at the front
label = Draft.make_shapestring(String=f"R {RADII[0]:g}-{RADII[-1]:g}", FontFile=FONT, Size=4.5)
doc.recompute()
txt = label.Shape.copy()
txt.translate(V(OUT / 2 - txt.BoundBox.XLength / 2, OUT / 2 - 2, H - 0.6))
lid = lid.cut(txt.extrude(V(0, 0, 1)))
doc.removeObject(label.Name)

# Self-check: the tile stack and the lid fit; the lid can't drop in, lift off or slide out the back.
stack = Part.makeBox(TILE, TILE, len(RADII) * T, V(WALL_C + CLR, WALL_C + CLR, FLOOR_C))
assert stack.common(box).Volume < 0.01 and stack.common(lid).Volume < 0.01, "tiles don't fit the case"
assert lid.common(box).Volume < 0.01, "lid binds"
for d, what in [(V(0, 0, -0.5), "drops in"), (V(0, 0, 0.5), "lifts off"), (V(0, 0.5, 0), "slides out the back")]:
    assert lid.translated(d).common(box).Volume > 0.01, f"lid {what}"
lid.translate(V(OUT + 5, 0, LID - H))                                   # print flat, wide face down, beside the box
Part.show(box, "Case")
Part.show(lid, "CaseLid")
doc.recompute()
for name, shape in [("radius_gauge", gauge), ("radius_gauge_case", box), ("radius_gauge_lid", lid)]:
    MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.02, AngularDeflection=0.1).write(
        os.path.join(DIR, "stl", name + ".stl"))
print("radius gauge:", ", ".join(f"{r:g}" for r in RADII))
