#!/usr/bin/env bash

ip="10.10.10.50"

rsync -rvzP . root@$ip:/media/pit/volumes/homeassistant
