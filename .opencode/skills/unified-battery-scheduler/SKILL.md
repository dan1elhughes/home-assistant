---
name: unified-battery-scheduler
description: >
  Debug and modify the unified battery schedule optimizer. Use when the user
  reports unexpected battery schedule behavior, wants to analyze the DP
  decisions, or needs to reproduce a schedule with live Home Assistant data.
---

# Unified Battery Scheduler Skill

This skill guides debugging and modification of the home battery
charge/discharge optimizer that runs as a Home Assistant python_script.

## Key Files

- `static/python_scripts/src/unified/` — source fragments (concatenated at build)
  - `10_helpers.py` — rate lookups, charge/discharge value functions
  - `20_dp.py` — dynamic programming solver (`solve_dp`)
  - `30_events.py` — action list → event dict conversion
  - `40_api.py` — `compute_unified_schedule` and `compute_load_floor`
  - `90_glue.py` — Home Assistant sandbox glue (main entry point)
- `static/template.yaml` — `sensor.unified_battery_schedule_inputs` template
- `static/automations/unified_battery_schedule_py.yaml` — automation that triggers it
- `tests/test_unified_dp_internals.py` — pytest tests
- `scripts/repro_unified.py` — local reproduction script (see below)

## Debugging Workflow

When the user reports unexpected schedule behavior:

1. **Ask the user to paste the sensor state** from
   `sensor.unified_battery_schedule_inputs`. This sensor always contains the
   exact data dict that was passed to the python script.

   The sensor has these attributes:
   - `now_epoch` — current time (epoch seconds)
   - `import_rates` — list of {start, end, price}
   - `export_rates` — list of {start, end, price}
   - `saving_window` — {start, end} or None
   - `saving_bonus_events` — list of {start, end, bonus_pence}
   - `available_kwh`, `capacity_kwh`, `hard_lower_limit_kwh`, `lower_discharge_limit_kwh`
   - `idle_power_kw`, `power_rate_kw`, `efficiency`
   - `allow_discharge`, `charge_price_threshold`, `discharge_price_threshold`

2. **Reproduce locally** with `scripts/repro_unified.py`:

   Save the pasted sensor state to a JSON file (e.g. `/tmp/inputs.json`) and run:

   ```bash
   python3 scripts/repro_unified.py /tmp/inputs.json
   ```

   For debug output (per-step actions, floor levels, charge/discharge values):

   ```bash
   python3 scripts/repro_unified.py -d /tmp/inputs.json
   ```

   The script outputs the exact event list that the DP would produce, so you can
   compare it to the live sensor state.

3. **Analyze the floor**: If the issue involves load-aware reserve, use the `-d`
   flag to see the per-step floor levels and the first-pass next-charge window.

4. **Check the logs**: The script logs inputs and outputs via `logger.info()`
   in `90_glue.py`. Look for lines prefixed with
   `unified_battery_schedule:` in the Home Assistant logs.

## Common Issues

- **"It should discharge but doesn't"** → Check `discharge_value` in
  `10_helpers.py`. The value should be the export price (not import price). The
  load-aware reserve floor (`idle_power_kw`) already covers house load, so the
  import price is irrelevant for the export decision.

- **"It discharges too early"** → Check the `discharge_price_threshold`.
  Also verify the first-pass next-charge window hasn't shifted.

- **"The floor is too high"** → Check if `idle_power_kw` or
  `lower_discharge_limit_kwh` are set unexpectedly high.

- **"No schedule produced"** → Check `available_kwh` and `capacity_kwh` in the
  sensor. If either is None, the script returns empty.

## Build and Deploy

After any changes to the source fragments:

```bash
./build.sh   # assemble fragments, render templates
./upload.sh  # rsync to Home Assistant
```

Then reload Template Entities in HA (Developer Tools → YAML → Template Entities).

## Tests

```bash
python3 -m pytest tests/ -v
```

Add new test cases for any floor or DP behavior changes.
