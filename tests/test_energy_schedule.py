"""
Unit tests for energy schedule templates extracted from template.yaml.

These tests parse the actual Home Assistant template.yaml configuration
and test the template logic without requiring a running HA instance.
"""

import json
import unittest
import yaml
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Environment, BaseLoader, select_autoescape

from tests.ha_test_utils import HomeAssistantContext, assert_events_equal


def load_template_yaml():
    """Load and parse the template.yaml configuration file."""
    template_path = Path(__file__).parent.parent / 'static' / 'template.yaml'
    with open(template_path, 'r') as f:
        return yaml.safe_load(f)


def find_sensor_template(config, sensor_name):
    """Find a specific sensor's template from the configuration."""
    for section in config:
        if 'sensor' in section:
            for sensor in section['sensor']:
                if sensor.get('name') == sensor_name:
                    return sensor
    return None


def get_template_attribute(sensor_config, attr_name):
    """Get a template attribute from a sensor configuration."""
    if 'attributes' in sensor_config and attr_name in sensor_config['attributes']:
        return sensor_config['attributes'][attr_name]
    return None


class TestEnergyScheduleTemplates(unittest.TestCase):
    """Test cases for energy schedule templates from template.yaml."""

    @classmethod
    def setUpClass(cls):
        """Load template configuration and set up Jinja2 environment."""
        cls.config = load_template_yaml()
        cls.env = Environment(
            loader=BaseLoader(),
            autoescape=False,  # Disable autoescape for template testing
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add Home Assistant's to_json filter
        cls.env.filters['to_json'] = lambda x: json.dumps(x)

        # Find the Energy intents sensor
        cls.energy_intents_sensor = find_sensor_template(cls.config, 'Energy intents')
        if cls.energy_intents_sensor is None:
            raise ValueError("Could not find 'Energy intents' sensor in template.yaml")

        # Extract the events template
        cls.events_template = get_template_attribute(cls.energy_intents_sensor, 'events')
        if cls.events_template is None:
            raise ValueError("Could not find 'events' attribute in Energy intents sensor")

    def render_template(self, template_str, context: HomeAssistantContext | None = None, **extra_vars):
        """Helper to render a template with HA context."""
        ctx = context or HomeAssistantContext()

        # Build mock state_attr function that looks up in extra_vars
        def mock_state_attr(entity_id, attr):
            key = f"{entity_id}.{attr}"
            return extra_vars.get(key)

        def mock_states(entity_id):
            # Try both 'states.entity_id' and just 'entity_id'
            key = f"states.{entity_id}"
            result = extra_vars.get(key)
            if result is None:
                result = extra_vars.get(entity_id, '')
            return result

        template = self.env.from_string(template_str)
        result = template.render(
            as_datetime=ctx.as_datetime,
            now=ctx.now,
            timedelta=ctx.timedelta,
            state_attr=mock_state_attr,
            states=mock_states,
        )
        return result.strip()

    def test_energy_intents_sensor_exists(self):
        """Verify the Energy intents sensor is defined in template.yaml."""
        self.assertIsNotNone(self.energy_intents_sensor)
        self.assertEqual(self.energy_intents_sensor['name'], 'Energy intents')

    def test_events_attribute_exists(self):
        """Verify the events attribute template exists."""
        self.assertIsNotNone(self.events_template)
        self.assertIn('ns', self.events_template.lower())

    def test_empty_events_list(self):
        """Test that template can process off-peak sensor events and returns valid JSON structure."""
        ctx = HomeAssistantContext(now=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc))

        mock_attrs = {
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.end_time': None,
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.current_start': None,
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.current_end': None,
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.next_start': None,
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.next_end': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.end_time': None,
        }
        mock_states = {
            'sensor.envoy_122322027694_available_battery_energy': '10000',  # 10kWh
            'input_number.minimum_discharge_threshold': '2',
            'input_number.battery_power_rate_kw': '9.6',
        }

        result = self.render_template(
            self.events_template,
            **{**mock_attrs, **mock_states}
        )

        # Parse JSON and verify structure
        events = json.loads(result)
        self.assertIsInstance(events, list)
        self.assertEqual(len(events), 0)

    def test_template_handles_off_peak_events(self):
        """Test that template can process off-peak sensor events and returns valid JSON structure."""
        # Set "now" to 12:00 on Jan 15, so that "current" off-peak (00:30-05:00) has already passed
        # and the "next" off-peak (Jan 16 00:30-05:00) is in the future
        ctx = HomeAssistantContext(now=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc))

        mock_attrs = {
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.end_time': None,
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.current_start': '2025-01-15T00:30:00+00:00',
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.current_end': '2025-01-15T05:00:00+00:00',
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.next_start': '2025-01-16T00:30:00+00:00',
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.next_end': '2025-01-16T05:00:00+00:00',
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.end_time': None,
        }
        mock_states = {
            'sensor.envoy_122322027694_available_battery_energy': '10000',  # 10kWh
            'input_number.minimum_discharge_threshold': '2',
            'input_number.battery_power_rate_kw': '9.6',
        }

        result = self.render_template(
            self.events_template,
            context=ctx,
            **{**mock_attrs, **mock_states}
        )

        # Parse JSON and verify structure
        events = json.loads(result)
        self.assertIsInstance(events, list)

        expected_events = [
            {'intent': 'Discharge', 'start': '2025-01-15T23:40:00+00:00', 'end': '2025-01-16T00:25:00+00:00'},
            {'intent': 'Charge', 'start': '2025-01-16T00:30:00+00:00', 'end': '2025-01-16T05:00:00+00:00'},
        ]

        assert_events_equal(self, events, expected_events)

    def test_template_handles_saving_sessions(self):
        """Test that the template can process saving session events and returns valid JSON structure."""
        ctx = HomeAssistantContext(now=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc))

        mock_attrs = {
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.end_time': None,
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.current_start': None,
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.current_end': None,
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.next_start': None,
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.next_end': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.start_time': '2025-01-15T17:00:00+00:00',
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.end_time': '2025-01-15T18:30:00+00:00',
        }
        mock_states = {
            'sensor.envoy_122322027694_available_battery_energy': '5000',
            'input_number.minimum_discharge_threshold': '2',
            'input_number.battery_power_rate_kw': '9.6',
        }

        result = self.render_template(
            self.events_template,
            context=ctx,
            **{**mock_attrs, **mock_states}
        )

        # Parse JSON and verify structure
        events = json.loads(result)
        self.assertIsInstance(events, list)

        expected_events = [
            {'intent': 'Discharge', 'start': '2025-01-15T17:00:00+00:00', 'end': '2025-01-15T18:30:00+00:00'},
        ]

        assert_events_equal(self, events, expected_events)


