#!/usr/bin/env bash

set -euo pipefail

rsync -a --delete static/ dist/

# Assemble the live unified_battery_schedule python_script from source
# fragments (pure core 10-40 + HA glue 90). The HA python_script sandbox
# forbids imports, so we concatenate rather than import.
mkdir -p dist/python_scripts
cat \
  static/python_scripts/src/unified/10_helpers.py \
  static/python_scripts/src/unified/20_dp.py \
  static/python_scripts/src/unified/30_events.py \
  static/python_scripts/src/unified/40_api.py \
  static/python_scripts/src/unified/90_glue.py \
  > dist/python_scripts/unified_battery_schedule.py

# Do not ship the raw source fragments as their own python_scripts.
rm -rf dist/python_scripts/src

npx nunjucks-cli \*\*/\*.tpl data.json -o dist -p src -e yaml -O nunjucks.json

yamllint dist

rm -r dist/macros
