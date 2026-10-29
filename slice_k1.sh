#!/bin/bash
# Slice the printable parts (clamshell, slate, fit tests, radius gauge and its case) for a Creality K1 with generic PLA into gcode/k1-pla/.
# Profiles (inherits resolved, so the CLI can't fill gaps with its own defaults): profiles/k1_pla_filament.json
# (the PLA @K1 cobanov preset, copied from the vault's 3d-print/profiles/cli/pla_k1_cobanov.json),
# profiles/k1_base_process.json (no supports), profiles/k1_lid_process.json (tree supports under the hinge knuckles).
H=$(cd "$(dirname "$0")" && pwd)
P=/Applications/OrcaSlicer.app/Contents/Resources/profiles/Creality
O=/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer
mkdir -p "$H/gcode/k1-pla"
sl() {
  out=$1 proc=$2; shift 2
  t=$(mktemp -d)
  "$O" --load-settings "$P/machine/Creality K1 (0.4 nozzle).json;$H/profiles/k1_${proc}_process.json" \
       --load-filaments "$H/profiles/k1_pla_filament.json" \
       --arrange 1 --slice 0 --outputdir "$t" "$@" > "$t/log.txt" 2>&1
  [ -f "$t/plate_2.gcode" ] && { echo "$out: parts don't fit one plate"; exit 1; }
  if [ -f "$t/plate_1.gcode" ]; then
    f="$H/gcode/k1-pla/$out"; mv "$t/plate_1.gcode" "$f"
    for k in nozzle_temperature nozzle_temperature_initial_layer fan_min_speed additional_cooling_fan_speed filament_flow_ratio \
             pressure_advance filament_max_volumetric_speed filament_density cool_plate_temp_initial_layer; do
      want=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]][0])" "$H/profiles/k1_pla_filament.json" $k)
      grep -q "^; $k = $want\$" "$f" || { echo "$out: $k is not $want"; exit 1; }
    done
    echo "$out | $(grep -m1 'estimated printing time (normal mode)' "$f" | sed 's/.*= //') | $(grep -m1 '^; filament used \[g\]' "$f" | sed 's/.*= //') g"
    rm -rf "$t"   # kept when slicing fails: its log.txt says why
  else
    echo "$out FAILED"; tail -3 "$t/log.txt"
  fi
}
sl base_PLA.gcode base "$H/stl/base.stl"
sl lid_PLA.gcode lid "$H/stl/lid.stl"
# First plate: radius gauge and the phone bay test (supports only under fit_phone's hinge knuckle).
sl fit-phone-gauge_PLA.gcode lid "$H/stl/radius_gauge.stl" "$H/stl/fit_phone.stl"
sl fit-keyboards_PLA.gcode base "$H/stl/fit_keyboard.stl" "$H/stl/fit_slate_keyboard.stl"
sl radius-gauge-case_PLA.gcode base "$H/stl/radius_gauge_case.stl" "$H/stl/radius_gauge_lid.stl"
sl slate_PLA.gcode base "$H/stl/slate.stl"
