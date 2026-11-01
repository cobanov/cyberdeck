# Cyberdeck

Two pocket cyberdecks from a Torima M7 mini Bluetooth keyboard and an iPhone 12 mini, printed on a Creality K1:

- **Clamshell** (`cyberdeck.py`): keyboard in the base, phone in a lid that locks open at 112°.
- **Slate** (`slate.py`): one 2DS-style piece, phone on top held by MagSafe, keyboard below.

Both share the measurements and the MagSafe phone pocket in `deck.py`. Turn the models in a browser and download them
at [cyberdeck.cobanov.dev](https://cyberdeck.cobanov.dev).

![The clamshell on an oak desk](render/cyberdeck_render.png)

![The slate on an oak desk](render/slate_hero.png)

## Highlights

- **Matched footprints.** The keyboard (133 × 68 mm) and the phone (131.5 × 64.2 mm) are almost the same size. The
  clamshell closes to 138 × 81 × 24.5 mm; the slate is 138 × 141 × 13.4 mm.
- **MagSafe phone, nothing over the screen.** The phone drops screen out into an open pocket, and its own MagSafe
  magnets hold it to a steel ring sticker in a round recess in the pocket's floor. No slide, latch or frame lip. The side
  key and the Lightning end sit in slots open to the face; a groove keeps the wall off the volume buttons. A window in
  the back pushes the phone out. In the slate the screen is flush with the face, so edge swipes start on the frame; in
  the clamshell it sits 1.2 mm in, so the closed lid keeps it clear of the keys.
- **Keys at rim height.** In the clamshell the rim stands 0.3 mm above the key tops, so edge keys are easy to press.
  With it closed only the screen glass faces the keys, 1.5 mm above them. In the slate the keyboard's housing sits
  2.7 mm below the screen face and the key tops 1.2 mm below it. A notch at its USB-C port leaves room for the port.
- **Clamshell stops at 112°.** A web across the back of the lid lands flat on the base just behind the hinge pins.
  Open, the lid and phone weigh behind the axis, so gravity keeps the lid on its stop and taps on the screen push
  into it. The base ends at the hinge, with nothing sticking out behind. Pull the lid forward to close it. A slot
  behind the keyboard fits a USB-C plug to charge it in place.
- **Both hold the keyboard without glue.** It presses into a pocket 0.4 mm larger all round and stays by friction;
  a window in the back pushes it out again.
- **Made to print.** Every part prints in one piece. The lid needs supports under its two hinge knuckles only; the
  slate needs none and has no bridges: every pocket and slot opens to the face or goes through the back. Every square
  edge the pockets leave is chamfered, and the pocket's heights sit on layer lines.
- **Self-checking.** The scripts assert that the lid swings clear up to the stop, the stop engages and the lid's weight holds it open, that the
  keyboard and phone fit, that the phone rests between four walls and lifts straight out, that a 56 mm ring sticker
  fits its recess, and that the closed lid keeps the screen off the keys.

## Parts and print times

Creality K1, the `PLA @K1 cobanov` preset (Elas PLA Pro values), 0.2 mm layers, 3 walls, 20 % gyroid, no brim or skirt
(`slice_k1.sh`, OrcaSlicer estimates). Plates in print order:

| File | What | Print | Time | PLA |
|---|---|---|---|---|
| `stl/fit_keyboard.stl` | Clamshell: keyboard pocket slice | Before the base: try the keyboard's fit | 7 min | 3 g |
| `stl/base.stl` | Clamshell: keyboard tray and hinge | Floor down, no supports | 57 min | 32 g |
| `stl/lid.stl` | Clamshell: phone pocket, hinge knuckles | Plate down, tree supports under the knuckles | 1 h 4 min | 34 g |
| `stl/slate.stl` | Slate | Back down, no supports, screen face ironed | 1 h 33 min | 53 g |
| `stl/radius_gauge.stl` | Corner radius gauge, 7–11.5 mm | Flat; only for a different keyboard or phone | 31 min | 13 g |
| `stl/radius_gauge_case.stl`, `stl/radius_gauge_lid.stl` | Case for the gauge tiles, sliding lid | Upright and flat, no supports | 32 min | 15 g |

The clamshell is about 2 h 1 min and 67 g; the slate 1 h 33 min and 53 g. No part needs a brim or a skirt (the
K1 draws its own purge line). `slice_k1.sh` switches the side fan on for bridges only (it stays off otherwise, since it
blows on the bed): the old frame lips' long bridges sagged on the part fan alone.

## Hardware

- Clamshell: 2 × M3×20 socket head screws, the hinge pins. They self-tap into the inner base knuckle, no nuts.
- Both: a MagSafe steel ring sticker, about 56 mm across and 0.6 mm thick (the recess is 58 mm; set `RING_D` to yours).

## Assembly

**Phone, both builds.** Stick the ring sticker into the round recess in the phone pocket's floor. Drop the phone in
screen out, camera on the left over the camera window; the magnets pull it home. To take it out, push it up through
the window in the back at the Lightning end.

**Clamshell.** The hinge is not print-in-place. Close the lid on the base: each lid knuckle drops into the gap between two base
knuckles. From each side, drive an M3×20 through the counterbored outer knuckle and the lid knuckle into the inner
knuckle. The screw is the hinge pin, and tightening it adds friction. The lid's bore is 3.1 mm so the shank sits
snugly; if it binds, run a 3 mm drill through. Drop the keyboard into the tray.

**Slate.** Press the keyboard in keys up. To remove it, push it out through the window in the back; take it out to
charge it.

## Customizing

Measurements and fits shared by both builds are in `deck.py`; each script holds its own mechanism (`cyberdeck.py`
the hinge and how far in the screen sits, `SINK`; `slate.py` its sunken keyboard). `RING_D` and `MAG_DX`/`MAG_DY` in
`deck.py` size and place the ring. `CORNER_R` is the corner radius shared by the keyboard and the
phone: press a corner into each tile of the radius gauge, and use the one that touches along the whole arc.

Regenerate from FreeCAD's Python console (or its MCP):

```python
exec(open("/Volumes/cobanov-ssd/Workspace/3d-projects/cyberdeck/cyberdeck.py").read(), {})
exec(open("/Volumes/cobanov-ssd/Workspace/3d-projects/cyberdeck/slate.py").read(), {})
```

This rebuilds the `.FCStd` files, the STLs and the render meshes. Then `./slice_k1.sh` writes G-code to
`gcode/k1-pla/`; it refuses a file whose filament settings don't match `profiles/k1_pla_filament.json`.

## Terminal app

The phone runs [DeckTerm](https://github.com/cobanov/deckterm), a landscape SSH terminal made for this deck. It has
its own repo.

## Render

`render/scene.py` builds the scene in Blender 5.2 (Cycles): the deck on an oak desk lit by the `artist_workshop`
HDRI, with a lit terminal on the phone. It renders every shot in its `SHOTS` table unless shots are named.
`--color=white`, `mint` or `black` prints the lid or slate in that colour into `render/colors/` (the default is red;
the clamshell base stays charcoal).

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -P render/scene.py -- --render [--preview] [--slate] [--color=mint] [shot ...]
```

Assets in `render/assets/` are CC0 from Poly Haven.

## Website

`site/` is [cyberdeck.cobanov.dev](https://cyberdeck.cobanov.dev): static files on Cloudflare and a three.js viewer
that opens and closes the clamshell, in any of the four colours. `site/deploy.sh` publishes it with the STLs from the last commit, so the
downloads never carry a change still being tried.

## Status

The radius gauge and the phone bay test are printed. `CORNER_R` is 10 mm, measured on both the keyboard and the
iPhone 12 mini. The first full lid and base (2026-10-31) printed cleanly and the keyboard fits well. Two changes came
after them and are not printed yet:

- The phone stopped 1-2 mm short of the bay's closed end, so the latch bump only half caught its edge. The lid now has
  the slate's MagSafe pocket instead (see below): no slide, latch or frame lips, so nothing can stop the phone short.
- The 14 mm hinge foot behind the keyboard looked bulky. The base now ends at the hinge pins (91 → 81 mm deep) and
  the open-lock magnets are gone. The lid now lands on a 2.5 mm strip instead of 10.5 mm, so print errors move the
  open angle more: 0.1 mm moves it about 2°. The deck also tips back more easily on a desk.

Nothing holds the lid closed yet; a closing lock is still to design.

The first slate (2026-11-01) printed without supports: its frame lips sagged, the keyboard sat too deep and the
phone latch broke. The key height was remeasured (housing 9.5 mm, keys 1.5 mm proud; the clamshell base is 1 mm
thinner for it too), and the slate was redrawn: no latch, keyboard press-fit and flush, 2 mm walls, 11.6 mm thick
instead of 14.4, and a lead-in at the phone bay's mouth. That version (white, 2026-11-01) had two faults. The tree
supports under the lips couldn't be removed from inside the bay. The keyboard's housing stayed 0.5–1 mm proud and
sprang back out, as its top edge never got inside the pocket. The pocket went 1.2 mm deeper (12 mm thick), and a
one-layer skin replaced the supports. That third slate's lips came out flat, but the frame over the open end still
sagged and the keyboard still sat flush: the clamshell base has a slot at the keyboard's USB-C port, the slate had none.
The fourth got the notch, a pocket 1.5 mm deeper again (13.4 mm thick), bed-only tree supports for the open end and
chamfers. Meanwhile the third's phone worked loose after a few insertions: with no ring sticker it hung 0.6 mm loose
between frame and plate, and nothing closed the open end. So the slate dropped the slide-in bay altogether: the phone
now sits in an open pocket, held by its own MagSafe magnets to a steel ring sticker, and the slate prints with no
supports, skins or bridges. The clamshell's lid got the same pocket, and every square edge on both was chamfered.
