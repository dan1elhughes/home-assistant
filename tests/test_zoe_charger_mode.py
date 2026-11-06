import unittest
from pathlib import Path

import yaml
from jinja2.nativetypes import NativeEnvironment


class ZoeChargerModeTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).parents[1] / "static/automations/zappi.yaml"
        self.automation = next(
            (item for item in yaml.safe_load(path.read_text())
             if item["alias"] == "Select Zoe charger mode when plugged in at home"),
            None,
        )
        self.assertIsNotNone(self.automation, "Zoe charger mode automation is missing")

    def test_trigger_requires_plugged_in_and_home(self):
        trigger = self.automation["trigger"][0]
        self.assertEqual(trigger["platform"], "template")
        for plug in ["on", "off", "unknown", "unavailable"]:
            for location in ["home", "not_home", "unknown", "unavailable"]:
                with self.subTest(plug=plug, location=location):
                    states = {
                        "binary_sensor.wp22lxc_plug": plug,
                        "device_tracker.wp22lxc_location": location,
                    }
                    env = NativeEnvironment()
                    env.globals["is_state"] = lambda entity, state: states[entity] == state
                    result = env.from_string(trigger["value_template"]).render()
                    self.assertEqual(result, plug == "on" and location == "home")

    def test_selects_zoe_on_the_dashboard_input(self):
        self.assertEqual(self.automation["action"], [{
            "action": "input_select.select_option",
            "target": {"entity_id": "input_select.charger_mode"},
            "data": {"option": "Zoe"},
        }])


if __name__ == "__main__":
    unittest.main()
