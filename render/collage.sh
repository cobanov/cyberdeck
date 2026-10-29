#!/bin/bash
# Social media collages: six shots per build in a 2 x 3 grid, one image per portrait aspect, into render/collage/.
# Tiles are centre crops of the 9:16 renders (Blender ... scene.py -- --render [--slate] 9:16), which leave the most
# height to crop from. Usage: render/collage.sh
H=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$H/collage"
W=2160 M=36 G=24        # canvas width, outer margin, gutter (px)
collage() {
  model=$1 aw=$2 ah=$3; shift 3
  ch=$((W * ah / aw))
  tw=$(((W - 2 * M - G) / 2)) th=$(((ch - 2 * M - 2 * G) / 3))
  in=() f=""
  for i in 0 1 2 3 4 5; do
    in+=(-i "$H/aspect/${model}_$1_9x16.png"); shift
    f+="[$i]crop=iw:iw*$th/$tw:0:(ih-iw*$th/$tw)/2,scale=$tw:$th[t$i];"
  done
  x1=$((tw + G)) y1=$((th + G)) y2=$((2 * (th + G)))
  f+="[t0][t1][t2][t3][t4][t5]xstack=inputs=6:layout=0_0|${x1}_0|0_${y1}|${x1}_${y1}|0_${y2}|${x1}_${y2}:fill=0x101012,"
  f+="pad=$W:$ch:$M:$M:color=0x101012"
  ffmpeg -loglevel error -y "${in[@]}" -filter_complex "$f" -q:v 2 "$H/collage/${model}_${aw}x${ah}.jpg" &&
    echo "collage/${model}_${aw}x${ah}.jpg ${W}x${ch}"
}
for a in "2 3" "3 4" "9 16"; do
  collage cyberdeck $a render front closed back profile slot
  collage slate $a hero top angle back profile slot
done
