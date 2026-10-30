# Cyberdeck clamshell: mini BT keyboard (base) + iPhone 12 mini (lid).
# Run inside FreeCAD: exec(open("/Volumes/cobanov-ssd/Workspace/3d-projects/cyberdeck/cyberdeck.py").read(), {})
# Frame: x = width (left->right), y = front->back, z = up. Lid is modelled closed, then opened via Placement.
import json, os
import FreeCAD as App, Part, MeshPart
from FreeCAD import Vector as V

DIR = "/Volumes/cobanov-ssd/Workspace/3d-projects/cyberdeck"

exec(open(os.path.join(DIR, "deck.py")).read(), globals())   # measured parts, fits, phone bay

# --- hinge: 2x (base | lid | base) knuckles, M3x20 socket screw self-tapped into the inner base knuckle ---
HR, HG, KG = 4.0, 0.5, 0.4      # knuckle radius, radial gap, axial gap
K_BASE, K_LID = 7.0, 10.0
FOOT = 14.0              # base extends this far behind the axis: lid stop + anti-tip
M3_CLR, M3_TAP, M3_HEAD = 3.3, 2.7, 6.0
M3_PIN = 3.1             # lid knuckle bore, snug on the screw shank so the lid can't rattle; ream with a 3 mm drill if tight
MAG_D, MAG_H = 8.0, 1.0  # open lock: disc magnets in the lid's landing web meet ones in the foot
MAG_X = (-25.0, 0.0, 25.0)   # magnet pairs, x from the middle; clear of the USB-C slot
TIP = 1.6                # landing web stops this far from the axis instead of a knife edge

# Keyboard port/switch slots: (side, mm from keyboard's left edge (front/back) or front edge (left/right), width)
KB_CUTOUTS = [("back", 28 - 7.5, 15)]   # USB-C on the back edge, centred ~28 mm from the left; slot fits the plug overmould

R_BACK = 6.0                                        # base's back corners stay tight so the hinge foot keeps its material
HB = FLOOR + KB_KEYS + KEY_GAP
YA, ZA = D + HR + HG, HB         # hinge axis
Y_END = YA + FOOT
OPEN = 180 - math.degrees(math.atan2(HL, HR + HG))   # lid's back-top edge lands on the foot here
RAY = V(0, -(HR + HG), HL).normalize()               # axis -> lid's back-top edge: the face that lands on the foot
NRM = V(0, RAY.z, -RAY.y)                            # that face's outward normal
MAG_S = (TIP + math.hypot(HR + HG, HL)) / 2          # magnet centre's distance from the axis along the face


def xcyl(r, x0, x1):
    c = Part.makeCylinder(r, x1 - x0, V(x0, YA, ZA), V(1, 0, 0))
    c.rotate(V(x0, YA, ZA), V(1, 0, 0), 45)   # keep the seam off the z=ZA face for clean booleans
    return c


def hinge_spans(left):
    a = (0.0, K_BASE)
    b = (a[1] + KG, a[1] + KG + K_LID)
    c = (b[1] + KG, b[1] + KG + K_BASE)
    if left:
        return a, b, c
    m = lambda s: (W - s[1], W - s[0])
    return m(a), m(b), m(c)


def make_base():
    s = rbox(W, Y_END, HB, R_OUT, r_back=R_BACK)
    s = s.makeFillet(EDGE_R, [e for e in s.Edges if e.BoundBox.ZLength < 1e-6])
    s = s.cut(rbox(PW, PD, HB, CORNER_R + KB_CLR, WALL, WALL, FLOOR))  # keyboard pocket
    s = s.cut(rbox(W - 30, D - 30, FLOOR + 2, 4, 15, 15, -1))          # push-out window
    s = s.cut(Part.makeCylinder(10, WALL + 2, V(W / 2, -1, HB + 6), V(0, 1, 0)))   # finger notch to lift the lid
    for side, pos, width in KB_CUTOUTS:
        if side in ("left", "right"):
            x = -1 if side == "left" else W - WALL - 1
            s = s.cut(Part.makeBox(WALL + 2, width, HB, V(x, WALL + KB_CLR + pos, FLOOR)))
        else:   # back slot runs out through the hinge foot
            y = -1 if side == "front" else D - WALL - 1
            depth = WALL + 2 if side == "front" else Y_END - y + 1
            s = s.cut(Part.makeBox(width, depth, HB, V(WALL + KB_CLR + pos, y, FLOOR)))
    for left in (True, False):
        bo, li, bi = hinge_spans(left)
        s = s.cut(xcyl(HR + HG, li[0] - KG, li[1] + KG))                # groove for the lid knuckle
        s = s.fuse(xcyl(HR, *bo)).fuse(xcyl(HR, *bi))
        if left:
            clr, tap, head = (-1, bi[0]), bi, (-1, 3.5)
        else:
            clr, tap, head = (bi[1], W + 1), bi, (W - 3.5, W + 1)
        s = s.cut(xcyl(M3_CLR / 2, *clr)).cut(xcyl(M3_TAP / 2, *tap)).cut(xcyl(M3_HEAD / 2, *head))
    for dx in MAG_X:
        s = s.cut(Part.makeCylinder(MAG_D / 2 + 0.1, MAG_H + 1.2, V(W / 2 + dx, YA + MAG_S, ZA - MAG_H - 0.2)))
    return s.removeSplitter()


