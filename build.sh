#!/usr/bin/env bash

rsync -a --delete static/ dist/
nunjucks \*\*/\*.tpl data.json -o dist -p src -e yaml -O nunjucks.json
yamllint dist
