#!/usr/bin/env bash

server="10.10.10.20"
config="/mnt/cephfs/homeassistant"

rsync -rvzP dist/ "$server:$config"
