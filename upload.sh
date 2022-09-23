#!/usr/bin/env bash

ssh root@10.10.10.10 "rm -rv /config/automations"
ssh root@10.10.10.10 "rm -rv /config/scenes"
scp -rp ./dist/* root@10.10.10.10:config
