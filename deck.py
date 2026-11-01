# Shared by cyberdeck.py (clamshell) and slate.py (one-piece handheld): measured parts, fits, and the phone pocket.
# Not run on its own; each script loads it with exec(open(os.path.join(DIR, "deck.py")).read(), globals()).
# Frame: x = width (left->right), y = the phone's top edge -> bottom edge, z = screen face -> back (screen faces -z).
import math
import FreeCAD as App, Part
from FreeCAD import Vector as V

# --- measured / spec (mm) ---
KB_W, KB_D = 133.0, 68.0
KB_BODY = 9.5            # plastic housing
KB_KEYS = 11.0           # housing + membrane keys: they stand 1.5 mm proud (measured; 12.0 was a guess)
KB_INSET = 3.0           # key field starts this far in from the housing edge (retainers grip the band outside it)
# Keyboard port/switch slots: (side, mm from keyboard's left edge (front/back) or front edge (left/right), width)
KB_CUTOUTS = [("back", 28 - 7.5, 15)]   # USB-C on the back edge, centred ~28 mm from the left; slot fits the plug overmould
PH_W, PH_D, PH_T = 131.5, 64.2, 7.4   # iPhone 12 mini, Apple spec
PH_SCREEN = 124.9, 57.6  # its active area: 2340 x 1080 px at 476 ppi, so a 3.3 mm black border all round
CORNER_R = 10.0          # keyboard and iPhone 12 mini share this corner radius, both measured with stl/radius_gauge.stl
                         # too large binds the corners once it exceeds the real radius by ~1 mm; too small only leaves gaps

# --- fit ---
KB_CLR, PH_CLR = 0.4, 0.5
WALL, FLOOR, PLATE = 2.0, 2.0, 2.0
KEY_GAP = 0.3            # rim above key tops: edge keys stay easy to press
RING = 0.6               # MagSafe steel ring sticker behind the phone, in a recess in the pocket's floor
EDGE_R = 1.0             # outer edges
LAYER = 0.2              # print layer height: the phone pocket's heights sit on layer lines


# --- the phone drops in face up; its own MagSafe magnets hold it to the ring sticker ---
# Until 2026-11-01 it slid in from the left under a frame lip, and a flexing tongue latched it (clamshell) or nothing did
# (slate). The slate's phone loosened once its print burrs wore off, and the frame lips needed bridges, skins or supports.
RING_D = 58.0            # ring recess diameter: common stickers are 56 mm across; measure yours
MAG_DX, MAG_DY = 0.0, 0.0   # ring centre from the phone's centre (the Apple logo); stick the ring on the phone, where its
                            # magnets centre it, and measure if it sits off-centre
CHAMFER = 0.6            # every convex square edge the pocket leaves: rims, slots, windows
CHAMFER_THIN = 0.3       # where there's no room for CHAMFER: the ring recess, the volume-button groove, the camera
                         # window's rim (0.6 mm from the pocket's corner), and the Lightning slot's sloped ends

PW, PD = KB_W + 2 * KB_CLR, KB_D + 2 * KB_CLR
W, D = PW + 2 * WALL, PD + 2 * WALL                 # footprint: the keyboard's, the phone pocket shares it
R_OUT = CORNER_R + KB_CLR + WALL                    # outer corners concentric with the keyboard and phone
PH_R = CORNER_R + PH_CLR
PPW, PPD = PH_W + 2 * PH_CLR, PH_D + 2 * PH_CLR
PX, PY = (W - PPW) / 2, (D - PPD) / 2                  # phone pocket, centred (slate.py moves it)
PHONE_X, PHONE_Y = PX + PH_CLR, PY + PH_CLR


def rbox(w, d, h, r, x=0, y=0, z=0, r_back=None):
    """Box with rounded vertical edges; the two back (max y) edges get r_back if given."""
    b = Part.makeBox(w, d, h, V(x, y, z))
    vert = lambda s: [e for e in s.Edges if e.BoundBox.XLength < 1e-6 and e.BoundBox.YLength < 1e-6]
    if r_back is None:
        return b.makeFillet(r, vert(b)) if r > 0 else b
    is_back = lambda e: abs(e.BoundBox.YMin - (y + d)) < 1e-6
    b = b.makeFillet(r, [e for e in vert(b) if not is_back(e)])
    return b.makeFillet(r_back, [e for e in vert(b) if is_back(e)])


def camera_window(z, h, grow=0.0):
    """The plate's window over the camera bump, as a solid from z to z + h, `grow` larger all round."""
    return rbox(PX + 35 - PHONE_X - 1 + 2 * grow, 30 + 2 * grow, h, 6 + grow, PHONE_X + 1 - grow, PY + 2 - grow, z)



def ring_centre():
    return PHONE_X + PH_W / 2 + MAG_DX, PHONE_Y + PH_D / 2 + MAG_DY


def notch(c, length, z0, depth, y0, y1, across_x=True):
    """Open slot down from the face at z0, `length` long at its floor `depth` below the face, its ends rising at 45 deg
    to the face, through y0..y1 (or x0..x1 with across_x=False, centred at c on y)."""
    e = depth + 1
    pts = [(c - length / 2 - e, z0 - 1), (c - length / 2, z0 + depth), (c + length / 2, z0 + depth),
           (c + length / 2 + e, z0 - 1)]
    if across_x:
        return Part.Face(Part.makePolygon([V(a, y0, z) for a, z in pts + pts[:1]])).extrude(V(0, y1 - y0, 0))
    return Part.Face(Part.makePolygon([V(y0, a, z) for a, z in pts + pts[:1]])).extrude(V(y1 - y0, 0, 0))


