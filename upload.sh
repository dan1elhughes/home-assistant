#!/usr/bin/env bash

set -euo pipefail

server="10.10.10.20"
config="/mnt/cephfs/homeassistant"

# Sync the repo-managed automations dir with --delete so removed automations
# are also removed on the server. Scoped to the automations/ subdir ONLY — never
# the config root, which holds .storage, the DB, secrets and UI automations.yaml.
rsync -rvzP --delete dist/automations/ "$server:$config/automations/"

# Everything else: additive/overwrite, no --delete (would wipe HA-managed files).
rsync -rvzP dist/ "$server:$config"