def make_lid():
    s = rbox(W, D, HL, R_OUT, 0, 0, HB)
    s = s.makeFillet(EDGE_R, [e for e in s.Edges if e.BoundBox.ZLength < 1e-6])
    s = phone_bay(s, HB, HB + HL)
    # Web behind the OPEN ray: lands flat on the foot at the stop, at the knuckles and all the way between the hinges.
    tip = V(0, YA, ZA) + RAY * TIP
    web = Part.Face(Part.makePolygon([V(0, D - 3, ZA), V(0, YA - TIP, ZA), V(0, tip.y, tip.z), V(0, D, ZA + HL),
                                      V(0, D - 3, ZA + HL), V(0, D - 3, ZA)]))
    mid = (hinge_spans(True)[2][1] + KG, hinge_spans(False)[2][0] - KG)
    for x0, x1 in (hinge_spans(True)[1], mid, hinge_spans(False)[1]):
        s = s.fuse(web.extrude(V(x1 - x0, 0, 0)).translate(V(x0, 0, 0)))
    for left in (True, False):
        li = hinge_spans(left)[1]
        s = s.fuse(xcyl(HR, *li)).cut(xcyl(M3_PIN / 2, li[0] - 1, li[1] + 1))
    for dx in MAG_X:
        mag = V(W / 2 + dx, YA, ZA) + RAY * MAG_S
        s = s.cut(Part.makeCylinder(MAG_D / 2 + 0.1, MAG_H + 0.7, mag + NRM * 0.5, NRM * -1))
    return s.removeSplitter()


def opened(shape, deg):
    c = shape.copy()
    c.rotate(V(0, YA, ZA), V(1, 0, 0), -deg)
    return c


base, lid = make_base(), make_lid()
kb = keyboard(WALL + KB_CLR, WALL + KB_CLR, FLOOR)
phone = check_phone(lid, HB)

# Self-check: lid swings freely up to the stop, the stop engages, parts fit their pockets.
for deg in (0, 45, 90, OPEN - 0.5):
    assert opened(lid, deg).common(base).Volume < 0.01, f"lid hits base at {deg:.1f} deg"
assert opened(lid, OPEN + 3).common(base).Volume > 0.01, "stop does not engage"
assert kb.common(base).Volume < 0.01, "keyboard pocket too small"
# The web lands flat on the foot at the stop, so each lid magnet meets the foot magnet at YA + MAG_S.
assert (App.Rotation(V(1, 0, 0), -OPEN).multVec(RAY) - V(0, 1, 0)).Length < 1e-6, "web not flat on the foot"

if "Cyberdeck" in App.listDocuments():
    App.closeDocument("Cyberdeck")
doc = App.newDocument("Cyberdeck")
pl = App.Placement(V(0, 0, 0), App.Rotation(V(1, 0, 0), -OPEN), V(0, YA, ZA))
for name, shape, color, transp, place in [
    ("Base", base, (0.13, 0.13, 0.15), 0, None),
    ("Keyboard", kb, (0.8, 0.8, 0.8), 0, None),
    ("Lid", lid, (0.61, 0.07, 0.12), 0, pl),
    ("Phone", phone, (0.05, 0.05, 0.08), 40, pl),
]:
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    if place:
        o.Placement = pl
    if App.GuiUp:
        o.ViewObject.ShapeColor = color
        o.ViewObject.Transparency = transp
doc.recompute()
doc.saveAs(os.path.join(DIR, "cyberdeck.FCStd"))

# STL in print orientation: base floor down, lid plate down.
lid_p = lid.copy()
lid_p.rotate(V(0, 0, 0), V(1, 0, 0), 180)
lid_p.translate(V(0, -lid_p.BoundBox.YMin, -lid_p.BoundBox.ZMin))
fit_kb = rbox(W, D, 3, R_OUT).cut(rbox(PW, PD, 5, CORNER_R + KB_CLR, WALL, WALL, -1))
fit_ph = lid_p.common(Part.makeBox(35, D + 1, HL + 1, V(-1, -1, -1)))   # left end: rails, lips and latch
os.makedirs(os.path.join(DIR, "stl"), exist_ok=True)
for name, shape in [("base", base), ("lid", lid_p), ("fit_keyboard", fit_kb), ("fit_phone", fit_ph)]:
    MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.05, AngularDeflection=0.2).write(
        os.path.join(DIR, "stl", name + ".stl"))

# Meshes for render/scene.py, in the assembled closed frame (the scene swings the lid open itself).
kb_body = rbox(KB_W, KB_D, KB_BODY, CORNER_R, WALL + KB_CLR, WALL + KB_CLR, FLOOR)
for name, shape in [("base", base), ("lid", lid), ("kb_body", kb_body), ("phone", phone)]:
    MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.02, AngularDeflection=0.1).write(
        os.path.join(DIR, "render", name + ".stl"))
dims = {k: globals()[k] for k in ("W", "D", "HB", "HL", "YA", "ZA", "OPEN", "KB_W", "KB_D", "KB_BODY", "KB_KEYS",
                                  "WALL", "KB_CLR", "FLOOR", "PH_W", "PH_D", "PH_T", "LIP_T", "PX", "PPW")}
dims.update(PHONE_X=PHONE_X, PHONE_Y=PHONE_Y)
json.dump(dims, open(os.path.join(DIR, "render", "dims.json"), "w"), indent=1)

print(f"closed {W:.1f} x {Y_END:.1f} x {HB + HL:.1f} mm, opens to {OPEN:.1f} deg")
print(f"base {base.Volume / 1000:.1f} cm3, lid {lid.Volume / 1000:.1f} cm3")