class TestEnergyIntentsComprehensive(unittest.TestCase):
    """
    Comprehensive test for Energy intents sensor with all input sources.

    This test simulates a realistic scenario with:
    - Free electricity session (calendar)
    - Off-peak sensor (current and next)
    - Saving session (calendar)
    - Battery with enough charge for pre-discharge
    """

    @classmethod
    def setUpClass(cls):
        cls.config = load_template_yaml()
        cls.env = Environment(
            loader=BaseLoader(),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        cls.env.filters['to_json'] = lambda x: json.dumps(x)

        cls.energy_intents_sensor = find_sensor_template(cls.config, 'Energy intents')
        if cls.energy_intents_sensor is None:
            raise ValueError("Could not find 'Energy intents' sensor in template.yaml")

        cls.events_template = get_template_attribute(cls.energy_intents_sensor, 'events')
        if cls.events_template is None:
            raise ValueError("Could not find 'events' attribute")

    def render_template(self, template_str, context: HomeAssistantContext | None = None, **extra_vars):
        """Helper to render a template with HA context."""
        ctx = context or HomeAssistantContext()

        def mock_state_attr(entity_id, attr):
            return extra_vars.get(f"{entity_id}.{attr}")

        def mock_states(entity_id):
            result = extra_vars.get(f"states.{entity_id}")
            if result is None:
                result = extra_vars.get(entity_id, '')
            return result

        template = self.env.from_string(template_str)
        result = template.render(
            as_datetime=ctx.as_datetime,
            now=ctx.now,
            timedelta=ctx.timedelta,
            state_attr=mock_state_attr,
            states=mock_states,
        )
        return result.strip()

    def test_comprehensive_energy_scenario(self):
        """
        Test a comprehensive energy scenario with all input sources.

        Scenario: It's Tuesday Jan 14, 2025 at noon.
        - Free electricity session: Tuesday night 00:30-05:00 (already passed, but future relative to "now" is 00:30 Wed)
        - Off-peak sensor: current passed, next is Wednesday 00:30-05:00
        - Saving session: Tuesday 17:00-19:00 (future)
        - Battery: 10kWh available, can discharge before charge slots

        Expected events:
        1. Saving session discharge: 17:00-19:00
        2. Pre-charge discharge for Wed 00:30-05:00: 23:30-00:25
        3. Charge slot (off-peak next): 00:30-05:00
        """
        ctx = HomeAssistantContext(
            now=datetime(2025, 1, 14, 12, 0, 0, tzinfo=timezone.utc)
        )

        mock_attrs = {
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.start_time': '2025-01-14T00:30:00+00:00',
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.end_time': '2025-01-14T05:00:00+00:00',
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.current_start': '2025-01-14T00:30:00+00:00',
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.current_end': '2025-01-14T05:00:00+00:00',
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.next_start': '2025-01-15T00:30:00+00:00',
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.next_end': '2025-01-15T05:00:00+00:00',
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.start_time': '2025-01-14T17:00:00+00:00',
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.end_time': '2025-01-14T19:00:00+00:00',
        }

        mock_states = {
            'sensor.envoy_122322027694_available_battery_energy': '10000',  # 10kWh
            'input_number.minimum_discharge_threshold': '2',
            'input_number.battery_power_rate_kw': '9.6',
        }

        result = self.render_template(
            self.events_template,
            context=ctx,
            **{**mock_attrs, **mock_states}
        )

        events = json.loads(result)

        expected_events = [
            {'intent': 'Discharge', 'start': '2025-01-14T17:00:00+00:00', 'end': '2025-01-14T19:00:00+00:00'},
            {'intent': 'Discharge', 'start': '2025-01-14T23:40:00+00:00', 'end': '2025-01-15T00:25:00+00:00'},
            {'intent': 'Charge', 'start': '2025-01-15T00:30:00+00:00', 'end': '2025-01-15T05:00:00+00:00'},
        ]

        assert_events_equal(self, events, expected_events)

    def test_no_battery_prevents_pre_discharge(self):
        """
        Test that low battery prevents pre-charge discharge generation.

        Scenario: Battery has very little charge, so pre-discharge slots
        should not be generated (or should be minimal).
        """
        ctx = HomeAssistantContext(
            now=datetime(2025, 1, 14, 12, 0, 0, tzinfo=timezone.utc)
        )

        mock_attrs = {
            # Free electricity - Tuesday night
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.start_time': '2025-01-14T23:30:00+00:00',
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.end_time': '2025-01-15T05:00:00+00:00',
            # No off-peak events
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.current_start': None,
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.current_end': None,
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.next_start': None,
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.next_end': None,
            # No saving sessions
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.end_time': None,
        }

        # Very low battery - only 1kWh (below 2kWh threshold)
        mock_states = {
            'sensor.envoy_122322027694_available_battery_energy': '1000',  # 1kWh - below threshold
            'input_number.minimum_discharge_threshold': '2',
            'input_number.battery_power_rate_kw': '9.6',
        }

        result = self.render_template(
            self.events_template,
            context=ctx,
            **{**mock_attrs, **mock_states}
        )

        events = json.loads(result)

        # With very low battery (1kWh) below threshold (2kWh), no pre-discharge is generated
        # Only the charge slot is expected
        expected_events = [
            {'intent': 'Charge', 'start': '2025-01-14T23:30:00+00:00', 'end': '2025-01-15T05:00:00+00:00'},
        ]

        assert_events_equal(self, events, expected_events)

    def test_multiple_saving_sessions(self):
        """Test handling of saving session calendar event."""
        ctx = HomeAssistantContext(
            now=datetime(2025, 1, 14, 12, 0, 0, tzinfo=timezone.utc)
        )

        mock_attrs = {
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.end_time': None,
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.current_start': None,
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.current_end': None,
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.next_start': None,
            'binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak.next_end': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.start_time': '2025-01-14T17:00:00+00:00',
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.end_time': '2025-01-14T19:00:00+00:00',
        }

        mock_states = {
            'sensor.envoy_122322027694_available_battery_energy': '10000',
            'input_number.minimum_discharge_threshold': '2',
            'input_number.battery_power_rate_kw': '9.6',
        }

        result = self.render_template(
            self.events_template,
            context=ctx,
            **{**mock_attrs, **mock_states}
        )

        events = json.loads(result)

        expected_events = [
            {'intent': 'Discharge', 'start': '2025-01-14T17:00:00+00:00', 'end': '2025-01-14T19:00:00+00:00'},
        ]

        assert_events_equal(self, events, expected_events)


class TestCurrentEnergyIntent(unittest.TestCase):
    """Test cases for Current energy intent sensor."""

    @classmethod
    def setUpClass(cls):
        cls.config = load_template_yaml()
        cls.env = Environment(
            loader=BaseLoader(),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        cls.sensor = find_sensor_template(cls.config, 'Current energy intent')
        if cls.sensor is None:
            raise ValueError("Could not find 'Current energy intent' sensor in template.yaml")

        cls.template = cls.sensor.get('state', '')

    def test_sensor_exists(self):
        """Verify the Current energy intent sensor is defined."""
        self.assertIsNotNone(self.sensor)

    def test_template_structure(self):
        """Verify the template has expected structure."""
        self.assertIn('events', self.template)
        self.assertIn('for', self.template.lower())

    def test_idle_when_no_events(self):
        """Test that sensor returns Idle when no events are active."""
        ctx = HomeAssistantContext(now=datetime(2025, 1, 15, 12, 0, 0))

        # Events at times that don't overlap with "now"
        events = [
            {'start': '2025-01-15T02:00:00', 'end': '2025-01-15T05:00:00', 'intent': 'Charge'},
            {'start': '2025-01-15T17:00:00', 'end': '2025-01-15T19:00:00', 'intent': 'Discharge'},
        ]

        template = self.env.from_string(self.template)
        result = template.render(
            state_attr=lambda entity, attr: events if attr == 'events' else None,
            as_datetime=ctx.as_datetime,
            now=ctx.now,
            timedelta=ctx.timedelta,
        )

        self.assertEqual(result.strip(), 'Idle')

    def test_shows_active_charge_intent(self):
        """Test that sensor shows Charge when a charge event is active."""
        # Set "now" to be during a charge event
        ctx = HomeAssistantContext(now=datetime(2025, 1, 15, 3, 0, 0))

        events = [
            {'start': '2025-01-15T02:00:00', 'end': '2025-01-15T05:00:00', 'intent': 'Charge'},
        ]

        template = self.env.from_string(self.template)
        result = template.render(
            state_attr=lambda entity, attr: events if attr == 'events' else None,
            as_datetime=ctx.as_datetime,
            now=ctx.now,
            timedelta=ctx.timedelta,
        )

        self.assertEqual(result.strip(), 'Charge')

    def test_shows_active_discharge_intent(self):
        """Test that sensor shows Discharge when a discharge event is active."""
        # Set "now" to be during a discharge event
        ctx = HomeAssistantContext(now=datetime(2025, 1, 15, 18, 0, 0))

        events = [
            {'start': '2025-01-15T17:00:00', 'end': '2025-01-15T19:00:00', 'intent': 'Discharge'},
        ]

        template = self.env.from_string(self.template)
        result = template.render(
            state_attr=lambda entity, attr: events if attr == 'events' else None,
            as_datetime=ctx.as_datetime,
            now=ctx.now,
            timedelta=ctx.timedelta,
        )

        self.assertEqual(result.strip(), 'Discharge')


class TestNextEnergyIntent(unittest.TestCase):
    """Test cases for Next energy intent sensor."""

    @classmethod
    def setUpClass(cls):
        cls.config = load_template_yaml()
        cls.env = Environment(
            loader=BaseLoader(),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        cls.sensor = find_sensor_template(cls.config, 'Next energy intent')
        if cls.sensor is None:
            raise ValueError("Could not find 'Next energy intent' sensor in template.yaml")

        cls.template = cls.sensor.get('state', '')

    def test_sensor_exists(self):
        """Verify the Next energy intent sensor is defined."""
        self.assertIsNotNone(self.sensor)

    def test_shows_current_intent(self):
        """Test showing current intent when active."""
        ctx = HomeAssistantContext(now=datetime(2025, 1, 15, 3, 0, 0))

        events = [
            {'start': '2025-01-15T02:00:00', 'end': '2025-01-15T05:00:00', 'intent': 'Charge'},
        ]

        template = self.env.from_string(self.template)
        result = template.render(
            state_attr=lambda entity, attr: events if attr == 'events' else None,
            as_datetime=ctx.as_datetime,
            now=ctx.now,
            timedelta=ctx.timedelta,
        )

        self.assertIn('Charge', result)
        self.assertIn('until', result)
        self.assertIn('05:00', result)

    def test_shows_next_intent(self):
        """Test showing next intent when no current intent."""
        ctx = HomeAssistantContext(now=datetime(2025, 1, 15, 1, 0, 0))

        events = [
            {'start': '2025-01-15T02:00:00', 'end': '2025-01-15T05:00:00', 'intent': 'Charge'},
        ]

        template = self.env.from_string(self.template)
        result = template.render(
            state_attr=lambda entity, attr: events if attr == 'events' else None,
            as_datetime=ctx.as_datetime,
            now=ctx.now,
            timedelta=ctx.timedelta,
        )

        self.assertIn('Charge', result)
        self.assertIn('at', result)
        self.assertIn('02:00', result)

    def test_shows_none_when_no_events(self):
        """Test showing None when no events exist."""
        ctx = HomeAssistantContext()

        events = []

        template = self.env.from_string(self.template)
        result = template.render(
            state_attr=lambda entity, attr: events if attr == 'events' else None,
            as_datetime=ctx.as_datetime,
            now=ctx.now,
            timedelta=ctx.timedelta,
        )

        self.assertEqual(result.strip(), 'None')


class TestTemplateIntegrity(unittest.TestCase):
    """Tests to verify template.yaml structure is valid."""

    def test_yaml_is_valid(self):
        """Verify template.yaml can be parsed as valid YAML."""
        config = load_template_yaml()
        self.assertIsInstance(config, list)
        self.assertGreater(len(config), 0)

    def test_required_sensors_exist(self):
        """Verify all expected energy-related sensors exist."""
        config = load_template_yaml()

        required_sensors = [
            'Energy intents',
            'Current energy intent',
            'Next energy intent',
            'Battery total power',
            'Battery total discharge power',
            'Battery total charge power',
        ]

        found_sensors = set()
        for section in config:
            if 'sensor' in section:
                for sensor in section['sensor']:
                    name = sensor.get('name', '')
                    if name in required_sensors:
                        found_sensors.add(name)

        missing = set(required_sensors) - found_sensors
        self.assertEqual(missing, set(), f"Missing sensors: {missing}")


if __name__ == '__main__':
    unittest.main()
