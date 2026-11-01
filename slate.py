# Slate: one-piece 2DS-style handheld. The iPhone 12 mini slides into the top half on the clamshell lid's rails and is
# held by its snug fit; the keyboard presses into the bottom half like the clamshell base. Neither needs a latch.
# Run inside FreeCAD: exec(open("/Volumes/cobanov-ssd/Workspace/3d-projects/cyberdeck/slate.py").read(), {})
# Modelled face down in deck.py's frame (screen face at z=0, y=0 the top edge); printed back down with no supports.
# The print STL closes the screen window with a one-layer skin under the frame lips: cut it out after printing.
import json, os
import FreeCAD as App, Part, MeshPart
from FreeCAD import Vector as V

DIR = "/Volumes/cobanov-ssd/Workspace/3d-projects/cyberdeck"
exec(open(os.path.join(DIR, "deck.py")).read(), globals())   # measured parts, fits, phone bay

# The phone bay is only as deep as the phone: WALL above and below it, so the top-edge button sits behind 2 mm of wall
# instead of the keyboard-wide bay's 3.8. phone_bay reads these from the globals deck.py was run in.
D = PPD + 2 * WALL
PY, PHONE_Y = (D - PPD) / 2, (D - PH_D) / 2
GRIP_R = 3.0             # back edges, where the hands are
LEAD = 1.0               # 45 deg lead-in round the phone bay's open end
MOUTH_R = GRIP_R + 0.5   # outer corner at the bay's open end: R_OUT there ran out into a knife edge along the 2 mm rail;
                         # just over GRIP_R so the back fillet still runs round it

# The keyboard's housing sits KB_SINK below the screen face, its keys stand proud. With the pocket exactly KB_BODY deep
# (2026-11-01) the housing stayed 0.5-1 mm proud and sprang back out: the walls only hold it once its top edge is inside.
# Printed back down, so the thickness is rounded up to whole layers to keep the phone bay's heights on layer lines.
KB_SINK = 1.2
BACK = 1.2               # floor behind the keyboard; the push-out window leaves only a 13 mm frame of it
T = math.ceil((KB_BODY + KB_SINK + BACK) / LAYER - 1e-6) * LAYER
YK = D                                            # keyboard pocket's top wall
L = YK + PD + WALL
KX, KY = WALL + KB_CLR, YK + KB_CLR               # keyboard housing corner
YA, ZA = (WALL + PD + YK) / 2, T / 2              # flip axis to face up; puts the keyboard where render/scene.py expects


def make_slate():
    s = Part.makeBox(W, L, T)
    # Corners concentric with what they wrap: the bay's closed end (CORNER_R - 2) and the keyboard.
    for x, y, r in ((0, 0, MOUTH_R), (W, 0, CORNER_R - 2 + WALL_R), (0, L, R_OUT), (W, L, R_OUT)):
        s = s.makeFillet(r, [e for e in s.Edges if e.BoundBox.XLength < 1e-6 and e.BoundBox.YLength < 1e-6
                             and abs(e.BoundBox.XMin - x) < 1e-6 and abs(e.BoundBox.YMin - y) < 1e-6])
    flat = [e for e in s.Edges if e.BoundBox.ZLength < 1e-6]
    s = s.makeFillet(EDGE_R, [e for e in flat if e.BoundBox.ZMax < 1e-6])
    s = s.makeFillet(GRIP_R, [e for e in s.Edges if e.BoundBox.ZLength < 1e-6 and e.BoundBox.ZMin > T - 1e-6])
    s = phone_bay(s, 0, T, latch=False, lead=LEAD)
    s = s.cut(rbox(PW, PD, KB_BODY + KB_SINK + 1, CORNER_R + KB_CLR, WALL, YK, -1))            # keyboard pocket
    s = s.cut(rbox(W - 30, PD + 2 * WALL - 30, BACK + 2, 4, 15, YK - WALL + 15, T - BACK - 1))     # push-out window, as the base's
    return s.removeSplitter()


slate = make_slate()
kb = keyboard(KX, KY, KB_BODY - KB_KEYS + KB_SINK, face_down=True)
phone = check_phone(slate, 0, latch=False)
assert kb.common(slate).Volume < 0.01, "keyboard pocket too small"
assert kb.translated(V(0, 0, 0.5)).common(slate).Volume > 0.01, "keyboard not on the pocket floor"

if "Slate" in App.listDocuments():
    App.closeDocument("Slate")
doc = App.newDocument("Slate")
pl = App.Placement(V(0, 0, 0), App.Rotation(V(1, 0, 0), 180), V(0, YA, ZA))   # face up on the desk
for name, shape, color, transp in [("Body", slate, (0.61, 0.07, 0.12), 0), ("Keyboard", kb, (0.8, 0.8, 0.8), 0),
                                   ("Phone", phone, (0.05, 0.05, 0.08), 40)]:
    o = doc.addObject("Part::Feature", name)
    o.Shape, o.Placement = shape, pl
    if App.GuiUp:
        o.ViewObject.ShapeColor = color
        o.ViewObject.Transparency = transp
doc.recompute()
doc.saveAs(os.path.join(DIR, "slate.FCStd"))

# STL in print orientation: back down. A one-layer skin closes the screen window at the lips' underside, so the slicer
# bridges the lips across the bay's 65 mm width, wall to wall. Bridged lengthwise (126 mm) they sagged; on tree supports
# the supports fused under them and couldn't be removed.
slate_p = slate.fuse(screen_window(LIP_T - LAYER, LAYER)).removeSplitter()
slate_p.rotate(V(0, 0, 0), V(1, 0, 0), 180)
slate_p.translate(V(0, -slate_p.BoundBox.YMin, -slate_p.BoundBox.ZMin))
MeshPart.meshFromShape(Shape=slate_p, LinearDeflection=0.05, AngularDeflection=0.2).write(os.path.join(DIR, "stl", "slate.stl"))

# Meshes for render/scene.py --slate: body and phone face down (the scene flips them about YA, ZA), keyboard face up.
out = os.path.join(DIR, "render", "slate")
os.makedirs(out, exist_ok=True)
kb_body = rbox(KB_W, KB_D, KB_BODY, CORNER_R, WALL + KB_CLR, WALL + KB_CLR, T - KB_BODY - KB_SINK)
for name, shape in [("slate", slate), ("kb_body", kb_body), ("phone", phone)]:
    MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.02, AngularDeflection=0.1).write(os.path.join(out, name + ".stl"))
dims = {k: globals()[k] for k in ("W", "D", "HL", "YA", "ZA", "T", "L", "KB_W", "KB_D", "KB_BODY", "KB_KEYS",
                                  "WALL", "KB_CLR", "FLOOR", "PH_W", "PH_D", "PH_T", "LIP_T", "PX", "PPW",
                                  "PHONE_X", "PHONE_Y")}
dims.update(HB=0.0, OPEN=180.0, FLOOR=T - KB_BODY - KB_SINK)   # the scene stands the keys on FLOOR + KB_BODY
json.dump(dims, open(os.path.join(out, "dims.json"), "w"), indent=1)

print(f"slate {W:.1f} x {L:.1f} x {T:.1f} mm, {slate.Volume / 1000:.1f} cm3")
