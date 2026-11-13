import json
import unittest
from pathlib import Path

import yaml
from jinja2.nativetypes import NativeEnvironment


ROOT = Path(__file__).parents[1]


class BarnHeatingTests(unittest.TestCase):
    def test_virtual_thermostat_supports_low_temperatures(self):
        climates = yaml.safe_load((ROOT / "static/climate.yaml").read_text())
        thermostat = next(
            (item for item in climates if item["name"] == "Virtual barn heating"),
            None,
        )
        self.assertIsNotNone(thermostat)
        self.assertEqual(thermostat["platform"], "generic_thermostat")
        self.assertEqual(thermostat["heater"], "switch.barn_ac_power")
        self.assertEqual(thermostat["target_sensor"], "sensor.barn_ac_temperature")
        self.assertEqual(thermostat["min_temp"], 1)

    def test_temperature_sensor_uses_ac_reading(self):
        sensors = yaml.safe_load((ROOT / "static/templates/sensors.yaml").read_text())[0]["sensor"]
        sensor = next((item for item in sensors if item["name"] == "Barn AC temperature"), None)
        self.assertIsNotNone(sensor)
        self.assertEqual(sensor["device_class"], "temperature")
        self.assertEqual(sensor["unit_of_measurement"], "°C")
        env = NativeEnvironment()
        env.globals["is_number"] = lambda value: isinstance(value, (int, float))
        for reading in [3.0, 5.5, -2.0, None]:
            with self.subTest(reading=reading):
                def state_attr(entity, attribute):
                    self.assertEqual(entity, "climate.garden_barn_ac")
                    self.assertEqual(attribute, "current_temperature")
                    return reading

                self.assertEqual(env.from_string(sensor["state"]).render(state_attr=state_attr), reading)
                self.assertEqual(
                    env.from_string(sensor["availability"]).render(state_attr=state_attr),
                    reading is not None,
                )

    def test_switch_controls_current_ac_entity(self):
        path = ROOT / "static/templates/switches.yaml"
        self.assertTrue(path.exists())
        switch = yaml.safe_load(path.read_text())[0]["switch"][0]
        self.assertEqual(switch["default_entity_id"], "switch.barn_ac_power")
        for command, mode in [("turn_on", "heat"), ("turn_off", "off")]:
            self.assertEqual(switch[command], [{
                "action": "climate.set_hvac_mode",
                "target": {"entity_id": "climate.garden_barn_ac"},
                "data": {"hvac_mode": mode},
            }])
        env = NativeEnvironment()
        for mode in ["heat", "cool", "heat_cool", "fan_only", "dry", "off", "unknown", "unavailable"]:
            with self.subTest(mode=mode):
                def states(entity):
                    self.assertEqual(entity, "climate.garden_barn_ac")
                    return mode

                result = env.from_string(switch["state"]).render(states=states)
                self.assertEqual(result, mode in ["heat", "cool", "heat_cool", "fan_only", "dry"])

    def test_barn_dashboard_exposes_thermostat(self):
        data = json.loads((ROOT / "data.json").read_text())
        rooms = next(value for value in data.values() if isinstance(value, list)
                     and any(isinstance(item, dict) and item.get("id") == "barn" for item in value))
        barn = next(room for room in rooms if room.get("id") == "barn")
        self.assertIn("climate.virtual_barn_heating", barn.get("other_entities", []))
