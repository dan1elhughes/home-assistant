#!/usr/bin/env bash

ssh root@100.106.77.84 "rm -rv /config/automations"
ssh root@100.106.77.84 "rm -rv /config/scenes"
scp -rp ./dist/* root@100.106.77.84:config
