# Cyberdeck render scene, built from the FreeCAD meshes and dims.json in this folder.
# Room: oak desk + artist_workshop HDRI (CC0, Poly Haven, in assets/), same as the handheld-stand renders.
# Live Blender:  exec(open("/Volumes/cobanov-ssd/Workspace/cyberdeck/render/scene.py").read(), {})
# Render:        Blender -b -P scene.py -- --render [--preview] [--slate] [shot ...]   (default: every shot in SHOTS)
#                --slate renders the one-piece handheld from slate/ instead of the clamshell.
import bpy, bmesh, json, math, os, sys
from mathutils import Matrix, Vector

DIR = "/Volumes/cobanov-ssd/Workspace/cyberdeck/render"
S = 0.001                                    # FreeCAD mm -> Blender m
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODEL = "slate" if "--slate" in ARGS else "cyberdeck"
MD = os.path.join(DIR, "slate") if MODEL == "slate" else DIR   # meshes + dims.json; the slate is built face down
C = json.load(open(os.path.join(MD, "dims.json")))
PREVIEW = "--preview" in ARGS
# An aspect like 9:16 renders portrait frames into aspect/: same horizontal view as the 3:2 shots, zoomed in a little,
# so the taller frame adds room and desk instead of cropping the deck.
ASPECT = next((tuple(map(int, a.split(":"))) for a in ARGS if ":" in a), None)
ZOOM = {"profile": 1.5 if MODEL == "cyberdeck" else 1.0, "slot": 1.0}   # per shot in portrait frames, default 1.2
# name: camera azimuth (from +X towards +Y; the deck faces -Y) and elevation in degrees, distance in metres,
# focus target in mm, lens mm, f-stop, lid angle (None = open to the stop)
SHOTS = {
    "hero":    (245, 16, 0.46, (69, 60, 30), 60, 11, None),
    "front":   (268, 20, 0.52, (69, 45, 40), 70, 11, None),
    "profile": (182, 6, 0.50, (69, 60, 35), 70, 11, None),
    "back":    (62, 24, 0.40, (69, 82, 22), 60, 8, None),
    "closed":  (232, 32, 0.44, (69, 45, 14), 60, 11, 0),
    "slot":    (200, 16, 0.26, (0, 96, 50), 85, 5.6, None),   # phone slot at the open lid's left end
} if MODEL == "cyberdeck" else {
    "hero":    (244, 34, 0.40, (69, 73, 7), 60, 11, None),
    "top":     (270, 72, 0.52, (69, 73, 8), 60, 11, None),
    "profile": (200, 10, 0.40, (69, 73, 7), 70, 11, None),
    "back":    (60, 32, 0.50, (69, 73, 7), 60, 11, 0),             # flipped face down
    "angle":   (300, 26, 0.40, (69, 73, 7), 60, 11, None),
    "slot":    (196, 18, 0.24, (0, 108, 9), 85, 5.6, None),
}
HDRI_ROT = 260                              # stand renders' 110 deg, turned to this camera's heading


def mm(x, y, z):
    return Vector((x, y, z)) * S


for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.lights,
             bpy.data.cameras, bpy.data.images, bpy.data.worlds):
    for b in list(coll):
        if b.users == 0:
            coll.remove(b)
scene = bpy.context.scene
col = scene.collection
try:
    FONT = bpy.data.fonts.load("/System/Library/Fonts/Menlo.ttc", check_existing=True)
except RuntimeError:
    FONT = bpy.data.fonts.load("/System/Library/Fonts/Monaco.ttf", check_existing=True)


