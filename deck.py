# Shared by cyberdeck.py (clamshell) and slate.py (one-piece handheld): measured parts, fits, and the phone bay.
# Not run on its own; each script loads it with exec(open(os.path.join(DIR, "deck.py")).read(), globals()).
# Frame: x = width (left->right), y = the phone's top edge -> bottom edge, z = screen face -> back (screen faces -z).
import math
import FreeCAD as App, Part
from FreeCAD import Vector as V

# --- measured / spec (mm) ---
KB_W, KB_D = 133.0, 68.0
KB_BODY = 9.5            # plastic housing
KB_KEYS = 12.0           # housing + membrane keys
KB_INSET = 3.0           # key field starts this far in from the housing edge (retainers grip the band outside it)
PH_W, PH_D, PH_T = 131.5, 64.2, 7.4   # iPhone 12 mini, Apple spec
PH_SCREEN = 124.9, 57.6  # its active area: 2340 x 1080 px at 476 ppi, so a 3.3 mm black border all round
CORNER_R = 10.0          # keyboard and iPhone 12 mini share this corner radius, both measured with stl/radius_gauge.stl
                         # too large binds the corners once it exceeds the real radius by ~1 mm; too small only leaves gaps

# --- fit ---
KB_CLR, PH_CLR = 0.4, 0.5
WALL, FLOOR, PLATE = 2.0, 2.0, 2.0
KEY_GAP = 0.3            # rim above key tops: edge keys stay easy to press
RING = 0.6               # MagSafe steel ring sticker behind the phone (0 if none)
EDGE_R = 1.0             # outer edges
LAYER = 0.2              # print layer height: the phone bay's heights sit on layer lines (the lid is 56 layers)

# --- phone slides in from the left on rails, a flexing tongue in the plate latches it ---
LIP, LIP_T = 1.0, 1.2    # frame lip over the screen's black border, lip thickness
LIP_STEP = LAYER         # lip's left end starts one layer higher, so the slicer bridges it wall to wall on its own
WALL_R = 2.0             # closed right end (Lightning side)
TONGUE_L, TONGUE_W, SLIT = 25.0, 10.0, 1.0
BUMP_H = 2.0             # latch bump height above the plate; catches RING-less phone edge by BUMP_H - RING

PW, PD = KB_W + 2 * KB_CLR, KB_D + 2 * KB_CLR
W, D = PW + 2 * WALL, PD + 2 * WALL                 # footprint: the keyboard's, the phone bay shares it
R_OUT = CORNER_R + KB_CLR + WALL                    # outer corners concentric with the keyboard and phone
PH_R = CORNER_R + PH_CLR
HL = PLATE + RING + PH_T + LIP_T                    # phone bay thickness with the thinnest plate
PPW, PPD = PH_W + 2 * PH_CLR, PH_D + 2 * PH_CLR
PX, PY = W - WALL_R - PPW, (D - PPD) / 2               # phone pocket origin in the bay
PHONE_X, PHONE_Y = PX + PPW - PH_W, (D - PH_D) / 2     # phone slid home against the right end
YC = PY + PPD - PH_R - TONGUE_W / 2 - 3               # latch tongue centre, on the straight part of the phone's edge
assert LIP + PH_CLR < (PH_D - PH_SCREEN[1]) / 2, "frame lip reaches the active screen"
assert 1.5 * PLATE * BUMP_H / TONGUE_L ** 2 < 0.01, "latch tongue strained past 1 % (PLA)"
assert all(abs(h / LAYER - round(h / LAYER)) < 1e-6 for h in (LIP_T, PH_T + RING, HL)), "phone bay heights off layer lines"


def rbox(w, d, h, r, x=0, y=0, z=0, r_back=None):
    """Box with rounded vertical edges; the two back (max y) edges get r_back if given."""
    b = Part.makeBox(w, d, h, V(x, y, z))
    vert = lambda s: [e for e in s.Edges if e.BoundBox.XLength < 1e-6 and e.BoundBox.YLength < 1e-6]
    if r_back is None:
        return b.makeFillet(r, vert(b)) if r > 0 else b
    is_back = lambda e: abs(e.BoundBox.YMin - (y + d)) < 1e-6
    b = b.makeFillet(r, [e for e in vert(b) if not is_back(e)])
    return b.makeFillet(r_back, [e for e in vert(b) if is_back(e)])


