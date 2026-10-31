#!/bin/sh
# Publish cyberdeck.cobanov.dev. The models come from the last commit, not the working tree,
# so a design still being tried out never reaches the download links.
set -e
cd "$(dirname "$0")"
rm -rf public/models && mkdir -p public/models
git -C .. archive HEAD stl render/dims.json render/base.stl render/lid.stl render/phone.stl render/kb_body.stl \
  | tar -x -C public/models
wrangler deploy
