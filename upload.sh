#!/usr/bin/env bash

source .env

# Error if no HA_IP is set
if [ -z "$HA_IP" ]; then
  echo "Please set HA_IP in .env file"
  exit 1
fi

server="root@$HA_IP"

ssh "$server" "rm -rv /config/automations /config/scenes"

# brew install gnu-tar (macos)
gtar -czf - ./dist/* | ssh "$server" tar -xvzf -

# Todo: extract to /config folder instead of /root/dist
ssh "$server" '/bin/bash -c "mv -v /root/dist/* /config"'
