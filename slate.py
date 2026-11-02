# Slate: one-piece 2DS-style handheld. The iPhone 12 mini drops face up into an open pocket in the top half, its screen
# flush with the face, and its own MagSafe magnets hold it to a steel ring sticker in the pocket's floor; the keyboard
# presses into the bottom half like the clamshell base. No latch, no rails, no frame over the screen.
# Run: freecadcmd slate.py, or in FreeCAD's console: p = "<repo>/slate.py"; exec(open(p).read(), {"__file__": p})
# Modelled face down in deck.py's frame (screen face at z=0, y=0 the top edge); printed back down with no supports:
# everything opens towards the face or goes through the back.
import json, os
import FreeCAD as App, Part, MeshPart
from FreeCAD import Vector as V

DIR = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(DIR, "deck.py")).read(), globals())   # measured parts, fits, the MagSafe phone pocket

# The phone's half is only as deep as the phone pocket needs; deck.py's pocket functions read the PY, PHONE_Y set here.
D = PPD + 2 * WALL
PY = WALL
PHONE_Y = PY + PH_CLR
GRIP_R = 3.0             # back edges, where the hands are
BED_C = 1.0              # ...but 45 deg where they meet the bed: the 3 mm round alone left a 1.8 mm first-layer strip
                         # round the camera window, under a 70 deg overhang, and that corner lifted (2026-11-01)
SEP = 3.0                # wall between phone and keyboard: the volume-button groove and the keyboard's USB-C notch meet
                         # in it, and keep 0.9 mm between them

# The keyboard's housing sits KB_SINK below the screen face, its key tops 1.2 mm below it. With the pocket exactly KB_BODY
# deep (2026-11-01) the housing stayed 0.5-1 mm proud and sprang back out; 1.2 mm down it still sat flush. It
# held in the clamshell base, which is deeper and has a slot at the USB-C port; the slate had neither.
# Printed back down, so the thickness is rounded up to whole layers to keep the phone bay's heights on layer lines.
KB_SINK = 2.7
NOTCH = 1.3              # USB-C relief into the 2 mm wall between keyboard and phone: 1.7 mm of room with KB_CLR, and the
                         # wall's face edge keeps 0.7 mm (it opens into the phone's button groove, behind the screen frame)
BACK = 1.2               # floor behind the keyboard; the push-out window leaves only a 13 mm frame of it
T = math.ceil((KB_BODY + KB_SINK + BACK) / LAYER - 1e-6) * LAYER
YK = PY + PPD + SEP                               # keyboard pocket's top wall
L = YK + PD + WALL
KX, KY = WALL + KB_CLR, YK + KB_CLR               # keyboard housing corner
YA, ZA = (WALL + PD + YK) / 2, T / 2              # flip axis to face up; puts the keyboard where render/scene.py expects


def make_slate():
    s = rbox(W, L, T, R_OUT)
    flat = [e for e in s.Edges if e.BoundBox.ZLength < 1e-6]
    s = s.makeFillet(EDGE_R, [e for e in flat if e.BoundBox.ZMax < 1e-6])
    s = s.makeChamfer(BED_C, [e for e in s.Edges if e.BoundBox.ZLength < 1e-6 and e.BoundBox.ZMin > T - 1e-6])
    s = s.makeFillet(GRIP_R, [e for e in s.Edges if e.BoundBox.ZLength < 1e-6 and abs(e.BoundBox.ZMin - (T - BED_C)) < 1e-6])
    s = phone_pocket(s, 0, T)
    s = s.cut(rbox(PW, PD, KB_BODY + KB_SINK + 1, CORNER_R + KB_CLR, WALL, YK, -1))            # keyboard pocket
    s = s.cut(rbox(W - 30, PD + 2 * WALL - 30, BACK + 2, 4, 15, YK - WALL + 15, T - BACK - 1))     # push-out window, as the base's
    for side, pos, width in KB_CUTOUTS:   # the keyboard's back edge faces the phone; 45 deg ends, so no edge is square
        assert side == "back", "slate has slots on the keyboard's back edge only"
        x0, x1, y = KX + pos, KX + pos + width, YK - NOTCH
        ends = Part.Face(Part.makePolygon([V(x0 - NOTCH - 0.5, YK + 0.5, -1), V(x0, y, -1), V(x1, y, -1),
                                           V(x1 + NOTCH + 0.5, YK + 0.5, -1), V(x0 - NOTCH - 0.5, YK + 0.5, -1)]))
        s = s.cut(ends.extrude(V(0, 0, KB_BODY + KB_SINK + 1)))
    # The keyboard window's top has a 1.2 mm floor behind it, chamfered 0.6 from the back: no room for more.
    return chamfer_sharp(s.removeSplitter(), lambda p: pocket_thin(p, PH_T) or abs(p.z - (T - BACK)) < 0.1)


slate = make_slate()
kb = keyboard(KX, KY, KB_BODY - KB_KEYS + KB_SINK, face_down=True)
phone = check_pocket(slate, 0)
assert YK - NOTCH - (PY + PPD + 0.8) >= 0.8, "volume-button groove and USB-C notch meet in the wall"
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

# STL in print orientation: back down, no supports.
slate_p = slate.copy()
slate_p.rotate(V(0, 0, 0), V(1, 0, 0), 180)
slate_p.translate(V(0, L, T))   # exactly the face-up frame the site's viewer shows (BoundBox is loose round fillets)
MeshPart.meshFromShape(Shape=slate_p, LinearDeflection=0.05, AngularDeflection=0.2).write(os.path.join(DIR, "stl", "slate.stl"))

# Meshes for render/scene.py --slate and the site's viewer: body and phone face down (both flip them about YA, ZA),
# keyboard face up.
out = os.path.join(DIR, "render", "slate")
os.makedirs(out, exist_ok=True)
kb_body = rbox(KB_W, KB_D, KB_BODY, CORNER_R, WALL + KB_CLR, WALL + KB_CLR, T - KB_BODY - KB_SINK)
for name, shape in [("slate", slate), ("kb_body", kb_body), ("phone", phone)]:
    MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.02, AngularDeflection=0.1).write(os.path.join(out, name + ".stl"))
dims = {k: globals()[k] for k in ("W", "D", "YA", "ZA", "T", "L", "KB_W", "KB_D", "KB_BODY", "KB_KEYS",
                                  "WALL", "KB_CLR", "FLOOR", "PH_W", "PH_D", "PH_T", "PX", "PPW", "PHONE_X", "PHONE_Y")}
dims.update(HB=0.0, OPEN=180.0, FLOOR=T - KB_BODY - KB_SINK,   # the scene stands the keys on FLOOR + KB_BODY
            SINK=0.0)                                            # and the screen SINK in from the face: flush here
json.dump(dims, open(os.path.join(out, "dims.json"), "w"), indent=1)

print(f"slate {W:.1f} x {L:.1f} x {T:.1f} mm, {slate.Volume / 1000:.1f} cm3")
