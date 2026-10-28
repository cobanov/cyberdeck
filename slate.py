# Slate: one-piece 2DS-style handheld. The iPhone 12 mini slides into the top half on the same rails and latch as the
# clamshell lid; the keyboard tilts into the bottom half under two fixed lips and clicks in past two snap hooks.
# Run inside FreeCAD: exec(open("/Volumes/cobanov-ssd/Workspace/cyberdeck/slate.py").read(), {})
# Modelled face down in deck.py's frame (screen face at z=0, y=0 the top edge); printed back down, no supports.
import json, os
import FreeCAD as App, Part, MeshPart
from FreeCAD import Vector as V

DIR = "/Volumes/cobanov-ssd/Workspace/cyberdeck"
exec(open(os.path.join(DIR, "deck.py")).read(), globals())   # measured parts, fits, phone bay

# --- keyboard retention: tilt in under the lips at the spacebar edge, click past the hooks at the top edge ---
RET = 0.8                # fixed lips overlap the housing's edge band, outside the key field
LIPS_X, LIPS_L = (-32.0, 32.0), 30.0              # fixed lips: x from the middle, length
HOOK = 0.6               # snap hooks overlap the housing's top edge; 45 deg back face, so a push from behind frees it
HOOKS_X = (-22.0, 22.0)  # clear of the USB-C notch
TAB_L, TAB_T, TAB_H, TAB_SLOT = 14.0, 1.2, 11.0, 1.0   # hook tab: length, thickness, free height, slot behind it
KB_NOTCH = (28 - 7.5, 15)   # USB-C (and any switch) on the keyboard's top edge: x from its left end, width
BOT = 3.0                # wall below the keyboard
GRIP_R = 3.0             # back edges, where the hands are

T = KEY_GAP + KB_KEYS + FLOOR                     # one thickness: the keyboard sets it, the phone's plate takes the rest
YK = D + TAB_SLOT + TAB_T                         # keyboard pocket's top wall
L = YK + PD + BOT
KX, KY = WALL + KB_CLR, YK + KB_CLR               # keyboard housing corner
ZH = KEY_GAP + KB_KEYS - KB_BODY                  # housing's key-side face
YA, ZA = (WALL + PD + YK) / 2, T / 2              # flip axis to face up; puts the keyboard where render/scene.py expects


def make_slate():
    s = rbox(W, L, T, R_OUT, r_back=CORNER_R + KB_CLR + BOT)
    flat = [e for e in s.Edges if e.BoundBox.ZLength < 1e-6]
    s = s.makeFillet(EDGE_R, [e for e in flat if e.BoundBox.ZMax < 1e-6])
    s = s.makeFillet(GRIP_R, [e for e in s.Edges if e.BoundBox.ZLength < 1e-6 and e.BoundBox.ZMin > T - 1e-6])
    s = phone_bay(s, 0, T)
    s = s.cut(rbox(PW, PD, KEY_GAP + KB_KEYS + 1, CORNER_R + KB_CLR, WALL, YK, -1))   # keyboard pocket, keys to the screen face
    for dx in LIPS_X:
        s = s.fuse(rbox(LIPS_L, KB_CLR + RET + 1, ZH - 0.1, 0.8, W / 2 + dx - LIPS_L / 2, YK + PD - KB_CLR - RET, 0))
    y0 = YK - TAB_T - TAB_SLOT
    for dx in HOOKS_X:
        x0 = W / 2 + dx - TAB_L / 2
        s = s.cut(Part.makeBox(TAB_L + 2 * SLIT, TAB_SLOT, TAB_H + 1, V(x0 - SLIT, y0, -1)))   # slot behind the tab
        for xs in (x0 - SLIT, x0 + TAB_L):
            s = s.cut(Part.makeBox(SLIT, TAB_SLOT + TAB_T + 1, TAB_H + 1, V(xs, y0, -1)))     # side slits
        hook = Part.makePolygon([V(0, YK - 0.2, 0), V(0, YK, 0), V(0, YK + KB_CLR + HOOK, 1.6),
                                 V(0, YK + KB_CLR + HOOK, 2.1), V(0, YK + KB_CLR, ZH - 0.1), V(0, YK - 0.2, ZH - 0.1),
                                 V(0, YK - 0.2, 0)])
        s = s.fuse(Part.Face(hook).extrude(V(TAB_L - 1, 0, 0)).translate(V(x0 + 0.5, 0, 0)))
        # Push-out window behind each hook: press the keyboard's top edge out from the back.
        s = s.cut(port(24, 12, V(W / 2 + dx, YK + 16, T + 0.01), V(0, 0, -1), V(1, 0, 0), FLOOR + 0.5, 0.8))
    s = s.cut(rbox(KB_NOTCH[1], TAB_SLOT + TAB_T + 1, KEY_GAP + KB_KEYS + 1, 1.0, KX + KB_NOTCH[0], y0, -1))
    return s.removeSplitter()


slate = make_slate()
kb = keyboard(KX, KY, KEY_GAP, face_down=True)
phone = check_phone(slate, 0)

# Self-check: the keyboard fits, and both edges hold it against falling out of the screen face.
assert kb.common(slate).Volume < 0.01, "keyboard pocket too small"
for top, what in ((True, "snap hooks"), (False, "fixed lips")):
    half = Part.makeBox(W, PD / 2, T, V(0, YK if top else YK + PD / 2, 0))
    assert kb.translated(V(0, 0, -0.5)).common(slate).common(half).Volume > 0.01, f"keyboard not held by {what}"

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

# STL in print orientation: back down.
slate_p = slate.copy()
slate_p.rotate(V(0, 0, 0), V(1, 0, 0), 180)
slate_p.translate(V(0, -slate_p.BoundBox.YMin, -slate_p.BoundBox.ZMin))
ring = Part.makeBox(W + 2, L - YK + 5, T + 2, V(-1, YK - 4, -1)).cut(
    Part.makeBox(W - 28, PD - 28, T + 4, V(14, YK + 14, -2)))
fit = slate.common(ring)
fit.rotate(V(0, 0, 0), V(1, 0, 0), 180)
fit.translate(V(0, -fit.BoundBox.YMin, -fit.BoundBox.ZMin))   # keyboard pocket rim: lips, hooks, notch
for name, shape in [("slate", slate_p), ("fit_slate_keyboard", fit)]:
    MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.05, AngularDeflection=0.2).write(
        os.path.join(DIR, "stl", name + ".stl"))

# Meshes for render/scene.py --slate: body and phone face down (the scene flips them about YA, ZA), keyboard face up.
out = os.path.join(DIR, "render", "slate")
os.makedirs(out, exist_ok=True)
kb_body = rbox(KB_W, KB_D, KB_BODY, CORNER_R, WALL + KB_CLR, WALL + KB_CLR, FLOOR)
for name, shape in [("slate", slate), ("kb_body", kb_body), ("phone", phone)]:
    MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.02, AngularDeflection=0.1).write(os.path.join(out, name + ".stl"))
dims = {k: globals()[k] for k in ("W", "D", "HL", "YA", "ZA", "T", "L", "KB_W", "KB_D", "KB_BODY", "KB_KEYS",
                                  "WALL", "KB_CLR", "FLOOR", "PH_W", "PH_D", "PH_T", "LIP_T", "PX", "PPW",
                                  "PHONE_X", "PHONE_Y")}
dims.update(HB=0.0, OPEN=180.0)
json.dump(dims, open(os.path.join(out, "dims.json"), "w"), indent=1)

print(f"slate {W:.1f} x {L:.1f} x {T:.1f} mm, {slate.Volume / 1000:.1f} cm3")
