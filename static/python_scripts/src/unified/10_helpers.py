"""
Unified battery schedule — pure function for HA python_script sandbox.

SANDBOX CONSTRAINT
------------------
Home Assistant python_scripts run in a sandbox that forbids ``import``
statements.  This module therefore contains NO imports in its core logic.
The function ``compute_unified_schedule`` uses only Python builtins.

TIME REPRESENTATION
-------------------
All times are passed as **epoch seconds** (int/float), not datetime
objects.  The pure function performs arithmetic directly on these
int/float values (e.g. ``epoch + n * 60`` for n minutes).

INJECTED CALLABLES
------------------
Because no stdlib modules are available, callables are injected as
parameters:

  - ``epoch_to_iso(epoch_seconds) -> str`` — formats an epoch as ISO
    string (used in later slices for output serialisation).
  - ``add_minutes(epoch_seconds, n) -> epoch_seconds`` — adds n minutes
    (equivalent to ``epoch + n * 60`` but provides a consistent API).

ASSEMBLY
--------
This module is ASSEMBLED at build time from fragments in
static/python_scripts/src/unified/ (10_helpers, 20_dp, 30_events, 40_api)
plus the HA glue (90_glue).
"""


# --- Slice 2: per-minute transition valuation ---
# charge_value returns None when charging is unavailable (no import price
# and not free); discharge_value returns None when discharge is disallowed
# or no export price; otherwise they return the signed value contribution
# (in the caller's unit, e.g. pence) of moving ONE step at that minute.
#
# Efficiency modelling choice: round-trip efficiency is applied once on
# the import (charge) side.  The discharge value is simply
# (export_price + bonus) * step_kwh — no further efficiency discount,
# because that penalty is already factored into the charge cost.


def rate_at(rate_periods, minute_epoch):
    """Return price of first rate period containing minute_epoch, else None."""
    for period in rate_periods:
        if period["start"] <= minute_epoch < period["end"]:
            return period["price"]
    return None


def in_window(window, minute_epoch):
    """Return True iff window is not None and contains minute_epoch."""
    if window is None:
        return False
    return window["start"] <= minute_epoch < window["end"]


def in_any_window(windows, minute_epoch):
    """Return True iff minute_epoch falls in any window (start <= e < end)."""
    for w in windows:
        if w["start"] <= minute_epoch < w["end"]:
            return True
    return False


def bonus_at(saving_bonus_events, minute_epoch):
    """Return bonus_pence of first event containing minute_epoch, else 0.0."""
    for event in saving_bonus_events:
        if event["start"] <= minute_epoch < event["end"]:
            return event["bonus_pence"]
    return 0.0


def charge_value(minute_epoch, import_rates, free_sessions, efficiency, step_kwh,
                 charge_price_threshold=None):
    """Value (net contribution to objective, can be negative) of charging ONE step.

    Charging costs: import_price * (step_kwh / efficiency).  Inside a free
    session cost is 0.  Returns None if charging is unavailable this minute
    (no import rate and not free, or price above threshold).
    """
    if in_any_window(free_sessions, minute_epoch):
        return 0.0
    import_price = rate_at(import_rates, minute_epoch)
    if import_price is None:
        return None
    if charge_price_threshold is not None and import_price > charge_price_threshold:
        return None
    return -(import_price * (step_kwh / efficiency))


def discharge_value(minute_epoch, import_rates, export_rates, saving_bonus_events,
                    efficiency, step_kwh, allow_discharge,
                    discharge_price_threshold=None):
    """Value of discharging ONE step.  Returns None if unavailable.

    The discharged kWh can either:
      - power the house, avoiding import at *import_price* (self-consumption),
        or
      - export to the grid, earning *export_price + bonus*.

    We take the **higher** of the two because the battery's power displaces
    whichever is more valuable at that minute.  In practice the import price
    (avoided cost) is usually the binding one for a home with base load.

    When no export rate is known the price is treated as 0 (conservative).
    When no import rate is known we fall back to export-only valuation.
    """
    if not allow_discharge:
        return None

    export_price = rate_at(export_rates, minute_epoch)
    if export_price is None:
        export_price = 0.0

    import_price = rate_at(import_rates, minute_epoch)
    if import_price is None:
        import_price = 0.0

    bonus = bonus_at(saving_bonus_events, minute_epoch)
    effective_price = max(import_price, export_price + bonus)

    if discharge_price_threshold is not None and effective_price < discharge_price_threshold:
        return None

    return effective_price * step_kwh


def no_opposite_adjacency(actions):
    """True if no 'charge'->'discharge' or 'discharge'->'charge' adjacent pair."""
    for i in range(len(actions) - 1):
        a, b = actions[i], actions[i + 1]
        if (a == "charge" and b == "discharge") or (a == "discharge" and b == "charge"):
            return False
    return True
