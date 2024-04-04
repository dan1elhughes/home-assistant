#!/usr/bin/env bash

server="root@100.106.77.84"

ssh "$server" "rm -rv /config/automations /config/scenes"

# brew install gnu-tar (macos)
gtar -czf - ./dist/* | ssh "$server" tar -xvzf -

# Todo: extract to /config folder instead of /root/dist
ssh "$server" '/bin/bash -c "mv -v /root/dist/* /config"'