def material(name, color, rough=0.5, metal=0.0, emit=None, strength=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    if m.node_tree is None:
        m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    p.inputs["Coat Weight"].default_value = coat
    if emit:
        p.inputs["Emission Color"].default_value = (*emit, 1)
        p.inputs["Emission Strength"].default_value = strength
    return m


def bump(m, height_node_fn, strength, distance):
    nt = m.node_tree
    p = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = distance
    nt.links.new(height_node_fn(nt), b.inputs["Height"])
    nt.links.new(b.outputs["Normal"], p.inputs["Normal"])


def layer_lines(nt, layer=0.2):
    # FDM layer lines: bands along object Z (both parts print with Z as their layer axis).
    tc = nt.nodes.new("ShaderNodeTexCoord")
    w = nt.nodes.new("ShaderNodeTexWave")
    w.wave_type, w.bands_direction = "BANDS", "Z"
    w.inputs["Scale"].default_value = 2 * math.pi / (20 * layer * S)
    nt.links.new(tc.outputs["Object"], w.inputs["Vector"])
    return w.outputs["Fac"]


def link(o, mat=None):
    col.objects.link(o)
    if mat:
        o.data.materials.append(mat)
    return o


def stl(name, mat, bevel=0.0):
    bpy.ops.wm.stl_import(filepath=os.path.join(MD, name + ".stl"))
    o = bpy.context.view_layer.objects.active
    o.name = name
    o.data.transform(Matrix.Scale(S, 4))   # bake mm->m into the mesh so bevel and texture scales are in metres
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bm.to_mesh(o.data)
    bm.free()
    o.data.shade_smooth()
    o.data.set_sharp_from_angle(angle=math.radians(30))
    if bevel:
        b = o.modifiers.new("Bevel", "BEVEL")
        b.width, b.segments, b.limit_method, b.angle_limit = bevel * S, 3, "ANGLE", math.radians(40)
    o.data.materials.append(mat)
    return o


def rounded_box(name, w, d, h, r, segments=3):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * w, v.co.y * d, v.co.z * h)) * S
    bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges), offset=r * S, segments=segments,
                    affect="EDGES", profile=0.5)
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def rounded_rect(name, w, d, r):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    for v in bm.verts:
        v.co = Vector((v.co.x * w, v.co.y * d, 0)) * S       # grid size=0.5 spans +-0.5
    bmesh.ops.bevel(bm, geom=list(bm.verts), offset=r * S, segments=8, affect="VERTICES")
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def text(body, size, loc, mat, rot=(0, 0, 0), align="CENTER"):
    cu = bpy.data.curves.new("txt", "FONT")
    cu.body, cu.font, cu.size = body, FONT, size * S
    cu.align_x, cu.align_y = align, ("CENTER" if align == "CENTER" else "TOP")
    o = link(bpy.data.objects.new("txt", cu), mat)
    o.location, o.rotation_euler = loc, rot
    return o