def phone_pocket(s, z0, back, sink=0.0):
    """Cut the drop-in phone pocket into s: face at z0, the screen `sink` below it, the back face at `back`.
    Landscape, camera end on the left (x=0), y=0 the phone's top edge (side key)."""
    zf = z0 + sink + PH_T                                                    # floor: the phone's back rests here
    zm = zf - PH_T / 2                                                       # buttons and Lightning sit mid-edge
    thru = back - zf + 2
    mx, my = ring_centre()
    s = s.cut(rbox(PPW, PPD, zf - z0 + 1, PH_R, PX, PY, z0 - 1))
    s = s.cut(Part.makeCylinder(RING_D / 2, RING + 1, V(mx, my, zf - 1)))   # MagSafe ring recess
    s = s.cut(camera_window(zf - 1, thru))
    s = s.cut(rbox(22, 30, thru, 5, PHONE_X + PH_W - 29, my - 15, zf - 1))  # push the phone out here
    s = s.cut(notch(PHONE_X + 37.5, 25, z0, zm + 2 - z0, -1, PY + 0.5))      # side key, top edge
    s = s.cut(Part.makeBox(53, 1.3, 4, V(PHONE_X + 8, PY + PPD - 0.5, zm - 2)))   # volume buttons' relief
    # Lightning and speakers: down to the floor; 26 long there so its 45 deg ends reach the face before the corners
    return s.cut(notch(my, 26, z0, zf - z0, PX + PPW - 0.5, W + 1, across_x=False))


def check_pocket(s, z0, sink=0.0):
    """Self-check: the phone fits, rests on the floor between four walls, lifts straight out, and a 56 mm ring sticker
    fits its recess under the phone. Returns the phone."""
    zf = z0 + sink + PH_T
    ph = rbox(PH_W, PH_D, PH_T, CORNER_R, PHONE_X, PHONE_Y, z0 + sink)
    assert ph.common(s).Volume < 0.01, "phone pocket too small"
    for v, what in ((V(0, 0, 0.5), "floor"), (V(-1, 0, 0), "left wall"), (V(1, 0, 0), "right wall"),
                    (V(0, -1, 0), "top wall"), (V(0, 1, 0), "bottom wall")):
        assert ph.translated(v).common(s).Volume > 0.01, f"phone not held by the {what}"
    assert rbox(PH_W, PH_D, zf - z0 + PH_T + 1, CORNER_R, PHONE_X, PHONE_Y, z0 - PH_T - 1).common(s).Volume < 0.01, \
        "something overhangs the phone: it can't lift straight out"
    sticker = Part.makeCylinder(28, RING, V(*ring_centre(), zf))
    assert sticker.common(s).Volume < 0.01 and sticker.cut(ph.translated(V(0, 0, 1))).Volume < 0.01, \
        "ring sticker doesn't fit its recess under the phone"
    return ph


def mid(e):
    return e.valueAt((e.FirstParameter + e.LastParameter) / 2)


def sharp(s, e):
    """A convex edge whose two faces meet at 75 deg or sharper (outer edges are filleted, so they meet smoothly).
    Concave ones are left alone: chamfering them would fill the pockets' inside corners."""
    f = s.ancestorsOfType(e, Part.Face)
    if len(f) != 2:
        return False
    p = mid(e)
    n = [g.normalAt(*g.Surface.parameter(p)) for g in f]
    return n[0].getAngle(n[1]) > math.radians(75) and not s.isInside(p + (n[0] - n[1]) * 0.05, 1e-4, True)


def pocket_thin(p, zf):
    """Edges near point p that phone_pocket (floor at zf) leaves too little room for CHAMFER."""
    mx, my = ring_centre()
    ring = abs(math.hypot(p.x - mx, p.y - my) - RING_D / 2) < 0.1 and abs(p.z - zf) < 0.1
    groove = PY + PPD - 0.6 < p.y < PY + PPD + 0.9 and abs(p.z - (zf - PH_T / 2)) < 2.1
    camera = abs(p.z - zf) < 0.1 and p.x < PHONE_X + 36 and p.y < PHONE_Y + 33
    lightning = p.x > PX + PPW - 0.1 and abs(p.y - my) > 13.1 and p.z < zf - 0.1   # its 45 deg ends: 0.6 fails in the lid
    return ring or groove or camera or lightning


def chamfer_sharp(s, thin):
    """Chamfer every convex square edge of s: CHAMFER, or CHAMFER_THIN where thin(point) says there's no room."""
    for r, t in ((CHAMFER, False), (CHAMFER_THIN, True)):
        es = [e for e in s.Edges if thin(mid(e)) == t and sharp(s, e)]
        if es:
            s = s.makeChamfer(r, es).removeSplitter()
    return s


def keyboard(x, y, z, face_down=False):
    """Keyboard model: housing with its key field on top (or below if face_down), housing corner at (x, y, z)."""
    kh = KB_KEYS - KB_BODY
    zb, zk = (z + kh, z) if face_down else (z, z + KB_BODY)
    return rbox(KB_W, KB_D, KB_BODY, CORNER_R, x, y, zb).fuse(
        rbox(KB_W - 2 * KB_INSET, KB_D - 2 * KB_INSET, kh, 2, x + KB_INSET, y + KB_INSET, zk))