def rrect(w, d, r, x, y, z):
    """Rounded-rectangle wire in the plane at height z."""
    return min(rbox(w, d, 1, r, x, y, z).Faces, key=lambda f: f.CenterOfMass.z).OuterWire


def port(l, h, centre, inward, along, depth, flare=1.0, flare_h=None):
    """Stadium window l x h through a wall, flaring by `flare` per side at the outer face (`flare_h` across h, if given)."""
    fh = flare if flare_h is None else flare_h
    wires = [rrect(l + 2 * f, h + 2 * g, (h / 2 + g) * 0.999, -l / 2 - f, -h / 2 - g, z)
             for f, g, z in ((flare, fh, 0), (0, 0, depth))]
    ay = inward.cross(along)
    m = App.Matrix(along.x, ay.x, inward.x, centre.x, along.y, ay.y, inward.y, centre.y,
                   along.z, ay.z, inward.z, centre.z, 0, 0, 0, 1)
    return Part.makeLoft(wires, True, True).transformed(m)


def phone_bay(s, z0, back):
    """Cut the slide-in phone bay into s over the W x D footprint at the origin: screen face at z0, back face at back."""
    zp = z0 + LIP_T + PH_T + RING                                       # plate inner face
    zm = z0 + LIP_T + PH_T / 2                                           # phone mid-thickness: buttons, Lightning
    thru = back - zp + 2                                                 # cuts through the plate
    # Rail channel open at the left end (rbox starts off-part so the left corners vanish). Its closed end's corners are
    # 2 mm tighter than the phone's: on the first lid the phone stopped 1-2 mm short of this end, and a tighter corner
    # can't bind, it only leaves a gap under the lip.
    s = s.cut(rbox(PX + PPW + 10, PPD, zp - z0 - LIP_T, CORNER_R - 2, -10, PY, z0 + LIP_T))
    # Screen window: the lip runs all the way round as one frame, chamfered towards the screen.
    # The phone slides in above the lip's left end, so closing the frame there costs nothing.
    wx, wy, ww, wd, wr, c = PHONE_X + LIP, PHONE_Y + LIP, PH_W - 2 * LIP, PH_D - 2 * LIP, CORNER_R - LIP, 0.6
    s = s.cut(Part.makeLoft([rrect(ww + 2 * c, wd + 2 * c, wr + c, wx - c, wy - c, z0 - 0.01),
                             rrect(ww, wd, wr, wx, wy, z0 + c)], True, True))
    s = s.cut(rbox(ww, wd, LIP_T + 1, wr, wx, wy, z0 + c - 0.1))
    # Over the open slot the lip is a 65 mm bridge. On the same layer as the side lips the slicer hangs it from them
    # in short strands; one layer up it spans wall to wall, and the step leaves room for sag.
    s = s.cut(Part.makeBox(wx + 1, PPD, LIP_STEP + 0.01, V(-1, PY, z0 + LIP_T - LIP_STEP)))
    # Landscape, camera end on the user's left: y=0 is the phone's top edge.
    # Camera bump slides in along a groove in the plate, then sits in a window so the camera still sees.
    # Neither reaches the left end, so the plate's end stays whole. Both run 2 mm past the bump (35, was 33), the other
    # suspect for the phone stopping short of the right end.
    s = s.cut(rbox(PX + 35 + 10, 30, PLATE - 0.6 + 1, 6, -10, PY + 2, zp - 1))
    s = s.cut(rbox(PX + 35 - PHONE_X - 1, 30, thru, 6, PHONE_X + 1, PY + 2, zp - 1))
    # Latch: cantilever tongue in the plate, free end just inside a strip at the left end; a ramped bump there
    # holds the phone's left edge. Release: push the bump up through the open end.
    x0 = 1.2
    for y in (YC - TONGUE_W / 2 - SLIT, YC + TONGUE_W / 2):
        s = s.cut(Part.makeBox(TONGUE_L, SLIT, thru, V(x0, y, zp - 1)))
    s = s.cut(Part.makeBox(SLIT, TONGUE_W + 2 * SLIT, thru, V(x0, YC - TONGUE_W / 2 - SLIT, zp - 1)))
    zt = back - PLATE                                                    # tongue's phone-side face
    if zt > zp + 1e-6:   # thicker plate: recess the tongue from the phone's side, so it flexes and still prints on the bed
        s = s.cut(rbox(TONGUE_L + 4, TONGUE_W + 2 * SLIT + 2, zt - zp + 0.01, 2, x0, YC - TONGUE_W / 2 - SLIT - 1, zp))
        x1 = x0 + TONGUE_L + 4                                           # 45 deg far end: the phone's edge rides out
        ramp = Part.makePolygon([V(x1, 0, zp - 0.01), V(x1 + zt - zp, 0, zp - 0.01), V(x1, 0, zt), V(x1, 0, zp - 0.01)])
        s = s.cut(Part.Face(ramp).extrude(V(0, TONGUE_W + 2 * SLIT + 2, 0)).translate(V(0, YC - TONGUE_W / 2 - SLIT - 1, 0)))
    x0, bx = x0 + SLIT, PX + 2 * PH_CLR - 0.3
    bump = Part.makePolygon([V(x0, 0, zt + 0.5), V(x0, 0, zp), V(bx, 0, zp - BUMP_H), V(bx, 0, zt + 0.5),
                             V(x0, 0, zt + 0.5)])
    s = s.fuse(Part.Face(bump).extrude(V(0, TONGUE_W, 0)).translate(V(0, YC - TONGUE_W / 2, 0)))
    # Buttons: relief grooves so sliding in doesn't press them; the side button gets a flared window.
    for y in (PY - 0.8, PY + PPD - 0.5):
        s = s.cut(Part.makeBox(PX + 63, 1.3, 4, V(-1, y, zm - 2)))
    # Volume buttons: the window's ends ramp at ~45 deg so a fingertip slides in (a straight pit was hard to reach);
    # across the wall it flares only 1.2 mm, which keeps 1.2 mm of wall at the screen face.
    s = s.cut(port(47, 5, V(PX + 38.5, -0.01, zm), V(0, 1, 0), V(1, 0, 0), PY + 0.5, 4.0, 1.2))
    s = s.cut(port(30, 6.4, V(W + 0.01, D / 2, zm), V(-1, 0, 0), V(0, 1, 0), WALL_R + 0.5, 0.6))   # Lightning + speakers
    return s


