#!/usr/bin/env bash

rsync -rvzP . root@10.10.10.50:/media/pit/volumes/homeassistant
scp -rp ./* root@10.10.10.10:/config/
