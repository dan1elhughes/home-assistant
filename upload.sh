#!/usr/bin/env bash

ip="100.77.199.70"

rsync -rvzP . root@$ip:/media/pit/volumes/homeassistant
