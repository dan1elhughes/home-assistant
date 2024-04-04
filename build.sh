#!/usr/bin/env bash

rsync -a --delete static/ dist/
npx nunjucks-cli \*\*/\*.tpl data.json -o dist -p src -e yaml -O nunjucks.json
yamllint dist

rm -r dist/macros