def phone_in_bay(z0):
    return rbox(PH_W, PH_D, PH_T, CORNER_R, PHONE_X, PHONE_Y, z0 + LIP_T)


def check_phone(s, z0):
    """Self-check: the phone fits the bay, is held by latch, lips and plate, and only the latch is in its way out."""
    ph = phone_in_bay(z0)
    assert ph.common(s).Volume < 0.01, "phone pocket too small"
    for dx, dz, what in [(-1.0, 0, "latch"), (0, -1.0, "lips"), (0, 1.0, "plate")]:
        assert ph.translated(V(dx, 0, dz)).common(s).Volume > 0.01, f"phone not held by {what}"
    zp = z0 + LIP_T + PH_T + RING
    latch = Part.makeBox(TONGUE_L + 1, TONGUE_W, BUMP_H + 1, V(-1, YC - TONGUE_W / 2, zp - BUMP_H))
    for dx in (20, 60, 100):
        hit = ph.translated(V(-dx, 0, 0)).common(s)
        assert hit.Volume - hit.common(latch).Volume < 0.01, f"phone snags {dx} mm out"
    return ph


def keyboard(x, y, z, face_down=False):
    """Keyboard model: housing with its key field on top (or below if face_down), housing corner at (x, y, z)."""
    kh = KB_KEYS - KB_BODY
    zb, zk = (z + kh, z) if face_down else (z, z + KB_BODY)
    return rbox(KB_W, KB_D, KB_BODY, CORNER_R, x, y, zb).fuse(
        rbox(KB_W - 2 * KB_INSET, KB_D - 2 * KB_INSET, kh, 2, x + KB_INSET, y + KB_INSET, zk))
