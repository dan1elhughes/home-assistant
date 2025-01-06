#!/usr/bin/env bash

source .env

# Error if no HA_IP is set
if [ -z "$HA_IP" ]; then
  echo "Please set HA_IP in .env file"
  exit 1
fi

server="$HA_IP"
config="/mnt/cephfs/homeassistant"

ssh "$server" "rm -rv $config/automations $config/scenes"

rsync -rvzP dist/ "$server:$config"
