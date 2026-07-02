After making changes, run `./build.sh` and `./upload.sh`.

## Home Assistant API

The running instance is at `https://home.danhughes.dev`. The HA REST API
requires a long-lived token stored in 1Password as `PREDBAT_TOKEN` (in the
`my.1password.com` account — NOT the enode account). The canonical invocation
mirrors `../home-os/stacks/deploy.sh`:

```
op run --environment q5pfvfpsh44h7xywiqys2ff5ma \
  --account BMVXTKJWJNHKDFO36EZROR44HM \
  -- bash -c 'curl -s -H "Authorization: Bearer $PREDBAT_TOKEN" \
    https://home.danhughes.dev/api/states/<entity_id>'
```

- `GET /api/states` returns all entities; `GET /api/states/<entity_id>` returns one.
- `op run` redacts any stdout that matches a secret value (shows
  `<concealed by 1Password>`), which corrupts JSON. **Redirect the curl output
  to a file inside the `bash -c`** (`-o file` or `> file`) so the secret
  scanner never sees the body, then parse the file afterwards.
- The `$PREDBAT_TOKEN` reference must be inside the single-quoted `bash -c`
  string so `op run` performs the substitution; escaping it (`\$`) prevents
  `op run` from injecting the value and the request returns `401: Unauthorized`.
- Predbat's own web API at `https://predbat.danhughes.dev/api/state` exposes
  only a subset of entities (no `sensor.*` HA entities, no `predbat.soc_*`).
  Use the HA API above when you need the full entity set.
