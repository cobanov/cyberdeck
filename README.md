# Cyberdeck

A pocket clamshell cyberdeck: a Torima M7 mini Bluetooth keyboard in the base, an iPhone 12 mini as the screen
in the lid. One parametric FreeCAD script, printed on a Creality K1.

![The deck on an oak desk](render/cyberdeck_render.png)

## Highlights

- **Matched footprints.** The keyboard (133 × 68 mm) and the phone (131.5 × 64.2 mm) are almost the same size,
  so the deck closes to 138 × 91 × 26 mm.
- **Slide-in phone, one-piece frame.** The phone slides in from the left between the back plate and a lip that
  runs all the way round the screen. A flexing tongue in the plate clicks in behind it, and the camera bump runs in
  its own channel. The side button has a flared window; grooves keep the buttons from being pressed as it slides.
- **Locks at 112°.** A web across the back of the lid lands flat on the rear foot, and three pairs of magnets snap
  it there: no wobble, and taps on the screen push into the stop. Pull the lid forward to close it. The foot also
  keeps the deck from tipping backwards.
- **Charge in place.** A channel through the rear foot fits a USB-C plug for the keyboard's back-edge port.
- **Self-checking.** The script asserts that the lid swings clear from 0° to the stop, that the stop engages, and
  that the keyboard and phone fit their pockets and are held by the latch, lips and plate.

## Parts

| File | What | Print |
|---|---|---|
| `stl/base.stl` | Keyboard tray, hinge foot | Floor down, no supports |
| `stl/lid.stl` | Phone rails, latch | Plate down, supports under the two hinge knuckles. PETG suits the latch tongue |
| `stl/fit_keyboard.stl` | 3 mm slice of the keyboard pocket | Print first, check the fit |
| `stl/fit_phone.stl` | Left 35 mm of the lid: rails, lips, latch | Print first, check the slide and click |
| `stl/radius_gauge.stl` | Corner radius gauge, 7–11.5 mm | Find `CORNER_R` |

## Hardware

- 2 × M3×20 socket head screws: the hinge pins. They self-tap into the inner base knuckle, no nuts.
- 6 × 8×1 mm disc magnets for the open lock (3 pairs; 2 pairs also work).
- Optional MagSafe steel ring sticker behind the phone. Without it, set `RING = 0`.

## Assembly

Glue the magnets in first: three in the lid's back web and three in the foot. Stack each pair so they attract and
mark the faces that touch, then glue them in with CA glue, marked faces out.

The hinge is not print-in-place. Close the lid on the base: each lid knuckle drops into the gap between two base
knuckles. The lid's bore is 3.1 mm so the screw shank sits snugly in it; if it binds, run a 3 mm drill through. From each side, drive an M3×20 through the counterbored outer knuckle and the lid knuckle into the
inner knuckle. The screw is the hinge pin, and tightening it adds friction. Drop the keyboard into the tray, then
slide the phone in from the left until the latch clicks. To release it, press the latch bump down at the open end.

## Customizing

All dimensions are at the top of `cyberdeck.py`. `CORNER_R` is the corner radius shared by the keyboard and the
phone: press a corner into each tile of the radius gauge, and use the one that touches along the whole arc.
`KB_CUTOUTS` places slots for the keyboard's ports.

Regenerate everything from FreeCAD's Python console (or its MCP):

```python
exec(open("/Volumes/cobanov-ssd/Workspace/cyberdeck/cyberdeck.py").read(), {})
```

This rebuilds `cyberdeck.FCStd`, the STLs and the render meshes in `render/`.

## Render

`render/scene.py` builds the scene in Blender 5.2 (Cycles): the deck on an oak desk lit by the `artist_workshop`
HDRI, with a lit terminal on the phone.

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -P render/scene.py -- --render [--preview]
```

Assets in `render/assets/` are CC0 from Poly Haven.

## Status

Not printed yet. `CORNER_R` is an 11.5 mm estimate until it is measured with the gauge. If the keyboard or phone
binds at the corners of the fit tests, lower it.
