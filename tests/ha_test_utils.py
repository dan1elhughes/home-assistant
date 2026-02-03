"""
Shared test utilities for Home Assistant template testing.

These classes mock Home Assistant functions for testing Jinja2 templates
without requiring a running HA instance.
"""

import unittest
from datetime import datetime, timedelta, timezone


class MockDateTime:
    """Mock datetime object that behaves like Home Assistant's as_datetime result."""

    def __init__(self, dt: datetime):
        self._dt = dt
        self.weekday = self._dt.weekday
        self.minute = self._dt.minute
        self.second = self._dt.second
        self.microsecond = self._dt.microsecond
        self.tzinfo = self._dt.tzinfo

    def _compare(self, other, op):
        """Helper for comparisons that handles timezone-aware vs naive."""
        if isinstance(other, MockDateTime):
            other_dt = other._dt
        else:
            other_dt = other

        if self._dt.tzinfo is not None and other_dt.tzinfo is None:
            self_naive = self._dt.replace(tzinfo=None)
            return op(self_naive, other_dt)
        elif self._dt.tzinfo is None and other_dt.tzinfo is not None:
            other_naive = other_dt.replace(tzinfo=None)
            return op(self._dt, other_naive)
        return op(self._dt, other_dt)

    def strftime(self, fmt: str) -> str:
        return self._dt.strftime(fmt)

    def isoformat(self) -> str:
        return self._dt.isoformat()

    def replace(self, **kwargs):
        return MockDateTime(self._dt.replace(**kwargs))

    def __lt__(self, other):
        return self._compare(other, lambda a, b: a < b)

    def __le__(self, other):
        return self._compare(other, lambda a, b: a <= b)

    def __gt__(self, other):
        return self._compare(other, lambda a, b: a > b)

    def __ge__(self, other):
        return self._compare(other, lambda a, b: a >= b)

    def __eq__(self, other):
        if isinstance(other, MockDateTime):
            return self._dt == other._dt
        return self._dt == other

    def __sub__(self, other):
        if isinstance(other, MockDateTime):
            return self._dt - other._dt
        result = self._dt - other
        if isinstance(result, timedelta):
            return result
        return MockDateTime(result)

    def __add__(self, other):
        if isinstance(other, MockDateTime):
            raise TypeError("Cannot add two MockDateTime objects")
        result = self._dt + other
        return MockDateTime(result)


class HomeAssistantContext:
    """Provides mock Home Assistant functions for template testing."""

    def __init__(self, now: datetime | None = None):
        if now is not None:
            self._now = now
        else:
            self._now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    def now(self):
        """Mock Home Assistant's now() function."""
        return MockDateTime(self._now)

    def as_datetime(self, value):
        """Mock Home Assistant's as_datetime() function."""
        if isinstance(value, datetime):
            return MockDateTime(value)
        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return MockDateTime(dt)
            except ValueError:
                pass
            formats = [
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M",
                "%Y-%m-%d %H:%M",
            ]
            for fmt in formats:
                try:
                    dt = datetime.strptime(value, fmt)
                    return MockDateTime(dt)
                except ValueError:
                    continue
        raise ValueError(f"Cannot parse datetime: {value}")

    def timedelta(self, **kwargs):
        """Mock Home Assistant's timedelta() function."""
        return timedelta(**kwargs)


def assert_events_equal(test_case: unittest.TestCase, actual_events: list, expected_events: list):
    """
    Assert that actual events match expected events exactly.

    Args:
        test_case: The unittest.TestCase instance (for assertions)
        actual_events: List of event dicts from the template
        expected_events: List of expected event dicts with 'intent', 'start', 'end'

    Each event should have:
        - intent: 'Charge' or 'Discharge'
        - start: ISO format datetime string
        - end: ISO format datetime string
    """
    test_case.assertIsInstance(actual_events, list,
        "actual_events must be a list")

    test_case.assertEqual(len(actual_events), len(expected_events),
        f"Expected {len(expected_events)} events, got {len(actual_events)}:\n"
        f"Actual: {actual_events}\n"
        f"Expected: {expected_events}")

    for i, expected in enumerate(expected_events):
        actual = actual_events[i]

        test_case.assertEqual(actual.get('intent'), expected.get('intent'),
            f"Event {i} intent: expected '{expected.get('intent')}', "
            f"got '{actual.get('intent')}'")

        test_case.assertEqual(actual.get('start'), expected.get('start'),
            f"Event {i} start: expected '{expected.get('start')}', "
            f"got '{actual.get('start')}'")

        test_case.assertEqual(actual.get('end'), expected.get('end'),
            f"Event {i} end: expected '{expected.get('end')}', "
            f"got '{actual.get('end')}'")
