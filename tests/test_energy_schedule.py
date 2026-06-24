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

        # Add Home Assistant's custom filters
        cls.env.filters['to_json'] = lambda x: json.dumps(x)
        cls.env.filters['combine'] = lambda a, b: {**a, **b}

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
            'sensor.optimal_charge_slots.events': [],
            'event.octopus_energy_electricity_15p0706167_2000050773706_current_day_rates.rates': [],
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.end_time': None,
        }
        mock_states = {
            'sensor.envoy_122322027694_available_battery_energy': '10000',  # 10kWh
            'input_number.battery_power_rate_kw': '9.6',
            'input_number.charge_price_threshold': '0.15',
        }

        result = self.render_template(
            self.events_template,
            **{**mock_attrs, **mock_states}
        )

        # Parse JSON and verify structure
        events = json.loads(result)
        self.assertIsInstance(events, list)
        self.assertEqual(len(events), 0)

    def test_template_handles_charge_threshold_events(self):
        """Test that template can process charge threshold events and returns valid JSON structure."""
        # Set "now" to 12:00 on Jan 15, so that the charge slot (Jan 16 00:30-05:00) is in the future
        ctx = HomeAssistantContext(now=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc))

        mock_attrs = {
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.end_time': None,
            'sensor.optimal_charge_slots.events': [
                {'start': '2025-01-16T00:30:00+00:00', 'end': '2025-01-16T05:00:00+00:00', 'intent': 'Charge', 'import_price': 0.05},
            ],
            'event.octopus_energy_electricity_15p0706167_2000050773706_current_day_rates.rates': [
                {'start': '2025-01-16T00:30:00+00:00', 'end': '2025-01-16T05:00:00+00:00', 'value_inc_vat': 0.05},
            ],
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.end_time': None,
            'sensor.optimal_discharge_slots.events': [
                {'start': '2025-01-15T23:40:00+00:00', 'end': '2025-01-16T00:25:00+00:00', 'intent': 'Discharge', 'export_price': 15.0},
            ],
            'event.octopus_energy_electricity_15p0706167_2000060833200_export_current_day_rates.rates': [
                {'start': '2025-01-15T23:00:00+00:00', 'end': '2025-01-16T00:00:00+00:00', 'value_inc_vat': 15.0},
                {'start': '2025-01-16T00:00:00+00:00', 'end': '2025-01-16T01:00:00+00:00', 'value_inc_vat': 15.0},
            ],
        }
        mock_states = {
            'sensor.envoy_122322027694_available_battery_energy': '10000',  # 10kWh
            'input_number.battery_power_rate_kw': '9.6',
            'sensor.octopus_energy_electricity_15p0706167_2000050773706_current_rate': '10.0',
            'sensor.octopus_energy_electricity_15p0706167_2000050773706_next_rate': '10.0',
            'input_number.battery_round_trip_efficiency': '0.9',
            'input_boolean.allow_discharge': 'on',
            'input_number.charge_price_threshold': '0.15',
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
        cls.env.filters['combine'] = lambda a, b: {**a, **b}

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
        - Free electricity session: Tuesday night 00:30-05:00 (already passed)
        - Import rate below threshold: Wednesday 00:30-05:00
        - Battery: 10kWh available, can discharge before charge slots

        Expected events:
        1. Pre-charge discharge for Wed 00:30-05:00: 23:40-00:25
        2. Charge slot (threshold next): 00:30-05:00
        """
        ctx = HomeAssistantContext(
            now=datetime(2025, 1, 14, 12, 0, 0, tzinfo=timezone.utc)
        )

        mock_attrs = {
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.start_time': '2025-01-14T00:30:00+00:00',
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.end_time': '2025-01-14T05:00:00+00:00',
            'sensor.optimal_charge_slots.events': [
                {'start': '2025-01-15T00:30:00+00:00', 'end': '2025-01-15T05:00:00+00:00', 'intent': 'Charge', 'import_price': 0.05},
            ],
            'event.octopus_energy_electricity_15p0706167_2000050773706_current_day_rates.rates': [
                {'start': '2025-01-15T00:30:00+00:00', 'end': '2025-01-15T05:00:00+00:00', 'value_inc_vat': 0.05},
            ],
            'sensor.optimal_discharge_slots.events': [
                {'start': '2025-01-14T23:40:00+00:00', 'end': '2025-01-15T00:25:00+00:00', 'intent': 'Discharge', 'export_price': 15.0},
            ],
            'event.octopus_energy_electricity_15p0706167_2000060833200_export_current_day_rates.rates': [
                {'start': '2025-01-14T23:00:00+00:00', 'end': '2025-01-15T00:00:00+00:00', 'value_inc_vat': 15.0},
                {'start': '2025-01-15T00:00:00+00:00', 'end': '2025-01-15T01:00:00+00:00', 'value_inc_vat': 15.0},
            ],
        }

        mock_states = {
            'sensor.envoy_122322027694_available_battery_energy': '10000',  # 10kWh
            'input_number.battery_power_rate_kw': '9.6',
            'sensor.octopus_energy_electricity_15p0706167_2000050773706_current_rate': '10.0',
            'sensor.octopus_energy_electricity_15p0706167_2000050773706_next_rate': '10.0',
            'input_number.battery_round_trip_efficiency': '0.9',
            'input_boolean.allow_discharge': 'on',
            'input_number.charge_price_threshold': '0.15',
        }

        result = self.render_template(
            self.events_template,
            context=ctx,
            **{**mock_attrs, **mock_states}
        )

        events = json.loads(result)

        # Saving sessions are no longer processed - only pre-discharge and charge expected
        expected_events = [
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
            'sensor.optimal_charge_slots.events': [
                {'start': '2025-01-14T23:30:00+00:00', 'end': '2025-01-15T05:00:00+00:00', 'intent': 'Charge', 'import_price': 0.0},
            ],
            # No cheap import rates
            'event.octopus_energy_electricity_15p0706167_2000050773706_current_day_rates.rates': [],
            # No saving sessions
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.end_time': None,
        }

        # Very low battery - only 1kWh (below 2kWh threshold)
        mock_states = {
            'sensor.envoy_122322027694_available_battery_energy': '1000',  # 1kWh - below threshold
            'input_number.battery_power_rate_kw': '9.6',
            'input_number.charge_price_threshold': '0.15',
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

    def test_allow_discharge_off_blocks_discharge_events(self):
        """
        Test that when allow_discharge is off, no discharge events are generated.

        Scenario: Same as comprehensive scenario with battery available for discharge,
        but allow_discharge is off.

        Expected events:
        1. Only the charge slot - no discharge event
        """
        ctx = HomeAssistantContext(
            now=datetime(2025, 1, 14, 12, 0, 0, tzinfo=timezone.utc)
        )

        mock_attrs = {
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.start_time': '2025-01-14T00:30:00+00:00',
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.end_time': '2025-01-14T05:00:00+00:00',
            'sensor.optimal_charge_slots.events': [
                {'start': '2025-01-15T00:30:00+00:00', 'end': '2025-01-15T05:00:00+00:00', 'intent': 'Charge', 'import_price': 0.05},
            ],
            'event.octopus_energy_electricity_15p0706167_2000050773706_current_day_rates.rates': [
                {'start': '2025-01-15T00:30:00+00:00', 'end': '2025-01-15T05:00:00+00:00', 'value_inc_vat': 0.05},
            ],
            'sensor.optimal_discharge_slots.events': [
                {'start': '2025-01-14T23:40:00+00:00', 'end': '2025-01-15T00:25:00+00:00', 'intent': 'Discharge', 'export_price': 15.0},
            ],
            'event.octopus_energy_electricity_15p0706167_2000060833200_export_current_day_rates.rates': [
                {'start': '2025-01-14T23:00:00+00:00', 'end': '2025-01-15T00:00:00+00:00', 'value_inc_vat': 15.0},
                {'start': '2025-01-15T00:00:00+00:00', 'end': '2025-01-15T01:00:00+00:00', 'value_inc_vat': 15.0},
            ],
        }

        mock_states = {
            'sensor.envoy_122322027694_available_battery_energy': '10000',  # 10kWh
            'input_number.battery_power_rate_kw': '9.6',
            'sensor.octopus_energy_electricity_15p0706167_2000050773706_current_rate': '10.0',
            'sensor.octopus_energy_electricity_15p0706167_2000050773706_next_rate': '10.0',
            'input_number.battery_round_trip_efficiency': '0.9',
            'input_boolean.allow_discharge': 'off',
            'input_number.charge_price_threshold': '0.15',
        }

        result = self.render_template(
            self.events_template,
            context=ctx,
            **{**mock_attrs, **mock_states}
        )

        events = json.loads(result)

        # No discharge events should appear when allow_discharge is off
        # Only the charge slot is expected
        expected_events = [
            {'intent': 'Charge', 'start': '2025-01-15T00:30:00+00:00', 'end': '2025-01-15T05:00:00+00:00'},
        ]

        assert_events_equal(self, events, expected_events)

    def test_export_price_single_rate(self):
        """Test that export_price is correctly set for a discharge slot within a single rate period."""
        ctx = HomeAssistantContext(now=datetime(2025, 1, 14, 12, 0, 0, tzinfo=timezone.utc))

        mock_attrs = {
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.end_time': None,
            'sensor.optimal_charge_slots.events': [],
            'event.octopus_energy_electricity_15p0706167_2000050773706_current_day_rates.rates': [],
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.end_time': None,
            'sensor.optimal_discharge_slots.events': [
                {'start': '2025-01-14T19:00:00+00:00', 'end': '2025-01-14T19:30:00+00:00', 'intent': 'Discharge', 'export_price': 15.5},
            ],
            'event.octopus_energy_electricity_15p0706167_2000060833200_export_current_day_rates.rates': [
                {'start': '2025-01-14T19:00:00+00:00', 'end': '2025-01-14T19:30:00+00:00', 'value_inc_vat': 15.5},
            ],
        }
        mock_states = {
            'sensor.octopus_energy_electricity_15p0706167_2000050773706_current_rate': '10.0',
            'sensor.octopus_energy_electricity_15p0706167_2000050773706_next_rate': '10.0',
            'input_number.battery_round_trip_efficiency': '0.9',
            'input_boolean.allow_discharge': 'on',
            'input_number.minimum_slot_length': '0',
            'input_number.charge_price_threshold': '0.15',
        }

        result = self.render_template(self.events_template, context=ctx, **{**mock_attrs, **mock_states})
        events = json.loads(result)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['intent'], 'Discharge')
        self.assertEqual(events[0]['export_price'], 15.5)

    def test_nearly_expired_slot_keeps_original_start(self):
        """A live slot (10:00-10:30) at 10:29 must stay emitted with its ORIGINAL start.

        Regression: the start used to be chopped to 'now' every minute (churn), and the
        min_slot_length gate measured remaining-from-now time, so a near-expired slot would
        be dropped. Neither should happen: the slot's own length is 30 min (>= min), and the
        start stays 10:00 regardless of how late in the slot we render.
        """
        ctx = HomeAssistantContext(now=datetime(2025, 1, 14, 10, 29, 0, tzinfo=timezone.utc))

        mock_attrs = {
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.end_time': None,
            'sensor.optimal_charge_slots.events': [],
            'event.octopus_energy_electricity_15p0706167_2000050773706_current_day_rates.rates': [],
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.end_time': None,
            'sensor.optimal_discharge_slots.events': [
                {'start': '2025-01-14T10:00:00+00:00', 'end': '2025-01-14T10:30:00+00:00', 'intent': 'Discharge', 'export_price': 15.5},
            ],
            'event.octopus_energy_electricity_15p0706167_2000060833200_export_current_day_rates.rates': [
                {'start': '2025-01-14T10:00:00+00:00', 'end': '2025-01-14T10:30:00+00:00', 'value_inc_vat': 15.5},
            ],
        }
        mock_states = {
            'sensor.octopus_energy_electricity_15p0706167_2000050773706_current_rate': '10.0',
            'sensor.octopus_energy_electricity_15p0706167_2000050773706_next_rate': '10.0',
            'input_number.battery_round_trip_efficiency': '0.9',
            'input_boolean.allow_discharge': 'on',
            'input_number.minimum_slot_length': '5',
            'input_number.charge_price_threshold': '0.15',
        }

        result = self.render_template(self.events_template, context=ctx, **{**mock_attrs, **mock_states})
        events = json.loads(result)

        expected = [
            {'intent': 'Discharge', 'start': '2025-01-14T10:00:00+00:00', 'end': '2025-01-14T10:30:00+00:00'},
        ]
        assert_events_equal(self, events, expected)

    def test_export_price_multiple_rates(self):
        """Test that export_price is the time-weighted average across multiple 30-min rate periods."""
        ctx = HomeAssistantContext(now=datetime(2025, 1, 14, 12, 0, 0, tzinfo=timezone.utc))

        mock_attrs = {
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.end_time': None,
            'sensor.optimal_charge_slots.events': [],
            'event.octopus_energy_electricity_15p0706167_2000050773706_current_day_rates.rates': [],
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.end_time': None,
            'sensor.optimal_discharge_slots.events': [
                {'start': '2025-01-14T23:40:00+00:00', 'end': '2025-01-15T00:25:00+00:00', 'intent': 'Discharge', 'export_price': 14.44},
            ],
            'event.octopus_energy_electricity_15p0706167_2000060833200_export_current_day_rates.rates': [
                {'start': '2025-01-14T23:00:00+00:00', 'end': '2025-01-15T00:00:00+00:00', 'value_inc_vat': 20.0},
                {'start': '2025-01-15T00:00:00+00:00', 'end': '2025-01-15T01:00:00+00:00', 'value_inc_vat': 10.0},
            ],
        }
        mock_states = {
            'sensor.octopus_energy_electricity_15p0706167_2000050773706_current_rate': '5.0',
            'sensor.octopus_energy_electricity_15p0706167_2000050773706_next_rate': '5.0',
            'input_number.battery_round_trip_efficiency': '0.9',
            'input_boolean.allow_discharge': 'on',
            'input_number.minimum_slot_length': '0',
            'input_number.charge_price_threshold': '0.15',
        }

        result = self.render_template(self.events_template, context=ctx, **{**mock_attrs, **mock_states})
        events = json.loads(result)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['intent'], 'Discharge')
        # Weighted average: (20 min * 20.0 + 25 min * 10.0) / 45 min = 14.44...
        expected_avg = (20 * 20.0 + 25 * 10.0) / 45
        self.assertAlmostEqual(events[0]['export_price'], expected_avg, places=2)

    def test_export_price_saving_session(self):
        """Test that export_price includes the saving session bonus."""
        ctx = HomeAssistantContext(now=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc))

        mock_attrs = {
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.end_time': None,
            'sensor.optimal_charge_slots.events': [],
            'event.octopus_energy_electricity_15p0706167_2000050773706_current_day_rates.rates': [],
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.start_time': '2025-01-15T19:00:00+00:00',
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.end_time': '2025-01-15T19:30:00+00:00',
            'sensor.optimal_discharge_slots.events': [
                {'start': '2025-01-15T19:00:00+00:00', 'end': '2025-01-15T19:30:00+00:00', 'intent': 'Discharge', 'export_price': 5.01},
            ],
            'event.octopus_energy_electricity_15p0706167_2000060833200_export_current_day_rates.rates': [
                {'start': '2025-01-15T19:00:00+00:00', 'end': '2025-01-15T19:30:00+00:00', 'value_inc_vat': 5.0},
            ],
        }
        mock_states = {
            'sensor.octopus_energy_electricity_15p0706167_2000050773706_current_rate': '3.0',
            'sensor.octopus_energy_electricity_15p0706167_2000050773706_next_rate': '3.0',
            'input_number.battery_round_trip_efficiency': '0.9',
            'input_boolean.allow_discharge': 'on',
            'input_number.minimum_slot_length': '0',
            'input_number.charge_price_threshold': '0.15',
        }

        result = self.render_template(self.events_template, context=ctx, **{**mock_attrs, **mock_states})
        events = json.loads(result)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['intent'], 'Discharge')
        self.assertEqual(events[0]['export_price'], 5.01)


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

    def test_charge_wins_on_overlap_at_boundary(self):
        """Charge should win when a Charge and Discharge event overlap at a boundary."""
        # Set "now" to be exactly at the boundary where both events overlap
        ctx = HomeAssistantContext(now=datetime(2025, 1, 15, 17, 0, 0))

        events = [
            {'start': '2025-01-15T16:00:00', 'end': '2025-01-15T17:00:00', 'intent': 'Discharge'},
            {'start': '2025-01-15T17:00:00', 'end': '2025-01-15T19:00:00', 'intent': 'Charge'},
        ]

        template = self.env.from_string(self.template)
        result = template.render(
            state_attr=lambda entity, attr: events if attr == 'events' else None,
            as_datetime=ctx.as_datetime,
            now=ctx.now,
            timedelta=ctx.timedelta,
        )

        # With strict boundary (start <= now < end), only Charge should match
        self.assertEqual(result.strip(), 'Charge')

    def test_charge_wins_when_both_overlap(self):
        """Charge should win when both Charge and Discharge overlap at the same time."""
        ctx = HomeAssistantContext(now=datetime(2025, 1, 15, 17, 30, 0))

        events = [
            {'start': '2025-01-15T17:00:00', 'end': '2025-01-15T18:00:00', 'intent': 'Discharge'},
            {'start': '2025-01-15T17:00:00', 'end': '2025-01-15T18:00:00', 'intent': 'Charge'},
        ]

        template = self.env.from_string(self.template)
        result = template.render(
            state_attr=lambda entity, attr: events if attr == 'events' else None,
            as_datetime=ctx.as_datetime,
            now=ctx.now,
            timedelta=ctx.timedelta,
        )

        # Charge should win over Discharge when both are active
        self.assertEqual(result.strip(), 'Charge')


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


class TestOptimalDischargeSavingSession(unittest.TestCase):
    """
    Test that the Optimal discharge slots sensor prioritises discharging during
    saving sessions, even when better export prices are available outside the
    session window, while still respecting the battery reserve (no flat battery).
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
        cls.env.filters['combine'] = lambda a, b: {**a, **b}

        cls.sensor = find_sensor_template(cls.config, 'Optimal discharge slots')
        if cls.sensor is None:
            raise ValueError("Could not find 'Optimal discharge slots' sensor in template.yaml")

        cls.events_template = get_template_attribute(cls.sensor, 'events')
        if cls.events_template is None:
            raise ValueError("Could not find 'events' attribute in Optimal discharge slots sensor")

    def render_template(self, template_str, context: HomeAssistantContext | None = None, **extra_vars):
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

    def _base_states(self, usable_kwh):
        """Battery sized so usable_kwh = available - reserve.

        With discharge_rate_kw=60, minutes_needed = usable_kwh / 60 * 60 = usable_kwh,
        so usable_kwh equals the number of dischargeable minutes.
        """
        return {
            'sensor.envoy_122322027694_available_battery_energy': str(int(usable_kwh * 1000)),
            'sensor.power_requirement_until_cheap_slot': '0',
            'input_number.battery_power_rate_kw': '60',
            'input_number.minimum_slot_length': '0',
        }

    def test_saving_session_minutes_filled_before_higher_priced_export(self):
        """
        With only enough battery for 30 minutes of discharge, the 30-minute saving
        session window (at a LOW export price) must be selected ahead of a
        higher-priced export window outside the session.
        """
        ctx = HomeAssistantContext(now=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc))

        mock_attrs = {
            # Saving session 19:00-19:30 at a low export price
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.start_time': '2025-01-15T19:00:00+00:00',
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.end_time': '2025-01-15T19:30:00+00:00',
            'event.octopus_energy_electricity_15p0706167_2000060833200_export_current_day_rates.rates': [
                # High-priced export window (would normally win) 17:00-17:30
                {'start': '2025-01-15T17:00:00+00:00', 'end': '2025-01-15T17:30:00+00:00', 'value_inc_vat': 30.0},
                # Low-priced export covering the saving session 19:00-19:30
                {'start': '2025-01-15T19:00:00+00:00', 'end': '2025-01-15T19:30:00+00:00', 'value_inc_vat': 5.0},
            ],
        }
        # Only 30 minutes of usable battery (usable_kwh == minutes at 60kW)
        mock_states = self._base_states(usable_kwh=30)

        result = self.render_template(self.events_template, context=ctx, **{**mock_attrs, **mock_states})

        events = json.loads(result)
        # The single selected discharge block must be the saving session window,
        # not the higher-priced export window.
        expected = [
            {'intent': 'Discharge', 'start': '2025-01-15T19:00:00+00:00', 'end': '2025-01-15T19:30:00+00:00'},
        ]
        assert_events_equal(self, events, expected)

    def test_saving_session_respects_reserve_no_flat_battery(self):
        """
        Reserve must still bound discharge: with usable_kwh of only 15 (15 min),
        only 15 minutes of the 30-minute saving session are selected, and because
        the window is filled tail-end-first, it is the LAST 15 minutes (19:15-19:30).
        """
        ctx = HomeAssistantContext(now=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc))

        mock_attrs = {
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.start_time': '2025-01-15T19:00:00+00:00',
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.end_time': '2025-01-15T19:30:00+00:00',
            'event.octopus_energy_electricity_15p0706167_2000060833200_export_current_day_rates.rates': [
                {'start': '2025-01-15T19:00:00+00:00', 'end': '2025-01-15T19:30:00+00:00', 'value_inc_vat': 5.0},
            ],
        }
        # available 30 kWh, reserve 15 kWh => usable 15 kWh => 15 minutes at 60kW
        mock_states = {
            'sensor.envoy_122322027694_available_battery_energy': '30000',
            'sensor.power_requirement_until_cheap_slot': '15000',
            'input_number.battery_power_rate_kw': '60',
            'input_number.minimum_slot_length': '0',
            'sensor.octopus_energy_electricity_15p0706167_2000050773706_current_rate': '10.0',
            'sensor.octopus_energy_electricity_15p0706167_2000050773706_next_rate': '10.0',
            'input_number.battery_round_trip_efficiency': '0.9',
        }

        result = self.render_template(self.events_template, context=ctx, **{**mock_attrs, **mock_states})
        events = json.loads(result)

        # Tail-end-first: the last 15 minutes of the session (19:15-19:30)
        expected = [
            {'intent': 'Discharge', 'start': '2025-01-15T19:15:00+00:00', 'end': '2025-01-15T19:30:00+00:00'},
        ]
        assert_events_equal(self, events, expected)


