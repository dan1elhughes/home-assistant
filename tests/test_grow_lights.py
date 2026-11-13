import unittest
from pathlib import Path

import yaml


LIGHT = "light.bedroom_bedroom_shelf_power_grow_lights"


class GrowLightsTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).parents[1] / "static/automations/grow_lights.yaml"
        self.automations = yaml.safe_load(path.read_text())
        self.on = next(item for item in self.automations if item["alias"] == "Grow lights on at 10am")
        self.off = next(item for item in self.automations if item["alias"] == "Grow lights off at sunset")

    def test_turn_on_at_ten_and_after_startup(self):
        self.assertIn({"trigger": "time", "at": "10:00:00"}, self.on["triggers"])
        self.assertIn({"trigger": "homeassistant", "event": "start"}, self.on["triggers"])

    def test_recovery_does_not_override_manual_turn_off(self):
        triggers = [item for item in self.on["triggers"] if item["trigger"] == "state"]
        self.assertEqual(triggers, [{
            "trigger": "state",
            "entity_id": LIGHT,
            "from": ["unavailable", "unknown"],
            "to": "off",
        }])

    def test_turn_on_only_during_schedule_when_available_and_off(self):
        self.assertEqual(self.on.get("conditions"), [
            {"condition": "time", "after": "10:00:00"},
            {"condition": "sun", "before": "sunset"},
            {"condition": "state", "entity_id": LIGHT, "state": "off"},
        ])
        self.assertEqual(self.on["action"], [{
            "action": "light.turn_on",
            "target": {"entity_id": LIGHT},
        }])

    def test_sunset_shutoff_is_unchanged(self):
        self.assertEqual(self.off["triggers"], [{"trigger": "sun", "event": "sunset"}])
        self.assertEqual(self.off["action"], [{
            "action": "light.turn_off",
            "target": {"entity_id": LIGHT},
        }])
