#!/usr/bin/env bash

set -euo pipefail

rsync -a --delete static/ dist/

# npm i -g nunjucks-cli
nunjucks \*\*/\*.tpl data.json -o dist -p src -e yaml -O nunjucks.json

yamllint dist

rm -r dist/macros