class TestEnergyIntentsSavingSessionFilterBypass(unittest.TestCase):
    """
    Test that the Energy intents export-price filter (block 4b) does NOT drop a
    discharge slot that overlaps a saving session, even when its export rate is
    below the minimum import rate.
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
        cls.env.filters['combine'] = lambda a, b: {**a, **b}

        cls.energy_intents_sensor = find_sensor_template(cls.config, 'Energy intents')
        cls.events_template = get_template_attribute(cls.energy_intents_sensor, 'events')

    def render_template(self, template_str, context: HomeAssistantContext | None = None, **extra_vars):
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

    def test_saving_session_bonus_includes_in_export_price(self):
        """
        Discharge slot inside a saving session has a low export rate (5p) but the
        bonus is included in export_price. With a low import threshold, the slot passes.
        """
        ctx = HomeAssistantContext(now=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc))

        mock_attrs = {
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.end_time': None,
            'sensor.optimal_charge_slots.events': [],
            'event.octopus_energy_electricity_15p0706167_2000050773706_current_day_rates.rates': [],
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.start_time': '2025-01-15T19:00:00+00:00',
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.end_time': '2025-01-15T19:30:00+00:00',
            'sensor.optimal_discharge_slots.events': [
                {'start': '2025-01-15T19:00:00+00:00', 'end': '2025-01-15T19:30:00+00:00', 'intent': 'Discharge', 'export_price': 5.01},
            ],
            'event.octopus_energy_electricity_15p0706167_2000060833200_export_current_day_rates.rates': [
                {'start': '2025-01-15T19:00:00+00:00', 'end': '2025-01-15T19:30:00+00:00', 'value_inc_vat': 5.0},
            ],
        }
        mock_states = {
            'sensor.octopus_energy_electricity_15p0706167_2000050773706_current_rate': '3.0',
            'sensor.octopus_energy_electricity_15p0706167_2000050773706_next_rate': '3.0',
            'input_number.battery_round_trip_efficiency': '0.9',
            'input_boolean.allow_discharge': 'on',
            'input_number.minimum_slot_length': '0',
            'input_number.charge_price_threshold': '0.15',
        }

        result = self.render_template(self.events_template, context=ctx, **{**mock_attrs, **mock_states})
        events = json.loads(result)

        expected = [
            {'intent': 'Discharge', 'start': '2025-01-15T19:00:00+00:00', 'end': '2025-01-15T19:30:00+00:00'},
        ]
        assert_events_equal(self, events, expected)

    def test_low_priced_discharge_without_saving_session_is_dropped(self):
        """
        Control: the same low-priced discharge slot WITHOUT a saving session is
        dropped by the export-price filter.
        """
        ctx = HomeAssistantContext(now=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc))

        mock_attrs = {
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.end_time': None,
            'sensor.optimal_charge_slots.events': [],
            'event.octopus_energy_electricity_15p0706167_2000050773706_current_day_rates.rates': [],
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_saving_sessions.end_time': None,
            'sensor.optimal_discharge_slots.events': [
                {'start': '2025-01-15T19:00:00+00:00', 'end': '2025-01-15T19:30:00+00:00', 'intent': 'Discharge', 'export_price': 5.0},
            ],
            'event.octopus_energy_electricity_15p0706167_2000060833200_export_current_day_rates.rates': [
                {'start': '2025-01-15T19:00:00+00:00', 'end': '2025-01-15T19:30:00+00:00', 'value_inc_vat': 5.0},
            ],
        }
        mock_states = {
            'sensor.octopus_energy_electricity_15p0706167_2000050773706_current_rate': '30.0',
            'sensor.octopus_energy_electricity_15p0706167_2000050773706_next_rate': '30.0',
            'input_number.battery_round_trip_efficiency': '0.9',
            'input_boolean.allow_discharge': 'on',
            'input_number.minimum_slot_length': '0',
            'input_number.charge_price_threshold': '0.15',
        }

        result = self.render_template(self.events_template, context=ctx, **{**mock_attrs, **mock_states})
        events = json.loads(result)

        assert_events_equal(self, events, [])


class TestOptimalChargeSlots(unittest.TestCase):
    """Test cases for Optimal charge slots sensor."""

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
        cls.env.filters['combine'] = lambda a, b: {**a, **b}

        cls.sensor = find_sensor_template(cls.config, 'Optimal charge slots')
        if cls.sensor is None:
            raise ValueError("Could not find 'Optimal charge slots' sensor in template.yaml")

        cls.events_template = get_template_attribute(cls.sensor, 'events')
        if cls.events_template is None:
            raise ValueError("Could not find 'events' attribute in Optimal charge slots sensor")

    def render_template(self, template_str, context: HomeAssistantContext | None = None, **extra_vars):
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

    def test_empty_slots(self):
        ctx = HomeAssistantContext(now=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc))

        mock_attrs = {
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.end_time': None,
            'event.octopus_energy_electricity_15p0706167_2000050773706_current_day_rates.rates': [],
        }
        mock_states = {
            'input_number.charge_price_threshold': '0.15',
        }

        result = self.render_template(self.events_template, context=ctx, **{**mock_attrs, **mock_states})
        events = json.loads(result)

        self.assertEqual(events, [])

    def test_free_electricity_session(self):
        ctx = HomeAssistantContext(now=datetime(2025, 1, 14, 12, 0, 0, tzinfo=timezone.utc))

        mock_attrs = {
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.start_time': '2025-01-14T23:30:00+00:00',
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.end_time': '2025-01-15T05:00:00+00:00',
            'event.octopus_energy_electricity_15p0706167_2000050773706_current_day_rates.rates': [],
        }
        mock_states = {
            'input_number.charge_price_threshold': '0.15',
        }

        result = self.render_template(self.events_template, context=ctx, **{**mock_attrs, **mock_states})
        events = json.loads(result)

        # No import rates provided, so import_price is None
        expected = [
            {'intent': 'Charge', 'start': '2025-01-14T23:30:00+00:00', 'end': '2025-01-15T05:00:00+00:00'},
        ]
        assert_events_equal(self, events, expected)

    def test_import_rates_below_threshold(self):
        ctx = HomeAssistantContext(now=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc))

        mock_attrs = {
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.end_time': None,
            'event.octopus_energy_electricity_15p0706167_2000050773706_current_day_rates.rates': [
                {'start': '2025-01-16T00:30:00+00:00', 'end': '2025-01-16T05:00:00+00:00', 'value_inc_vat': 0.05},
                {'start': '2025-01-16T05:00:00+00:00', 'end': '2025-01-16T05:30:00+00:00', 'value_inc_vat': 0.20},
            ],
        }
        mock_states = {
            'input_number.charge_price_threshold': '0.15',
        }

        result = self.render_template(self.events_template, context=ctx, **{**mock_attrs, **mock_states})
        events = json.loads(result)

        expected = [
            {'intent': 'Charge', 'start': '2025-01-16T00:30:00+00:00', 'end': '2025-01-16T05:00:00+00:00', 'import_price': 0.05},
        ]
        assert_events_equal(self, events, expected)

    def test_free_session_splits_import_rate(self):
        ctx = HomeAssistantContext(now=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc))

        mock_attrs = {
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.start_time': '2025-01-16T00:00:00+00:00',
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.end_time': '2025-01-16T01:00:00+00:00',
            'event.octopus_energy_electricity_15p0706167_2000050773706_current_day_rates.rates': [
                {'start': '2025-01-16T00:30:00+00:00', 'end': '2025-01-16T05:00:00+00:00', 'value_inc_vat': 0.05},
            ],
        }
        mock_states = {
            'input_number.charge_price_threshold': '0.15',
        }

        result = self.render_template(self.events_template, context=ctx, **{**mock_attrs, **mock_states})
        events = json.loads(result)

        # Free session 00:00-01:00 splits the import rate 00:30-05:00:
        # - 00:00-01:00: free (price 0)
        # - 01:00-05:00: import after free (price 0.05)
        expected = [
            {'intent': 'Charge', 'start': '2025-01-16T00:00:00+00:00', 'end': '2025-01-16T01:00:00+00:00'},
            {'intent': 'Charge', 'start': '2025-01-16T01:00:00+00:00', 'end': '2025-01-16T05:00:00+00:00'},
        ]
        assert_events_equal(self, events, expected)
        self.assertEqual(len(events), 2)
        self.assertAlmostEqual(events[0]['import_price'], 0.0, places=4)
        self.assertAlmostEqual(events[1]['import_price'], 0.05, places=4)

    def test_cross_midnight_merges_current_and_next_day_rates(self):
        """A cheap block spanning midnight should merge current + next day rates into one slot."""
        ctx = HomeAssistantContext(now=datetime(2025, 1, 15, 22, 0, 0, tzinfo=timezone.utc))

        mock_attrs = {
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.start_time': None,
            'calendar.octopus_energy_a_fad3b08a_octoplus_free_electricity_session.end_time': None,
            'event.octopus_energy_electricity_15p0706167_2000050773706_current_day_rates.rates': [
                {'start': '2025-01-15T23:30:00+00:00', 'end': '2025-01-16T00:00:00+00:00', 'value_inc_vat': 0.05},
            ],
            'event.octopus_energy_electricity_15p0706167_2000050773706_next_day_rates.rates': [
                {'start': '2025-01-16T00:00:00+00:00', 'end': '2025-01-16T05:30:00+00:00', 'value_inc_vat': 0.05},
            ],
        }
        mock_states = {
            'input_number.charge_price_threshold': '0.15',
        }

        result = self.render_template(self.events_template, context=ctx, **{**mock_attrs, **mock_states})
        events = json.loads(result)

        # The 23:30-00:00 (current day) and 00:00-05:30 (next day) cheap blocks share a
        # price and are adjacent, so they merge into a single continuous charge slot.
        expected = [
            {'intent': 'Charge', 'start': '2025-01-15T23:30:00+00:00', 'end': '2025-01-16T05:30:00+00:00', 'import_price': 0.05},
        ]
        assert_events_equal(self, events, expected)
        self.assertEqual(len(events), 1)


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
            'Optimal charge slots',
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
