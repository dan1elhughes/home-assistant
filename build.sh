#!/usr/bin/env bash

rsync -a --delete static/ dist/
rsync -a local/ dist/
nunjucks \*\*/\*.tpl data.json -o dist -p src -e yaml
