#!/usr/bin/env python3
"""Run the unified battery schedule with real HA inputs and print the output."""

import json
import sys
import os
import datetime

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'static/python_scripts/src'))

# Read the concatenated script (which has all the core functions)
script_path = os.path.join(os.path.dirname(__file__), 'dist/python_scripts/unified_battery_schedule.py')
with open(script_path) as f:
    script_content = f.read()

# Mock the HA sandbox globals
class MockLogger:
    def debug(self, msg, *args):
        print(f"DEBUG: {msg % args}")
    def info(self, msg, *args):
        print(f"INFO: {msg % args}")
    def warning(self, msg, *args):
        print(f"WARNING: {msg % args}")
    def error(self, msg, *args):
        print(f"ERROR: {msg % args}")

class MockHass:
    class states:
        @staticmethod
        def set(entity_id, state, attributes=None):
            print(f"HASS SET: {entity_id} = {state}")
            if attributes:
                print(f"  attrs: {json.dumps(attributes, indent=2, default=str)}")

# BST (UTC+1) for summer time
BST = datetime.timezone(datetime.timedelta(hours=1))

class MockDtUtil:
    @staticmethod
    def utc_from_timestamp(ts):
        return datetime.datetime.utcfromtimestamp(ts)

    @staticmethod
    def as_local(dt):
        import datetime
        return dt.replace(tzinfo=datetime.timezone.utc).astimezone(BST)

    @staticmethod
    def as_timestamp(dt):
        if hasattr(dt, 'timestamp'):
            return int(dt.timestamp())
        return int(dt)

    @staticmethod
    def parse_datetime(dt_str):
        import datetime
        return datetime.datetime.fromisoformat(dt_str)

# Create the sandbox environment
sandbox = {
    'logger': MockLogger(),
    'hass': MockHass(),
    'dt_util': MockDtUtil(),
    'data': None,
    'output': {},
    'datetime': __import__('datetime'),
}

