from pathlib import Path

import pytest
import yaml
from jinja2.nativetypes import NativeEnvironment


ROOT = Path(__file__).resolve().parents[1]


def recovery_steps(entry_id, entries):
    automation = yaml.safe_load(
        (ROOT / "static/automations/integration_reload.yaml").read_text()
    )[0]
    actions = automation["action"][3]["repeat"]["sequence"][0]["repeat"]["sequence"][0]["then"]
    environment = NativeEnvironment()
    result = []
    for action in actions:
        if "if" in action:
            matches = all(
                environment.from_string(condition["value_template"]).render(
                    enabled_entries=entries, repeat={"item": entry_id}
                )
                for condition in action["if"]
            )
            if matches:
                result.extend(action["then"])
        else:
            result.append(action)
    return result


@pytest.mark.parametrize(
    ("entry_id", "expected"),
    [
        ("zigbee", ["rest_command.zigbee_radio_restart", "delay", "homeassistant.reload_config_entry"]),
        ("other", ["homeassistant.reload_config_entry"]),
    ],
)
def test_only_zha_resets_radio_before_reload(entry_id, expected):
    entries = [
        {"entry_id": "zigbee", "domain": "zha"},
        {"entry_id": "other", "domain": "mqtt"},
    ]
    steps = recovery_steps(entry_id, entries)
    assert [step.get("action", "delay") for step in steps] == expected
    if entry_id == "zigbee":
        assert steps[1]["delay"]["seconds"] >= 5


def test_radio_restart_uses_radio_reset_not_network_or_factory_reset():
    loader = type("Loader", (yaml.SafeLoader,), {})
    loader.add_constructor("!secret", lambda loader, node: loader.construct_scalar(node))
    commands = yaml.load((ROOT / "static/rest_command.yaml").read_text(), Loader=loader)
    assert "zigbee_radio_restart" in commands
    command = commands["zigbee_radio_restart"]
    assert command["url"] == "http://10.10.10.11/api2?action=4&cmd=1"
    assert command["method"] == "GET"
