import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import yaml
from jinja2.nativetypes import NativeEnvironment


class ZhaRecoveryTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).parents[1] / "static/automations/integration_reload.yaml"
        self.automations = yaml.safe_load(path.read_text())
        self.automation = self.automations[0]
        self.trigger = next(
            (item for item in self.automation["trigger"] if item.get("id") == "zha_failure"),
            None,
        )
        self.assertIsNotNone(self.trigger, "ZHA runtime recovery trigger is missing")
        self.runtime = self.automation["action"][0]["then"]
        self.loop = next(item["repeat"] for item in self.runtime if "repeat" in item)
        self.now = datetime(2026, 11, 5, 14, tzinfo=timezone.utc)
        self.last_started = None
        self.entry = {"state": "setup_retry", "disabled_by": None, "source": "user"}
        self.env = NativeEnvironment()
        self.env.globals.update(
            now=lambda: self.now,
            config_entry_attr=lambda entry_id, attr: self.entry.get(attr),
            as_timestamp=lambda value, default=0: value.timestamp() if value else default,
            state_attr=lambda entity_id, attr: self.last_started,
        )

    def render(self, template, **context):
        return self.env.from_string(template).render(
            zha_entry_id="test-entry", **context
        )

    def test_only_enabled_failed_or_stuck_zha_triggers_recovery(self):
        for state, expected in [
            ("loaded", False), ("not_loaded", False),
            ("setup_retry", True), ("setup_error", True),
            ("setup_in_progress", True), (None, False),
        ]:
            with self.subTest(state=state):
                self.entry["state"] = state
                self.assertEqual(self.render(self.trigger["value_template"]), expected)
        self.entry.update(state="setup_error", disabled_by="user")
        self.assertFalse(self.render(self.trigger["value_template"]))
        self.entry.update(disabled_by=None, source="ignore")
        self.assertFalse(self.render(self.trigger["value_template"]))
        self.assertEqual(self.trigger["for"], {"minutes": 2})

    def test_cooldown_waits_only_the_remaining_time(self):
        delay = self.runtime[0]["delay"]["seconds"]
        for elapsed, expected in [(0, 900), (300, 600), (900, 0), (1200, 0)]:
            self.last_started = (self.now - timedelta(seconds=elapsed)).timestamp()
            self.assertEqual(self.render(delay), expected)
        self.last_started = None
        self.assertEqual(self.render(delay), 0)

    def test_recovery_stops_after_three_attempts_or_when_loaded(self):
        condition = self.loop["while"][0]["value_template"]
        for attempt, expected in [(1, True), (2, True), (3, True), (4, False)]:
            self.assertEqual(
                self.render(condition, repeat=SimpleNamespace(index=attempt)), expected
            )
        self.entry["state"] = "loaded"
        self.assertFalse(self.render(condition, repeat=SimpleNamespace(index=1)))
        self.entry.update(state="setup_retry", disabled_by="user")
        self.assertFalse(self.render(condition, repeat=SimpleNamespace(index=1)))

    def test_cooldown_uses_actual_recovery_start_after_a_delayed_run(self):
        self.env.globals["state_attr"] = lambda entity_id, attr: (
            self.now - timedelta(minutes=2)
        ).timestamp()
        context = SimpleNamespace(attributes=SimpleNamespace(
            last_triggered=self.now - timedelta(minutes=12)
        ))
        delay = self.runtime[0]["delay"]["seconds"]
        self.assertEqual(self.render(delay, this=context), 780)

    def test_radio_restart_precedes_reload_and_startup_is_not_run_afterwards(self):
        stamp = self.runtime[1]
        self.assertEqual(stamp["action"], "input_datetime.set_datetime")
        self.assertEqual(self.render(stamp["data"]["timestamp"]), self.now.timestamp())
        actions = self.loop["sequence"]
        self.assertEqual(actions[0]["action"], "rest_command.zigbee_radio_restart")
        self.assertEqual(actions[1]["delay"], {"seconds": 5})
        self.assertEqual(actions[2]["action"], "homeassistant.reload_config_entry")
        self.assertEqual(self.render(actions[2]["data"]["entry_id"]), "test-entry")
        self.assertEqual(actions[3]["delay"], {"seconds": 20})
        self.assertIn("stop", self.runtime[-1])

    def test_notification_is_only_created_if_recovery_still_failed(self):
        result = self.runtime[3]
        condition = result["if"][0]["value_template"]
        self.assertTrue(self.render(condition))
        self.assertEqual(result["then"][0]["action"], "persistent_notification.create")
        self.entry["state"] = "loaded"
        self.assertFalse(self.render(condition))
        self.assertEqual(result["else"][0]["action"], "persistent_notification.dismiss")

    def test_repeated_send_errors_reload_loaded_zha_without_restarting_radio(self):
        self.assertFalse(any(item.get("event_type") == "system_log_event"
                             for item in self.automation["trigger"]))
        recovery = next(item for item in self.automations
                        if item["id"] == "zha_reload_after_send_errors")
        self.assertEqual(recovery["mode"], "queued")
        event_trigger = next(
            (item for item in recovery["trigger"]
             if item.get("event_type") == "system_log_event"), None
        )
        self.assertIsNotNone(event_trigger, "ZHA send errors have no recovery trigger")
        self.assertEqual(event_trigger["event_data"], {"level": "ERROR"})
        guard, snapshot, remember, recover = recovery["action"]
        error = "Failed to send request: <Status.INVALID_PARAMETER: 2>"
        context = SimpleNamespace(event=SimpleNamespace(data={
            "message": ["Error during service call: " + error],
            "name": "homeassistant.components.websocket_api.http.connection",
            "timestamp": self.now.timestamp(),
        }))
        self.entry["state"] = "loaded"
        stamps = {}
        self.env.globals["state_attr"] = lambda entity, attr: stamps.get(entity)
        template = guard["value_template"]
        matches = recovery["condition"][0]["value_template"]
        self.assertTrue(self.render(template, trigger=context))
        self.assertTrue(self.render(matches, trigger=context))
        repeat = recover["if"][0]["value_template"]
        for elapsed, expected in [(121, False), (120, True), (30, True), (-1, False)]:
            self.assertEqual(self.render(repeat, trigger=context,
                                         previous_error=self.now.timestamp() - elapsed), expected)
        self.assertEqual(self.render(remember["data"]["timestamp"], trigger=context),
                         self.now.timestamp())
        self.assertEqual(remember["action"], "input_datetime.set_datetime")
        self.assertEqual([step["action"] for step in recover["then"]],
                         ["input_datetime.set_datetime", "homeassistant.reload_config_entry"])
        self.assertEqual(self.render(recover["then"][1]["data"]["entry_id"]), "test-entry")
        stamps["input_datetime.zha_invalid_parameter_last_seen"] = self.now.timestamp() - 30
        self.assertEqual(self.render(snapshot["variables"]["previous_error"]),
                         self.now.timestamp() - 30)
        stamps["input_datetime.zha_recovery_last_started"] = self.now.timestamp() - 899
        self.assertFalse(self.render(template, trigger=context))
        stamps.clear()
        self.entry["state"] = "setup_retry"
        self.assertFalse(self.render(template, trigger=context))
        self.entry["state"] = "loaded"
        context.event.data["message"] = ["Failed to send request: <Status.MAC_NO_ACK: 233>"]
        self.assertFalse(self.render(matches, trigger=context))
        context.event.data.update(name="homeassistant.components.automation.test",
                                  message=["Error while executing automation: " + error])
        self.assertFalse(self.render(matches, trigger=context))
        context.event.data["message"] = ["Error executing script. Error for if at pos 1: " + error]
        self.assertFalse(self.render(matches, trigger=context))
        context.event.data["message"] = ["Error executing script. Error for call_service at pos 1: " + error]
        self.assertTrue(self.render(matches, trigger=context))


if __name__ == "__main__":
    unittest.main()
