#!/usr/bin/env bash

set -euo pipefail

rsync -a --delete static/ dist/

# npm i -g nunjucks-cli
nunjucks \*\*/\*.tpl data.json -o dist -p src -e yaml -O nunjucks.json

nunjucks get-enphase-token.tpl enphase.json -o dist/scripts -p scripts -e sh -O nunjucks.json
chmod +x dist/scripts/get-enphase-token.sh

yamllint dist

rm -r dist/macros
