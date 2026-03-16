#!/usr/bin/env bash

set -euo pipefail

rsync -a --delete static/ dist/

npx nunjucks-cli \*\*/\*.tpl data.json -o dist -p src -e yaml -O nunjucks.json

npx nunjucks-cli \*.tpl enphase.json -o dist/scripts -p scripts -e sh -O nunjucks.json
chmod +x dist/scripts/*.sh

yamllint dist

rm -r dist/macros
