#!/usr/bin/env python3
"""Run the unified battery schedule with real HA inputs and print the output."""

import json
import sys
import os

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

class MockDtUtil:
    @staticmethod
    def utc_from_timestamp(ts):
        import datetime
        return datetime.datetime.utcfromtimestamp(ts)
    
    @staticmethod
    def as_local(dt):
        import datetime
        return dt.replace(tzinfo=datetime.timezone.utc)

# Create the sandbox environment
sandbox = {
    'logger': MockLogger(),
    'hass': MockHass(),
    'dt_util': MockDtUtil(),
    'data': None,
    'output': {},
    'datetime': __import__('datetime'),
}

# Inputs from the debug template
inputs = {
    "now_epoch": 1782395100,
    "horizon_end_epoch": 1782424800,
    "step_minutes": 5,
    "import_rates": [
        {"end": 1782396000, "price": 0.03993, "start": 1782394200},
        {"end": 1782397800, "price": 0.03993, "start": 1782396000},
        {"end": 1782399600, "price": 0.03993, "start": 1782397800}
    ],
    "export_rates": [
        {"end": 1782396000, "price": 0.0854, "start": 1782394200},
        {"end": 1782397800, "price": 0.088, "start": 1782396000},
        {"end": 1782399600, "price": 0.0892, "start": 1782397800},
        {"end": 1782401400, "price": 0.171, "start": 1782399600},
        {"end": 1782403200, "price": 0.1723, "start": 1782401400},
        {"end": 1782405000, "price": 0.1817, "start": 1782403200},
        {"end": 1782406800, "price": 0.1942, "start": 1782405000},
        {"end": 1782408600, "price": 0.2359, "start": 1782406800},
        {"end": 1782410400, "price": 0.2396, "start": 1782408600},
        {"end": 1782412200, "price": 0.1607, "start": 1782410400},
        {"end": 1782414000, "price": 0.1653, "start": 1782412200},
        {"end": 1782415800, "price": 0.1616, "start": 1782414000},
        {"end": 1782417600, "price": 0.158, "start": 1782415800},
        {"end": 1782419400, "price": 0.151, "start": 1782417600},
        {"end": 1782421200, "price": 0.1493, "start": 1782419400},
        {"end": 1782423000, "price": 0.1249, "start": 1782421200},
        {"end": 1782424800, "price": 0.1118, "start": 1782423000}
    ],
    "free_sessions": [],
    "saving_window": {"end": 1782412200, "start": 1782408600},
    "saving_bonus_events": [
        {"bonus_pence": 0.135, "end": 1782412200, "start": 1782408600}
    ],
    "available_kwh": 9.1,
    "capacity_kwh": 15.0,
    "reserve_kwh": 0.85,
    "hard_lower_limit_kwh": 0.85,
    "lower_discharge_limit_kwh": 1.5,
    "idle_power_kw": 0.75,
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

# The script should have set output["events"] and called hass.states.set
# Let's print the output
print("\n" + "="*60)
print("OUTPUT")
print("="*60)
print(json.dumps(sandbox['output'], indent=2, default=str))

# Also show the computed events if available
if 'events' in sandbox['output']:
    print("\n" + "="*60)
    print("EVENTS")
    print("="*60)
    for ev in sandbox['output']['events']:
        print(f"  {ev['intent']}: {ev['start']} -> {ev['end']}")
        for key, val in ev.items():
            if key not in ('intent', 'start', 'end'):
                print(f"    {key}: {val}")
        print()
