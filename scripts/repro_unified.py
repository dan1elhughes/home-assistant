#!/usr/bin/env python3
"""
Reproduce the unified battery schedule from a sensor.unified_battery_schedule_inputs
JSON dump.

Usage:
    python3 scripts/repro_unified.py path/to/sensor_state.json
    cat sensor_state.json | python3 scripts/repro_unified.py -
    python3 scripts/repro_unified.py -d path/to/sensor_state.json  # debug mode

The JSON file should contain the exact attributes of the sensor, e.g.:

    {
      "now_epoch": 1782492300,
      "horizon_end_epoch": 1782601200,
      "step_minutes": 5,
      "import_rates": [...],
      "export_rates": [...],
      "available_kwh": 12.4,
      "capacity_kwh": 15.0,
      ...
    }
"""

import json
import sys
import os
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Reproduce unified battery schedule from sensor state JSON"
    )
    parser.add_argument("input", help="Path to JSON file, or '-' for stdin")
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Print DP internals (floor, actions)"
    )
    parser.add_argument(
        "--limit-actions",
        type=int,
        default=100,
        help="Number of per-step actions to print in debug mode",
    )
    args = parser.parse_args()

    # Load input data
    if args.input == "-":
        raw = sys.stdin.read()
    else:
        with open(args.input) as f:
            raw = f.read()
    data = json.loads(raw)

    # Load the built script
    script_path = os.path.join(
        os.path.dirname(__file__), "..", "dist/python_scripts/unified_battery_schedule.py"
    )
    with open(script_path) as f:
        script_content = f.read()

    # Minimal sandbox to satisfy the HA python_script
    sandbox = {
        "logger": _FakeLogger(),
        "hass": _FakeHass(),
        "dt_util": _FakeDtUtil(),
        "data": data,
        "output": {},
        "datetime": __import__("datetime"),
    }

    exec(script_content, sandbox)

    events = sandbox["output"].get("events", [])
    _print_events(events)

    if args.debug:
        _print_debug(data, events, args.limit_actions)


def _print_events(events):
    print("=" * 60)
    print("EVENTS")
    print("=" * 60)
    if not events:
        print("  (no events)")
    for ev in events:
        print(f"  {ev['intent']}: {ev['start']} -> {ev['end']}")
        for key, val in ev.items():
            if key not in ("intent", "start", "end"):
                print(f"    {key}: {val}")
        print()