# YOUR DATA: sensor.unified_battery_schedule_inputs at ~23:10 local (June 25 2026)
inputs = {
    "now_epoch": 1782461700,       # ~June 25 23:10 local = June 26 00:10 BST
    "horizon_end_epoch": 1782534600,
    "step_minutes": 5,
    "import_rates": [
        {"start": 1782460800, "end": 1782462600, "price": 0.291866},
        {"start": 1782462600, "end": 1782464400, "price": 0.291866},
        {"start": 1782464400, "end": 1782466200, "price": 0.291866},
        {"start": 1782466200, "end": 1782468000, "price": 0.291866},
        {"start": 1782468000, "end": 1782469800, "price": 0.291866},
        {"start": 1782469800, "end": 1782471600, "price": 0.291866},
        {"start": 1782471600, "end": 1782473400, "price": 0.291866},
        {"start": 1782473400, "end": 1782475200, "price": 0.291866},
        {"start": 1782475200, "end": 1782477000, "price": 0.291866},
        {"start": 1782477000, "end": 1782478800, "price": 0.291866},
        {"start": 1782478800, "end": 1782480600, "price": 0.291866},
        {"start": 1782480600, "end": 1782482400, "price": 0.291866},
        {"start": 1782482400, "end": 1782484200, "price": 0.291866},
        {"start": 1782484200, "end": 1782486000, "price": 0.291866},
        {"start": 1782486000, "end": 1782487800, "price": 0.291866},
        {"start": 1782487800, "end": 1782489600, "price": 0.291866},
        {"start": 1782489600, "end": 1782491400, "price": 0.291866},
        {"start": 1782491400, "end": 1782493200, "price": 0.291866},
        {"start": 1782493200, "end": 1782495000, "price": 0.291866},
        {"start": 1782495000, "end": 1782496800, "price": 0.291866},
        {"start": 1782496800, "end": 1782498600, "price": 0.291866},
        {"start": 1782498600, "end": 1782500400, "price": 0.291866},
        {"start": 1782500400, "end": 1782502200, "price": 0.291866},
        {"start": 1782502200, "end": 1782504000, "price": 0.291866},
        {"start": 1782504000, "end": 1782505800, "price": 0.291866},
        {"start": 1782505800, "end": 1782507600, "price": 0.291866},
        {"start": 1782507600, "end": 1782509400, "price": 0.291866},
        {"start": 1782509400, "end": 1782511200, "price": 0.291866},
        {"start": 1782511200, "end": 1782513000, "price": 0.291866},
        {"start": 1782513000, "end": 1782514800, "price": 0.03993},
        {"start": 1782514800, "end": 1782516600, "price": 0.03993},
        {"start": 1782516600, "end": 1782518400, "price": 0.03993},
        {"start": 1782518400, "end": 1782520200, "price": 0.03993},
        {"start": 1782520200, "end": 1782522000, "price": 0.03993},
        {"start": 1782522000, "end": 1782523800, "price": 0.03993},
        {"start": 1782523800, "end": 1782525600, "price": 0.03993},
        {"start": 1782525600, "end": 1782527400, "price": 0.03993},
        {"start": 1782527400, "end": 1782529200, "price": 0.03993},
        {"start": 1782529200, "end": 1782531000, "price": 0.03993},
        {"start": 1782531000, "end": 1782532800, "price": 0.03993},
        {"start": 1782532800, "end": 1782534600, "price": 0.03993},
    ],
    "export_rates": [
        {"start": 1782460800, "end": 1782462600, "price": 0.0975},
        {"start": 1782462600, "end": 1782464400, "price": 0.0977},
        {"start": 1782464400, "end": 1782466200, "price": 0.0948},
        {"start": 1782466200, "end": 1782468000, "price": 0.0922},
        {"start": 1782468000, "end": 1782469800, "price": 0.0912},
        {"start": 1782469800, "end": 1782471600, "price": 0.0888},
        {"start": 1782471600, "end": 1782473400, "price": 0.0884},
        {"start": 1782473400, "end": 1782475200, "price": 0.0884},
        {"start": 1782475200, "end": 1782477000, "price": 0.0878},
        {"start": 1782477000, "end": 1782478800, "price": 0.0826},
        {"start": 1782478800, "end": 1782480600, "price": 0.0859},
        {"start": 1782480600, "end": 1782482400, "price": 0.0845},
        {"start": 1782482400, "end": 1782484200, "price": 0.0926},
        {"start": 1782484200, "end": 1782486000, "price": 0.0895},
        {"start": 1782486000, "end": 1782487800, "price": 0.1726},
        {"start": 1782487800, "end": 1782489600, "price": 0.1738},
        {"start": 1782489600, "end": 1782491400, "price": 0.1956},
        {"start": 1782491400, "end": 1782493200, "price": 0.2085},
        {"start": 1782493200, "end": 1782495000, "price": 0.2803},
        {"start": 1782495000, "end": 1782496800, "price": 0.2791},
        {"start": 1782496800, "end": 1782498600, "price": 0.2131},
        {"start": 1782498600, "end": 1782500400, "price": 0.2106},
        {"start": 1782500400, "end": 1782502200, "price": 0.2062},
        {"start": 1782502200, "end": 1782504000, "price": 0.1987},
        {"start": 1782504000, "end": 1782505800, "price": 0.1961},
        {"start": 1782505800, "end": 1782507600, "price": 0.1747},
        {"start": 1782507600, "end": 1782509400, "price": 0.1456},
        {"start": 1782509400, "end": 1782511200, "price": 0.1462},
    ],
    "free_sessions": [],
    "saving_window": None,
    "saving_bonus_events": [],
    "available_kwh": 11.7,
    "capacity_kwh": 15.0,
    "reserve_kwh": 0.85,
    "hard_lower_limit_kwh": 0.85,
    "lower_discharge_limit_kwh": 1.5,
    "idle_power_kw": 1.0,
    "power_rate_kw": 9.6,
    "efficiency": 0.9,
    "minimum_slot_length": 5,
    "allow_discharge": True,
    "charge_price_threshold": 0.1,
    "discharge_price_threshold": 0.15,
}

sandbox['data'] = inputs

# Execute the script in the sandbox environment
exec(script_content, sandbox)

# Show the computed events
print("\n" + "="*60)
print("EVENTS")
print("="*60)
for ev in sandbox['output'].get('events', []):
    print(f"  {ev['intent']}: {ev['start']} -> {ev['end']}")
    for key, val in ev.items():
        if key not in ('intent', 'start', 'end'):
            print(f"    {key}: {val}")
    print()

# Also print the raw output
print("OUTPUT:", json.dumps(sandbox['output'], indent=2, default=str))