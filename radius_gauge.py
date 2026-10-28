# Corner radius gauge for the keyboard (same radius as the iPhone 12 mini): press the corner into each
# tile's inside corner; the right one touches along the whole arc and both straight edges with no light gap.
# Smaller radius: the corner sits clear of the straight edges. Larger: light shows at the middle of the arc.
# Run inside FreeCAD: exec(open("/Volumes/cobanov-ssd/Workspace/cyberdeck/radius_gauge.py").read(), {})
import os
import FreeCAD as App, Part, MeshPart, Draft
from FreeCAD import Vector as V

DIR = "/Volumes/cobanov-ssd/Workspace/cyberdeck"
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
doc.recompute()
MeshPart.meshFromShape(Shape=gauge, LinearDeflection=0.02, AngularDeflection=0.1).write(
    os.path.join(DIR, "stl", "radius_gauge.stl"))
print("radius gauge:", ", ".join(f"{r:g}" for r in RADII))