# --- materials ---
pla = material("PLA charcoal", (0.035, 0.036, 0.04), rough=0.55)
bump(pla, layer_lines, 0.18, 0.00003)
ruby = material("PLA ruby red", (0.40, 0.008, 0.02), rough=0.32)
bump(ruby, layer_lines, 0.18, 0.00003)
kb_plastic = material("Keyboard body", (0.02, 0.02, 0.022), rough=0.75)
key_rim = material("Key rim", (0.55, 0.56, 0.58), rough=0.5)
key_top = material("Key top", (0.012, 0.012, 0.014), rough=0.8)
legend = material("Legend", (0.85, 0.86, 0.88), rough=0.6)
phone_body = material("iPhone black", (0.015, 0.016, 0.02), rough=0.25, metal=0.6)
steel = material("Black oxide", (0.05, 0.05, 0.055), rough=0.35, metal=1.0)
screen = material("Screen", (0.0, 0.0, 0.0), rough=0.03, emit=(0.012, 0.016, 0.024), strength=1.0)
next(n for n in screen.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Specular IOR Level"].default_value = 0.2   # AR-coated glass
notch = material("Notch", (0.0, 0.0, 0.0), rough=0.45)
TERM = {k: material("Term " + k, (0, 0, 0), rough=1.0, emit=c, strength=4.0) for k, c in {
    "green": (0.25, 1.0, 0.45), "white": (0.85, 0.88, 0.92), "gray": (0.45, 0.5, 0.56), "orange": (1.0, 0.45, 0.15)}.items()}

# --- oak desk in a real room: same CC0 Poly Haven assets as the handheld-stand renders ---
ASSETS = os.path.join(DIR, "assets")
bpy.ops.mesh.primitive_plane_add(size=1, location=(0.07, 0.15, 0))
desk = bpy.context.view_layer.objects.active
desk.name, desk.scale = "Desk", (1.6, 1.0, 1)
oak = material("Oak", (0.5, 0.4, 0.3))
nt = oak.node_tree
p = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
uv = nt.nodes.new("ShaderNodeTexCoord")
mp = nt.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (1.6, 1.0, 1)        # texture tile = 1 m
nt.links.new(uv.outputs["UV"], mp.inputs["Vector"])


def oak_tex(name, colorspace):
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(os.path.join(ASSETS, name), check_existing=True)
    t.image.colorspace_settings.name = colorspace
    nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
    return t.outputs["Color"]


nt.links.new(oak_tex("oak_veneer_01_diff_2k.jpg", "sRGB"), p.inputs["Base Color"])
nt.links.new(oak_tex("oak_veneer_01_rough_2k.jpg", "Non-Color"), p.inputs["Roughness"])
nm = nt.nodes.new("ShaderNodeNormalMap")
nt.links.new(oak_tex("oak_veneer_01_nor_gl_2k.jpg", "Non-Color"), nm.inputs["Color"])
nt.links.new(nm.outputs["Normal"], p.inputs["Normal"])
desk.data.materials.append(oak)

# --- base, keyboard, screws ---
if MODEL == "cyberdeck":
    stl("base", pla, bevel=0.35)
before = set(bpy.data.objects)
stl("kb_body", kb_plastic, bevel=0.6)
KX, KY, KZ = C["WALL"] + C["KB_CLR"], C["WALL"] + C["KB_CLR"], C["FLOOR"] + C["KB_BODY"]
CAP_H = C["KB_KEYS"] - C["KB_BODY"]
MARGIN = 3.0
PX_, PY_ = (C["KB_W"] - 2 * MARGIN) / 13, (C["KB_D"] - 2 * MARGIN) / 6
ROWS = [
    [("Esc", 1)] + [(f"F{i}", 1) for i in range(1, 13)],
    [('"', 1)] + [(c, 1) for c in "1234567890*"] + [("Back", 1)],
    [("Tab", 1)] + [(c, 1) for c in "QWERTYUIOPĞÜ"],
    [("Caps", 1)] + [(c, 1) for c in "ASDFGHJKLŞİ"] + [("Enter", 1)],
    [("Shift", 1)] + [(c, 1) for c in "ZXCVBNMÖÇ."] + [("↑", 1), ("End", 1)],
    [("Fn", 1), ("Ctrl", 1), ("Alt", 1), ("", 4), ("AltGr", 1), ("Cmd", 1), ("Home", 1), ("←", 1), ("↓", 1), ("→", 1)],
]
meshes = {}
for r, row in enumerate(ROWS):
    cy = KY + C["KB_D"] - MARGIN - (r + 0.5) * PY_
    col_i = 0
    for label, units in row:
        w = units * PX_ - 1.3
        d = PY_ - 1.5
        cx = KX + MARGIN + (col_i + units / 2) * PX_
        col_i += units
        if units not in meshes:
            meshes[units] = (rounded_box("cap", w, d, CAP_H, 0.6), rounded_box("top", w - 1.4, d - 1.4, 0.2, 0.3))
        cap = link(bpy.data.objects.new("key", meshes[units][0]), key_rim)
        cap.location = mm(cx, cy, KZ + CAP_H / 2)
        top = link(bpy.data.objects.new("keytop", meshes[units][1]), key_top)
        top.location = mm(cx, cy, KZ + CAP_H - 0.05)
        if label:
            size = 3.4 if len(label) == 1 else (2.4 if len(label) <= 3 else 1.9)
            text(label, size, mm(cx, cy, KZ + CAP_H + 0.06), legend)
kb_parts = [o for o in bpy.data.objects if o not in before]
for x0, x1 in [(0.5, 3.5), (C["W"] - 3.5, C["W"] - 0.5)] if MODEL == "cyberdeck" else []:
    bpy.ops.mesh.primitive_cylinder_add(radius=2.75 * S, depth=(x1 - x0) * S, vertices=32,
                                        location=mm((x0 + x1) / 2, C["YA"], C["ZA"]), rotation=(0, math.pi / 2, 0))
    bpy.context.view_layer.objects.active.data.materials.append(steel)

# --- lid group, modelled closed then swung open on the hinge ---
hinge = bpy.data.objects.new("Hinge", None)
col.objects.link(hinge)
hinge.location = mm(0, C["YA"], C["ZA"])
bpy.context.view_layer.update()
lid_parts = [stl("lid" if MODEL == "cyberdeck" else "slate", ruby, bevel=0.35), stl("phone", phone_body, bevel=0.0)]

SW, SD = 124.9, 57.6                                 # iPhone 12 mini active area
pcx, pcy = C["PHONE_X"] + C["PH_W"] / 2, C["PHONE_Y"] + C["PH_D"] / 2
sz = C["HB"] + C["LIP_T"] - 0.03                     # screen faces -Z while closed
FLIP = (math.pi, 0, 0)
scr = link(bpy.data.objects.new("Screen", rounded_rect("screen", SW, SD, 6.0)), screen)
scr.location, scr.rotation_euler = mm(pcx, pcy, sz), FLIP
nt = link(bpy.data.objects.new("Notch", rounded_box("notch", 5.6, 34.8, 0.1, 0.04, 2)), notch)
nt.location = mm(pcx - SW / 2 + 2.8, pcy, sz - 0.06)
lid_parts += [scr, nt]

LINES = [
    [("cobanov@cyberdeck ~ % ", "green"), ("ssh nuc", "white")],
    [("Welcome to Ubuntu 24.04.3 LTS", "gray")],
    [("cobanov@nuc:~$ ", "green"), ("uptime", "white")],
    [(" 01:42:10 up 42 days,  3:17,  1 user,  load average: 0.21, 0.18, 0.15", "gray")],
    [("cobanov@nuc:~$ ", "green"), ('docker ps --format "{{.Names}}\\t{{.Status}}"', "white")],
    [("watchdock      Up 12 days (healthy)", "gray")],
    [("grafana        Up 12 days", "gray")],
    [("prometheus     Up 12 days", "gray")],
    [("caddy          Up 30 days", "gray")],
    [("cobanov@nuc:~$ ", "green"), ("claude", "white")],
    [("* Welcome to Claude Code!", "orange")],
    [("> ", "orange"), ("build me a cyberdeck", "white"), ("█", "gray")],
]
layers = {k: [] for k in TERM}
for line in LINES:
    for k in layers:
        layers[k].append("".join(t if c == k else " " * len(t) for t, c in line))
tx, ty = pcx - SW / 2 + 8.5, pcy - SD / 2 + 3.5
for k, rows in layers.items():
    o = text("\n".join(rows).rstrip(), 3.5, mm(tx, ty, sz - 0.05), TERM[k], rot=FLIP, align="LEFT")
    lid_parts.append(o)

for o in lid_parts:
    o.parent = hinge
    o.matrix_parent_inverse = hinge.matrix_world.inverted()
hinge.rotation_euler = (math.radians(-C["OPEN"]), 0, 0)
if MODEL == "slate":   # the keyboard sits in the slate: it follows the body when a shot flips it face down
    bpy.context.view_layer.update()
    for o in kb_parts:
        o.parent = hinge
        o.matrix_parent_inverse = hinge.matrix_world.inverted()

# --- room light (HDRI only, like the stand renders), camera ---
world = bpy.data.worlds.new("Workshop")
scene.world = world
if world.node_tree is None:
    world.use_nodes = True
wt = world.node_tree
bg = next(n for n in wt.nodes if n.type == "BACKGROUND")
env = wt.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(os.path.join(ASSETS, "artist_workshop_2k.hdr"), check_existing=True)
wmap = wt.nodes.new("ShaderNodeMapping")
wmap.inputs["Rotation"].default_value[2] = math.radians(HDRI_ROT)
wt.links.new(wt.nodes.new("ShaderNodeTexCoord").outputs["Generated"], wmap.inputs["Vector"])
wt.links.new(wmap.outputs["Vector"], env.inputs["Vector"])
wt.links.new(env.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0

target = bpy.data.objects.new("Target", None)       # focus point: hinge line, mid-width
col.objects.link(target)
cam_data = bpy.data.cameras.new("Camera")
cam_data.dof.use_dof = True
cam_data.dof.focus_object = target
cam = link(bpy.data.objects.new("Camera", cam_data))
scene.camera = cam


def shot(name):
    az, el, dist, tgt, lens, fstop, lid = SHOTS[name]
    az, el = math.radians(az), math.radians(el)
    target.location = mm(*tgt)
    cam_data.lens, cam_data.dof.aperture_fstop = lens * (ZOOM.get(name, 1.2) if ASPECT else 1.0), fstop
    cam.location = target.location + dist * Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
    cam.rotation_euler = (target.location - cam.location).to_track_quat("-Z", "Y").to_euler()
    hinge.rotation_euler = (math.radians(-(C["OPEN"] if lid is None else lid)), 0, 0)


shot("hero")

# --- render settings ---
scene.render.engine = "CYCLES"
scene.cycles.device = "GPU"
scene.cycles.samples = 48 if PREVIEW else 384
scene.cycles.use_denoising = True
LONG = 960 if PREVIEW else 2400
aw, ah = ASPECT or (3, 2)
scene.render.resolution_x, scene.render.resolution_y = (LONG, round(LONG * ah / aw)) if aw >= ah else (round(LONG * aw / ah), LONG)
cam_data.sensor_fit = "HORIZONTAL"
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = "AgX"
scene.view_settings.exposure = 0.6
for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
    try:
        scene.view_settings.look = look
        break
    except TypeError:
        pass

if bpy.app.background and "--render" in ARGS:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.refresh_devices()
    for dev in prefs.devices:
        dev.use = True
    for name in [a for a in ARGS if a in SHOTS] or list(SHOTS):
        shot(name)
        out = "cyberdeck_render.png" if (MODEL, name) == ("cyberdeck", "hero") else f"{MODEL}_{name}.png"
        if ASPECT:
            out = os.path.join("aspect", out.replace(".png", f"_{aw}x{ah}.png"))
        scene.render.filepath = os.path.join(DIR, ("preview_" + out) if PREVIEW else out)
        bpy.ops.render.render(write_still=True)
print("scene ready:", len(bpy.data.objects), "objects")