def _print_debug(data, events, limit_actions):
    import datetime

    # Re-run the core functions to get internals
    script_path = os.path.join(
        os.path.dirname(__file__), "..", "dist/python_scripts/unified_battery_schedule.py"
    )
    with open(script_path) as f:
        script_content = f.read()

    # Strip the `main()` call at the end so we can import the functions
    lines = script_content.splitlines()
    while lines and lines[-1].strip() == "":
        lines.pop()
    if lines and lines[-1].strip() == "main()":
        lines.pop()

    sandbox = {}
    exec("\n".join(lines), sandbox)

    compute_unified_schedule = sandbox["compute_unified_schedule"]
    compute_load_floor = sandbox["compute_load_floor"]
    solve_dp = sandbox["solve_dp"]
    rate_at = sandbox["rate_at"]
    charge_value = sandbox["charge_value"]
    discharge_value = sandbox["discharge_value"]

    now_epoch = data["now_epoch"]
    horizon_end_epoch = data["horizon_end_epoch"]
    step_minutes = data.get("step_minutes", 5)
    import_rates = data["import_rates"]
    export_rates = data["export_rates"]
    free_sessions = data.get("free_sessions", [])
    saving_bonus_events = data.get("saving_bonus_events", [])
    available_kwh = data["available_kwh"]
    capacity_kwh = data["capacity_kwh"]
    reserve_kwh = data.get("reserve_kwh", 0)
    hard_lower_limit_kwh = data.get("hard_lower_limit_kwh")
    lower_discharge_limit_kwh = data.get("lower_discharge_limit_kwh", 0)
    idle_power_kw = data.get("idle_power_kw", 0)
    power_rate_kw = data["power_rate_kw"]
    efficiency = data["efficiency"]
    allow_discharge = data.get("allow_discharge", True)
    charge_price_threshold = data.get("charge_price_threshold")
    discharge_price_threshold = data.get("discharge_price_threshold")

    step_kwh = power_rate_kw * (step_minutes / 60.0)
    total_steps = int((horizon_end_epoch - now_epoch) // (step_minutes * 60))
    lower_bound_kwh = (
        hard_lower_limit_kwh if hard_lower_limit_kwh is not None else reserve_kwh
    )
    n_levels = int(round((capacity_kwh - lower_bound_kwh) / step_kwh))
    start_level = int(round((available_kwh - lower_bound_kwh) / step_kwh))
    start_level = max(0, min(start_level, n_levels))

    print("=" * 60)
    print("DERIVED")
    print("=" * 60)
    print(f"  total_steps:        {total_steps}")
    print(f"  step_kwh:           {step_kwh:.4f}")
    print(f"  lower_bound_kwh:    {lower_bound_kwh}")
    print(f"  n_levels:           {n_levels}")
    print(f"  start_level:        {start_level}")
    print(f"  start_kwh:          {start_level * step_kwh + lower_bound_kwh:.4f}")

    # First pass
    actions_pass1 = solve_dp(
        now_epoch,
        total_steps,
        n_levels,
        start_level,
        step_kwh,
        efficiency,
        import_rates,
        export_rates,
        free_sessions,
        saving_bonus_events,
        allow_discharge,
        step_minutes,
        charge_price_threshold=charge_price_threshold,
        discharge_price_threshold=discharge_price_threshold,
    )

    next_charge_step = total_steps
    for t, a in enumerate(actions_pass1):
        if a == "charge":
            next_charge_step = t
            break

    print(f"  next_charge_step:   {next_charge_step}")
    print(f"  next_charge_epoch:  {now_epoch + next_charge_step * step_minutes * 60}")
    print(f"  next_charge_time:   {datetime.datetime.fromtimestamp(now_epoch + next_charge_step * step_minutes * 60, datetime.timezone.utc).astimezone()}")

    if idle_power_kw > 0 or lower_discharge_limit_kwh > 0:
        floor = compute_load_floor(
            total_steps,
            next_charge_step,
            n_levels,
            step_minutes,
            idle_power_kw,
            lower_discharge_limit_kwh,
            step_kwh,
            now_epoch=now_epoch,
            import_rates=import_rates,
            export_rates=export_rates,
            saving_bonus_events=saving_bonus_events,
            efficiency=efficiency,
        )
        print()
        print("=" * 60)
        print("FLOOR (pass 1)")
        print("=" * 60)
        print(f"  t=0:   {floor[0]} levels = {floor[0] * step_kwh:.4f} kWh")
        print(f"  t=10:  {floor[10] if total_steps > 10 else 'N/A'} levels")
        print(f"  t=60:  {floor[60] if total_steps > 60 else 'N/A'} levels")

    print()
    print("=" * 60)
    print("PER-STEP ACTIONS")
    print("=" * 60)
    print(f"  t     action    epoch        import    export    charge_val  discharge_val")
    for t in range(min(total_steps, limit_actions)):
        epoch = now_epoch + t * step_minutes * 60
        a = actions_pass1[t]
        ip = rate_at(import_rates, epoch)
        ep = rate_at(export_rates, epoch)
        cv = charge_value(
            epoch, import_rates, free_sessions, efficiency, step_kwh, charge_price_threshold
        )
        dv = discharge_value(
            epoch,
            import_rates,
            export_rates,
            saving_bonus_events,
            efficiency,
            step_kwh,
            allow_discharge,
            discharge_price_threshold,
        )
        print(
            f"  {t:3d}   {a:7s}   {epoch}   {ip:7.4f}   {ep:7.4f}   {str(cv):10s}  {str(dv):10s}"
        )


class _FakeLogger:
    def debug(self, msg, *args):
        pass
    def info(self, msg, *args):
        if args:
            print(f"INFO: {msg % args}")
        else:
            print(f"INFO: {msg}")
    def warning(self, msg, *args):
        print(f"WARNING: {msg % args}")
    def error(self, msg, *args):
        print(f"ERROR: {msg % args}")


class _FakeHass:
    class states:
        @staticmethod
        def set(entity_id, state, attributes=None):
            pass


class _FakeDtUtil:
    @staticmethod
    def utc_from_timestamp(ts):
        import datetime
        return datetime.datetime.utcfromtimestamp(ts)
    @staticmethod
    def as_local(dt):
        import datetime
        return dt.replace(tzinfo=datetime.timezone.utc).astimezone(
            datetime.timezone(datetime.timedelta(hours=1))
        )
    @staticmethod
    def as_timestamp(dt):
        if hasattr(dt, "timestamp"):
            return int(dt.timestamp())
        return int(dt)
    @staticmethod
    def parse_datetime(dt_str):
        import datetime
        return datetime.datetime.fromisoformat(dt_str)


if __name__ == "__main__":
    main()
